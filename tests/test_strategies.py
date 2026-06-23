import unittest
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from simulation_engine.models import Request, Server
from simulation_engine.strategies import (
    LeastLoadedMemoryStrategy,
    RoundRobinStrategy,
    BestFitStrategy,
)

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


class TestRoundRobinStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = RoundRobinStrategy()

    def test_standard_round_robin(self):
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s2 = Server(id="s2", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s3 = Server(id="s3", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)

        req = Request(id="r1", arrival_t=0, work_units=5, mem_mb=100)

        # First request should pick the first server
        selected = self.strategy.select_server(req, [s1, s2, s3])
        self.assertEqual(selected, s1)

        # Second request should pick the second server
        selected = self.strategy.select_server(req, [s1, s2, s3])
        self.assertEqual(selected, s2)

        # Third request should pick the third server
        selected = self.strategy.select_server(req, [s1, s2, s3])
        self.assertEqual(selected, s3)

        # Fourth request should wrap back to the first server
        selected = self.strategy.select_server(req, [s1, s2, s3])
        self.assertEqual(selected, s1)

    def test_skip_busy_server(self):
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s2 = Server(id="s2", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s3 = Server(id="s3", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)

        # Make s2 busy
        s2.start_request(Request(id="dummy", arrival_t=0, work_units=10, mem_mb=10))

        req = Request(id="r1", arrival_t=0, work_units=5, mem_mb=100)

        # 1. First choice: s1
        selected = self.strategy.select_server(req, [s1, s2, s3])
        self.assertEqual(selected, s1)

        # 2. Second choice: s2 is busy, so it should skip s2 and select s3
        selected = self.strategy.select_server(req, [s1, s2, s3])
        self.assertEqual(selected, s3)

        # 3. Third choice: since last selected was s3, cyclic search from next index is s1
        selected = self.strategy.select_server(req, [s1, s2, s3])
        self.assertEqual(selected, s1)

    def test_no_servers_available(self):
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s1.start_request(Request(id="dummy", arrival_t=0, work_units=10, mem_mb=10))

        req = Request(id="r1", arrival_t=0, work_units=5, mem_mb=100)
        selected = self.strategy.select_server(req, [s1])
        self.assertIsNone(selected)


class TestBestFitStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = BestFitStrategy()

    def test_minimize_runtime(self):
        # s1: 10 units/tick -> runtime 1 for 10 units
        # s2: 5 units/tick -> runtime 2 for 10 units
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s2 = Server(id="s2", cpu_units_per_tick=5, mem_mb=1000, rate_limit_per_tick=5)

        req = Request(id="r1", arrival_t=0, work_units=10, mem_mb=100)
        selected = self.strategy.select_server(req, [s2, s1])
        self.assertEqual(selected, s1)

    def test_minimize_cpu_waste(self):
        # Request needs 5 work units.
        # s1: 10 units/tick -> runtime = ceil(5/10) = 1
        # s2: 5 units/tick -> runtime = ceil(5/5) = 1
        # Both servers finish in 1 tick, but s2 has smaller CPU (5 vs 10).
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s2 = Server(id="s2", cpu_units_per_tick=5, mem_mb=1000, rate_limit_per_tick=5)

        req = Request(id="r1", arrival_t=0, work_units=5, mem_mb=100)
        selected = self.strategy.select_server(req, [s1, s2])
        self.assertEqual(selected, s2)

    def test_minimize_ram_waste(self):
        # Both have cpu=10, but s2 has smaller RAM (500 vs 1000).
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s2 = Server(id="s2", cpu_units_per_tick=10, mem_mb=500, rate_limit_per_tick=5)

        req = Request(id="r1", arrival_t=0, work_units=5, mem_mb=100)
        selected = self.strategy.select_server(req, [s1, s2])
        self.assertEqual(selected, s2)

    def test_tie_breaker(self):
        # Identical specs, should break tie alphabetically by id.
        s_b = Server(id="s_b", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s_a = Server(id="s_a", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)

        req = Request(id="r1", arrival_t=0, work_units=5, mem_mb=100)
        selected = self.strategy.select_server(req, [s_b, s_a])
        self.assertEqual(selected, s_a)

    def test_ceiling_division_runtime_tie(self):
        # Request: 11 work units.
        # s1: cpu=10 -> runtime = ceil(11/10) = 2.
        # s2: cpu=6 -> runtime = ceil(11/6) = 2.
        # Both take 2 ticks, but s2 has smaller CPU (6 vs 10).
        s1 = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=5)
        s2 = Server(id="s2", cpu_units_per_tick=6, mem_mb=1000, rate_limit_per_tick=5)

        req = Request(id="r1", arrival_t=0, work_units=11, mem_mb=100)
        selected = self.strategy.select_server(req, [s1, s2])
        self.assertEqual(selected, s2)


if __name__ == '__main__':
    unittest.main()

