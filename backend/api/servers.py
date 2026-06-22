from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.database import get_db
from schemas.server import ServerCreate, ServerUpdate, ServerResponse
from services import server_service
from services.sync_service import sync_db_to_json

router = APIRouter(tags=["servers"])

@router.get("/servers", response_model=List[ServerResponse])
async def get_servers(db: AsyncSession = Depends(get_db)):
    """Retrieves all servers from SQLite database."""
    return await server_service.get_servers(db)

@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(server_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves a single server by its ID."""
    return await server_service.get_server(db, server_id)

@router.post("/servers", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server: ServerCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Creates a new server, saving it to DB and syncing back to servers.json."""
    db_server = await server_service.create_server(db, server)
    background_tasks.add_task(sync_db_to_json)
    return db_server

@router.put("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: str,
    server_update: ServerUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Updates an existing server, updating the DB and syncing back to servers.json."""
    db_server = await server_service.update_server(db, server_id, server_update)
    background_tasks.add_task(sync_db_to_json)
    return db_server

@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Deletes a server from the DB and triggers a background sync to servers.json."""
    await server_service.delete_server(db, server_id)
    background_tasks.add_task(sync_db_to_json)
    return

