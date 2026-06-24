import csv
import json
import os
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
import threading
from core.config import settings
from core.logging import get_logger
from core.exceptions import SimulationRunningError
from simulation_engine.models import Request, Server
from simulation_engine.engine import SimulationEngine
from simulation_engine.strategy_registry import get_strategy
from services.metrics_service import calculate_and_save_metrics, set_run_failed

logger = get_logger(__name__)

# State management for simulation execution
_state_lock = threading.Lock()
_is_running = False
_latest_run_file = None

def get_simulation_status() -> bool:
    """Returns True if a simulation run is currently in progress."""
    with _state_lock:
        return _is_running

def get_latest_run_file() -> str:
    """Returns the filename of the latest simulation run."""
    with _state_lock:
        return _latest_run_file

def start_simulation(strategy_name: str = "least_loaded_memory") -> str:
    """
    Checks if a simulation is running, raises SimulationRunningError if so.
    Otherwise sets the running state to True and returns the target run filename.
    """
    global _is_running, _latest_run_file
    with _state_lock:
        if _is_running:
            raise SimulationRunningError()
        _is_running = True
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    _latest_run_file = f"run_{timestamp}.jsonl"
    return _latest_run_file

def clear_simulation_running():
    """Resets the running state to False."""
    global _is_running
    with _state_lock:
        _is_running = False

def load_servers(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    servers = []
    for s in data.get("servers", []):
        servers.append(Server(
            id=s["id"],
            cpu_units_per_tick=float(s["cpu_units_per_tick"]),
            mem_mb=float(s["mem_mb"]),
            rate_limit_per_tick=int(s["rate_limit_per_sec"])
        ))
    return servers

def load_requests(path: Path) -> list:
    requests = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            requests.append(Request(
                id=row["request_id"].strip(),
                arrival_t=int(row["t"]),
                work_units=float(row["work_units"]),
                mem_mb=float(row["mem_mb"])
            ))
    return requests

def run_simulation_task(run_filename: str, strategy_name: str = "least_loaded_memory"):
    """
    Synchronous task that runs the simulation, writes output to timestamped run
    and copies it to run.jsonl. Clears running state when done.
    """
    try:
        logger.info(f"Starting simulation run with strategy '{strategy_name}'. Target file: {run_filename}")
        
        servers_path = Path(settings.SERVERS_PATH)
        requests_path = Path(settings.REQUESTS_PATH)
        runs_dir = Path(settings.RUNS_DIR)
        run_jsonl_path = Path(settings.RUN_JSONL_PATH)
        
        # Verify inputs exist
        if not servers_path.exists():
            logger.error(f"Cannot run simulation: servers file not found at {servers_path}")
            asyncio.run(set_run_failed(run_filename))
            return
        if not requests_path.exists():
            logger.error(f"Cannot run simulation: requests file not found at {requests_path}")
            asyncio.run(set_run_failed(run_filename))
            return
            
        runs_dir.mkdir(parents=True, exist_ok=True)
        timestamped_run_path = runs_dir / run_filename
        
        # Load inputs
        servers = load_servers(servers_path)
        requests = load_requests(requests_path)
        
        logger.info(f"Loaded {len(servers)} servers and {len(requests)} requests for simulation.")
        
        # Execute engine
        strategy = get_strategy(strategy_name)
        engine = SimulationEngine(servers=servers, requests=requests, strategy=strategy)
        engine.run(str(timestamped_run_path))
        
        # Copy to run.jsonl 
        shutil.copy2(timestamped_run_path, run_jsonl_path)
        
        logger.info(f"Simulation run completed successfully. Outputs saved to {timestamped_run_path} and {run_jsonl_path}")

        # Calculate and save metrics to DB
        try:
            calculate_and_save_metrics(run_filename, strategy_name)
        except Exception as em:
            logger.error(f"Failed to compute/save metrics: {em}", exc_info=True)
            asyncio.run(set_run_failed(run_filename))
    except Exception as e:
        logger.error(f"Simulation failed with error: {e}", exc_info=True)
        asyncio.run(set_run_failed(run_filename))
    finally:
        clear_simulation_running()
