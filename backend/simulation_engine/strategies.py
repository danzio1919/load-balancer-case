from abc import ABC, abstractmethod
from typing import List, Optional
from simulation_engine.models import Request, Server

class SchedulingStrategy(ABC):
    @abstractmethod
    def select_server(self, request: Request, servers: List[Server]) -> Optional[Server]:
        """
        Selects a server for the given request from a list of servers.
        Returns None if no server can accept the request.
        """
        pass


class LeastLoadedMemoryStrategy(SchedulingStrategy):
    def select_server(self, request: Request, servers: List[Server]) -> Optional[Server]:
        """
        Selects the server with the lowest memory usage percentage.
        Ties are broken alphabetically by server.id for determinism.
        """
        # Filter out servers that cannot accept the request
        available_servers = [s for s in servers if s.can_accept(request)]
        if not available_servers:
            return None

        # Sort by memory usage percentage ascending, then by server ID alphabetically ascending
        available_servers.sort(
            key=lambda s: (
                (s.current_memory_usage / s.mem_mb) if s.mem_mb > 0 else 0.0,
                s.id
            )
        )

        return available_servers[0]


class RoundRobinStrategy(SchedulingStrategy):
    def __init__(self):
        self.last_server_id: Optional[str] = None

    def select_server(self, request: Request, servers: List[Server]) -> Optional[Server]:
        """
        Selects a server cyclically starting from the one after the last scheduled server.
        """
        if not servers:
            return None

        start_idx = 0
        if self.last_server_id is not None:
            for i, s in enumerate(servers):
                if s.id == self.last_server_id:
                    start_idx = (i + 1) % len(servers)
                    break

        n = len(servers)
        for i in range(n):
            idx = (start_idx + i) % n
            server = servers[idx]
            if server.can_accept(request):
                self.last_server_id = server.id
                return server

        return None


class BestFitStrategy(SchedulingStrategy):
    def select_server(self, request: Request, servers: List[Server]) -> Optional[Server]:
        """
        Selects the server that finishes the job as quickly as possible, using the least
        amount of excess power, memory, and breaking ties using server ID.
        """
        available_servers = [s for s in servers if s.can_accept(request)]
        if not available_servers:
            return None

        # Sort by:
        # 1. Minimize Runtime: (work_units + cpu - 1) // cpu (ascending)
        # 2. Minimize CPU Waste: cpu (ascending)
        # 3. Minimize RAM Waste: mem_mb (ascending)
        # 4. Tie-Breaker: id (ascending)
        available_servers.sort(
            key=lambda s: (
                (int(request.work_units) + int(s.cpu_units_per_tick) - 1) // int(s.cpu_units_per_tick),
                s.cpu_units_per_tick,
                s.mem_mb,
                s.id
            )
        )

        return available_servers[0]

