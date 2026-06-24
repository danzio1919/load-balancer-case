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
  id: string;
  status: string;
}

export interface SimulationStatusResponse {
  id: string;
  status: 'processing' | 'completed' | 'failed';
  strategy_name: string;
  created_at: string;
  is_valid: boolean;
}

export interface ServerMetric {
  server_id: string;
  requests_handled: number;
  utilization_percent: number;
  resource_efficiency_percent: number;
  avg_service_time: number;
}

export interface Strategy {
  key: string;
  display_name: string;
}

export interface SimulationRunSummary {
  id: string;
  status: 'processing' | 'completed' | 'failed';
  strategy_name: string;
  is_valid: boolean;
  created_at: string;
  system_throughput?: number;
  avg_turnaround_time?: number;
  overall_utilization?: number;
}

export interface PaginatedRuns {
  items: SimulationRunSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface SimulationMetricsResponse {
  id: string;
  strategy_name?: string;
  created_at?: string;
  is_valid: boolean;
  total_duration_ticks: number;
  system_throughput: number;
  avg_turnaround_time: number;
  avg_service_time: number;
  overall_utilization: number;
  overall_resource_efficiency: number;
  validation_output_log: string;
  server_metrics: ServerMetric[];
}

