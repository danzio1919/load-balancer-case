import React, { useState, useEffect } from 'react';
import { client } from '../api/client';
import type { SimulationRunSummary } from '../types';
import { ChevronLeft, ChevronRight, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';

interface RunHistoryProps {
  selectedRunId: string | null;
  onSelectRun: (runId: string) => void;
  refreshTrigger: number;
}

export const RunHistory: React.FC<RunHistoryProps> = ({
  selectedRunId,
  onSelectRun,
  refreshTrigger
}) => {
  const [runs, setRuns] = useState<SimulationRunSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const pageSize = 10;

  useEffect(() => {
    fetchRuns();
  }, [page, refreshTrigger]);

  // Reset page to 1 when a new simulation finishes and history is refreshed
  useEffect(() => {
    if (page !== 1) {
      setPage(1);
    } else {
      fetchRuns();
    }
  }, [refreshTrigger]);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await client.getSimulationRuns(page, pageSize);
      setRuns(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Error fetching runs history', err);
      toast.error('Failed to load simulation run history.');
    } finally {
      setLoading(false);
    }
  };

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

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString();
    } catch (e) {
      return dateStr;
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  const handlePrevPage = () => {
    if (page > 1) {
      setPage(page - 1);
    }
  };

  const handleNextPage = () => {
    if (page < totalPages) {
      setPage(page + 1);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-slate-850 pb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            Simulation History & Runs
          </h3>
          <p className="text-slate-400 text-sm">
            Select a past run from the list to display its detailed execution metrics.
          </p>
        </div>
        <div className="text-xs bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-400 font-semibold">
          Total Runs: {total}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[700px]">
          <thead>
            <tr className="border-b border-slate-800/80 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <th className="py-3 px-4">Run File Name</th>
              <th className="py-3 px-4">Strategy</th>
              <th className="py-3 px-4">Created At</th>
              <th className="py-3 px-4 text-center">Status</th>
              <th className="py-3 px-4 text-right">Throughput</th>
              <th className="py-3 px-4 text-right">Overall Util.</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850 text-sm">
            {loading && runs.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-450">
                  <div className="flex items-center justify-center gap-2">
                    <Clock className="h-5 w-5 animate-spin text-purple-500" />
                    Loading runs...
                  </div>
                </td>
              </tr>
            ) : runs.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-450">
                  No simulation runs found. Trigger a simulation to start!
                </td>
              </tr>
            ) : (
              runs.map((run) => {
                const isSelected = selectedRunId === run.id;
                const canSelect = run.status === 'completed';
                return (
                  <tr
                    key={run.id}
                    onClick={() => canSelect && onSelectRun(run.id)}
                    className={`group transition-all duration-150 ${
                      canSelect
                        ? 'cursor-pointer hover:bg-slate-850/60'
                        : 'cursor-not-allowed opacity-60'
                    } ${
                      isSelected
                        ? 'bg-purple-950/20 border-l-2 border-l-purple-500'
                        : 'border-l-2 border-l-transparent'
                    }`}
                  >
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-300 group-hover:text-purple-300 transition-colors">
                      {run.id}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${getStrategyBadgeStyles(run.strategy_name)}`}>
                        {formatStrategyName(run.strategy_name)}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-450 text-xs">
                      {formatDate(run.created_at)}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <div className="flex items-center justify-center">
                        {run.status === 'processing' ? (
                          <span className="flex items-center gap-1 text-xs text-purple-450 font-semibold bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded-md animate-pulse">
                            <Clock className="h-3.5 w-3.5 text-purple-400 animate-spin" />
                            Running
                          </span>
                        ) : run.status === 'failed' ? (
                          <span className="flex items-center gap-1 text-xs text-rose-450 font-semibold bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-md">
                            <XCircle className="h-3.5 w-3.5 text-rose-450" />
                            Failed
                          </span>
                        ) : run.is_valid ? (
                          <span className="flex items-center gap-1 text-xs text-emerald-450 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-md">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                            Valid
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs text-rose-450 font-semibold bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-md">
                            <XCircle className="h-3.5 w-3.5 text-rose-450" />
                            Invalid
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right font-semibold text-slate-200">
                      {run.system_throughput != null ? `${run.system_throughput.toFixed(4)} req/t` : 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 text-right font-semibold text-slate-200">
                      {run.overall_utilization != null ? `${run.overall_utilization.toFixed(2)}%` : 'N/A'}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-850 pt-4 mt-2">
          <div className="text-xs text-slate-450 font-medium">
            Showing Page <span className="text-slate-255 font-semibold">{page}</span> of{' '}
            <span className="text-slate-255 font-semibold">{totalPages}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrevPage}
              disabled={page === 1 || loading}
              className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-300 hover:bg-slate-850 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition cursor-pointer"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={handleNextPage}
              disabled={page === totalPages || loading}
              className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-300 hover:bg-slate-850 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition cursor-pointer"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
