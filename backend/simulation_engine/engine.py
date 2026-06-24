import heapq
import json
import os
from typing import List, Tuple, Optional
from simulation_engine.models import Request, Server
from simulation_engine.load_balancer import LoadBalancer

EVENT_PRECEDENCE = {
    "REQUEST_FINISHED": 1,
    "REQUEST_ARRIVED": 2,
    "REQUEST_STARTED": 3,
    "REQUEST_DROPPED": 4
}

class SimulationEngine:
    def __init__(self, servers: List[Server], requests: List[Request], strategy=None):
        """
        Initializes the Simulation Engine.
        
        Args:
            servers: List of servers to register with the load balancer.
            requests: List of requests to simulate.
            strategy: Optional scheduling strategy to use.
        """
        self.load_balancer = LoadBalancer(strategy=strategy)
        for server in servers:
            self.load_balancer.add_server(server)
            
        # Requests in a min heap
        self.request_heap = []
        for req in requests:
            heapq.heappush(self.request_heap, (req.arrival_t, req.id, req))
            
        self.current_tick = 0
        self.finished_in_previous_tick: List[Tuple[Request, Server]] = []

    def run(self, output_filepath: str):
        """
        Runs the simulation until all requests are processed and all servers are idle.
        Writes the simulation trace to the specified output file in JSONL format.
        
        Args:
            output_filepath: Path to write the run.jsonl trace.
        """
        dir_name = os.path.dirname(output_filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(output_filepath, "w", encoding="utf-8") as f:
            while True:
                tick_events = []
                
                # 1. Process Finishes
                # Emit REQUEST_FINISHED for anything in finished_in_previous_tick.
                for req, srv in self.finished_in_previous_tick:
                    tick_events.append({
                        "t": self.current_tick,
                        "event": "REQUEST_FINISHED",
                        "request_id": req.id,
                        "server_id": srv.id
                    })
                self.finished_in_previous_tick.clear()
                
                # 2. Process Arrivals
                # Find all requests arriving at current_tick, emit REQUEST_ARRIVED,
                # and call load_balancer.receive_request(req).
                while self.request_heap and self.request_heap[0][0] <= self.current_tick:
                    arrival_t, req_id, req = heapq.heappop(self.request_heap)
                    tick_events.append({
                        "t": self.current_tick,
                        "event": "REQUEST_ARRIVED",
                        "request_id": req.id
                    })
                    self.load_balancer.receive_request(req)
                    
                # 3. Reset Rate Limits
                # Iterate through all servers (sorted by ID) and call server.reset_tick_limits().
                # Rate limits are obsolete but kept for backward compatibility
                sorted_servers = sorted(self.load_balancer.servers.values(), key=lambda s: s.id)
                for srv in sorted_servers:
                    srv.reset_tick_limits()
                    
                # 4. Schedule
                # Drop inherently unsatisfiable requests (e.g. req.mem_mb > max server capacity)
                max_server_mem = max((srv.mem_mb for srv in self.load_balancer.servers.values()), default=0.0)
                unsatisfiable_requests = []
                remaining_queue = []
                for req in self.load_balancer.queue:
                    if req.mem_mb > max_server_mem:
                        unsatisfiable_requests.append(req)
                    else:
                        remaining_queue.append(req)
                self.load_balancer.queue = remaining_queue
                
                for req in unsatisfiable_requests:
                    tick_events.append({
                        "t": self.current_tick,
                        "event": "REQUEST_DROPPED",
                        "request_id": req.id
                    })

                # Call load_balancer.tick_schedule() and emit REQUEST_STARTED for successfully scheduled pairs.
                scheduled_pairs = self.load_balancer.tick_schedule()
                for req, srv in scheduled_pairs:
                    tick_events.append({
                        "t": self.current_tick,
                        "event": "REQUEST_STARTED",
                        "request_id": req.id,
                        "server_id": srv.id
                    })
                    
                # 5. Emit Events
                # Sort all events generated in steps 1-4 deterministically and write them to the JSONL file.
                # Sorting key: type precedence (FINISHED -> ARRIVED -> STARTED), then request_id.
                tick_events.sort(
                    key=lambda ev: (EVENT_PRECEDENCE.get(ev["event"], 99), ev["request_id"])
                )
                
                for ev in tick_events:
                    f.write(json.dumps(ev) + "\n")
                f.flush()
                
                # 6. Check Termination
                # Break if no more arrivals in heap, load balancer queue is empty,
                # servers are idle, and no finished requests are buffered.
                heap_empty = len(self.request_heap) == 0
                queue_empty = len(self.load_balancer.queue) == 0
                servers_idle = all(srv.active_request is None for srv in self.load_balancer.servers.values())
                finished_empty = len(self.finished_in_previous_tick) == 0
                
                if heap_empty and queue_empty and servers_idle and finished_empty:
                    break
                    
                # 7. Execute Tick
                # Iterate through all servers (sorted by ID) and call server.tick().
                # Append returned completed requests to finished_in_previous_tick.
                for srv in sorted_servers:
                    finished_reqs = srv.tick()
                    for req in finished_reqs:
                        self.finished_in_previous_tick.append((req, srv))
                        
                # 8. Increment current_tick
                self.current_tick += 1
