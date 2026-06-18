# Simulation Engine Specifications

## Overview
Design and implement a deterministic load balancer simulation using Python. The system must distribute incoming requests across heterogeneous servers (cluster) while respecting: CPU capacity, memory limits, and rate limits.

## Determinism
The simulation must be deterministic. Given the same:
- `servers.json`
- `requests.csv`
- configuration

The system must produce the same `run.jsonl` output. If multiple scheduling decisions are possible at the same tick, you must define and document a deterministic tie-breaking strategy.

## Provided Data
- **servers.json**: Defines the initial server configuration (`id`, `cpu_units_per_tick`, `mem_mb`, `rate_limit_per_sec`).
- **requests.csv**: Defines incoming requests over time (`t` arrival tick, `request_id`, `work_units`, `mem_mb`).

## Output: run.jsonl
Your simulation must generate a file named `run.jsonl` representing the full simulation trace. Each line must be a JSON object. Supported events:
- `REQUEST_ARRIVED`
- `REQUEST_STARTED`
- `REQUEST_FINISHED`
- `REQUEST_DROPPED` (optional)

## Load Balancer Engine
- Simulate discrete time (ticks). (1 tick = 1 second)
- Assign requests to servers.
- Respect CPU, memory, and rate constraints.
- Ensure no request runs on multiple servers simultaneously.
- Ensure deterministic execution.
- Requests that cannot be scheduled immediately may either queue or be dropped.
- You may choose your own scheduling strategy and rate limiting implementation.
- Events at time `t` describe the system state after processing tick `t-1` (or at the start of tick `t`).

## Execution Model
A server may execute multiple requests concurrently, as long as:
- Total reserved memory does not exceed `mem_mb`
- Per-tick CPU allocation does not exceed `cpu_units_per_tick`
- Rate limits are respected: `max REQUEST_STARTED events per server per tick <= rate_limit_per_sec`

Additionally:
- Memory is reserved for the full duration of a request's execution.
- At each tick, a server distributes its `cpu_units_per_tick` evenly across all currently running requests.
- A request's remaining work is reduced by its allocated CPU share each tick.
- A request finishes when its remaining work reaches zero or below.
- All CPU allocation and completion checks must occur in a deterministic order.
