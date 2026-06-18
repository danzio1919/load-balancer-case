import unittest
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from simulation_engine.models import Request, Server

class TestRequestModel(unittest.TestCase):
    def test_request_initialization(self):
        req = Request(id="r1", arrival_t=0, work_units=20, mem_mb=200)
        self.assertEqual(req.id, "r1")
        self.assertEqual(req.arrival_t, 0)
        self.assertEqual(req.work_units, 20)
        self.assertEqual(req.mem_mb, 200)
        self.assertEqual(req.remaining_work, 20.0)


class TestServerModel(unittest.TestCase):
    def test_server_initialization(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=1024, rate_limit_per_tick=2)
        self.assertEqual(srv.id, "s1")
        self.assertEqual(srv.cpu_units_per_tick, 10)
        self.assertEqual(srv.mem_mb, 1024)
        self.assertEqual(srv.rate_limit_per_tick, 2)
        self.assertEqual(srv.active_requests, [])
        self.assertEqual(srv.started_this_tick, 0)

    def test_memory_tracking(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=1024, rate_limit_per_tick=2)
        self.assertEqual(srv.current_memory_usage, 0)
        self.assertEqual(srv.available_memory, 1024)

        req1 = Request(id="r1", arrival_t=0, work_units=20, mem_mb=200)
        srv.start_request(req1)
        self.assertEqual(srv.current_memory_usage, 200)
        self.assertEqual(srv.available_memory, 824)

        req2 = Request(id="r2", arrival_t=0, work_units=10, mem_mb=100)
        srv.start_request(req2)
        self.assertEqual(srv.current_memory_usage, 300)
        self.assertEqual(srv.available_memory, 724)

    def test_can_accept_memory_limit(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=300, rate_limit_per_tick=2)
        req1 = Request(id="r1", arrival_t=0, work_units=20, mem_mb=200)
        req2 = Request(id="r2", arrival_t=0, work_units=10, mem_mb=150)

        self.assertTrue(srv.can_accept(req1))
        srv.start_request(req1)

        # req2 requires 150MB, but only 100MB is available
        self.assertFalse(srv.can_accept(req2))
        with self.assertRaises(ValueError):
            srv.start_request(req2)

    def test_can_accept_rate_limit(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=1)
        req1 = Request(id="r1", arrival_t=0, work_units=20, mem_mb=100)
        req2 = Request(id="r2", arrival_t=0, work_units=10, mem_mb=100)

        self.assertTrue(srv.can_accept(req1))
        srv.start_request(req1)

        # Rate limit is 1 per tick, so we cannot accept req2 in this tick
        self.assertFalse(srv.can_accept(req2))
        with self.assertRaises(ValueError):
            srv.start_request(req2)

        # Reset tick limits should allow accepting new request
        srv.reset_tick_limits()
        self.assertTrue(srv.can_accept(req2))
        srv.start_request(req2)

    def test_single_request_tick_execution(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=1024, rate_limit_per_tick=2)
        req = Request(id="r1", arrival_t=0, work_units=25, mem_mb=200)

        srv.start_request(req)
        
        # Tick 1: reduces remaining work from 25 to 15
        finished = srv.tick()
        self.assertEqual(finished, [])
        self.assertEqual(req.remaining_work, 15.0)
        self.assertEqual(len(srv.active_requests), 1)

        # Tick 2: reduces remaining work from 15 to 5
        finished = srv.tick()
        self.assertEqual(finished, [])
        self.assertEqual(req.remaining_work, 5.0)

        # Tick 3: reduces remaining work from 5 to -5, should finish
        finished = srv.tick()
        self.assertEqual(finished, [req])
        self.assertEqual(req.remaining_work, -5.0)
        self.assertEqual(srv.active_requests, [])

    def test_concurrent_requests_tick_execution(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=1024, rate_limit_per_tick=2)
        req1 = Request(id="r1", arrival_t=0, work_units=10, mem_mb=200)
        req2 = Request(id="r2", arrival_t=0, work_units=15, mem_mb=200)

        srv.start_request(req1)
        srv.start_request(req2)

        # CPU units per tick = 10. Divides evenly: 5 units per request.
        # Tick 1: req1 remaining 10 -> 5. req2 remaining 15 -> 10.
        finished = srv.tick()
        self.assertEqual(finished, [])
        self.assertEqual(req1.remaining_work, 5.0)
        self.assertEqual(req2.remaining_work, 10.0)

        # Tick 2: cpu share is still 5.
        # req1 remaining 5 -> 0 (finishes). req2 remaining 10 -> 5.
        finished = srv.tick()
        self.assertEqual(finished, [req1])
        self.assertEqual(req2.remaining_work, 5.0)
        self.assertEqual(srv.active_requests, [req2])

        # Tick 3: Only req2 is active, gets full 10 CPU units.
        # req2 remaining 5 -> -5 (finishes).
        finished = srv.tick()
        self.assertEqual(finished, [req2])
        self.assertEqual(srv.active_requests, [])


if __name__ == '__main__':
    unittest.main()
