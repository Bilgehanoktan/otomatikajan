"use client";

import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Server, 
  ShieldCheck, 
  Zap, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  Cpu, 
  Layers, 
  Globe,
  Wind,
  FileText,
  ChevronRight,
  Target
} from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

const Card = ({ children, className = "", onClick }: { children: React.ReactNode, className?: string, onClick?: () => void }) => (
  <div onClick={onClick} className={`bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-md shadow-xl ${className}`}>
    {children}
  </div>
);

const Badge = ({ children, variant = "info" }: { children: React.ReactNode, variant?: string }) => {
  const styles: Record<string, string> = {
    info: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    error: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    critical: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border ${styles[variant] || styles.info}`}>
      {children}
    </span>
  );
};

export const ResiliencyMeshPanel = () => {
  const [meshHealth, setMeshHealth] = useState<{ global_federation_health_index: number; total_nodes: number }>({
    global_federation_health_index: 0,
    total_nodes: 0,
  });
  const [nodes, setNodes] = useState<any[]>([]);
  const [decisions, setDecisions] = useState<any[]>([]);
  const [slos, setSlos] = useState<any[]>([]);
  const [postmortems, setPostmortems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeNode, setActiveNode] = useState<any>(null);

  useEffect(() => {
    fetchMeshData();
  }, []);

  const fetchMeshData = async () => {
    try {
      const [meshHealthData, decisionsData, slosData, postmortemsData] = await Promise.all([
        safeFetchJson<any>('/api/v1/ui-repair/mesh/health'),
        safeFetchJson<any[]>('/api/v1/ui-repair/mesh/steering/decisions'),
        safeFetchJson<any[]>('/api/v1/ui-repair/mesh/slo/snapshots'),
        safeFetchJson<any[]>('/api/v1/ui-repair/mesh/postmortems')
      ]);

      setMeshHealth({
        global_federation_health_index: meshHealthData.global_federation_health_index ?? 0,
        total_nodes: meshHealthData.total_nodes ?? 0,
      });
      setNodes(meshHealthData.nodes ?? []);
      setDecisions(decisionsData);
      setSlos(slosData);
      setPostmortems(postmortemsData);
    } catch (err) {
      console.error("Failed to fetch mesh data", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-20 text-center flex flex-col items-center">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mb-4" />
        <p className="text-slate-500 font-bold uppercase tracking-widest text-xs">Aggregating Mesh Health...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Mesh Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6 border-l-4 border-l-blue-500">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Layers className="w-5 h-5 text-blue-400" />
            </div>
            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">Mesh Nodes</h4>
          </div>
          <div className="text-3xl font-black text-white">{meshHealth.total_nodes}</div>
          <p className="text-[10px] text-slate-500 mt-2">Active federated clusters in mesh</p>
        </Card>

        <Card className="p-6 border-l-4 border-l-emerald-500">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-emerald-500/10 rounded-lg">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            </div>
            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">Global Health</h4>
          </div>
          <div className="text-3xl font-black text-white">
            {slos.length > 0
              ? slos[0].federation_health_score.toFixed(0)
              : meshHealth.global_federation_health_index.toFixed(0)}%
          </div>
          <p className="text-[10px] text-slate-500 mt-2">Aggregate federation health index</p>
        </Card>

        <Card className="p-6 border-l-4 border-l-amber-500">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-amber-500/10 rounded-lg">
              <Zap className="w-5 h-5 text-amber-400" />
            </div>
            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">Steering Actions</h4>
          </div>
          <div className="text-3xl font-black text-white">{decisions.length}</div>
          <p className="text-[10px] text-slate-500 mt-2">Autonomous load steering decisions</p>
        </Card>

        <Card className="p-6 border-l-4 border-l-rose-500">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-rose-500/10 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-rose-400" />
            </div>
            <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">Incidents</h4>
          </div>
          <div className="text-3xl font-black text-white">{postmortems.length}</div>
          <p className="text-[10px] text-slate-500 mt-2">Self-healed incident post-mortems</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        
        {/* Mesh Nodes Visualization */}
        <div className="xl:col-span-8 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Globe className="w-5 h-5 text-blue-400" />
              Federated Node Topology
            </h3>
            <button 
              onClick={fetchMeshData}
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-500 hover:text-blue-400 transition-all"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {nodes.map((node, i) => (
              <Card 
                key={i} 
                className={`p-5 transition-all hover:border-blue-500/30 cursor-pointer ${activeNode?.id === node.id ? 'border-blue-500 bg-blue-500/5 shadow-blue-500/10' : ''}`}
                onClick={() => setActiveNode(node)}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${node.status === 'HEALTHY' ? 'bg-emerald-500/10' : 'bg-rose-500/10'}`}>
                      <Server className={`w-4 h-4 ${node.status === 'HEALTHY' ? 'text-emerald-400' : 'text-rose-400'}`} />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">{node.cluster_key}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{node.region} | {node.tenant_key}</div>
                    </div>
                  </div>
                  <Badge variant={node.status === 'HEALTHY' ? 'success' : 'error'}>{node.status}</Badge>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="p-2 bg-slate-950/50 rounded-lg border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase font-black mb-1">Health Score</div>
                    <div className="text-sm font-mono text-emerald-400">{node.health_score.toFixed(0)}%</div>
                  </div>
                  <div className="p-2 bg-slate-950/50 rounded-lg border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase font-black mb-1">Latency</div>
                    <div className="text-sm font-mono text-blue-400">{node.latency_ms}ms</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-[10px]">
                    <span className="text-slate-500">Queue Depth</span>
                    <span className="text-slate-300 font-mono">{node.queue_depth} jobs</span>
                  </div>
                  <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-1000 ${node.queue_depth > 80 ? 'bg-rose-500' : 'bg-blue-500'}`}
                      style={{ width: `${Math.min(node.queue_depth, 100)}%` }} 
                    />
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Load Steering Decisions */}
          <Card className="overflow-hidden">
            <div className="p-6 border-b border-slate-800">
              <h3 className="text-sm font-black text-slate-100 uppercase tracking-widest flex items-center gap-2">
                <Target className="w-4 h-4 text-amber-500" />
                Global Load Steering History
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-slate-950/30 text-[9px] text-slate-500 uppercase font-black tracking-widest">
                  <tr>
                    <th className="px-6 py-4">Workload</th>
                    <th className="px-6 py-4">Source → Target</th>
                    <th className="px-6 py-4">Reason</th>
                    <th className="px-6 py-4 text-right">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {decisions.map((dec, i) => (
                    <tr key={i} className="hover:bg-slate-800/20 transition-colors text-xs">
                      <td className="px-6 py-4">
                        <div className="font-mono text-blue-400">{dec.workload_type}</div>
                        <div className="text-[10px] text-slate-500">{dec.tenant_key}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-500">{dec.source_cluster_key || "ANY"}</span>
                          <ChevronRight className="w-3 h-3 text-slate-700" />
                          <span className="text-emerald-400 font-bold">{dec.selected_cluster_key}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 max-w-[200px] truncate text-slate-400">
                        {dec.decision_reason}
                      </td>
                      <td className="px-6 py-4 text-right font-mono text-slate-500">
                        {new Date(dec.created_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* SLO & Post-Mortems */}
        <div className="xl:col-span-4 space-y-6">
          
          {/* SLO Health */}
          <Card className="p-6 bg-gradient-to-br from-indigo-500/10 to-transparent border-indigo-500/20">
            <h3 className="text-sm font-black text-indigo-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4" />
              Mesh SLO Status
            </h3>
            <div className="space-y-4">
              {slos.slice(0, 3).map((slo, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between text-[10px] uppercase font-bold">
                    <span className="text-slate-400">Federation Availability</span>
                    <span className="text-white">{slo.federation_health_score.toFixed(2)}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                    <div 
                      className="h-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" 
                      style={{ width: `${Math.min(slo.federation_health_score, 100)}%` }} 
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6 pt-4 border-t border-indigo-500/20 grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-[10px] text-slate-500 uppercase font-bold">MTTR</div>
                <div className="text-lg font-black text-white">12.4m</div>
              </div>
              <div className="text-center">
                <div className="text-[10px] text-slate-500 uppercase font-bold">MTBF</div>
                <div className="text-lg font-black text-white">18.2d</div>
              </div>
            </div>
          </Card>

          {/* Automated Post-Mortems */}
          <div className="flex items-center justify-between px-2">
            <h3 className="font-bold flex items-center gap-2 text-slate-100">
              <FileText className="w-4 h-4 text-rose-500" />
              Mesh Post-Mortems
            </h3>
            <span className="text-[10px] font-black bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">{postmortems.length}</span>
          </div>

          <div className="space-y-4">
            {postmortems.map((pm, i) => (
              <Card key={i} className="p-4 hover:border-rose-500/30 transition-all border-l-4 border-l-rose-500/50 bg-rose-500/5">
                <div className="flex justify-between items-start mb-2">
                  <Badge variant="critical">Self-Healed</Badge>
                  <span className="text-[10px] font-mono text-slate-600">{new Date(pm.generated_at).toLocaleDateString()}</span>
                </div>
                <h4 className="text-xs font-bold text-slate-200 mb-1">{pm.title}</h4>
                <p className="text-[10px] text-slate-500 mb-3 line-clamp-2">
                  {pm.impact_summary}
                </p>
                <button className="w-full py-2 bg-slate-950 border border-slate-800 rounded-lg text-[10px] font-bold text-slate-400 hover:text-white hover:border-slate-700 transition-all flex items-center justify-center gap-2">
                  <Wind className="w-3 h-3" />
                  View Incident Timeline
                </button>
              </Card>
            ))}
            {postmortems.length === 0 && (
              <div className="text-center py-10 border-2 border-dashed border-slate-800 rounded-2xl">
                <p className="text-xs text-slate-600">No mesh incidents recorded.</p>
              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
};
