import axios from 'axios';
import type { Server, ServerCreateInput, ServerUpdateInput, SimulationResponse, SimulationStatusResponse } from '../types';

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

  runSimulation: async (): Promise<SimulationResponse> => {
    const response = await api.post<SimulationResponse>('/simulate');
    return response.data;
  },

  getSimulationStatus: async (): Promise<SimulationStatusResponse> => {
    const response = await api.get<SimulationStatusResponse>('/simulate/status');
    return response.data;
  },
};
