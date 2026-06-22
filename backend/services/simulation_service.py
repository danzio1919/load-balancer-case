import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import threading
from core.config import settings
from core.logging import get_logger
from core.exceptions import SimulationRunningError
from simulation_engine.models import Request, Server
from simulation_engine.engine import SimulationEngine

logger = get_logger(__name__)

# State management for simulation execution
_state_lock = threading.Lock()
_is_running = False

def get_simulation_status() -> bool:
    """Returns True if a simulation run is currently in progress."""
    with _state_lock:
        return _is_running

def start_simulation() -> str:
    """
    Checks if a simulation is running, raises SimulationRunningError if so.
    Otherwise sets the running state to True and returns the target run filename.
    """
    global _is_running
    with _state_lock:
        if _is_running:
            raise SimulationRunningError()
        _is_running = True
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"run_{timestamp}.jsonl"

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

def run_simulation_task(run_filename: str):
    """
    Synchronous task that runs the simulation, writes output to timestamped run
    and copies it to run.jsonl. Clears running state when done.
    """
    try:
        logger.info(f"Starting simulation run. Target file: {run_filename}")
        
        servers_path = Path(settings.SERVERS_PATH)
        requests_path = Path(settings.REQUESTS_PATH)
        runs_dir = Path(settings.RUNS_DIR)
        run_jsonl_path = Path(settings.RUN_JSONL_PATH)
        
        # Verify inputs exist
        if not servers_path.exists():
            logger.error(f"Cannot run simulation: servers file not found at {servers_path}")
            return
        if not requests_path.exists():
            logger.error(f"Cannot run simulation: requests file not found at {requests_path}")
            return
            
        runs_dir.mkdir(parents=True, exist_ok=True)
        timestamped_run_path = runs_dir / run_filename
        
        # Load inputs
        servers = load_servers(servers_path)
        requests = load_requests(requests_path)
        
        logger.info(f"Loaded {len(servers)} servers and {len(requests)} requests for simulation.")
        
        # Execute engine
        engine = SimulationEngine(servers=servers, requests=requests)
        engine.run(str(timestamped_run_path))
        
        # Copy to run.jsonl 
        shutil.copy2(timestamped_run_path, run_jsonl_path)
        
        logger.info(f"Simulation run completed successfully. Outputs saved to {timestamped_run_path} and {run_jsonl_path}")
    except Exception as e:
        logger.error(f"Simulation failed with error: {e}", exc_info=True)
    finally:
        clear_simulation_running()
