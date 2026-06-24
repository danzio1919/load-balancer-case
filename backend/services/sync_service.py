import json
import os
import asyncio
import aiofiles
from sqlalchemy import select, delete
from core.config import settings
from core.logging import get_logger
from db.models import DBServer, DBRun
from db.database import SessionLocal, engine, Base

logger = get_logger(__name__)
_sync_lock = asyncio.Lock()

async def cleanup_stale_runs():
    """
    Finds any simulation runs with status='processing' and marks them as 'failed'
    since they are stale across server restarts.
    """
    async with SessionLocal() as db:
        try:
            result = await db.execute(select(DBRun).filter(DBRun.status == "processing"))
            stale_runs = result.scalars().all()
            if stale_runs:
                for run in stale_runs:
                    run.status = "failed"
                await db.commit()
                logger.info(f"Cleaned up {len(stale_runs)} stale 'processing' runs to 'failed'")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error cleaning up stale runs: {e}", exc_info=True)

async def seed_db_from_json():
    """
    Reads servers.json and seeds SQLite.
    Creates tables if they don't exist.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    if not os.path.exists(settings.SERVERS_PATH):
        logger.warning(f"servers.json not found at {settings.SERVERS_PATH}. Skipping seeding.")
        return
        
    async with SessionLocal() as db:
        try:
            async with aiofiles.open(settings.SERVERS_PATH, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
            
            servers_data = data.get("servers", [])
            
            # Clear existing using SQLAlchemy 2.0 delete query
            await db.execute(delete(DBServer))
            
            for s in servers_data:
                db_server = DBServer(
                    id=s["id"],
                    cpu_units_per_tick=float(s["cpu_units_per_tick"]),
                    mem_mb=float(s["mem_mb"]),
                    rate_limit_per_sec=int(s["rate_limit_per_sec"])
                )
                db.add(db_server)
                
            await db.commit()
            logger.info(f"Successfully seeded DB with {len(servers_data)} servers from {settings.SERVERS_PATH}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error seeding database from json: {e}", exc_info=True)

async def sync_db_to_json():
    """
    Serializes current SQLite database state and overwrites servers.json.
    Runs inside a lock to prevent concurrent write conflicts.
    """
    async with _sync_lock:
        async with SessionLocal() as db:
            try:
                result = await db.execute(select(DBServer))
                db_servers = result.scalars().all()
                
                # Read existing tick_seconds to preserve it, default to 1
                tick_seconds = 1
                if os.path.exists(settings.SERVERS_PATH):
                    try:
                        async with aiofiles.open(settings.SERVERS_PATH, "r", encoding="utf-8") as f:
                            content = await f.read()
                            existing_data = json.loads(content)
                            tick_seconds = existing_data.get("tick_seconds", 1)
                    except Exception:
                        pass
                
                servers_list = []
                for s in db_servers:
                    cpu = int(s.cpu_units_per_tick) if s.cpu_units_per_tick.is_integer() else s.cpu_units_per_tick
                    mem = int(s.mem_mb) if s.mem_mb.is_integer() else s.mem_mb
                    
                    servers_list.append({
                        "id": s.id,
                        "cpu_units_per_tick": cpu,
                        "mem_mb": mem,
                        "rate_limit_per_sec": int(s.rate_limit_per_sec)
                    })
                    
                out_data = {
                    "tick_seconds": tick_seconds,
                    "servers": servers_list
                }
                
                # Write atomically using a temp file
                temp_path = f"{settings.SERVERS_PATH}.tmp"
                async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(out_data, indent=2))
                    
                os.replace(temp_path, settings.SERVERS_PATH)
                logger.info(f"Successfully synced DB state to {settings.SERVERS_PATH} ({len(servers_list)} servers)")
            except Exception as e:
                logger.error(f"Error syncing database to JSON: {e}", exc_info=True)
