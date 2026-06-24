# Frontend Implementation Guide

## 1. Infrastructure & Architecture

- **Framework:** React.
- **Styling:** Tailwind CSS. Keep styling strictly utilitarian and minimalistic. The focus is purely on functional layout and state management, not complex design.
- **Containerization:** Multi-stage `Dockerfile`.
  - **Stage 1 (Builder):** Node environment to install dependencies and build the static assets.
  - **Stage 2 (Runtime):** Nginx alpine image to serve the built application.
- **Network:** Must communicate with the FastAPI backend via relative or environment-configured API URLs.

## 2. UI Layout & Components

The application should be a clean, single-page dashboard divided into two primary logical sections:

### Section A: Cluster Management (CRUD)

- **Add Server Form:** A simple form to input properties (`id`, `cpu_units_per_tick`, `mem_mb`, `rate_limit_per_sec`) and create a new server.
- **Server Data Table:** A clear table listing all current servers in the cluster.
  - Must display all server properties.
  - Must include inline actions to "Edit" or "Delete" each specific server row.

### Section B: Simulation Control

- **Action Panel:** A dedicated area containing a prominent button to trigger the simulation.
- **Feedback Mechanism:** The UI must display a clear loading state while the simulation runs and provide a success or error notification upon completion.

## 3. Data Flow & API Integration

The frontend must synchronize with the backend using the following exact endpoints:

- **Server State:** \* Fetch cluster state: `GET /servers`
  - Add a server: `POST /servers`
  - Update a server: `PUT /servers/{id}`
  - Remove a server: `DELETE /servers/{id}`
- **Simulation:**
  - Trigger execution: `POST /simulations`
  - Get simulation runs history: `GET /simulations`
  - Get simulation status: `GET /simulations/{id}`
  - Get simulation metrics: `GET /simulations/{id}/metrics`
  - Get simulation strategies: `GET /simulations/strategies`
- **State Synchronization:** The UI must automatically refresh the server list after any successful mutation (Add, Edit, Delete) to ensure the user is always looking at the current cluster configuration.

