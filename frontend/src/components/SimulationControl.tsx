import React, { useState, useEffect, useRef } from 'react';
import { client } from '../api/client';
import { Play, Loader2, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

export const SimulationControl: React.FC = () => {
  const [status, setStatus] = useState<'idle' | 'running'>('idle');
  const [runFile, setRunFile] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef<any>(null);

  // Poll status when mounting to check if a simulation is already running
  useEffect(() => {
    checkStatus();
    return () => stopPolling();
  }, []);

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const startPolling = () => {
    stopPolling();
    intervalRef.current = setInterval(async () => {
      try {
        const res = await client.getSimulationStatus();
        if (!res.is_running) {
          setStatus('idle');
          setLoading(false);
          stopPolling();
          toast.success('Simulation completed successfully! run.jsonl has been updated.');
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
      const res = await client.getSimulationStatus();
      if (res.is_running) {
        setStatus('running');
        startPolling();
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
      const res = await client.runSimulation();
      setRunFile(res.run_file);
      setStatus('running');
      toast.info('Simulation started in the background...');
      startPolling();
    } catch (err: any) {
      console.error(err);
      const errorMsg = err.response?.data?.detail || 'Failed to start simulation.';
      toast.error(errorMsg);
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 mb-1 flex items-center gap-2">
            Simulation Control Engine
          </h3>
          <p className="text-slate-400 text-sm max-w-xl">
            Execute the deterministic load balancer simulation on the configured cluster. This will replay the request logs and output the execution trace.
          </p>
        </div>

        <div>
          {status === 'running' || loading ? (
            <button
              disabled
              className="w-full md:w-auto px-6 py-3.5 bg-purple-900/50 text-purple-300 font-semibold rounded-xl flex items-center justify-center gap-2.5 border border-purple-500/20 shadow-lg shadow-purple-950/20 cursor-not-allowed"
            >
              <Loader2 className="h-5 w-5 animate-spin" />
              Running Simulation...
            </button>
          ) : (
            <button
              onClick={handleStartSimulation}
              className="w-full md:w-auto px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2.5 shadow-lg shadow-purple-600/20 hover:shadow-purple-600/30 transition cursor-pointer"
            >
              <Play className="h-5 w-5 fill-current" />
              Trigger Simulation Run
            </button>
          )}
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
