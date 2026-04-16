"use client";

import React, { useState, useEffect } from "react";
import { 
  Boxes, 
  Activity, 
  Layers, 
  Cpu, 
  Zap,
  LayoutGrid,
  ShieldCheck,
  RefreshCcw,
  Search,
  Filter
} from "lucide-react";

import FleetHeatmap from "../../components/fleet/FleetHeatmap";
import ResourceArbitrationChart from "../../components/fleet/ResourceArbitrationChart";
import { FleetEconomicsMonitor } from "../../components/fleet/FleetEconomicsMonitor";
import { QuotaElasticityDetails } from "../../components/fleet/QuotaElasticityDetails";
import { FinancialGovernancePanel } from "../../components/fleet/FinancialGovernancePanel";

// API Base
const API_BASE = "http://localhost:8000/api/v1/fleet";

export default function FleetHub() {
  const [projects, setProjects] = useState<any[]>([]);
  const [arbitration, setArbitration] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState<string>("");

  const fetchFleetState = async () => {
    try {
      const statusRes = await fetch(`${API_BASE}/status`);
      const statusData = await statusRes.json();
      setStats(statusData); // Store full statusData for components
      setArbitration(statusData.arbitration);

      const projectsRes = await fetch(`${API_BASE}/projects`);
      const projectsData = await projectsRes.json();
      setProjects(projectsData);
      
      setLastSync(new Date().toLocaleTimeString());
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch fleet state:", err);
    }
  };

  useEffect(() => {
    fetchFleetState();
    const interval = setInterval(fetchFleetState, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0c10] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-[#66fcf1]">
           <RefreshCcw className="w-12 h-12 animate-spin" />
           <span className="font-black uppercase tracking-tighter">Synchronizing Fleet State...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 bg-[#0b0c10] text-[#c5c6c7]">
      {/* HEADER */}
      <header className="flex justify-between items-end mb-10">
        <div className="flex items-center gap-6">
          <div className="p-4 bg-blue-500/10 rounded-2xl border border-blue-500/20 shadow-[0_0_30px_rgba(59,130,246,0.1)]">
            <Boxes className="w-10 h-10 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-4xl font-black text-white tracking-tighter">Global Fleet Hub</h1>
              <span className="px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30 text-[10px] text-cyan-400 font-black uppercase">Phase 26</span>
            </div>
            <p className="text-[#45a29e] tracking-[0.2em] text-xs font-bold uppercase mt-1.5 opacity-80 flex items-center gap-2">
              <Activity size={12} /> Fleet-scale Multi-Project Orchestration
            </p>
          </div>
        </div>

        <div className="flex gap-4">
           {/* QUICK STATS */}
           <StatBox label="Total Projects" value={stats?.total_projects || 0} icon={<LayoutGrid size={14}/>} />
           <StatBox label="Active Threads" value={Math.round(arbitration.reduce((acc,s) => acc + s.usage_pct, 0))} icon={<Cpu size={14}/>} color="text-[#66fcf1]" />
           <div className="flex flex-col items-end gap-1 ml-4 justify-center">
              <span className="text-[10px] font-black text-[#45a29e] uppercase">Last Sync</span>
              <span className="text-xs font-mono text-white/60">{lastSync}</span>
           </div>
        </div>
      </header>

      {/* SEARCH / FILTER BAR */}
      <div className="flex gap-4 mb-8">
         <div className="flex-grow relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[#45a29e] w-4 h-4" />
            <input 
              type="text" 
              placeholder="SEARCH FLEET (ID, TAG, TIER)..."
              className="w-full bg-[#1f2833]/30 border border-[#1f2833] rounded-xl py-3 px-12 text-sm font-bold text-white placeholder:text-[#45a29e]/50 focus:outline-none focus:border-[#66fcf1]/50 transition-all"
            />
         </div>
         <button className="px-6 py-3 bg-[#1f2833]/50 border border-[#1f2833] rounded-xl flex items-center gap-2 text-xs font-black uppercase text-[#c5c6c7] hover:bg-[#1f2833] transition-all">
            <Filter size={14} /> Filters
         </button>
      </div>

      {/* MAIN GRID */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* HEATMAP - 2/3 Width */}
        <div className="xl:col-span-2 space-y-8">
           <FleetHeatmap projects={projects} />
           
           {/* FLEET ALERTS / LOGS */}
           <section className="p-6 rounded-2xl bg-[#0b0c10] border border-[#1f2833] h-[300px] overflow-hidden flex flex-col">
              <div className="flex items-center gap-3 mb-4">
                 <ShieldCheck className="text-green-400 w-5 h-5" />
                 <h3 className="text-sm font-black text-white uppercase tracking-tight">Fleet-wide Security Events</h3>
              </div>
              <div className="space-y-3 overflow-y-auto pr-2 custom-scrollbar">
                 <AlertItem tier={0} msg="PROJECT-782: Critical preemption event triggered by priority shift." time="2m ago" />
                 <AlertItem tier={1} msg="MESH: Regional workload re-balanced from us-east-1 to eu-central-1." time="5m ago" />
                 <AlertItem tier={3} msg="AUTONOMY: Project-Sandbox-99 breached local risk threshold. Advisory transition complete." time="12m ago" />
              </div>
           </section>
        </div>

        {/* SIDEBAR - 1/3 Width */}
        <div className="flex flex-col gap-8">
           <FleetEconomicsMonitor data={{
             global_burn_rate: stats?.global_burn_rate || 0,
             mesh_concurrency_total: stats?.mesh_concurrency_total || 0,
             forecast_window_hours: stats?.forecast_window_hours || 4
           }} />
           
           <QuotaElasticityDetails projects={projects} />
           
           <FinancialGovernancePanel projects={projects} />

           <ResourceArbitrationChart stats={arbitration} />
           
           {/* MASS ACTIONS */}
           <section className="p-6 rounded-2xl bg-gradient-to-br from-[#1f2833]/40 to-[#0b0c10] border border-[#45a29e]/20 backdrop-blur-xl">
             <div className="flex items-center gap-3 mb-6">
                <Zap className="text-yellow-400 w-6 h-6" />
                <h3 className="text-lg font-black text-white uppercase tracking-tighter">Mass Actions</h3>
             </div>
             <div className="grid gap-3">
                <ActionButton label="Quarantine Tier-3 Projects" mode="danger" />
                <ActionButton label="Freeze Low Priority Fleet" mode="warning" />
                <ActionButton label="Recalibrate Global Quotas" mode="primary" />
             </div>
             <p className="mt-6 text-[9px] text-[#45a29e] font-bold uppercase leading-relaxed text-center opacity-60">
                * Actions will propagate across all mesh regions within 15 seconds. Identity verification required for global state mutations.
             </p>
           </section>
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, value, icon, color = "text-white" }: { label: string, value: any, icon: any, color?: string }) {
  return (
    <div className="px-5 py-3 rounded-xl bg-[#1f2833]/30 border border-[#1f2833] flex flex-col gap-1 min-w-[140px]">
       <div className="flex items-center gap-1.5 text-[9px] font-black text-[#45a29e] uppercase">
          {icon} {label}
       </div>
       <div className={`text-xl font-black ${color} tracking-tighter`}>{value}</div>
    </div>
  );
}

function AlertItem({ tier, msg, time }: { tier: number, msg: string, time: string }) {
  return (
    <div className="flex items-start gap-4 p-3.5 rounded-xl bg-[#1f2833]/15 border border-[#1f2833]/30 hover:bg-[#1f2833]/25 transition-all group">
       <span className={`px-2 py-0.5 rounded text-[8px] font-black mt-0.5 ${tier === 0 ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>T{tier}</span>
       <div className="flex-grow">
          <p className="text-[11px] text-[#c5c6c7] font-medium group-hover:text-white transition-colors">{msg}</p>
          <span className="text-[9px] text-[#45a29e] font-mono mt-1 block">{time}</span>
       </div>
    </div>
  );
}

function ActionButton({ label, mode }: { label: string, mode: 'primary' | 'warning' | 'danger' }) {
  return (
    <button className={`w-full py-3.5 rounded-xl text-[10px] font-black uppercase tracking-tighter border transition-all active:scale-95 
      ${mode === 'primary' ? 'bg-[#66fcf1] text-[#0b0c10] border-[#66fcf1] hover:brightness-110 shadow-[0_0_15px_rgba(102,252,241,0.2)]' : 
        mode === 'warning' ? 'bg-transparent text-yellow-500 border-yellow-500/50 hover:bg-yellow-500/10' : 
        'bg-transparent text-red-500 border-red-500/50 hover:bg-red-500/10'}`}>
      {label}
    </button>
  );
}
