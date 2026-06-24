## Getting Started

The entire application is containerized. Running it requires Docker and Docker Compose.

### Running with Docker

To build and start the frontend and backend services:

```bash
docker compose up --build -d
```

Once running:

- **Frontend Dashboard:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Swagger API Docs:** http://localhost:8000/docs

To stop and remove containers:

```bash
docker compose down
```

### Running Simulations

You can run simulations either directly via the command line (CLI) or through the frontend dashboard.

#### 1. Via the Simulation CLI

To run the simulation engine directly inside the container without using the frontend interface:

- **To run using the root configuration (`servers.json` and `requests.csv` at the root):**

  ```bash
  docker compose exec backend python /app/run_simulation.py
  ```

  This reads the root configuration and outputs the trace to the root `run.jsonl`.

- **To run a specific scenario under the `scenarios/` folder (e.g., `case1`):**
  ```bash
  docker compose exec backend python /app/run_simulation.py case1
  ```
  This reads from `scenarios/case1/` and outputs the trace to `scenarios/case1/run.jsonl`.

_Note: Running simulations directly via the CLI bypasses the API database and will not populate the simulation history or metrics shown on the frontend dashboard._

#### 2. Via the Frontend Dashboard

To trigger simulations with full database metric tracking, run history, and performance stats:

1. Open the dashboard at http://localhost:3000.
2. Manage your cluster servers dynamically (using the Add/Edit/Delete actions) or modify the root `servers.json` and `requests.csv` files on disk (requires restarting the backend container to re-seed: `docker compose restart backend`).
3. Choose a scheduling strategy on the dashboard and click **Run Simulation**.

#### Running Unit Tests

To run the Python test suite inside the container:

```bash
docker compose exec backend pytest
```

## Directory Structure

- `backend/`: FastAPI application code and API endpoints.
- `backend/simulation_engine/`: Core simulation scheduler, models, and scheduling strategies.
- `frontend/`: React + Vite dashboard for managing servers and running simulations.
- `scenarios/`: Test cases containing input files (`servers.json`, `requests.csv`) and output trace logs (`run.jsonl`).

For a detailed explanation of the scheduler algorithms, assumptions, and design choices, see [Design Documentation](docs/design_document.md).

### Evaluation Artifacts

As per the assignment requirements, a pre-generated, valid `run.jsonl` trace example is located at the root of this repository.
