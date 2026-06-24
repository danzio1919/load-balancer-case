# Backend Implementation Guide

## 1. Infrastructure & Architecture

- **Framework:** FastAPI (Python 3.10+) running on Uvicorn.
- **Containerization:** Multi-stage `Dockerfile` and `docker-compose.yml`.

## 2. Data Persistence

- **System of Record:** `servers.json` remains the ultimate source of truth to satisfy evaluation constraints and determinism requirements.
- **Runtime Storage:** Local SQLite database (e.g., `sqlite:///./data/cluster.db`) to handle all CRUD operations.
- **Lifecycle Management:**
  - **Startup Seeding:** On FastAPI startup, read the provided `servers.json` file and initialize/seed the SQLite database.
  - **Runtime:** Route all API reads and writes to SQLite. SQLite natively handles concurrent API requests, write locks, and transactional safety.
  - **Synchronization:** After any successful write operation (POST, PUT, DELETE) to SQLite, trigger a FastAPI `BackgroundTask` to serialize the current database state and immediately overwrite `servers.json` to keep the file in sync.

## 3. API Endpoints

- **Server Management:** \* Implement standard CRUD (GET, POST, PUT, DELETE) querying the SQLite database.
  - Use strictly typed Pydantic models for request/response validation.
- **Simulation Execution:**
  - **Asynchronous Execution:** Trigger the Simulation Engine using FastAPI's `BackgroundTasks` to return a `202 Accepted` immediately and prevent thread blocking.
  - **Versioning:** Save outputs with timestamps (e.g., `runs/run_<timestamp>.jsonl`) and programmatically update a `run.jsonl` symlink/copy to point to the latest trace.

## 4. Engineering Enhancements

- **Dependency Injection:** Use FastAPI's `Depends` to inject the SQLite DB session and the `SimulationEngine` into routes, ensuring the API layer remains highly unit-testable.
- **Custom Exception Handlers:** Map domain-specific errors (e.g., `ServerNotFoundError`, `SimulationRunningError`) to clean, standardized HTTP JSON responses.
- **Structured Logging:** Replace standard `print()` statements with Python's `logging` module to output structured logs, demonstrating production-grade container observability.
