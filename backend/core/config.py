import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):

    DATABASE_URL: str = f"sqlite+aiosqlite:///{BACKEND_DIR}/data/cluster.db"
    
    SERVERS_PATH: str = str(ROOT_DIR / "servers.json")
    REQUESTS_PATH: str = str(ROOT_DIR / "requests.csv")
    
    RUNS_DIR: str = str(ROOT_DIR / "runs")
    RUN_JSONL_PATH: str = str(ROOT_DIR / "run.jsonl")

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]


    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
