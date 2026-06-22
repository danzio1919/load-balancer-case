from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DBServer
from schemas.server import ServerCreate, ServerUpdate
from core.exceptions import ServerNotFoundError, DuplicateServerError

async def get_servers(db: AsyncSession) -> List[DBServer]:
    """Retrieves all servers from SQLite database."""
    result = await db.execute(select(DBServer))
    return list(result.scalars().all())

async def get_server(db: AsyncSession, server_id: str) -> DBServer:
    """Retrieves a single server by its ID. Raises ServerNotFoundError if not found."""
    result = await db.execute(select(DBServer).filter(DBServer.id == server_id))
    db_server = result.scalars().first()
    if not db_server:
        raise ServerNotFoundError(server_id)
    return db_server

async def create_server(db: AsyncSession, server: ServerCreate) -> DBServer:
    """Creates a new server. Raises DuplicateServerError if server ID exists."""
    result = await db.execute(select(DBServer).filter(DBServer.id == server.id))
    existing = result.scalars().first()
    if existing:
        raise DuplicateServerError(server.id)
        
    db_server = DBServer(
        id=server.id,
        cpu_units_per_tick=server.cpu_units_per_tick,
        mem_mb=server.mem_mb,
        rate_limit_per_sec=server.rate_limit_per_sec
    )
    try:
        db.add(db_server)
        await db.commit()
        await db.refresh(db_server)
    except Exception:
        await db.rollback()
        raise
        
    return db_server

async def update_server(db: AsyncSession, server_id: str, server_update: ServerUpdate) -> DBServer:
    """Updates an existing server. Raises ServerNotFoundError if not found."""
    result = await db.execute(select(DBServer).filter(DBServer.id == server_id))
    db_server = result.scalars().first()
    if not db_server:
        raise ServerNotFoundError(server_id)
        
    update_data = server_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_server, key, value)
        
    try:
        await db.commit()
        await db.refresh(db_server)
    except Exception:
        await db.rollback()
        raise
        
    return db_server

async def delete_server(db: AsyncSession, server_id: str) -> None:
    """Deletes a server from the DB. Raises ServerNotFoundError if not found."""
    result = await db.execute(select(DBServer).filter(DBServer.id == server_id))
    db_server = result.scalars().first()
    if not db_server:
        raise ServerNotFoundError(server_id)
        
    try:
        await db.delete(db_server)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
