from pydantic import BaseModel, Field

class ServerBase(BaseModel):
    cpu_units_per_tick: float = Field(..., gt=0, description="CPU units processed per simulation tick")
    mem_mb: float = Field(..., gt=0, description="Memory limit in megabytes")
    rate_limit_per_sec: int = Field(..., gt=0, description="Maximum requests started per second")

class ServerCreate(ServerBase):
    id: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-]+$", description="Unique identifier for the server")

class ServerUpdate(BaseModel):
    cpu_units_per_tick: float | None = Field(None, gt=0)
    mem_mb: float | None = Field(None, gt=0)
    rate_limit_per_sec: int | None = Field(None, gt=0)

class ServerResponse(ServerBase):
    id: str

    model_config = {
        "from_attributes": True
    }
