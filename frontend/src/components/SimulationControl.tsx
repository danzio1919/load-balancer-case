import React, { useState, useEffect, useRef } from 'react';
import { client } from '../api/client';
import { Play, Loader2, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import type { Strategy } from '../types';

interface SimulationControlProps {
  onSimulationFinished: (runFile: string) => void;
}

export const SimulationControl: React.FC<SimulationControlProps> = ({ onSimulationFinished }) => {
  const [status, setStatus] = useState<'idle' | 'running'>('idle');
  const [runFile, setRunFile] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('least_loaded_memory');
  const intervalRef = useRef<any>(null);

  // Poll status and fetch strategies when mounting
  useEffect(() => {
    checkStatus();
    fetchStrategies();
    return () => stopPolling();
  }, []);

  const fetchStrategies = async () => {
    try {
      const data = await client.getStrategies();
      setStrategies(data);
      if (data.length > 0) {
        const hasLeastLoaded = data.some(s => s.key === 'least_loaded_memory');
        setSelectedStrategy(hasLeastLoaded ? 'least_loaded_memory' : data[0].key);
      }
    } catch (err) {
      console.error('Error fetching strategies', err);
    }
  };

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const startPolling = (simId: string) => {
    stopPolling();
    intervalRef.current = setInterval(async () => {
      try {
        const res = await client.getSimulationStatus(simId);
        if (res.status === 'completed') {
          setStatus('idle');
          setLoading(false);
          stopPolling();
          toast.success('Simulation completed successfully! run.jsonl has been updated.');
          setRunFile(simId);
          onSimulationFinished(simId);
        } else if (res.status === 'failed') {
          setStatus('idle');
          setLoading(false);
          stopPolling();
          toast.error('Simulation run failed on the server.');
        } else {
          setStatus('running');
        }
      } catch (err) {
        console.error('Error polling simulation status', err);
      }
    }, 2000);
  };

  const checkStatus = async () => {
    try {
      // Fetch latest run from the paginated list to see if it's currently processing
      const res = await client.getSimulationRuns(1, 1);
      if (res.items && res.items.length > 0) {
        const latest = res.items[0];
        if (latest.status === 'processing') {
          setStatus('running');
          setRunFile(latest.id);
          startPolling(latest.id);
        } else {
          setStatus('idle');
          setRunFile(latest.id);
          onSimulationFinished(latest.id);
        }
      } else {
        setStatus('idle');
      }
    } catch (err) {
      console.error('Error fetching initial simulation status', err);
    }
  };

  const handleStartSimulation = async () => {
    setLoading(true);
    try {
      const res = await client.runSimulation(selectedStrategy);
      setRunFile(res.id);
      setStatus('running');
      toast.info('Simulation started in the background...');
      startPolling(res.id);
    } catch (err: any) {
      console.error(err);
      const errorMsg = err.response?.data?.detail || 'Failed to start simulation.';
      toast.error(errorMsg);
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-slate-100 mb-1 flex items-center gap-2">
            Simulation Control Engine
          </h3>
          <p className="text-slate-400 text-sm max-w-xl">
            Execute the deterministic load balancer simulation on the configured cluster. Choose a scheduling strategy and trigger the run.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-end gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Scheduling Strategy
            </label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              disabled={status === 'running' || loading}
              className="bg-slate-950 border border-slate-800 hover:border-slate-700 focus:border-purple-500 text-slate-200 text-sm rounded-xl px-4 py-3.5 focus:outline-none transition cursor-pointer min-w-[220px]"
            >
              {strategies.map((strat) => (
                <option key={strat.key} value={strat.key} className="bg-slate-900 text-slate-200">
                  {strat.display_name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            {status === 'running' || loading ? (
              <button
                disabled
                className="w-full sm:w-auto px-6 py-3.5 bg-purple-900/50 text-purple-300 font-semibold rounded-xl flex items-center justify-center gap-2.5 border border-purple-500/20 shadow-lg shadow-purple-950/20 cursor-not-allowed"
              >
                <Loader2 className="h-5 w-5 animate-spin" />
                Running Simulation...
              </button>
            ) : (
              <button
                onClick={handleStartSimulation}
                className="w-full sm:w-auto px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2.5 shadow-lg shadow-purple-600/20 hover:shadow-purple-600/30 transition cursor-pointer"
              >
                <Play className="h-5 w-5 fill-current" />
                Trigger Simulation Run
              </button>
            )}
          </div>
        </div>
      </div>

      {(status === 'running' || runFile) && (
        <div className="mt-6 pt-5 border-t border-slate-800/60 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl flex items-start gap-3">
            {status === 'running' ? (
              <Loader2 className="h-5 w-5 text-purple-400 animate-spin mt-0.5" />
            ) : (
              <CheckCircle2 className="h-5 w-5 text-emerald-400 mt-0.5" />
            )}
            <div>
              <span className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                Engine State
              </span>
              <span className={`text-sm font-semibold ${status === 'running' ? 'text-purple-400' : 'text-emerald-400'}`}>
                {status === 'running' ? 'Processing csv trace...' : 'Ready & Idle'}
              </span>
            </div>
          </div>

          {runFile && (
            <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl flex items-start gap-3">
              <CheckCircle2 className="h-5 w-5 text-indigo-400 mt-0.5" />
              <div>
                <span className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  Latest Run Output Target
                </span>
                <span className="text-sm font-mono text-indigo-300 break-all select-all">
                  {runFile}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
