"use client";

import React, { useState, useEffect } from "react";
import { 
  Boxes, 
  Activity, 
  Cpu, 
  Zap,
  LayoutGrid,
  ShieldCheck,
  RefreshCcw,
  Search,
  Filter,
  AlertTriangle,
  Clock,
  Globe,
  TrendingUp,
  Server,
  Terminal,
  Lock,
  ChevronRight
} from "lucide-react";

import FleetHeatmap from "../../components/fleet/FleetHeatmap";
import ResourceArbitrationChart from "../../components/fleet/ResourceArbitrationChart";
import { FleetEconomicsMonitor } from "../../components/fleet/FleetEconomicsMonitor";
import { QuotaElasticityDetails } from "../../components/fleet/QuotaElasticityDetails";
import { FinancialGovernancePanel } from "../../components/fleet/FinancialGovernancePanel";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";

// API Base
const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
const API_BASE = `${API_URL}/fleet`;

export default function FleetHub() {
  const [isClient, setIsClient] = useState(false);
  const [projects, setProjects] = useState<any[]>([]);
  const [arbitration, setArbitration] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState<string>("");

  useEffect(() => { setIsClient(true); }, []);

  const fetchFleetState = async () => {
    try {
      const statusData = await safeFetchJson(`${API_BASE}/status`);
      setStats(statusData); 
      setArbitration(statusData.arbitration || []);

      const projectsData = await safeFetchJson(`${API_BASE}/projects`);
      setProjects(projectsData || []);
      
      setLastSync(new Date().toLocaleTimeString());
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch fleet state:", err);
    }
  };

  useEffect(() => {
    if (!isClient) return;
    fetchFleetState();
    const interval = setInterval(fetchFleetState, 5000);
    return () => clearInterval(interval);
  }, [isClient]);

  if (!isClient || loading) {
    return (
      <div className="min-h-screen bg-[#060a12] flex items-center justify-center p-8">
        <div className="w-full max-w-7xl space-y-8">
           <Skeleton className="h-24 w-full rounded-2xl" />
           <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 space-y-8">
                  <Skeleton className="h-[400px] w-full rounded-3xl" />
                  <Skeleton className="h-[300px] w-full rounded-3xl" />
              </div>
              <div className="space-y-8">
                  <Skeleton className="h-64 w-full rounded-3xl" />
                  <Skeleton className="h-64 w-full rounded-3xl" />
              </div>
           </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Fleet Hub" 
        subtitle="Autonomous Multi-project Orchestration & Resource Arbitration" 
        icon={<Boxes size={32} />}
        badge="Enterprise Core"
        actions={
          <div className="flex items-center gap-6">
             <div className="flex items-center gap-4 bg-white/[0.02] border border-white/5 px-6 py-2 rounded-2xl">
                <div className="text-right">
                   <p className="text-[8px] text-gray-500 font-black uppercase tracking-widest leading-none">Global Load</p>
                   <p className="text-xs font-black text-[var(--primary)] mt-1.5">78.4% NOMINAL</p>
                </div>
                <div className="w-[px] h-6 bg-white/10 mx-2" />
                <div className="text-right">
                   <p className="text-[8px] text-gray-500 font-black uppercase tracking-widest leading-none">Cluster Health</p>
                   <p className="text-xs font-black text-white mt-1.5">{stats?.total_projects || 0} ZONES</p>
                </div>
             </div>
             
             <button className="p-4 bg-[var(--primary)]/10 text-[var(--primary)] rounded-2xl border border-[var(--primary)]/20 hover:bg-[var(--primary)]/20 transition-all active:scale-95 shadow-xl">
                <TrendingUp size={20} />
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* HEATMAP / MAIN MONITOR - Left Column */}
        <div className="xl:col-span-8 flex flex-col gap-10">
           {/* Orchestration Map */}
           <section className="glass-panel p-2 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.015] to-transparent shadow-[0_32px_64px_rgba(0,0,0,0.4)]">
              <div className="p-8 pb-2 border-b border-white/[0.03] flex justify-between items-center bg-black/20 rounded-t-[2.5rem]">
                 <div className="flex items-center gap-3">
                    <Globe size={18} className="text-[var(--primary)] animate-spin-slow" />
                    <h3 className="text-[10px] font-black text-white uppercase tracking-[0.3em]">Federated Heatmap</h3>
                 </div>
                 <div className="flex items-center gap-4 text-[9px] font-mono text-gray-600 uppercase">
                    <span>Precision: 0.001ms</span>
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
                 </div>
              </div>
              <div className="p-6">
                 <FleetHeatmap projects={projects} />
              </div>
           </section>
           
           {/* OPERATIONAL LOGS / ALERTS */}
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-[#060a12]/50 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity pointer-events-none">
                 <Terminal size={140} />
              </div>

              <div className="flex items-center justify-between mb-8 relative z-10">
                 <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shadow-[0_0_12px_rgba(251,191,36,0.6)]" />
                    <h3 className="text-[10px] font-black text-white uppercase tracking-[0.3em]">Fleet Integrity Logs</h3>
                 </div>
                 <div className="flex items-center gap-6">
                    <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">DRIVE_ID: SOV-M-17</span>
                    <span className="text-[9px] font-mono text-gray-600 uppercase">SYNC: {lastSync}</span>
                 </div>
              </div>

              <div className="space-y-4 overflow-y-auto pr-3 custom-scrollbar max-h-[400px]">
                 <EliteAlertItem tier={0} msg="PROJECT-782: Critical priority shift detected. Triggering immediate pre-emption event across us-east-1." time="2m ago" zone="US-EAST" />
                 <EliteAlertItem tier={1} msg="NETWORK: Mesh topology readjusted for latency balancing. Regional traffic routed through eu-central-1." time="5m ago" zone="EU-CENTRAL" />
                 <EliteAlertItem tier={3} msg="AUTONOMY: Sandbox-99 Project exceeded regional risk threshold. Advisory transition complete." time="12m ago" zone="AP-SOUTH" />
                 <EliteAlertItem tier={1} msg="QUOTA: Global elasticity threshold reached 85%. Scaling event successfully queued." time="18m ago" zone="GLOBAL" />
                 <EliteAlertItem tier={2} msg="COMPLIANCE: Auto-audit sealed for project group 'Alpha-9'. Proof of decision established." time="24m ago" zone="US-WEST" />
              </div>
           </section>
        </div>

        {/* SIDEBAR - Right Column */}
        <div className="xl:col-span-4 flex flex-col gap-10">
           {/* Economics Section */}
           <div className="glass-panel rounded-[2.5rem] overflow-hidden border-white/[0.05] shadow-2xl">
              <div className="p-8 bg-black/10 border-b border-white/[0.03]">
                 <div className="flex items-center gap-3">
                    <Activity size={18} className="text-emerald-400" />
                    <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Resource Economics</h3>
                 </div>
              </div>
              <div className="p-8">
                 <FleetEconomicsMonitor data={{
                   global_burn_rate: stats?.global_burn_rate || 0,
                   mesh_concurrency_total: stats?.mesh_concurrency_total || 0,
                   forecast_window_hours: stats?.forecast_window_hours || 4
                 }} />
              </div>
           </div>
           
           {/* Elasticity Details */}
           <div className="glass-panel p-10 rounded-[2.5rem] border-white/[0.05] bg-white/[0.012] group hover:border-[var(--primary)]/20 transition-all">
              <div className="flex items-center gap-3 mb-8">
                 <Cpu size={18} className="text-[var(--primary)]" />
                 <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Quota Elasticity</h3>
              </div>
              <QuotaElasticityDetails projects={projects} />
           </div>

           {/* Arbitration Analysis */}
           <div className="glass-panel p-10 rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/80">
              <div className="flex items-center gap-3 mb-8">
                 <Server size={18} className="text-blue-400" />
                 <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Arbitration Analysis</h3>
              </div>
              <ResourceArbitrationChart stats={arbitration} />
           </div>
           
           {/* COMMAND CONTROL PANEL */}
           <section className="glass-panel p-10 rounded-[3rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.05] to-transparent relative overflow-hidden group">
             <div className="relative z-10">
               <div className="flex flex-col gap-2 mb-10">
                  <div className="flex items-center justify-between">
                     <div className="flex items-center gap-3">
                        <Zap className="text-[var(--primary)] w-8 h-8 animate-pulse" />
                        <h3 className="text-2xl font-black text-white uppercase tracking-tighter">Strategic Deck</h3>
                     </div>
                     <Lock size={16} className="text-gray-600" />
                  </div>
                  <p className="text-[10px] text-gray-500 font-bold tracking-widest uppercase">Emergency System Override Controls</p>
               </div>
               
               <div className="grid gap-4">
                  <EliteActionButton label="Contain Tier-3 Projects" mode="danger" />
                  <EliteActionButton label="Drain Low Priority Fleet" mode="warning" />
                  <EliteActionButton label="Global Quota Recalibration" mode="primary" />
               </div>
               
               <div className="mt-10 pt-8 border-t border-white/[0.05] flex flex-col items-center gap-4">
                  <p className="text-[9px] text-gray-600 font-black uppercase tracking-[0.2em] leading-relaxed text-center opacity-80 max-w-[240px]">
                     Propagation window across all zones is ~15s. Requires Quorum sign-off.
                  </p>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/40 border border-white/5">
                     <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)]" />
                     <span className="text-[8px] font-bold text-gray-500 uppercase tracking-widest">Protocol: Active-Active</span>
                  </div>
               </div>
             </div>
             
             {/* Holographic grid background */}
             <div className="absolute inset-x-0 bottom-0 top-1/2 bg-[var(--primary)]/[0.02] mask-gradient pointer-events-none" 
                  style={{ backgroundImage: 'linear-gradient(rgba(102, 252, 241, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(102, 252, 241, 0.1) 1px, transparent 1px)', backgroundSize: '20px 20px' }} />
             
             <div className="absolute -bottom-16 -right-16 w-48 h-48 bg-[var(--primary)]/10 blur-[80px] rounded-full group-hover:bg-[var(--primary)]/20 transition-all duration-1000" />
           </section>
        </div>
      </div>
    </div>
  );
}

function EliteAlertItem({ tier, msg, time, zone }: { tier: number, msg: string, time: string, zone: string }) {
  const isCritical = tier === 0;
  const colors = isCritical 
    ? {
        border: 'border-red-500/30',
        bg: 'bg-red-500/[0.02]',
        badge: 'text-red-500 bg-red-500/10 border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.2)]',
        accent: 'bg-red-400'
      }
    : {
        border: 'border-white/5',
        bg: 'bg-white/[0.01]',
        badge: 'text-[var(--primary)] bg-[var(--primary)]/10 border-[var(--primary)]/20',
        accent: 'bg-[var(--primary)]'
      };
  
  return (
    <div className={`flex items-start gap-6 p-6 rounded-3xl border transition-all duration-500 hover:bg-white/[0.04] hover:border-white/10 group ${colors.border} ${colors.bg}`}>
       <div className="flex flex-col items-center gap-2">
          <span className={`px-2.5 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border transition-all ${colors.badge}`}>T{tier}</span>
          <div className={`w-0.5 h-full min-h-[40px] rounded-full opacity-10 ${colors.accent}`} />
       </div>
       
       <div className="flex-grow">
          <div className="flex items-center justify-between mb-2">
             <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">{zone} NODE ACCESS</span>
             <div className="flex items-center gap-2">
                <Clock size={10} className="text-gray-700" />
                <span className="text-[9px] text-gray-600 font-mono font-bold tracking-widest uppercase">{time}</span>
             </div>
          </div>
          <p className={`text-[11px] font-bold leading-relaxed tracking-tight transition-colors group-hover:text-white ${isCritical ? 'text-red-200' : 'text-gray-400'}`}>
            {msg}
          </p>
       </div>
    </div>
  );
}

function EliteActionButton({ label, mode }: { label: string, mode: 'primary' | 'warning' | 'danger' }) {
  const variants = {
    primary: "bg-[var(--primary)] text-[#060a12] border-[var(--primary)]/50 hover:shadow-[0_12px_48px_rgba(102,252,241,0.4)]",
    warning: "bg-transparent text-amber-500 border-amber-500/20 hover:bg-amber-500/10 hover:border-amber-500/50",
    danger: "bg-transparent text-red-500 border-red-500/20 hover:bg-red-500/10 hover:border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.05)]"
  };

  return (
    <button className={`w-full py-5 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] border transition-all duration-500 active:scale-95 flex items-center justify-center gap-3 group/btn ${variants[mode]}`}>
      {label}
      <ChevronRight size={14} className="group-hover/btn:translate-x-1 transition-transform" />
    </button>
  );
}
