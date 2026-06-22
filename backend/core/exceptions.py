from fastapi import Request
from fastapi.responses import JSONResponse

class ServerNotFoundError(Exception):
    def __init__(self, server_id: str):
        self.server_id = server_id
        super().__init__(f"Server with ID '{server_id}' not found.")

class SimulationRunningError(Exception):
    def __init__(self):
        super().__init__("Simulation is already running.")

class DuplicateServerError(Exception):
    def __init__(self, server_id: str):
        self.server_id = server_id
        super().__init__(f"Server with ID '{server_id}' already exists.")

async def server_not_found_handler(request: Request, exc: ServerNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "error_code": "SERVER_NOT_FOUND"}
    )

async def simulation_running_handler(request: Request, exc: SimulationRunningError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_code": "SIMULATION_RUNNING"}
    )

async def duplicate_server_handler(request: Request, exc: DuplicateServerError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_code": "DUPLICATE_SERVER"}
    )
