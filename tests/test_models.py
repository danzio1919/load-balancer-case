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
        self.assertIsNone(srv.active_request)
        self.assertEqual(srv.started_this_tick, 0)
        self.assertEqual(srv.remaining_ticks, 0)

    def test_memory_tracking_and_busy_state(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=1024, rate_limit_per_tick=2)
        self.assertEqual(srv.current_memory_usage, 0)
        self.assertEqual(srv.available_memory, 1024)

        req1 = Request(id="r1", arrival_t=0, work_units=20, mem_mb=200)
        srv.start_request(req1)
        self.assertEqual(srv.current_memory_usage, 200)
        self.assertEqual(srv.available_memory, 824)
        self.assertEqual(srv.active_request, req1)

        # Attempting to start another request while busy must raise ValueError
        req2 = Request(id="r2", arrival_t=0, work_units=10, mem_mb=100)
        self.assertFalse(srv.can_accept(req2))
        with self.assertRaises(ValueError):
            srv.start_request(req2)

    def test_can_accept_memory_limit(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=150, rate_limit_per_tick=2)
        req1 = Request(id="r1", arrival_t=0, work_units=20, mem_mb=200)

        # req1 exceeds capacity of srv (200MB > 150MB)
        self.assertFalse(srv.can_accept(req1))
        with self.assertRaises(ValueError):
            srv.start_request(req1)

    def test_can_accept_rate_limit(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=1000, rate_limit_per_tick=1)
        req1 = Request(id="r1", arrival_t=0, work_units=20, mem_mb=100)

        # Start req1
        self.assertTrue(srv.can_accept(req1))
        srv.start_request(req1)

        # Complete req1 in tick execution so server is not busy
        srv.tick() # remaining_ticks calculated as ceil(20/10) = 2. After 1 tick: 1 remaining.
        srv.tick() # after 2nd tick: 0 remaining. srv.active_request becomes None.
        self.assertIsNone(srv.active_request)

        # Rate limit per tick is 1. We already started 1 request this tick.
        # So even if server is now idle, it cannot accept req2 in the same tick.
        req2 = Request(id="r2", arrival_t=0, work_units=10, mem_mb=100)
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
        # ceil(25 / 10) = 3 ticks
        self.assertEqual(srv.remaining_ticks, 3)
        self.assertEqual(srv.active_request, req)

        # Tick 1: reduces remaining ticks from 3 to 2
        finished = srv.tick()
        self.assertEqual(finished, [])
        self.assertEqual(srv.remaining_ticks, 2)
        self.assertEqual(srv.active_request, req)

        # Tick 2: reduces remaining ticks from 2 to 1
        finished = srv.tick()
        self.assertEqual(finished, [])
        self.assertEqual(srv.remaining_ticks, 1)

        # Tick 3: reduces remaining ticks from 1 to 0, should finish
        finished = srv.tick()
        self.assertEqual(finished, [req])
        self.assertEqual(srv.remaining_ticks, 0)
        self.assertIsNone(srv.active_request)

    def test_remaining_ticks_exact_ceil(self):
        srv = Server(id="s1", cpu_units_per_tick=10, mem_mb=1024, rate_limit_per_tick=2)

        # work units = 20, cpu = 10 -> ceil(20 / 10) = 2 ticks exactly
        req1 = Request(id="r1", arrival_t=0, work_units=20, mem_mb=100)
        srv.start_request(req1)
        self.assertEqual(srv.remaining_ticks, 2)

        finished = srv.tick()
        self.assertEqual(finished, [])
        finished = srv.tick()
        self.assertEqual(finished, [req1])


if __name__ == '__main__':
    unittest.main()
