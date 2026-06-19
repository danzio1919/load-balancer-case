import unittest
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from simulation_engine.models import Request, Server
from simulation_engine.strategies import LeastLoadedMemoryStrategy

class TestLeastLoadedMemoryStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = LeastLoadedMemoryStrategy()

    def test_filter_out_servers(self):
        # s1: busy processing a dummy request
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s1.start_request(Request(id="dummy", arrival_t=0, work_units=10, mem_mb=10))

        # s2: idle, but doesn't have enough memory for the request (100MB capacity, request needs 200MB)
        s2 = Server(id="s2", cpu_units_per_tick=10, mem_mb=100, rate_limit_per_tick=5)

        # s3: idle, but rate limit is hit for this tick (rate limit = 0 means can't accept)
        s3 = Server(id="s3", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=0)

        # s4: idle, has room, rate limit allowed -> should be selected
        s4 = Server(id="s4", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)

        req = Request(id="test_req", arrival_t=0, work_units=5, mem_mb=200)

        selected = self.strategy.select_server(req, [s1, s2, s3, s4])
        self.assertEqual(selected, s4)

    def test_deterministic_tie_breaker(self):
        # s_b and s_a both have 0% load and can accept the request
        s_b = Server(id="s_b", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s_a = Server(id="s_a", cpu_units_per_tick=10, mem_mb=500, rate_limit_per_tick=5)

        req = Request(id="test_req", arrival_t=0, work_units=5, mem_mb=100)

        # alphabetical order: s_a before s_b
        selected = self.strategy.select_server(req, [s_b, s_a])
        self.assertEqual(selected, s_a)

    def test_no_servers_available(self):
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=100, rate_limit_per_tick=1)
        s1.start_request(Request(id="dummy", arrival_t=0, work_units=10, mem_mb=100))

        req = Request(id="test_req", arrival_t=0, work_units=5, mem_mb=50)

        # s1 has 0 available memory and is busy
        selected = self.strategy.select_server(req, [s1])
        self.assertIsNone(selected)


if __name__ == '__main__':
    unittest.main()
