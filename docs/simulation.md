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
A server executes requests **non-concurrently** (one request per server at a time):
- **No Overlapping Runs**: A server can only process exactly one request at a time. It cannot start a new request until the currently running request is fully finished.
- **Resource Dedication**: The running request uses the server's full `cpu_units_per_tick` capacity.
- **Runtime Calculation**: A request's total execution time in ticks is calculated as `ceil(work_units / cpu_units_per_tick)`.
- **Memory Check**: A server can only accept a request if its `mem_mb` is sufficient (`request.mem_mb <= server.mem_mb`).
- **Rate Limits**: The rate limit constraint (`max REQUEST_STARTED events per server per tick <= rate_limit_per_sec`) is satisfied inherently by the non-overlap constraint, as a server starts at most 1 request per tick.

Additionally:
- All checks must occur in a deterministic order.
