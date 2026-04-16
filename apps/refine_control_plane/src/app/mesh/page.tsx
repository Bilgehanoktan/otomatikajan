"use client";

import React, { useState, useEffect } from "react";
import { 
  Globe, 
  ShieldCheck, 
  Activity, 
  RefreshCcw,
  Zap,
  LayoutDashboard,
  ArrowRightLeft,
  Lock,
  Unlock,
  AlertOctagon,
  Radar
} from "lucide-react";

import ChaosMap from "../../components/chaos/ChaosMap";
import QuorumHealthPanel from "../../components/chaos/QuorumHealthPanel";
import FailoverTimeline from "../../components/chaos/FailoverTimeline";
import OperatorConsole from "../../components/chaos/OperatorConsole";

const API_BASE = "http://localhost:8000/api/v1";

export default function MeshHub() {
  const [meshData, setMeshData] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [interceptActive, setInterceptActive] = useState(false);

  const fetchMeshState = async () => {
    try {
      // 1. Fetch Topology for ChaosMap
      const topoRes = await fetch(`${API_BASE}/fleet/mesh/topology`);
      const topoData = await topoRes.json();
      setMeshData(topoData);

      // 2. Fetch Evidence for Timeline
      const evidenceRes = await fetch(`${API_BASE}/fleet/evidence?limit=15`);
      const evidenceData = await evidenceRes.json();
      
      const formattedTimeline = evidenceData.map((e: any) => ({
          id: e.id,
          title: e.type.replace(/_/g, ' ').toUpperCase(),
          timestamp: new Date(e.created_at).toLocaleTimeString(),
          status: e.severity === 'critical' ? 'critical' : e.severity === 'warning' ? 'warning' : 'healthy',
          details: e.payload.reason || e.payload.target || "Operational Event Trace"
      }));
      setTimeline(formattedTimeline);
      
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch mesh state:", err);
    }
  };

  useEffect(() => {
    fetchMeshState();
    const interval = setInterval(fetchMeshState, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleOperatorAction = async (action: string, reason: string) => {
    // Simulated API call for demo
    console.log(`Executing operator action: ${action} for ${reason}`);
    fetchMeshState();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0c10] flex items-center justify-center">
        <div className="flex flex-col items-center gap-6">
          <div className="relative">
             <RefreshCcw className="w-16 h-16 text-[#66fcf1] animate-spin opacity-20" />
             <Radar className="w-8 h-8 text-[#66fcf1] absolute inset-0 m-auto animate-pulse" />
          </div>
          <p className="text-[#45a29e] font-black animate-pulse uppercase tracking-[0.3em] text-[10px]">Syncing Mesh Topology...</p>
        </div>
      </div>
    );
  }

  const regions = Object.entries(meshData.regions).map(([id, data]: [string, any]) => ({
    id,
    name: id.replace(/-/g, ' ').toUpperCase(),
    role: data.role || 'STANDBY',
    health: (data.latency > 500 ? 'critical' : (data.latency > 150 ? 'degraded' : 'healthy')) as "healthy" | "critical" | "degraded",
    latency: data.latency
  }));

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10] text-[#c5c6c7]">
      {/* HEADER */}
      <header className="flex justify-between items-start mb-12">
        <div className="flex items-center gap-6">
          <div className="p-4 bg-[#66fcf1]/10 rounded-2xl backdrop-blur-xl border border-[#66fcf1]/20 shadow-[0_0_30px_rgba(102,252,241,0.2)] group hover:rotate-3 transition-transform">
            <Globe className="w-10 h-10 text-[#66fcf1] group-hover:animate-spin-slow" />
          </div>
          <div>
            <div className="flex items-center gap-4 mb-1">
              <h1 className="text-4xl font-black text-white tracking-tighter uppercase italic">Control.Mesh</h1>
              <div className="px-3 py-1 rounded bg-[#66fcf1] text-[#0b0c10] text-[9px] font-black uppercase tracking-widest shadow-[0_0_15px_#66fcf1]">LIVE</div>
            </div>
            <p className="text-[#45a29e] tracking-[0.4em] text-[10px] font-black uppercase opacity-60">Global Sovereignty Protocol • Phase 22</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
           <div className="flex flex-col items-end gap-1">
              <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Global Sync Lag</span>
              <span className="text-2xl font-black text-white font-mono leading-none">0.04<span className="text-xs text-[#66fcf1]">ms</span></span>
           </div>
           <div className="w-[1px] h-10 bg-white/10"></div>
           <button 
              onClick={() => fetchMeshState()}
              className="group flex items-center gap-3 px-8 py-4 bg-white/5 border border-white/10 text-white font-black uppercase tracking-tighter rounded-2xl hover:bg-[#66fcf1] hover:text-[#0b0c10] transition-all active:scale-95 shadow-xl"
           >
             <RefreshCcw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
             Re-Sync Federation
           </button>
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-8 mb-12">
        {/* TOP LEFT: MAP */}
        <div className="xl:col-span-3">
          <ChaosMap regions={regions} links={[]} />
        </div>

        {/* TOP RIGHT: QUORUM & CONSOLE */}
        <div className="flex flex-col gap-8">
           <QuorumHealthPanel 
             totalNodes={meshData.region_count.total} 
             healthyNodes={meshData.region_count.healthy} 
             isMaintained={meshData.quorum_maintained} 
           />
           
           {/* REGIONAL TRAFFIC INTERCEPTOR */}
           <section className="glass-panel p-6 rounded-3xl border border-[#1f2833] bg-[#1f2833]/10 backdrop-blur-xl relative overflow-hidden group">
              <div className={`absolute inset-0 bg-red-500/10 pointer-events-none transition-opacity duration-500 ${interceptActive ? 'opacity-100' : 'opacity-0'}`}></div>
              <h3 className="text-white font-black text-xs uppercase tracking-widest mb-6 flex items-center justify-between">
                 <div className="flex items-center gap-2">
                    <ArrowRightLeft size={16} className="text-[#66fcf1]" />
                    Traffic Interceptor
                 </div>
                 {interceptActive ? <AlertOctagon size={16} className="text-red-500 animate-pulse" /> : <Lock size={16} className="text-gray-500" />}
              </h3>
              
              <div className="space-y-4">
                 <button 
                  onClick={() => setInterceptActive(!interceptActive)}
                  className={`w-full py-3 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] border transition-all ${
                    interceptActive 
                    ? 'bg-red-500/20 border-red-500 text-red-500 shadow-[0_0_20px_rgba(239,68,68,0.3)]' 
                    : 'bg-white/5 border-white/10 text-gray-400 opacity-60'
                  }`}>
                    {interceptActive ? 'OVERRIDE ACTIVE' : 'ENGAGE SECURITY OVERRIDE'}
                 </button>
                 
                 <div className="grid grid-cols-2 gap-3">
                    <InterceptControl label="Reroute" icon={<RefreshCcw size={10}/>} active={interceptActive} />
                    <InterceptControl label="Throttle" icon={<Zap size={10}/>} active={interceptActive} />
                 </div>
              </div>
              
              {!interceptActive && (
                 <div className="absolute inset-x-0 bottom-0 top-12 bg-[#0b0c10]/40 backdrop-blur-[2px] z-10 flex items-center justify-center">
                    <div className="flex flex-col items-center gap-2 opacity-40">
                       <Lock size={20} />
                       <span className="text-[10px] font-black">LOCKED - AUTH REQ</span>
                    </div>
                 </div>
              )}
           </section>

           <OperatorConsole onAction={handleOperatorAction} isLocked={!meshData.quorum_maintained} />
        </div>
      </div>

      {/* BOTTOM ROW: LOGS & MONITORING */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-3">
           <FailoverTimeline events={timeline} />
        </div>
        
        <section className="p-8 rounded-3xl border border-[#1f2833] bg-[#1f2833]/15 backdrop-blur-3xl flex flex-col gap-8 shadow-2xl relative overflow-hidden group">
           <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
              <ShieldCheck size={120} />
           </div>
           
           <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20">
                 <ShieldCheck className="text-blue-400 w-6 h-6" />
              </div>
              <div>
                 <h3 className="text-xl font-black text-white tracking-tighter uppercase">Audit Policy</h3>
                 <p className="text-[9px] text-blue-400 font-black tracking-widest uppercase">Drift Monitor v4.1</p>
              </div>
           </div>
           
           <div className="space-y-4 relative z-10">
              <DriftItem label="Emergency Failover" status="OPTIMAL" />
              <DriftItem label="Quorum Weights" status="SYNCED" />
              <DriftItem label="Key Rotation" status="ACTIVE" />
           </div>

           <div className="mt-auto p-4 rounded-2xl bg-[#0b0c10]/60 border border-white/5">
              <p className="text-[10px] text-[#45a29e] font-bold leading-relaxed mb-3">
                 <span className="text-white">SECURITY NOTICE:</span> Multi-region drift detection is currently enforcing strict parity across all 4 zones.
              </p>
              <div className="flex justify-between items-center text-[9px] font-black uppercase text-gray-500">
                 <span>Baseline Hash:</span>
                 <span className="font-mono text-white/40">7F2A...9E11</span>
              </div>
           </div>
        </section>
      </div>
    </div>
  );
}

function InterceptControl({ label, icon, active }: { label: string, icon: any, active: boolean }) {
  return (
    <button disabled={!active} className={`flex flex-col items-center p-3 rounded-xl border border-white/5 bg-white/5 transition-all ${
      active ? 'hover:bg-white/10 hover:border-[#66fcf1] text-[#c5c6c7] hover:text-white' : 'opacity-20 text-gray-500'
    }`}>
       <div className="mb-2 p-1.5 bg-[#0b0c10] rounded-lg">{icon}</div>
       <span className="text-[9px] font-black uppercase tracking-tighter">{label}</span>
    </button>
  );
}

function DriftItem({ label, status }: { label: string, status: string }) {
  return (
    <div className="flex justify-between items-center p-4 rounded-2xl bg-[#0b0c10]/40 border border-white/5 group hover:border-blue-400/30 transition-all cursor-help">
       <span className="text-xs font-black text-gray-400 group-hover:text-white transition-colors uppercase tracking-tight">{label}</span>
       <div className="flex items-center gap-3">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400 shadow-[0_0_8px_#3b82f6]"></div>
          <span className="text-[10px] font-black font-mono text-blue-400 px-2 py-0.5 rounded bg-blue-400/10 border border-blue-400/20">{status}</span>
       </div>
    </div>
  );
}
