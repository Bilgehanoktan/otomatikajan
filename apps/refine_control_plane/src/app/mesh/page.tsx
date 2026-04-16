"use client";

import React, { useState, useEffect } from "react";
import { 
  Globe, 
  ShieldCheck, 
  Activity, 
  RefreshCcw,
  Zap,
  LayoutDashboard
} from "lucide-react";

// Import new Phase 22 components
import ChaosMap from "../../components/chaos/ChaosMap";
import QuorumHealthPanel from "../../components/chaos/QuorumHealthPanel";
import FailoverTimeline from "../../components/chaos/FailoverTimeline";
import OperatorConsole from "../../components/chaos/OperatorConsole";

// API Base (Simulated or relative)
const API_BASE = "http://localhost:8000/api/v1";

export default function MeshHub() {
  const [meshData, setMeshData] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [pulse, setPulse] = useState(0);

  const fetchMeshState = async () => {
    try {
      const statusRes = await fetch(`${API_BASE}/mesh/status`);
      const statusData = await statusRes.json();
      setMeshData(statusData);

      const timelineRes = await fetch(`${API_BASE}/mesh/timeline`);
      const timelineData = await timelineRes.json();
      setTimeline(timelineData);
      
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch mesh state:", err);
    }
  };

  useEffect(() => {
    fetchMeshState();
    const interval = setInterval(() => {
      setPulse(p => p + 1);
      fetchMeshState();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleOperatorAction = async (action: string, reason: string) => {
    try {
      const endpoint = action === 'recalibrate' ? '/mesh/actions/recalibrate' : 
                       action === 'freeze' ? '/mesh/actions/freeze' : 
                       `/mesh/actions/quarantine/ap-southeast-1`; // Example

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operator_id: "SOVEREIGN-ADMIN", reason })
      });
      const data = await res.json();
      console.log(`Action ${action} result:`, data);
      fetchMeshState(); // Refresh after action
    } catch (err) {
      console.error(`Action ${action} failed:`, err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0c10] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <RefreshCcw className="w-12 h-12 text-[#66fcf1] animate-spin" />
          <p className="text-[#45a29e] font-mono animate-pulse uppercase tracking-tighter">Syncing Mesh Topology...</p>
        </div>
      </div>
    );
  }

  const regions = Object.entries(meshData.regions).map(([id, data]: [string, any]) => ({
    id,
    name: id.replace(/-/g, ' ').toUpperCase(),
    role: data.role || 'STANDBY',
    health: data.latency > 500 ? 'critical' : (data.latency > 150 ? 'degraded' : 'healthy'),
    latency: data.latency
  }));

  return (
    <div className="min-h-screen p-8 bg-[#0b0c10] text-[#c5c6c7] selection:bg-[#66fcf1] selection:text-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-5">
          <div className="p-3.5 bg-[#66fcf1]/10 rounded-2xl backdrop-blur-md border border-[#66fcf1]/20 shadow-[0_0_20px_rgba(102,252,241,0.15)] group transition-all hover:scale-105">
            <Globe className="w-9 h-9 text-[#66fcf1] group-hover:animate-spin-slow transition-all" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-4xl font-black text-white tracking-tighter">Sovereign Mesh</h1>
              <span className="px-2 py-1 rounded bg-[#66fcf1]/10 border border-[#66fcf1]/20 text-[10px] text-[#66fcf1] font-black uppercase">v22.ChaosOps</span>
            </div>
            <p className="text-[#45a29e] tracking-[0.2em] text-xs font-bold uppercase mt-1.5 opacity-80 flex items-center gap-2">
              <Activity size={12} /> Global Federation Command Hub
            </p>
          </div>
        </div>
        
        <div className="flex gap-4">
          <div className="px-5 py-2.5 rounded-xl bg-[#1f2833]/50 border border-[#45a29e]/20 flex items-center gap-3 backdrop-blur-md">
            <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_green]"></div>
            <span className="text-xs text-[#c5c6c7] font-bold">Mesh Connectivity:</span>
            <span className="text-white font-black font-mono text-sm tracking-widest">{meshData.quorum_maintained ? 'OPTIMAL' : 'PARTITIONED'}</span>
          </div>
          <button 
             onClick={() => fetchMeshState()}
             className="flex items-center gap-2 px-6 py-2.5 bg-[#66fcf1] text-[#0b0c10] font-black uppercase tracking-tighter rounded-xl hover:brightness-110 transition-all shadow-[0_0_25px_rgba(102,252,241,0.4)] active:scale-95"
          >
            <LayoutDashboard className="w-4 h-4" />
            Recalibrate
          </button>
        </div>
      </header>

      {/* TOP ROW: MAIN VISUALS */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
        <div className="xl:col-span-2">
          <ChaosMap regions={regions} links={[]} />
        </div>
        <div className="flex flex-col gap-8">
          <QuorumHealthPanel 
            totalNodes={meshData.region_count.total} 
            healthyNodes={meshData.region_count.healthy} 
            isMaintained={meshData.quorum_maintained} 
          />
          <OperatorConsole onAction={handleOperatorAction} isLocked={!meshData.quorum_maintained} />
        </div>
      </div>

      {/* BOTTOM ROW: LOGS & MONITORING */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
           <FailoverTimeline events={timeline} />
        </div>
        
        {/* DRIFT MONITOR SUMMARY */}
        <section className="p-6 rounded-2xl border border-[#1f2833] bg-[#1f2833]/10 backdrop-blur-xl flex flex-col justify-center gap-6">
           <div className="flex items-center gap-3">
              <ShieldCheck className="text-blue-400 w-6 h-6" />
              <h3 className="text-lg font-bold text-white tracking-tight">Policy Drift Monitor</h3>
           </div>
           <div className="space-y-4">
              <DriftItem label="Emergency Policy" status="VALID" />
              <DriftItem label="Federation Weights" status="VALID" />
              <DriftItem label="Autonomy Thresholds" status="VALID" />
           </div>
           <p className="text-[10px] text-[#45a29e] font-mono bg-blue-500/5 p-3 rounded-lg border border-blue-500/10 leading-relaxed">
              * GitOps baseline checks performed every 60s. Any unauthorized mutation in regional config directories will trigger an immediate quarantine event.
           </p>
        </section>
      </div>
    </div>
  );
}

function DriftItem({ label, status }: { label: string, status: string }) {
  return (
    <div className="flex justify-between items-center p-3.5 rounded-xl bg-[#0b0c10]/40 border border-[#1f2833] group hover:border-blue-400/30 transition-all">
       <span className="text-xs font-bold text-[#c5c6c7] group-hover:text-white transition-colors">{label}</span>
       <span className="text-[10px] font-black font-mono text-blue-400 px-2 py-0.5 rounded bg-blue-400/10 border border-blue-400/20">{status}</span>
    </div>
  );
}
