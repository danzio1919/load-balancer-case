import os
import json
import csv
import math
import sys
import subprocess
import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
from core.config import settings
from core.logging import get_logger
from sqlalchemy import select
from db.database import SessionLocal
from db.models import DBRun, DBServerMetric

logger = get_logger(__name__)

async def save_metrics_to_db(run_id: str, system_metrics: dict, server_metrics: list):
    """
    Saves the computed metrics to the SQLite database using an async session.
    """
    async with SessionLocal() as db:
        try:
            result = await db.execute(select(DBRun).filter(DBRun.id == run_id))
            db_run = result.scalars().first()
            
            if not db_run:
                db_run = DBRun(id=run_id)
                db.add(db_run)
                
            db_run.status = "completed"
            db_run.strategy_name = system_metrics.get("strategy_name")
            db_run.created_at = system_metrics.get("created_at")
            db_run.is_valid = system_metrics["is_valid"]
            db_run.total_duration_ticks = system_metrics["total_duration_ticks"]
            db_run.system_throughput = system_metrics["system_throughput"]
            db_run.avg_turnaround_time = system_metrics["avg_turnaround_time"]
            db_run.avg_service_time = system_metrics["avg_service_time"]
            db_run.overall_utilization = system_metrics["overall_utilization"]
            db_run.overall_resource_efficiency = system_metrics["overall_resource_efficiency"]
            db_run.validation_output_log = system_metrics["validation_output_log"]
            
            for sm in server_metrics:
                db_sm = DBServerMetric(
                    run_id=run_id,
                    server_id=sm["server_id"],
                    requests_handled=sm["requests_handled"],
                    utilization_percent=sm["utilization_percent"],
                    resource_efficiency_percent=sm["resource_efficiency_percent"],
                    avg_service_time=sm["avg_service_time"]
                )
                db.add(db_sm)
                
            await db.commit()
            logger.info(f"Successfully saved metrics to DB for run_id: {run_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save metrics to database for run_id {run_id}: {e}", exc_info=True)
            raise

async def set_run_failed(run_id: str):
    """Sets the status of a run to failed in the database."""
    async with SessionLocal() as db:
        try:
            result = await db.execute(select(DBRun).filter(DBRun.id == run_id))
            db_run = result.scalars().first()
            if db_run:
                db_run.status = "failed"
                await db.commit()
                logger.info(f"Set status of run {run_id} to failed")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to set run {run_id} to failed: {e}", exc_info=True)

def _extract_created_at(run_id: str) -> Optional[str]:
    """Extracts ISO timestamp from the run filename/id."""
    match = re.search(r"run_(\d{8})_(\d{6})", run_id)
    if match:
        date_str, time_str = match.groups()
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as te:
            logger.error(f"Failed to parse datetime from run_id {run_id}: {te}")
    return None

def _load_servers_spec() -> dict:
    """Loads and returns server specifications from servers.json."""
    servers_path = Path(settings.SERVERS_PATH)
    servers = {}
    if servers_path.exists():
        try:
            with open(servers_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for s in data.get("servers", []):
                servers[s["id"]] = {
                    "id": s["id"],
                    "cpu_units_per_tick": float(s["cpu_units_per_tick"]),
                    "mem_mb": float(s["mem_mb"]),
                    "rate_limit_per_sec": int(s["rate_limit_per_sec"])
                }
        except Exception as e:
            logger.error(f"Error loading servers.json for metrics: {e}")
    return servers

def _load_requests_spec() -> dict:
    """Loads and returns request specifications from requests.csv."""
    requests_path = Path(settings.REQUESTS_PATH)
    requests = {}
    if requests_path.exists():
        try:
            with open(requests_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rid = row["request_id"].strip()
                    requests[rid] = {
                        "id": rid,
                        "arrival_t": int(row["t"]),
                        "work_units": float(row["work_units"]),
                        "mem_mb": float(row["mem_mb"])
                    }
        except Exception as e:
            logger.error(f"Error loading requests.csv for metrics: {e}")
    return requests

def _load_events(run_path: Path) -> list:
    """Loads JSONL events from the simulation output file."""
    events = []
    try:
        with open(run_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                events.append(json.loads(line))
    except Exception as e:
        logger.error(f"Error loading run file {run_path} for metrics: {e}")
    return events

def _parse_request_lifecycles(events: list) -> Tuple[dict, int]:
    """Parses event logs to reconstruct request lifecycles and find max tick duration."""
    req_lifecycle = {}
    t_max = 0
    for ev in events:
        t = ev.get("t", 0)
        if t > t_max:
            t_max = t
        rid = ev.get("request_id")
        if not rid:
            continue
        if rid not in req_lifecycle:
            req_lifecycle[rid] = {
                "arrival_t": None,
                "start_t": None,
                "finish_t": None,
                "dropped_t": None,
                "server_id": None
            }
        event_type = ev.get("event")
        if event_type == "REQUEST_ARRIVED":
            req_lifecycle[rid]["arrival_t"] = t
        elif event_type == "REQUEST_STARTED":
            req_lifecycle[rid]["start_t"] = t
            req_lifecycle[rid]["server_id"] = ev.get("server_id")
        elif event_type == "REQUEST_FINISHED":
            req_lifecycle[rid]["finish_t"] = t
            req_lifecycle[rid]["server_id"] = ev.get("server_id")
        elif event_type == "REQUEST_DROPPED":
            req_lifecycle[rid]["dropped_t"] = t
    return req_lifecycle, t_max

def _compute_system_metrics(req_lifecycle: dict, requests: dict, total_duration_ticks: int) -> Tuple[float, float, float]:
    """Computes average turnaround time, average service time, and throughput."""
    finished_reqs = [r for r in req_lifecycle.values() if r["finish_t"] is not None and r["start_t"] is not None]
    
    turnaround_times = []
    service_times = []
    for rid, r in req_lifecycle.items():
        if r["finish_t"] is not None and r["start_t"] is not None:
            arr_t = r["arrival_t"]
            if arr_t is None and rid in requests:
                arr_t = requests[rid]["arrival_t"]
            if arr_t is not None:
                turnaround_times.append(r["finish_t"] - arr_t)
            service_times.append(r["finish_t"] - r["start_t"])
            
    avg_turnaround_time = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0.0
    avg_service_time = sum(service_times) / len(service_times) if service_times else 0.0
    system_throughput = len(finished_reqs) / total_duration_ticks if total_duration_ticks > 0 else 0.0
    
    return avg_turnaround_time, avg_service_time, system_throughput

def _compute_server_metrics(req_lifecycle: dict, requests: dict, servers: dict, total_duration_ticks: int) -> Tuple[list, float, float]:
    """Computes per-server metrics along with overall system utilization and efficiency."""
    server_metrics_data = {}
    for sid, s in servers.items():
        server_metrics_data[sid] = {
            "server_id": sid,
            "requests_handled": 0,
            "total_busy_ticks": 0,
            "total_service_time": 0,
            "total_work_units": 0.0,
            "total_active_capacity": 0.0
        }

    for rid, r in req_lifecycle.items():
        if r["finish_t"] is not None and r["start_t"] is not None:
            sid = r["server_id"]
            if not sid:
                continue
            if sid not in server_metrics_data:
                server_metrics_data[sid] = {
                    "server_id": sid,
                    "requests_handled": 0,
                    "total_busy_ticks": 0,
                    "total_service_time": 0,
                    "total_work_units": 0.0,
                    "total_active_capacity": 0.0
                }
            
            runtime_ticks = r["finish_t"] - r["start_t"]
            server_metrics_data[sid]["requests_handled"] += 1
            server_metrics_data[sid]["total_busy_ticks"] += runtime_ticks
            server_metrics_data[sid]["total_service_time"] += runtime_ticks
            
            work_units = 0.0
            if rid in requests:
                work_units = requests[rid]["work_units"]
            
            cpu_units = 1.0
            if sid in servers:
                cpu_units = servers[sid]["cpu_units_per_tick"]
                
            server_metrics_data[sid]["total_work_units"] += work_units
            server_metrics_data[sid]["total_active_capacity"] += (runtime_ticks * cpu_units)

    server_metrics_list = []
    for sid, sm in server_metrics_data.items():
        avg_st = sm["total_service_time"] / sm["requests_handled"] if sm["requests_handled"] > 0 else 0.0
        util_pct = (sm["total_busy_ticks"] / total_duration_ticks * 100) if total_duration_ticks > 0 else 0.0
        eff_pct = (sm["total_work_units"] / sm["total_active_capacity"] * 100) if sm["total_active_capacity"] > 0 else 0.0
        
        server_metrics_list.append({
            "server_id": sid,
            "requests_handled": sm["requests_handled"],
            "utilization_percent": round(util_pct, 2),
            "resource_efficiency_percent": round(eff_pct, 2),
            "avg_service_time": round(avg_st, 2)
        })

    overall_utilization = sum(sm["utilization_percent"] for sm in server_metrics_list) / len(server_metrics_list) if server_metrics_list else 0.0
    
    total_system_work = sum(sm["total_work_units"] for sm in server_metrics_data.values())
    total_system_capacity = sum(sm["total_active_capacity"] for sm in server_metrics_data.values())
    overall_resource_efficiency = (total_system_work / total_system_capacity * 100) if total_system_capacity > 0 else 0.0

    return server_metrics_list, overall_utilization, overall_resource_efficiency

def _run_validator(run_path: Path) -> Tuple[bool, str]:
    """Executes the external validation script validate_run.py."""
    validation_output_log = ""
    is_valid = False
    try:
        root_dir = Path(settings.SERVERS_PATH).parent
        validator_path = root_dir / "validate_run.py"
        cmd = [
            sys.executable,
            str(validator_path),
            "--servers", settings.SERVERS_PATH,
            "--requests", settings.REQUESTS_PATH,
            "--run", str(run_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        validation_output_log = res.stdout + "\n" + res.stderr
        is_valid = (res.returncode == 0)
    except Exception as e:
        logger.error(f"Error running validate_run.py: {e}")
        validation_output_log = f"Failed to execute validate_run.py: {e}"
        is_valid = False
    return is_valid, validation_output_log

def calculate_and_save_metrics(run_id: str, strategy_name: str):
    """
    Parses files, runs validate_run.py, calculates metrics, and triggers DB save.
    """
    logger.info(f"Calculating metrics for run_id: {run_id} using strategy: {strategy_name}")
    
    created_at = _extract_created_at(run_id)
    
    run_path = Path(settings.RUNS_DIR) / run_id
    if not run_path.exists():
        logger.error(f"Run file not found at {run_path}. Cannot calculate metrics.")
        return
        
    servers = _load_servers_spec()
    requests = _load_requests_spec()
    events = _load_events(run_path)
    
    if not events:
        logger.error(f"No events loaded from run file {run_path}. Aborting metric calculation.")
        return
        
    req_lifecycle, total_duration_ticks = _parse_request_lifecycles(events)
    
    avg_turnaround_time, avg_service_time, system_throughput = _compute_system_metrics(
        req_lifecycle, requests, total_duration_ticks
    )
    
    server_metrics_list, overall_utilization, overall_resource_efficiency = _compute_server_metrics(
        req_lifecycle, requests, servers, total_duration_ticks
    )
    
    is_valid, validation_output_log = _run_validator(run_path)
    
    system_metrics = {
        "strategy_name": strategy_name,
        "created_at": created_at,
        "is_valid": is_valid,
        "total_duration_ticks": total_duration_ticks,
        "system_throughput": round(system_throughput, 4),
        "avg_turnaround_time": round(avg_turnaround_time, 2),
        "avg_service_time": round(avg_service_time, 2),
        "overall_utilization": round(overall_utilization, 2),
        "overall_resource_efficiency": round(overall_resource_efficiency, 2),
        "validation_output_log": validation_output_log
    }

    # Save to DB (using asyncio.run since we are in a sync background thread)
    asyncio.run(save_metrics_to_db(run_id, system_metrics, server_metrics_list))
