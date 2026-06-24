from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from fastapi import Query

class StrategyResponse(BaseModel):
    key: str
    display_name: str

class SimulationTriggerRequest(BaseModel):
    strategy_name: str = Field(default="least_loaded_memory", description="The name of the scheduling strategy to use")

class SimulationTriggerResponse(BaseModel):
    message: str
    id: str
    status: str

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number, starts at 1")
    page_size: int = Field(default=10, ge=1, description="Number of items per page")

class SimulationRunResponse(BaseModel):
    id: str
    status: str
    strategy_name: str
    is_valid: bool
    created_at: Optional[str] = None
    system_throughput: Optional[float] = None
    avg_turnaround_time: Optional[float] = None
    overall_utilization: Optional[float] = None

    model_config = {
        "from_attributes": True
    }

class PaginatedSimulationResponse(BaseModel):
    items: List[SimulationRunResponse]
    total: int
    page: int
    page_size: int

class ServerMetricResponse(BaseModel):
    server_id: str
    requests_handled: int
    utilization_percent: float
    resource_efficiency_percent: float
    avg_service_time: float

    model_config = {
        "from_attributes": True
    }

class SimulationMetricsResponse(SimulationRunResponse):
    total_duration_ticks: Optional[int] = None
    avg_service_time: Optional[float] = None
    overall_resource_efficiency: Optional[float] = None
    validation_output_log: Optional[str] = None
    server_metrics: List[ServerMetricResponse] = []

    model_config = {
        "from_attributes": True
    }
