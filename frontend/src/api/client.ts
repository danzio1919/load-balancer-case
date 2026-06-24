import axios from 'axios';
import type { Server, ServerCreateInput, ServerUpdateInput, SimulationResponse, SimulationStatusResponse, SimulationMetricsResponse, Strategy, PaginatedRuns } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const client = {
  getServers: async (): Promise<Server[]> => {
    const response = await api.get<Server[]>('/servers');
    return response.data;
  },

  getServer: async (serverId: string): Promise<Server> => {
    const response = await api.get<Server>(`/servers/${serverId}`);
    return response.data;
  },

  createServer: async (server: ServerCreateInput): Promise<Server> => {
    const response = await api.post<Server>('/servers', server);
    return response.data;
  },

  updateServer: async (serverId: string, server: ServerUpdateInput): Promise<Server> => {
    const response = await api.put<Server>(`/servers/${serverId}`, server);
    return response.data;
  },

  deleteServer: async (serverId: string): Promise<void> => {
    await api.delete(`/servers/${serverId}`);
  },

  runSimulation: async (strategyName?: string): Promise<SimulationResponse> => {
    const url = strategyName ? `/simulations?strategy_name=${encodeURIComponent(strategyName)}` : '/simulations';
    const response = await api.post<SimulationResponse>(url);
    return response.data;
  },

  getSimulationStatus: async (simId: string): Promise<SimulationStatusResponse> => {
    const response = await api.get<SimulationStatusResponse>(`/simulations/${simId}`);
    return response.data;
  },

  getSimulationMetrics: async (runId: string): Promise<SimulationMetricsResponse> => {
    const response = await api.get<SimulationMetricsResponse>(`/simulations/${runId}/metrics`);
    return response.data;
  },

  getStrategies: async (): Promise<Strategy[]> => {
    const response = await api.get<Strategy[]>('/simulations/strategies');
    return response.data;
  },

  getSimulationRuns: async (page: number = 1, pageSize: number = 10): Promise<PaginatedRuns> => {
    const response = await api.get<PaginatedRuns>(`/simulations?page=${page}&page_size=${pageSize}`);
    return response.data;
  },
};

