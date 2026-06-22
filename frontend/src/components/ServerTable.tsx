import React from 'react';
import type { Server } from '../types';
import { Edit2, Trash2, Cpu, HardDrive, Zap, Server as ServerIcon } from 'lucide-react';
import { client } from '../api/client';
import { toast } from 'sonner';

interface ServerTableProps {
  servers: Server[];
  onRefresh: () => void;
  onEdit: (server: Server) => void;
}

export const ServerTable: React.FC<ServerTableProps> = ({
  servers,
  onRefresh,
  onEdit,
}) => {
  const handleDelete = async (id: string) => {
    if (!window.confirm(`Are you sure you want to delete server "${id}"? This change is permanent.`)) {
      return;
    }

    try {
      await client.deleteServer(id);
      toast.success(`Server "${id}" deleted successfully.`);
      onRefresh();
    } catch (err: any) {
      console.error(err);
      const errorMsg = err.response?.data?.detail || 'An error occurred while deleting the server.';
      toast.error(errorMsg);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
      <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
          <ServerIcon className="h-5 w-5 text-purple-400" />
          Cluster Nodes ({servers.length})
        </h3>
        <span className="text-xs bg-slate-800 text-slate-400 font-medium px-2.5 py-1 rounded-full uppercase tracking-wider">
          Active Cluster State
        </span>
      </div>

      <div className="overflow-x-auto">
        {servers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <ServerIcon className="h-12 w-12 text-slate-700 mb-4 stroke-[1.5]" />
            <h4 className="text-slate-400 font-semibold mb-1">No Servers Configured</h4>
            <p className="text-slate-500 text-sm max-w-sm">
              Add your first server using the configuration form to build your simulation cluster.
            </p>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/60 bg-slate-950/40 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <th className="px-6 py-4">Server ID</th>
                <th className="px-6 py-4">
                  <div className="flex items-center gap-1">
                    <Cpu className="h-3.5 w-3.5" />
                    CPU / Tick
                  </div>
                </th>
                <th className="px-6 py-4">
                  <div className="flex items-center gap-1">
                    <HardDrive className="h-3.5 w-3.5" />
                    Memory (MB)
                  </div>
                </th>
                <th className="px-6 py-4">
                  <div className="flex items-center gap-1">
                    <Zap className="h-3.5 w-3.5" />
                    Rate Limit (Req/s)
                  </div>
                </th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-slate-300">
              {servers.map((server) => (
                <tr key={server.id} className="hover:bg-slate-800/20 transition-colors">
                  <td className="px-6 py-4 font-mono font-medium text-slate-200">
                    {server.id}
                  </td>
                  <td className="px-6 py-4 font-mono text-sm">
                    {server.cpu_units_per_tick}
                  </td>
                  <td className="px-6 py-4 font-mono text-sm">
                    {server.mem_mb.toLocaleString()} MB
                  </td>
                  <td className="px-6 py-4 font-mono text-sm">
                    {server.rate_limit_per_sec}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onEdit(server)}
                        title="Edit Node"
                        className="p-2 text-slate-400 hover:text-purple-400 hover:bg-purple-500/10 rounded-lg transition cursor-pointer"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(server.id)}
                        title="Remove Node"
                        className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition cursor-pointer"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
