# System Design Document

This document outlines the architecture, scheduling strategies, rate-limiting constraints, assumptions, and development tooling for the Load Balancer Simulation.

## System Architecture

The application is split into three main components:

1.  **Frontend Dashboard (React, TypeScript, Vite):** Provides a UI to manage the cluster's servers (CRUD operations), select scheduling strategies, and trigger/monitor simulation runs.
2.  **Backend API (FastAPI, SQLite):**
    - Exposes endpoints for server CRUD operations and simulation execution.
    - **Persistence Sync:** A local SQLite database is used to handle concurrent API requests safely. On any database write, a background task synchronizes the updated server list back to the project's root `servers.json` file.
    - **Async execution:** Simulation requests return a `202 Accepted` immediately, running the simulation engine as a background thread.
3.  **Simulation Engine (Python):** Operates as a discrete-time engine executing scheduled simulations tick-by-tick and writing output events to `run.jsonl`.

---

## Scheduling Strategies

The load balancer implements the Strategy pattern, allowing interchangeable algorithms:

- **Least Loaded Memory:** Routes incoming requests to the server with the lowest memory usage percentage. Ties are resolved alphabetically by server ID.
- **Round Robin:** Cyclically selects the next available server starting after the last scheduled server.
- **Best Fit:** Evaluates available servers sequentially by: 1. Minimizing total tick runtime, 2. Minimizing wasted CPU capacity, 3. Minimizing wasted RAM, 4. Server ID (tie-breaker).

### Queuing and Dropping Strategy

When a request arrives, the load balancer evaluates whether it can be immediately scheduled:

- **Unbounded Queueing for Valid Requests:** Any request that is theoretically satisfiable (its memory requirement is below the maximum server capacity in the cluster) is placed into a First-In-First-Out (FIFO) queue. If the cluster is under heavy load and all servers are saturated, these requests simply queue indefinitely. The simulation is unbounded and will continue ticking until all queued requests are processed. No valid requests are ever dropped due to wait times or queue limits.

While an unbounded queue is not a good solution for real-world systems due to memory exhaustion and client-side timeouts, this approach was selected because the case specifications do not define a maximum queue depth. Therefore, the strategy deliberately prioritizes a 0% drop rate for satisfiable tasks to optimize the simulation's success metrics, relying on the engine to eventually process the backlog.

- **Head-of-Line Blocking Avoidance:** To prevent a large but valid request from stalling the entire queue while waiting for a high-capacity server to free up, the load balancer uses queue skipping. It skips over blocked requests and attempts to schedule subsequent smaller requests in the queue during the same tick, maximizing cluster throughput.
- **Dropping Unsatisfiable Requests:** If a request arrives requiring more memory than the absolute maximum capacity of the largest server in the cluster, it is immediately emitted as a `REQUEST_DROPPED` event. This prevents inherently impossible requests from clogging the queue forever.

---

## Rate Limiting

The simulation model specifies that a server executes requests non-concurrently (one request at a time).

- A server cannot start a new request until the currently active one finishes.
- Since execution takes at least 1 tick (second), a server starts at most one request per tick.
- Therefore, the non-concurrency constraint satisfies the rate-limiting requirement mathematically. The engine also maintains internal counters to track per-tick limits for verification, although the constraint is satisfied in itself.

---

## Key Assumptions and Trade-offs

- **Determinism:** Events inside a tick are sorted by type precedence (finished first, then arrived, then started, then dropped) and then by request ID. This ensures the output trace is reproducible.
- **Unsatisfiable Requests:** Requests requiring more memory than the maximum capacity of any server in the cluster are dropped immediately on arrival to avoid clogging the queue.
- **Persistence Layer Trade-off:** Managing the `servers.json` state natively required evaluating three distinct approaches:
  1.  **File-only approach:** Modifying the raw `servers.json` file directly on API calls. While simple, it lacks an ORM, has no ACID properties, and is extremely risky and hacky under concurrent API requests due to potential race conditions and file corruption.
  2.  **Standalone Relational Network DB (e.g., Postgres):** Highly robust and the optimal solution in a traditional real-world scenario, but severe overkill here. Crucially, because the assignment strictly dictates that the `servers.json` file must remain the ultimate source of truth, a standalone database would merely act as a heavy intermediary cache. Since external file modifications (e.g., by a reviewer) can cause a "split-brain" state, the application must completely wipe and re-seed the database from `servers.json` on every startup. Spinning up a heavy Postgres container and persistent volume just to use it as a disposable cache is an anti-pattern and unjustifiable infrastructure.
  3.  **SQLite + Write-Through Sync (Chosen Approach):** SQLite hits the perfect sweet spot. Since we must use a database as an ephemeral cache to solve API concurrency safely, SQLite is lightweight enough to be wiped and re-seeded instantly on every startup with zero overhead. It runs in the exact same process space as the backend, requiring no external daemons or networking. API calls safely mutate this ACID-compliant SQLite cache (leveraging SQLAlchemy), and a background task immediately serializes the new state back to the `servers.json` file. This gives us the transactional safety of a robust database while keeping the infrastructure footprint negligible.

---

## Tooling and AI Usage

- **Planning & Architecture:** Initial planning, architecture design, and specification documents (under the `/docs` folder) were drafted through discussions with chat-based LLMs.
- **Code Generation:** The entire codebase was generated using Google Antigravity.
- **Review & Verification:** Every line of AI-generated code was extensively reviewed manually for correctness, adherence to the case constraints and best coding practices. The final implementation was thoroughly verified and tested against multiple custom scenario definitions in the `/cases` .
