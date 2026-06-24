from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from core.exceptions import (
    ServerNotFoundError,
    SimulationRunningError,
    DuplicateServerError,
    server_not_found_handler,
    simulation_running_handler,
    duplicate_server_handler
)
from services.sync_service import seed_db_from_json, cleanup_stale_runs
from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Seed database from servers.json and clean up stale runs
    logger.info("Application starting up. Seeding SQLite database and cleaning up stale runs...")
    await seed_db_from_json()
    await cleanup_stale_runs()
    yield
    # Shutdown
    logger.info("Application shutting down.")

app = FastAPI(
    title="Load Balancer Simulation API",
    description="Backend API for managing cluster servers and running load balancer simulations.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Register custom exception handlers
app.add_exception_handler(ServerNotFoundError, server_not_found_handler)
app.add_exception_handler(SimulationRunningError, simulation_running_handler)
app.add_exception_handler(DuplicateServerError, duplicate_server_handler)

# Include API routes
app.include_router(api_router)

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}
