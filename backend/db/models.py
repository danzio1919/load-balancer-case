from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class DBServer(Base):
    __tablename__ = "servers"

    id = Column(String, primary_key=True, index=True)
    cpu_units_per_tick = Column(Integer, nullable=False)
    mem_mb = Column(Integer, nullable=False)
    rate_limit_per_sec = Column(Integer, nullable=False)

class DBRun(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False, default="processing")
    strategy_name = Column(String, nullable=True)
    created_at = Column(String, nullable=True)
    is_valid = Column(Boolean, nullable=False, default=False)
    total_duration_ticks = Column(Integer, nullable=True)
    system_throughput = Column(Float, nullable=True)
    avg_turnaround_time = Column(Float, nullable=True)
    avg_service_time = Column(Float, nullable=True)
    overall_utilization = Column(Float, nullable=True)
    overall_resource_efficiency = Column(Float, nullable=True)
    validation_output_log = Column(String, nullable=True)

    server_metrics = relationship("DBServerMetric", back_populates="run", cascade="all, delete-orphan", lazy="selectin")

class DBServerMetric(Base):
    __tablename__ = "run_server_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    server_id = Column(String, nullable=False)
    requests_handled = Column(Integer, nullable=False)
    utilization_percent = Column(Float, nullable=False)
    resource_efficiency_percent = Column(Float, nullable=False)
    avg_service_time = Column(Float, nullable=False)

    run = relationship("DBRun", back_populates="server_metrics")

