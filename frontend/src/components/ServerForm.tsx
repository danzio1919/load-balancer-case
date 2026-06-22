import React, { useState, useEffect } from 'react';
import type { Server, ServerCreateInput } from '../types';
import { client } from '../api/client';
import { PlusCircle, Save, X, Cpu, HardDrive, Zap } from 'lucide-react';
import { toast } from 'sonner';

interface ServerFormProps {
  onSubmit: () => void;
  editingServer: Server | null;
  onCancelEdit: () => void;
}

export const ServerForm: React.FC<ServerFormProps> = ({
  onSubmit,
  editingServer,
  onCancelEdit,
}) => {
  const [id, setId] = useState('');
  const [cpuUnits, setCpuUnits] = useState('');
  const [memMb, setMemMb] = useState('');
  const [rateLimit, setRateLimit] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (editingServer) {
      setId(editingServer.id);
      setCpuUnits(editingServer.cpu_units_per_tick.toString());
      setMemMb(editingServer.mem_mb.toString());
      setRateLimit(editingServer.rate_limit_per_sec.toString());
    } else {
      setId('');
      setCpuUnits('');
      setMemMb('');
      setRateLimit('');
    }
  }, [editingServer]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!id.trim() || !cpuUnits || !memMb || !rateLimit) {
      toast.error('All fields are required.');
      return;
    }

    const cpu = parseFloat(cpuUnits);
    const mem = parseFloat(memMb);
    const rate = parseInt(rateLimit, 10);

    if (isNaN(cpu) || cpu <= 0) {
      toast.error('CPU units per tick must be greater than 0.');
      return;
    }
    if (isNaN(mem) || mem <= 0) {
      toast.error('Memory (MB) must be greater than 0.');
      return;
    }
    if (isNaN(rate) || rate <= 0) {
      toast.error('Rate limit per second must be greater than 0.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (editingServer) {
        // Update server
        await client.updateServer(editingServer.id, {
          cpu_units_per_tick: cpu,
          mem_mb: mem,
          rate_limit_per_sec: rate,
        });
        toast.success(`Server "${editingServer.id}" updated successfully.`);
      } else {
        // Create server
        const idPattern = /^[a-zA-Z0-9_\-]+$/;
        if (!idPattern.test(id)) {
          toast.error('ID must contain only alphanumeric characters, underscores, or hyphens.');
          setIsSubmitting(false);
          return;
        }

        const newServer: ServerCreateInput = {
          id: id.trim(),
          cpu_units_per_tick: cpu,
          mem_mb: mem,
          rate_limit_per_sec: rate,
        };
        await client.createServer(newServer);
        toast.success(`Server "${newServer.id}" created successfully.`);
      }
      onSubmit();
      if (editingServer) {
        onCancelEdit();
      } else {
        setId('');
        setCpuUnits('');
        setMemMb('');
        setRateLimit('');
      }
    } catch (err: any) {
      console.error(err);
      const errorMsg = err.response?.data?.detail || 'An error occurred while saving the server.';
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl transition-all duration-300">
      <h3 className="text-lg font-semibold text-slate-100 mb-5 flex items-center gap-2">
        {editingServer ? (
          <>
            <Save className="h-5 w-5 text-purple-400 animate-pulse" />
            Edit Server: <span className="text-purple-400 font-mono">{editingServer.id}</span>
          </>
        ) : (
          <>
            <PlusCircle className="h-5 w-5 text-emerald-400" />
            Add Server Configuration
          </>
        )}
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Server ID */}
        <div>
          <label htmlFor="serverId" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Server ID
          </label>
          <input
            id="serverId"
            type="text"
            placeholder="e.g. server_1"
            value={id}
            onChange={(e) => setId(e.target.value)}
            disabled={!!editingServer}
            className={`w-full px-4 py-2.5 bg-slate-955 border rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 font-mono transition ${
              editingServer 
                ? 'border-slate-800 text-slate-500 cursor-not-allowed bg-slate-900/50' 
                : 'border-slate-800 hover:border-slate-700 focus:border-purple-500'
            }`}
          />
        </div>

        {/* CPU Units Per Tick */}
        <div>
          <label htmlFor="cpuUnits" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Cpu className="h-3.5 w-3.5 text-slate-500" />
            CPU Units Per Tick
          </label>
          <input
            id="cpuUnits"
            type="number"
            step="any"
            placeholder="e.g. 1.0"
            value={cpuUnits}
            onChange={(e) => setCpuUnits(e.target.value)}
            className="w-full px-4 py-2.5 bg-slate-955 border border-slate-800 hover:border-slate-700 focus:border-purple-500 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 transition"
          />
        </div>

        {/* Memory limit (MB) */}
        <div>
          <label htmlFor="memMb" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <HardDrive className="h-3.5 w-3.5 text-slate-500" />
            Memory (MB)
          </label>
          <input
            id="memMb"
            type="number"
            step="any"
            placeholder="e.g. 2048"
            value={memMb}
            onChange={(e) => setMemMb(e.target.value)}
            className="w-full px-4 py-2.5 bg-slate-955 border border-slate-800 hover:border-slate-700 focus:border-purple-500 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 transition"
          />
        </div>

        {/* Rate Limit per second */}
        <div>
          <label htmlFor="rateLimit" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5 text-slate-500" />
            Rate Limit (Req/Sec)
          </label>
          <input
            id="rateLimit"
            type="number"
            placeholder="e.g. 10"
            value={rateLimit}
            onChange={(e) => setRateLimit(e.target.value)}
            className="w-full px-4 py-2.5 bg-slate-955 border border-slate-800 hover:border-slate-700 focus:border-purple-500 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 transition"
          />
        </div>

        <div className="pt-2 flex gap-3">
          {editingServer && (
            <button
              type="button"
              onClick={onCancelEdit}
              className="flex-1 px-4 py-2.5 bg-slate-800 hover:bg-slate-750 text-slate-300 font-semibold rounded-xl flex items-center justify-center gap-2 border border-slate-700 transition cursor-pointer"
            >
              <X className="h-4 w-4" />
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className={`flex-1 px-4 py-2.5 font-semibold rounded-xl flex items-center justify-center gap-2 transition cursor-pointer ${
              isSubmitting 
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : editingServer 
                  ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/10'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/10'
            }`}
          >
            {isSubmitting ? (
              <span className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></span>
            ) : editingServer ? (
              <>
                <Save className="h-4 w-4" />
                Update
              </>
            ) : (
              <>
                <PlusCircle className="h-4 w-4" />
                Create
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
