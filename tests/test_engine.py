import unittest
import sys
import os
import json
import tempfile

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from simulation_engine.models import Request, Server
from simulation_engine.engine import SimulationEngine


class TestSimulationEngine(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for test run files
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_path = os.path.join(self.test_dir.name, "run.jsonl")

    def tearDown(self):
        self.test_dir.cleanup()

    def read_events(self) -> list:
        events = []
        with open(self.output_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return events

    def test_single_request_lifecycle(self):
        # 1 Server: CPU 10, Mem 1024, Rate Limit 2
        # 1 Request: Arrives 0, Work 25, Mem 200
        # Expected execution:
        # t=0: ARRIVED(r1), STARTED(r1 on s1)
        # s1.tick() runs, reduces remaining_work to 15
        # t=1: no new events. s1.tick() runs, reduces remaining_work to 5
        # t=2: no new events. s1.tick() runs, reduces remaining_work to -5 (finishes)
        # t=3: FINISHED(r1 on s1), then terminates
        servers = [Server(id="s1", cpu_units_per_tick=10.0, mem_mb=1024.0, rate_limit_per_tick=2)]
        requests = [Request(id="r1", arrival_t=0, work_units=25.0, mem_mb=200.0)]

        engine = SimulationEngine(servers=servers, requests=requests)
        engine.run(self.output_path)

        events = self.read_events()

        expected_events = [
            {"t": 0, "event": "REQUEST_ARRIVED", "request_id": "r1"},
            {"t": 0, "event": "REQUEST_STARTED", "request_id": "r1", "server_id": "s1"},
            {"t": 3, "event": "REQUEST_FINISHED", "request_id": "r1", "server_id": "s1"}
        ]
        self.assertEqual(events, expected_events)
        self.assertEqual(engine.current_tick, 3)

    def test_sequential_request_execution_and_queuing(self):
        # 1 Server: CPU 10, Mem 1000, Rate limit 5
        # 2 Requests arriving at t=0:
        # r1: work 10, mem 200 (runs for 1 tick)
        # r2: work 15, mem 200 (runs for 2 ticks)
        # Under the non-concurrent model:
        # Tick 0:
        #   t=0: ARRIVED(r1), ARRIVED(r2).
        #   s1 is idle, so it starts r1. r2 is queued (head-of-line blocking / queuing).
        #   s1.remaining_ticks = ceil(10 / 10) = 1.
        #   s1.tick() runs, reduces remaining_ticks to 0.
        #   Finished in tick 0: [r1] (buffered in finished_in_previous_tick)
        # Tick 1:
        #   t=1: starts with FINISHED(r1) event.
        #   s1 is now free.
        #   s1 starts r2.
        #   s1.remaining_ticks = ceil(15 / 10) = 2.
        #   s1.tick() runs, reduces remaining_ticks to 1.
        # Tick 2:
        #   t=2: no new events.
        #   s1.tick() runs, reduces remaining_ticks to 0.
        #   Finished in tick 2: [r2]
        # Tick 3:
        #   t=3: starts with FINISHED(r2) event.
        #   Loop breaks.
        servers = [Server(id="s1", cpu_units_per_tick=10.0, mem_mb=1000.0, rate_limit_per_tick=5)]
        requests = [
            Request(id="r1", arrival_t=0, work_units=10.0, mem_mb=200.0),
            Request(id="r2", arrival_t=0, work_units=15.0, mem_mb=200.0)
        ]

        engine = SimulationEngine(servers=servers, requests=requests)
        engine.run(self.output_path)

        events = self.read_events()

        # Expected events:
        expected_events = [
            {"t": 0, "event": "REQUEST_ARRIVED", "request_id": "r1"},
            {"t": 0, "event": "REQUEST_ARRIVED", "request_id": "r2"},
            {"t": 0, "event": "REQUEST_STARTED", "request_id": "r1", "server_id": "s1"},
            {"t": 1, "event": "REQUEST_FINISHED", "request_id": "r1", "server_id": "s1"},
            {"t": 1, "event": "REQUEST_STARTED", "request_id": "r2", "server_id": "s1"},
            {"t": 3, "event": "REQUEST_FINISHED", "request_id": "r2", "server_id": "s1"}
        ]
        self.assertEqual(events, expected_events)

    def test_event_sorting_within_tick(self):
        # We want to verify that when FINISHED, ARRIVED, and STARTED events occur
        # in the same tick, they are output in the correct sorted order:
        # FINISHED -> ARRIVED -> STARTED, then request_id alphabetically.
        # Let's arrange a scenario:
        # s1: CPU 10, Mem 1000, Rate Limit 5
        # s2: CPU 10, Mem 1000, Rate Limit 5
        # r_old: Arrives t=0, work 10, mem 100. Schedules at t=0 on s1, runs for 1 tick, finishes at t=1.
        # r_new1: Arrives t=1, work 5, mem 100. Schedules at t=1.
        # r_new2: Arrives t=1, work 5, mem 100. Schedules at t=1.
        # At t=1:
        # - REQUEST_FINISHED for r_old
        # - REQUEST_ARRIVED for r_new1, r_new2
        # - REQUEST_STARTED for r_new1, r_new2
        # Since we have two servers (s1 now idle, s2 idle), both r_new1 and r_new2 can schedule.
        # The expected output order for t=1 events must be:
        # 1. FINISHED r_old
        # 2. ARRIVED r_new1
        # 3. ARRIVED r_new2
        # 4. STARTED r_new1
        # 5. STARTED r_new2
        servers = [
            Server(id="s1", cpu_units_per_tick=10.0, mem_mb=1000.0, rate_limit_per_tick=5),
            Server(id="s2", cpu_units_per_tick=10.0, mem_mb=1000.0, rate_limit_per_tick=5)
        ]
        requests = [
            Request(id="r_old", arrival_t=0, work_units=10.0, mem_mb=100.0),
            # Add them out of alphabetical order to verify ID sorting too
            Request(id="r_new2", arrival_t=1, work_units=5.0, mem_mb=100.0),
            Request(id="r_new1", arrival_t=1, work_units=5.0, mem_mb=100.0)
        ]

        engine = SimulationEngine(servers=servers, requests=requests)
        engine.run(self.output_path)

        events = self.read_events()

        # Let's filter for t=1 events
        t1_events = [ev for ev in events if ev["t"] == 1]

        expected_t1_events = [
            {"t": 1, "event": "REQUEST_FINISHED", "request_id": "r_old", "server_id": "s1"},
            {"t": 1, "event": "REQUEST_ARRIVED", "request_id": "r_new1"},
            {"t": 1, "event": "REQUEST_ARRIVED", "request_id": "r_new2"},
            {"t": 1, "event": "REQUEST_STARTED", "request_id": "r_new1", "server_id": "s1"},
            {"t": 1, "event": "REQUEST_STARTED", "request_id": "r_new2", "server_id": "s2"}
        ]
        self.assertEqual(t1_events, expected_t1_events)

    def test_out_of_order_input_requests(self):
        # Requests are passed in non-chronological order of arrival_t:
        # r3 (t=2), r1 (t=0), r2 (t=1).
        # The min-heap should sort them and they should arrive in chronological order.
        servers = [Server(id="s1", cpu_units_per_tick=10.0, mem_mb=1000.0, rate_limit_per_tick=5)]
        requests = [
            Request(id="r3", arrival_t=2, work_units=5.0, mem_mb=100.0),
            Request(id="r1", arrival_t=0, work_units=5.0, mem_mb=100.0),
            Request(id="r2", arrival_t=1, work_units=5.0, mem_mb=100.0)
        ]

        engine = SimulationEngine(servers=servers, requests=requests)
        engine.run(self.output_path)

        events = self.read_events()

        # Let's check the arrival ticks
        arrivals = [ev for ev in events if ev["event"] == "REQUEST_ARRIVED"]
        expected_arrivals = [
            {"t": 0, "event": "REQUEST_ARRIVED", "request_id": "r1"},
            {"t": 1, "event": "REQUEST_ARRIVED", "request_id": "r2"},
            {"t": 2, "event": "REQUEST_ARRIVED", "request_id": "r3"}
        ]
        self.assertEqual(arrivals, expected_arrivals)

    def test_unsatisfiable_request_dropped(self):
        # 1 Server with 100MB Memory
        # 1 Request requiring 200MB Memory
        # It should be dropped, emitting REQUEST_ARRIVED and REQUEST_DROPPED.
        servers = [Server(id="s1", cpu_units_per_tick=10.0, mem_mb=100.0, rate_limit_per_tick=2)]
        requests = [Request(id="r_large", arrival_t=0, work_units=25.0, mem_mb=200.0)]

        engine = SimulationEngine(servers=servers, requests=requests)
        engine.run(self.output_path)

        events = self.read_events()
        expected_events = [
            {"t": 0, "event": "REQUEST_ARRIVED", "request_id": "r_large"},
            {"t": 0, "event": "REQUEST_DROPPED", "request_id": "r_large"}
        ]
        self.assertEqual(events, expected_events)
        self.assertEqual(engine.current_tick, 0)


if __name__ == '__main__':
    unittest.main()
