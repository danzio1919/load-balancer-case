export interface Server {
  id: string;
  cpu_units_per_tick: number;
  mem_mb: number;
  rate_limit_per_sec: number;
}

export type ServerCreateInput = Server;

export interface ServerUpdateInput {
  cpu_units_per_tick?: number;
  mem_mb?: number;
  rate_limit_per_sec?: number;
}

export interface SimulationResponse {
  message: string;
  run_file: string;
  status: string;
}

export interface SimulationStatusResponse {
  status: 'running' | 'idle';
  is_running: boolean;
}
