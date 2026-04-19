"use client";

import React, { useState, useEffect } from "react";
import { 
  Globe, 
  ShieldCheck, 
  Activity, 
  RefreshCcw,
  Zap,
  ArrowRightLeft,
  Lock,
  Unlock,
  AlertOctagon,
  Radar,
  Terminal,
  Server,
  Network,
  Cpu,
  Fingerprint,
  RotateCcw,
  Layers,
  Search,
  Filter
} from "lucide-react";

import ChaosMap from "../../components/chaos/ChaosMap";
import QuorumHealthPanel from "../../components/chaos/QuorumHealthPanel";
import FailoverTimeline from "../../components/chaos/FailoverTimeline";
import OperatorConsole from "../../components/chaos/OperatorConsole";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

const API_BASE = "/api/v1";

export default function MeshHub() {
  const [isClient, setIsClient] = useState(false);
  const [meshData, setMeshData] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [interceptActive, setInterceptActive] = useState(false);

  useEffect(() => { setIsClient(true); }, []);

  const fetchMeshState = async () => {
    try {
      const topoRes = await fetch(`${API_BASE}/fleet/mesh/topology`);
      const topoData = await topoRes.json();
      setMeshData(topoData);

      const evidenceRes = await fetch(`${API_BASE}/fleet/evidence?limit=15`);
      const evidenceData = await evidenceRes.json();
      
      const formattedTimeline = evidenceData.map((e: any) => ({
          event_id: e.id,
          region_id: e.payload.region || "global",
          action: e.type.replace(/_/g, ' ').toUpperCase(),
          timestamp: e.created_at,
          details: { 
            reason: e.payload.reason || e.payload.target || "Operational Event Trace" 
          }
      }));
      setTimeline(formattedTimeline);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch mesh state:", err);
    }
  };

  useEffect(() => {
    if (!isClient) return;
    fetchMeshState();
    const interval = setInterval(fetchMeshState, 5000);
    return () => clearInterval(interval);
  }, [isClient]);

  const handleOperatorAction = async (action: string, reason: string) => {
    console.log(`Executing operator action: ${action} for ${reason}`);
    fetchMeshState();
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  const regions = meshData ? Object.entries(meshData.regions).map(([id, data]: [string, any]) => ({
    id,
    name: id.replace(/-/g, ' ').toUpperCase(),
    role: data.role || 'STANDBY',
    health: (data.latency > 500 ? 'critical' : (data.latency > 150 ? 'degraded' : 'healthy')) as "healthy" | "critical" | "degraded",
    latency: data.latency
  })) : [];

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Control Mesh" 
        subtitle="Global High-Availability & Crisis Orchestration Grid" 
        icon={<Globe size={32} />}
        badge="Phase 22 Stable"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Global Sync</span>
                <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono tracking-tighter italic">0.04 MS NOMINAL</span>
             </div>
             <button 
               onClick={fetchMeshState}
               className="group p-4 bg-white/5 border border-white/5 rounded-2xl text-[var(--primary)] hover:text-white hover:bg-white/10 transition-all active:scale-95 shadow-xl"
             >
                <RotateCcw size={18} className={loading && !meshData ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-1000'} />
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* LEFT COLUMN: GLOBAL VIEW */}
        <div className="xl:col-span-8 flex flex-col gap-10">
           {/* MAP CONTAINER */}
           <div className="glass-panel p-2 rounded-[3rem] border-white/[0.05] bg-black/40 shadow-2xl relative overflow-hidden group">
              <div className="absolute top-10 left-10 z-10 p-5 bg-black/60 rounded-3xl border border-white/5 backdrop-blur-xl">
                 <div className="flex items-center gap-3 mb-4">
                    <Radar size={18} className="text-[var(--primary)] animate-pulse" />
                    <h3 className="text-[10px] font-black text-white uppercase tracking-[0.25em]">Live Topology</h3>
                 </div>
                 <div className="space-y-3">
                    <RegionMiniStat status="healthy" label="Europe-North" />
                    <RegionMiniStat status="healthy" label="Americas-East" />
                    <RegionMiniStat status="degraded" label="Asia-Pacific" />
                 </div>
              </div>
              
              {loading && !meshData ? (
                 <Skeleton className="h-[600px] w-full rounded-[2.8rem]" />
              ) : (
                <ChaosMap regions={regions} links={[]} />
              )}
           </div>

           {/* TIMELINE */}
           <div className="glass-panel p-1 rounded-[2.5rem] border-white/[0.03] bg-white/[0.01]">
              <FailoverTimeline events={timeline} />
           </div>
        </div>

        {/* RIGHT COLUMN: CONTROL & POLICY */}
        <div className="xl:col-span-4 flex flex-col gap-10">
           {/* QUORUM HEALTH */}
           <section className="glass-panel p-10 rounded-[3rem] border-white/[0.05] bg-gradient-to-br from-white/[0.015] to-transparent shadow-2xl">
              <div className="flex items-center gap-4 mb-10">
                 <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-xl">
                    <Activity size={24} className="text-[var(--primary)]" />
                 </div>
                 <div>
                    <h3 className="text-xl font-black text-white tracking-tighter uppercase leading-tight">Quorum Status</h3>
                    <p className="text-[9px] text-gray-500 font-black tracking-widest uppercase mt-1">Global Consensus Health</p>
                 </div>
              </div>
              <QuorumHealthPanel 
                totalNodes={meshData?.region_count?.total || 4} 
                healthyNodes={meshData?.region_count?.healthy || 4} 
                isMaintained={meshData?.quorum_maintained ?? true} 
              />
           </section>

           {/* TRAFFIC INTERCEPTOR */}
           <section className="glass-panel p-10 rounded-[3rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.03] to-transparent relative overflow-hidden group shadow-2xl">
              <div className={`absolute inset-0 bg-red-500/[0.03] pointer-events-none transition-opacity duration-1000 ${interceptActive ? 'opacity-100' : 'opacity-0'}`} />
              
              <div className="flex items-center justify-between mb-10 relative z-10 px-2">
                 <div className="flex items-center gap-4">
                    <div className="p-3 bg-black/40 rounded-xl border border-white/5 text-[var(--primary)]">
                       <ArrowRightLeft size={18} />
                    </div>
                    <h3 className="text-xs font-black text-white uppercase tracking-[0.3em] italic leading-tight">Traffic Hub</h3>
                 </div>
                 {interceptActive ? (
                   <div className="flex items-center gap-2">
                      <span className="text-[8px] font-black text-red-500 animate-pulse tracking-widest uppercase">OVERRIDE Engaging</span>
                      <AlertOctagon size={16} className="text-red-500 animate-pulse" /> 
                   </div>
                 ) : (
                   <Fingerprint size={16} className="text-gray-600" />
                 )}
              </div>
              
              <div className="space-y-6 relative z-10">
                 <button 
                  onClick={() => setInterceptActive(!interceptActive)}
                  className={`w-full py-5 rounded-2xl font-black text-[10px] uppercase tracking-[0.3em] border transition-all active:scale-95 shadow-xl ${
                    interceptActive 
                    ? 'bg-red-500/10 border-red-500/40 text-red-500 shadow-[0_0_40px_rgba(239,68,68,0.2)] hover:bg-red-500/20' 
                    : 'bg-white/5 border-white/10 text-gray-600 hover:text-white hover:border-white/20'
                  }`}>
                    {interceptActive ? 'Deactivate Security Override' : 'Engage Security Override'}
                 </button>
                 
                 <div className="grid grid-cols-2 gap-4">
                    <EliteInterceptControl label="Reroute" icon={<RefreshCcw size={14}/>} active={interceptActive} />
                    <EliteInterceptControl label="Throttle" icon={<Zap size={14}/>} active={interceptActive} />
                 </div>
              </div>
              
              {!interceptActive && (
                 <div className="absolute inset-x-0 bottom-0 top-[110px] bg-[#060a12]/70 backdrop-blur-[6px] z-20 flex flex-col items-center justify-center gap-4 border-t border-white/[0.03] animate-in fade-in duration-700">
                    <div className="p-4 bg-black/60 rounded-full border border-white/5 text-gray-700 shadow-inner">
                       <Lock size={24} />
                    </div>
                    <span className="text-[10px] font-black text-gray-700 uppercase tracking-[0.4em] italic">Operator Authority Required</span>
                 </div>
              )}
           </section>

           {/* POLICY DRIFT */}
           <section className="glass-panel p-10 rounded-[3rem] border-white/[0.03] bg-white/[0.012] relative overflow-hidden group shadow-xl">
              <div className="absolute top-0 right-0 p-8 opacity-[0.01] pointer-events-none text-[var(--primary)] group-hover:opacity-[0.03] transition-opacity">
                 <ShieldCheck size={200} />
              </div>
              
              <div className="flex items-center gap-4 mb-10 relative z-10 px-2">
                 <div className="p-3 bg-blue-500/10 rounded-2xl border border-blue-500/20 text-blue-400 shadow-xl">
                    <ShieldCheck size={20} />
                 </div>
                 <h3 className="text-xl font-black text-white tracking-tighter uppercase italic">Drift Policy</h3>
              </div>
              
              <div className="space-y-4 relative z-10">
                 <EliteDriftItem label="Emergency Failover" status="OPTIMAL" />
                 <EliteDriftItem label="Quorum Weights" status="SYNCED" />
                 <EliteDriftItem label="Baseline Parity" status="NOMINAL" />
              </div>

              <div className="mt-10 p-6 rounded-3xl bg-black/40 border border-white/5 border-l-2 border-l-[var(--primary)] relative z-10">
                 <p className="text-[10px] text-gray-600 font-bold leading-relaxed mb-6">
                    <span className="text-white text-[9px] font-black uppercase tracking-widest block mb-2 underline decoration-[var(--primary)] decoration-2">Security Notice</span>
                    Multi-region drift detection is currently enforcing strict parity across all zones.
                 </p>
                 <div className="flex justify-between items-center text-[9px] font-black uppercase text-gray-700 font-mono">
                    <div className="flex items-center gap-2">
                       <Terminal size={12} />
                       Baseline:
                    </div>
                    <span className="tracking-[0.2em] italic opacity-40">7F2A...9E11</span>
                 </div>
              </div>
           </section>

           <div className="glass-panel p-1 rounded-[2.5rem] border-white/[0.05] bg-white/[0.01] shadow-2xl">
              <OperatorConsole onAction={handleOperatorAction} isLocked={!meshData?.quorum_maintained} />
           </div>
        </div>
      </div>
    </div>
  );
}

function RegionMiniStat({ status, label }: { status: "healthy" | "critical" | "degraded", label: string }) {
  return (
    <div className="flex items-center gap-3 group/mini">
       <div className={`w-1.5 h-1.5 rounded-full ${status === 'healthy' ? 'bg-green-500' : status === 'degraded' ? 'bg-amber-500' : 'bg-red-500'} shadow-[0_0_8px_rgba(255,255,255,0.1)]`} />
       <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest group-hover/mini:text-white transition-colors">{label}</span>
    </div>
  );
}

function EliteInterceptControl({ label, icon, active }: { label: string, icon: any, active: boolean }) {
  return (
    <button 
      disabled={!active} 
      className={`flex flex-col items-center gap-4 p-6 rounded-3xl border transition-all duration-500 shadow-xl ${
        active 
          ? 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-[var(--primary)]/40 text-gray-400 hover:text-white group/btn' 
          : 'bg-black/40 border-white/5 opacity-10 cursor-not-allowed text-gray-800'
      }`}
    >
       <div className={`p-3 rounded-2xl transition-all shadow-inner ${active ? 'bg-black/60 text-[var(--primary)] group-hover/btn:scale-125' : 'bg-transparent text-gray-900'}`}>
         {icon}
       </div>
       <span className="text-[10px] font-black uppercase tracking-[0.2em]">{label}</span>
    </button>
  );
}

function EliteDriftItem({ label, status }: { label: string, status: string }) {
  return (
    <div className="flex justify-between items-center p-5 rounded-2xl bg-white/[0.012] border border-white/5 border-r-0 group/item hover:bg-white/[0.025] hover:border-blue-400/30 transition-all cursor-help shadow-lg">
       <div className="flex items-center gap-4">
          <Server size={14} className="text-gray-700 group-hover/item:text-blue-400 transition-colors" />
          <span className="text-[11px] font-black text-gray-600 group-hover/item:text-white transition-colors uppercase tracking-tight">{label}</span>
       </div>
       <div className="flex items-center gap-3">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.6)] group-hover/item:animate-ping" />
          <span className="text-[10px] font-black font-mono text-blue-400 px-3 py-1 rounded-xl bg-blue-400/10 border border-blue-400/30 tracking-widest">{status}</span>
       </div>
    </div>
  );
}
