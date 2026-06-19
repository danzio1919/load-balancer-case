from dataclasses import dataclass, field
from typing import List, Optional
import math

@dataclass
class Request:
    id: str
    arrival_t: int
    work_units: float
    mem_mb: float
    remaining_work: float = field(init=False)

    def __post_init__(self):
        self.remaining_work = float(self.work_units)


@dataclass
class Server:
    id: str
    cpu_units_per_tick: float
    mem_mb: float
    rate_limit_per_tick: int
    active_request: Optional[Request] = field(default=None, init=False)
    remaining_ticks: int = field(default=0, init=False)
    started_this_tick: int = field(default=0, init=False)

    @property
    def current_memory_usage(self) -> float:
        return self.active_request.mem_mb if self.active_request else 0.0

    @property
    def available_memory(self) -> float:
        return self.mem_mb - self.current_memory_usage

    def can_accept(self, req: Request) -> bool:
        """
        Checks if the server can accept the request in the current tick.
        Ensures memory constraints and rate limits are respected.
        """
        if self.active_request is not None:
            return False
        # Unreachable, but kept for backward compatibility
        if self.available_memory < req.mem_mb:
            return False
        # Unreachable, but kept for backward compatibility
        if self.started_this_tick >= self.rate_limit_per_tick:
            return False
        return True

    def start_request(self, req: Request):
        """
        Starts executing a request on this server.
        """
        if not self.can_accept(req):
            raise ValueError(f"Server {self.id} cannot accept request {req.id} due to resource or rate limits.")
        self.active_request = req
        self.remaining_ticks = math.ceil(req.work_units / self.cpu_units_per_tick)
        self.started_this_tick += 1

    def tick(self) -> List[Request]:
        """
        Simulates one tick of execution.
        Returns a list of requests that finished during this tick.
        """
        if self.active_request is None:
            return []

        self.remaining_ticks -= 1
        if self.remaining_ticks <= 0:
            finished = self.active_request
            self.active_request = None
            return [finished]

        return []

    def reset_tick_limits(self):
        """
        Resets per-tick state such as started_this_tick.
        Should be called at the beginning of each tick.
        """
        self.started_this_tick = 0
