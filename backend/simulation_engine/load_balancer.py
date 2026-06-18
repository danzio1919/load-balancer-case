from typing import Dict, List, Tuple, Optional
from simulation_engine.models import Request, Server
from simulation_engine.strategies import SchedulingStrategy, LeastLoadedMemoryStrategy

class LoadBalancer:
    def __init__(self, strategy: Optional[SchedulingStrategy] = None):
        """
        Initializes the Load Balancer.
        Allows injecting a custom SchedulingStrategy, defaulting to LeastLoadedMemoryStrategy.
        """
        self.servers: Dict[str, Server] = {}
        self.strategy: SchedulingStrategy = strategy or LeastLoadedMemoryStrategy()
        self.queue: List[Request] = []

    def add_server(self, server: Server):
        """
        Adds a server to the load balancer's cluster.
        """
        self.servers[server.id] = server

    def remove_server(self, server_id: str):
        """
        Removes a server from the load balancer's cluster.
        """
        if server_id in self.servers:
            del self.servers[server_id]

    def receive_request(self, request: Request):
        """
        Queues an incoming request in the FIFO queue.
        """
        self.queue.append(request)

    def tick_schedule(self) -> List[Tuple[Request, Server]]:
        """
        Attempts to schedule queued requests on available servers in FIFO order.
        
        To prevent head-of-line blocking and maximize throughput, if a request cannot
        be scheduled, it is skipped and remains in the queue, while the load balancer
        continues attempting to schedule subsequent requests in the queue.
        
        Returns:
            List[Tuple[Request, Server]]: A list of (Request, Server) pairs representing
                                          requests successfully scheduled in this tick.
        """
        scheduled: List[Tuple[Request, Server]] = []
        remaining_queue: List[Request] = []

        # Sort servers by ID to ensure input determinism for strategies
        server_list = sorted(self.servers.values(), key=lambda s: s.id)

        for req in self.queue:
            selected_server = self.strategy.select_server(req, server_list)
            if selected_server is not None:
                selected_server.start_request(req)
                scheduled.append((req, selected_server))
            else:
                remaining_queue.append(req)

        self.queue = remaining_queue
        return scheduled
