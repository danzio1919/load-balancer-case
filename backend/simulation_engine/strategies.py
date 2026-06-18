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
