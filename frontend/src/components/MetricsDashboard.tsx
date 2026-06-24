import React, { useState, useEffect } from 'react';
import { client } from '../api/client';
import type { SimulationMetricsResponse } from '../types';
import { 
  ChevronDown, 
  ChevronUp, 
  CheckCircle2, 
  XCircle, 
  Activity,
  FileText
} from 'lucide-react';
import { toast } from 'sonner';

interface MetricsDashboardProps {
  runFile: string | null;
}

export const MetricsDashboard: React.FC<MetricsDashboardProps> = ({ runFile }) => {
  const [metrics, setMetrics] = useState<SimulationMetricsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showLogs, setShowLogs] = useState<boolean>(false);

  useEffect(() => {
    if (!runFile) {
      setMetrics(null);
      return;
    }

    const fetchMetrics = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await client.getSimulationMetrics(runFile);
        setMetrics(data);
      } catch (err: any) {
        console.error('Error fetching simulation metrics:', err);
        const errMsg = err.response?.data?.detail || 'Failed to retrieve simulation metrics.';
        setError(errMsg);
        toast.error(errMsg);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, [runFile]);

  if (!runFile) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-slate-400">
        <Activity className="h-10 w-10 text-slate-600 mx-auto mb-3" />
        <p className="font-medium text-sm">No Simulation Run Selected</p>
        <p className="text-xs text-slate-500 mt-1">Trigger a simulation run above to compute and display analytics.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-3"></div>
        <p className="font-medium text-sm">Loading simulation performance metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-red-400">
        <XCircle className="h-10 w-10 mx-auto mb-3 text-red-500" />
        <p className="font-medium text-sm">Error Loading Metrics</p>
        <p className="text-xs mt-1 text-red-400/80">{error}</p>
      </div>
    );
  }

  if (!metrics) return null;

  const formatStrategyName = (key: string) => {
    switch (key) {
      case 'least_loaded_memory':
        return 'Least Loaded Memory';
      case 'round_robin':
        return 'Round Robin';
      case 'best_fit':
        return 'Best Fit';
      default:
        return key;
    }
  };

  const getStrategyBadgeStyles = (key: string) => {
    switch (key) {
      case 'least_loaded_memory':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'round_robin':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'best_fit':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Block */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/60 pb-5">
          <div>
            <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2 flex-wrap">
              <Activity className="h-5 w-5 text-purple-400" />
              Simulation Run Analytics
              {metrics.strategy_name && (
                <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${getStrategyBadgeStyles(metrics.strategy_name)}`}>
                  {formatStrategyName(metrics.strategy_name)}
                </span>
              )}
            </h3>
            <p className="text-slate-400 text-xs mt-1 font-mono">{metrics.id}</p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Validator Status:
            </span>
            {metrics.is_valid ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="h-3.5 w-3.5" />
                VALID RUN
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-450 border border-rose-500/20">
                <XCircle className="h-3.5 w-3.5" />
                INVALID RUN
              </span>
            )}
          </div>
        </div>

        {/* Global KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl">
            <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
              Duration
            </span>
            <span className="text-xl font-bold text-slate-200">
              {metrics.total_duration_ticks} <span className="text-xs font-medium text-slate-500">ticks</span>
            </span>
          </div>

          <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl">
            <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
              Throughput
            </span>
            <span className="text-xl font-bold text-slate-200 flex items-baseline gap-1">
              {metrics.system_throughput}
              <span className="text-xs font-medium text-slate-500">req/t</span>
            </span>
          </div>

          <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl">
            <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
              Avg Turnaround
            </span>
            <span className="text-xl font-bold text-slate-200">
              {metrics.avg_turnaround_time} <span className="text-xs font-medium text-slate-500">ticks</span>
            </span>
          </div>

          <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl">
            <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
              Avg Service
            </span>
            <span className="text-xl font-bold text-slate-200">
              {metrics.avg_service_time} <span className="text-xs font-medium text-slate-500">ticks</span>
            </span>
          </div>

          <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl">
            <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
              Avg Utilization
            </span>
            <span className="text-xl font-bold text-purple-400">
              {metrics.overall_utilization}%
            </span>
          </div>

          <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl">
            <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
              CPU Efficiency
            </span>
            <span className="text-xl font-bold text-indigo-400">
              {metrics.overall_resource_efficiency}%
            </span>
          </div>
        </div>
      </div>

      {/* Per-Server Metrics */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">
          Cluster Servers Leaderboard
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase">
                <th className="py-3 px-4">Server ID</th>
                <th className="py-3 px-4 text-right">Requests Handled</th>
                <th className="py-3 px-4 text-right">Utilization (%)</th>
                <th className="py-3 px-4 text-right">CPU Efficiency (%)</th>
                <th className="py-3 px-4 text-right">Avg Service Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-slate-300">
              {metrics.server_metrics.map((sm) => (
                <tr key={sm.server_id} className="hover:bg-slate-800/20 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-slate-200">{sm.server_id}</td>
                  <td className="py-3 px-4 text-right font-mono">{sm.requests_handled}</td>
                  <td className="py-3 px-4 text-right font-mono">
                    <span className={sm.utilization_percent > 80 ? 'text-purple-400 font-semibold' : ''}>
                      {sm.utilization_percent}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono">
                    <span className={sm.resource_efficiency_percent < 50 && sm.requests_handled > 0 ? 'text-amber-400 font-semibold' : ''}>
                      {sm.resource_efficiency_percent}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono">{sm.avg_service_time} ticks</td>
                </tr>
              ))}
              {metrics.server_metrics.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-550">
                    No server statistics available for this run.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Validation Logs Log Block */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        <button
          onClick={() => setShowLogs(!showLogs)}
          className="w-full flex items-center justify-between p-5 text-left font-medium text-slate-300 hover:bg-slate-800/30 transition-colors cursor-pointer"
        >
          <span className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider">
            <FileText className="h-4.5 w-4.5 text-slate-400" />
            Validation Output Logs (`validate_run.py`)
          </span>
          {showLogs ? (
            <ChevronUp className="h-5 w-5 text-slate-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-slate-400" />
          )}
        </button>

        {showLogs && (
          <div className="border-t border-slate-800 bg-slate-950 p-5">
            <pre className="text-xs font-mono text-slate-300 leading-relaxed overflow-x-auto whitespace-pre-wrap max-h-96 bg-slate-950 p-4 rounded-lg border border-slate-900 shadow-inner">
              {metrics.validation_output_log || "No log output available."}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
