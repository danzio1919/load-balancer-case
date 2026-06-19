import unittest
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from simulation_engine.models import Request, Server
from simulation_engine.load_balancer import LoadBalancer
from simulation_engine.strategies import SchedulingStrategy

class MockStrategy(SchedulingStrategy):
    def __init__(self, force_server=None):
        self.force_server = force_server
        self.called_with = []

    def select_server(self, request, servers):
        self.called_with.append((request, servers))
        return self.force_server


class TestLoadBalancer(unittest.TestCase):
    def test_registry_management(self):
        lb = LoadBalancer()
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s2 = Server(id="s2", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)

        lb.add_server(s1)
        lb.add_server(s2)
        self.assertEqual(len(lb.servers), 2)
        self.assertIn("s1", lb.servers)
        self.assertIn("s2", lb.servers)

        lb.remove_server("s1")
        self.assertEqual(len(lb.servers), 1)
        self.assertNotIn("s1", lb.servers)
        self.assertIn("s2", lb.servers)

    def test_receive_request_queues(self):
        lb = LoadBalancer()
        req = Request(id="r1", arrival_t=0, work_units=10, mem_mb=100)
        lb.receive_request(req)
        self.assertEqual(lb.queue, [req])

    def test_tick_schedule_success(self):
        lb = LoadBalancer()
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        lb.add_server(s1)

        req = Request(id="r1", arrival_t=0, work_units=10, mem_mb=100)
        lb.receive_request(req)

        scheduled = lb.tick_schedule()
        self.assertEqual(scheduled, [(req, s1)])
        self.assertEqual(lb.queue, [])
        self.assertEqual(s1.active_request, req)

    def test_head_of_line_blocking_skipping(self):
        lb = LoadBalancer()
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=100, rate_limit_per_tick=2)
        lb.add_server(s1)

        # req1 requires 200MB (s1 has only 100MB)
        # req2 requires 50MB (s1 can fit this)
        req1 = Request(id="r1", arrival_t=0, work_units=10, mem_mb=200)
        req2 = Request(id="r2", arrival_t=0, work_units=10, mem_mb=50)

        lb.receive_request(req1)
        lb.receive_request(req2)

        # Scheduling should skip req1 and schedule req2
        scheduled = lb.tick_schedule()
        
        self.assertEqual(scheduled, [(req2, s1)])
        self.assertEqual(lb.queue, [req1])
        self.assertEqual(s1.active_request, req2)

    def test_custom_strategy_injection(self):
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        mock_strategy = MockStrategy(force_server=s1)
        lb = LoadBalancer(strategy=mock_strategy)
        lb.add_server(s1)

        req = Request(id="r1", arrival_t=0, work_units=10, mem_mb=100)
        lb.receive_request(req)

        scheduled = lb.tick_schedule()
        self.assertEqual(scheduled, [(req, s1)])
        self.assertEqual(len(mock_strategy.called_with), 1)
        self.assertEqual(mock_strategy.called_with[0][0], req)
        self.assertEqual(mock_strategy.called_with[0][1], [s1])


if __name__ == '__main__':
    unittest.main()
