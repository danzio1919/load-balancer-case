#!/usr/bin/env python3
"""
run_simulation.py  --  Run a simulation scenario and optionally validate it.

Usage:
    ./run_simulation.py <scenario>

    <scenario>  Name of a folder under scenarios/ (e.g. case1, case2, ...).
                Reads  scenarios/<scenario>/servers.json
                        scenarios/<scenario>/requests.csv
                Writes scenarios/<scenario>/run.jsonl

Examples:
    ./run_simulation.py case1
    ./run_simulation.py case2
"""

import sys
import os
import json
import csv
import subprocess
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from simulation_engine.models import Request, Server
from simulation_engine.engine import SimulationEngine


def load_servers(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    servers = []
    for s in data.get("servers", []):
        servers.append(Server(
            id=s["id"],
            cpu_units_per_tick=float(s["cpu_units_per_tick"]),
            mem_mb=float(s["mem_mb"]),
            rate_limit_per_tick=int(s["rate_limit_per_sec"])
        ))
    return servers


def load_requests(path: Path) -> list:
    requests = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            requests.append(Request(
                id=row["request_id"].strip(),
                arrival_t=int(row["t"]),
                work_units=float(row["work_units"]),
                mem_mb=float(row["mem_mb"])
            ))
    return requests


def main():
    if len(sys.argv) < 2:
        # Fallback to root configuration if no scenario argument is provided
        root_dir = Path(__file__).parent
        servers_path  = root_dir / "servers.json"
        requests_path = root_dir / "requests.csv"
        output_path   = root_dir / "run.jsonl"
        print("\n=== Scenario: Root Configuration ===")
    else:
        scenario = sys.argv[1]
        scenario_dir = Path(__file__).parent / "scenarios" / scenario

        if not scenario_dir.is_dir():
            print(f"Error: scenario '{scenario}' not found at {scenario_dir}")
            print("       Available scenarios:", list_scenarios())
            sys.exit(1)

        servers_path  = scenario_dir / "servers.json"
        requests_path = scenario_dir / "requests.csv"
        output_path   = scenario_dir / "run.jsonl"
        print(f"\n=== Scenario: {scenario} ===")

    print(f"  servers  : {servers_path}")
    print(f"  requests : {requests_path}")
    print(f"  output   : {output_path}\n")

    if not servers_path.exists():
        print(f"Error: servers file not found at {servers_path}")
        sys.exit(1)
    if not requests_path.exists():
        print(f"Error: requests file not found at {requests_path}")
        sys.exit(1)

    servers  = load_servers(servers_path)
    requests = load_requests(requests_path)
    print(f"Loaded {len(servers)} server(s), {len(requests)} request(s).")

    engine = SimulationEngine(servers=servers, requests=requests)
    engine.run(str(output_path))
    print(f"Simulation completed in {engine.current_tick} tick(s).")

    # Auto-validate with validate_run.py if it exists
    validator = Path(__file__).parent / "validate_run.py"
    if validator.exists():
        print("\nRunning validator...")
        result = subprocess.run(
            [sys.executable, str(validator),
             "--servers", str(servers_path),
             "--requests", str(requests_path),
             "--run", str(output_path)],
            capture_output=False
        )
        sys.exit(result.returncode)


def list_scenarios() -> list:
    scenarios_dir = Path(__file__).parent / "scenarios"
    if not scenarios_dir.is_dir():
        return []
    return sorted(d.name for d in scenarios_dir.iterdir() if d.is_dir())


if __name__ == "__main__":
    main()
