import { useState, useEffect } from 'react';
import type { Server } from './types';
import { client } from './api/client';
import { ServerForm } from './components/ServerForm';
import { ServerTable } from './components/ServerTable';
import { SimulationControl } from './components/SimulationControl';
import { Toaster, toast } from 'sonner';
import { Server as ServerIcon, RefreshCw, Layers } from 'lucide-react';

function App() {
  const [servers, setServers] = useState<Server[]>([]);
  const [editingServer, setEditingServer] = useState<Server | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchServers = async () => {
    setLoading(true);
    try {
      const data = await client.getServers();
      setServers(data);
    } catch (err: any) {
      console.error(err);
      toast.error('Failed to fetch cluster state from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  const handleEditServer = (server: Server) => {
    setEditingServer(server);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased selection:bg-purple-500/30 selection:text-purple-200">
      <Toaster position="top-right" theme="dark" closeButton richColors />

      {/* Navigation Header */}
      <header className="border-b border-slate-900 bg-slate-900/50 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-tr from-purple-600 to-indigo-600 rounded-xl shadow-lg shadow-purple-500/10">
              <Layers className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white m-0 leading-none">
                Load Balancer
              </h1>
              <p className="text-xs text-slate-400 mt-1 leading-none">
                Deterministic Simulator & Cluster Configurator
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchServers}
              disabled={loading}
              title="Refresh Cluster State"
              className="p-2.5 text-slate-400 hover:text-white bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`h-4.5 w-4.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <span className="flex items-center gap-2 px-3.5 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs font-semibold text-emerald-400 font-mono">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              ONLINE
            </span>
          </div>
        </div>
      </header>

      {/* Main Body Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        <section>
          <SimulationControl />
        </section>
        
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          <div className="lg:col-span-1">
            <ServerForm
              onSubmit={fetchServers}
              editingServer={editingServer}
              onCancelEdit={() => setEditingServer(null)}
            />
          </div>

          <div className="lg:col-span-2">
            {loading && servers.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[300px]">
                <ServerIcon className="h-10 w-10 text-slate-600 animate-pulse mb-3" />
                <p className="text-slate-400 text-sm font-medium">Fetching cluster layout...</p>
              </div>
            ) : (
              <ServerTable
                servers={servers}
                onRefresh={fetchServers}
                onEdit={handleEditServer}
              />
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
