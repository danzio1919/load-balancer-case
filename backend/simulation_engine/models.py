from dataclasses import dataclass, field
from typing import List

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
    active_requests: List[Request] = field(default_factory=list, init=False)
    started_this_tick: int = field(default=0, init=False)

    @property
    def current_memory_usage(self) -> float:
        return sum(req.mem_mb for req in self.active_requests)

    @property
    def available_memory(self) -> float:
        return self.mem_mb - self.current_memory_usage

    def can_accept(self, req: Request) -> bool:
        """
        Checks if the server can accept the request in the current tick.
        Ensures memory constraints and rate limits are respected.
        """
        if self.available_memory < req.mem_mb:
            return False
        if self.started_this_tick >= self.rate_limit_per_tick:
            return False
        return True

    def start_request(self, req: Request):
        """
        Starts executing a request on this server.
        """
        if not self.can_accept(req):
            raise ValueError(f"Server {self.id} cannot accept request {req.id} due to resource or rate limits.")
        self.active_requests.append(req)
        self.started_this_tick += 1

    def tick(self) -> List[Request]:
        """
        Simulates one tick of execution.
        Distributes CPU units evenly among active requests.
        Returns a list of requests that finished during this tick.
        """
        if not self.active_requests:
            return []

        finished_requests: List[Request] = []
        cpu_share = self.cpu_units_per_tick / len(self.active_requests)

        # Distribute CPU
        for req in self.active_requests:
            req.remaining_work -= cpu_share
            if req.remaining_work <= 1e-9: # Handle float inaccuracies
                finished_requests.append(req)

        # Remove finished requests
        for req in finished_requests:
            self.active_requests.remove(req)

        return finished_requests

    def reset_tick_limits(self):
        """
        Resets per-tick state such as started_this_tick.
        Should be called at the beginning of each tick.
        """
        self.started_this_tick = 0
