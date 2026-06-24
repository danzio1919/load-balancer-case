from fastapi import APIRouter, BackgroundTasks, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from services.simulation_service import start_simulation, run_simulation_task, clear_simulation_running
from db.database import get_db
from db.models import DBRun
from simulation_engine.strategy_registry import STRATEGY_MAP, get_strategy_names

router = APIRouter(prefix="/simulations", tags=["simulation"])

@router.get("/strategies")
def get_strategies():
    """
    Returns available scheduling strategies.
    """
    return [
        {"key": key, "display_name": display_name}
        for key, (_, display_name) in STRATEGY_MAP.items()
    ]

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def trigger_simulation(
    background_tasks: BackgroundTasks,
    strategy_name: str = "least_loaded_memory",
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers a simulation execution in the background if none is currently active.
    Immediately creates a DBRun row with status='processing' and returns 202.
    """
    if strategy_name not in get_strategy_names():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy name '{strategy_name}'. Valid strategies are: {', '.join(get_strategy_names())}"
        )

    # start_simulation raises SimulationRunningError if already active
    try:
        run_filename = start_simulation(strategy_name)
    except Exception as e:
        # Check if already running
        raise HTTPException(
            status_code=409,
            detail="A simulation is already in progress."
        )
    
    # Create the DB entry immediately with status="processing"
    created_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    db_run = DBRun(
        id=run_filename,
        status="processing",
        strategy_name=strategy_name,
        created_at=created_at,
        is_valid=False
    )
    
    try:
        db.add(db_run)
        await db.commit()
    except Exception as e:
        await db.rollback()
        # Clean up the in-memory lock if database fails
        clear_simulation_running()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize simulation record in database: {e}"
        )
    
    # Enqueue execution
    background_tasks.add_task(run_simulation_task, run_filename, strategy_name)
    
    return {
        "message": "Simulation run accepted and started in background.",
        "id": run_filename,
        "status": "processing"
    }

@router.get("")
async def get_simulation_runs(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a paginated list of past simulation runs.
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
        
    offset = (page - 1) * page_size
    
    total_count_query = select(func.count(DBRun.id))
    total_count_result = await db.execute(total_count_query)
    total = total_count_result.scalar() or 0
    
    runs_query = (
        select(DBRun)
        .order_by(DBRun.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    runs_result = await db.execute(runs_query)
    db_runs = runs_result.scalars().all()
    
    items = []
    for run in db_runs:
        items.append({
            "id": run.id,
            "status": run.status,
            "strategy_name": run.strategy_name or "least_loaded_memory",
            "is_valid": run.is_valid,
            "created_at": run.created_at,
            "system_throughput": run.system_throughput,
            "avg_turnaround_time": run.avg_turnaround_time,
            "overall_utilization": run.overall_utilization
        })
        
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{sim_id}")
async def get_simulation_status(sim_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the status and basic details of a specific simulation run.
    """
    result = await db.execute(select(DBRun).filter(DBRun.id == sim_id))
    db_run = result.scalars().first()
    
    if not db_run:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation '{sim_id}' not found."
        )
        
    return {
        "id": db_run.id,
        "status": db_run.status,
        "strategy_name": db_run.strategy_name or "least_loaded_memory",
        "created_at": db_run.created_at,
        "is_valid": db_run.is_valid
    }

@router.get("/{sim_id}/metrics")
async def get_simulation_metrics(sim_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches computed metrics for a specific simulation run by its ID.
    """
    result = await db.execute(select(DBRun).filter(DBRun.id == sim_id))
    db_run = result.scalars().first()
    
    if not db_run:
        raise HTTPException(
            status_code=404,
            detail=f"Metrics for run '{sim_id}' not found."
        )
        
    if db_run.status == "processing":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation '{sim_id}' is still processing. Metrics are not available yet."
        )
        
    if db_run.status == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation '{sim_id}' failed. Metrics are not available."
        )
        
    return {
        "id": db_run.id,
        "status": db_run.status,
        "strategy_name": db_run.strategy_name or "least_loaded_memory",
        "created_at": db_run.created_at,
        "is_valid": db_run.is_valid,
        "total_duration_ticks": db_run.total_duration_ticks,
        "system_throughput": db_run.system_throughput,
        "avg_turnaround_time": db_run.avg_turnaround_time,
        "avg_service_time": db_run.avg_service_time,
        "overall_utilization": db_run.overall_utilization,
        "overall_resource_efficiency": db_run.overall_resource_efficiency,
        "validation_output_log": db_run.validation_output_log,
        "server_metrics": [
            {
                "server_id": sm.server_id,
                "requests_handled": sm.requests_handled,
                "utilization_percent": sm.utilization_percent,
                "resource_efficiency_percent": sm.resource_efficiency_percent,
                "avg_service_time": sm.avg_service_time
            }
            for sm in db_run.server_metrics
        ]
    }
