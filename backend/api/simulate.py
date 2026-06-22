from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse

from services.simulation_service import start_simulation, run_simulation_task, get_simulation_status

router = APIRouter(tags=["simulation"])

@router.post("/simulate", status_code=status.HTTP_202_ACCEPTED)
def trigger_simulation(background_tasks: BackgroundTasks):
    """
    Triggers a simulation execution in the background if none is currently active.
    Returns 202 Accepted with the target output filename.
    """
    # This checks running state, raises SimulationRunningError if already active,
    # otherwise marks as running and generates the filename.
    run_filename = start_simulation()
    
    # Enqueue execution
    background_tasks.add_task(run_simulation_task, run_filename)
    
    return {
        "message": "Simulation run accepted and started in background.",
        "run_file": run_filename,
        "status": "processing"
    }

@router.get("/simulate/status")
def check_simulation_status():
    """Checks the current simulation execution state."""
    is_running = get_simulation_status()
    return {
        "status": "running" if is_running else "idle",
        "is_running": is_running
    }
