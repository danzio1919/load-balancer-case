from sqlalchemy import Column, String, Float, Integer
from db.database import Base

class DBServer(Base):
    __tablename__ = "servers"

    id = Column(String, primary_key=True, index=True)
    cpu_units_per_tick = Column(Float, nullable=False)
    mem_mb = Column(Float, nullable=False)
    rate_limit_per_sec = Column(Integer, nullable=False)
