"use client";

import React, { useState, useEffect } from "react";
import { useOne, useList } from "@refinedev/core";
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  PieChart, 
  ArrowUpRight, 
  ShieldAlert, 
  Clock, 
  Zap,
  TrendingDown,
  Activity,
  Lock,
  ChevronRight,
  Server,
  Globe,
  Wallet,
  ArrowRight
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function CostsPage() {
  const [isClient, setIsClient] = useState(false);
  useEffect(() => setIsClient(true), []);

  // Global Analytics
  const { query: { data: analyticsData, isLoading: isAnalyticsLoading } } = useOne({
    resource: "governance/analytics/costs",
    id: "summary",
    queryOptions: { enabled: isClient }
  });

  // Project-level Economics
  const { query: { data: projectsData, isLoading: isProjectsLoading } } = useList({
    resource: "projects",
    pagination: { pageSize: 100 },
    queryOptions: { enabled: isClient }
  });

  const stats = analyticsData?.data ?? {
    total_cost_usd: 0,
    budget_limit_usd: 1000,
    usage_pct: 0,
    top_projects: []
  };

  const projects = projectsData?.data ?? [];
  const totalBurnRate = projects.reduce((acc, p) => acc + (p.hourly_burn_rate || 0), 0);
  const totalBudget = projects.reduce((acc, p) => acc + (p.current_budget_usd || 0), 0);
  
  // Calculate "Days of Sovereignty"
  const hoursLeft = totalBurnRate > 0 ? totalBudget / totalBurnRate : 0;
  const daysLeft = (hoursLeft / 24).toFixed(1);

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Cost Governance" 
        subtitle="Autonomous Financial Guardrails & Sovereignty Runway" 
        icon={<Wallet size={32} />}
        badge="Financial Tier-1"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Sovereignty Runway</span>
                <div className="flex items-center gap-3 mt-2 group cursor-help">
                   <Clock className="w-4 h-4 text-orange-400 group-hover:animate-spin-slow" />
                   <span className="text-sm font-black text-white group-hover:text-orange-400 transition-colors uppercase tracking-tight">{daysLeft} Days Remaining</span>
                </div>
             </div>
             <button className="flex items-center gap-2 px-8 py-3 bg-[var(--primary)] text-[#060a12] text-[10px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95">
                <ShieldAlert size={14} />
                <span>Adjust Guardrails</span>
             </button>
          </div>
        }
      />

      {/* OVERVIEW CARDS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-8 mb-10">
         <EliteCostCard 
            label="Total Consumption" 
            val={`$${(stats.total_cost_usd ?? 0).toFixed(2)}`} 
            subtitle="MTD Aggregate" 
            icon={<DollarSign size={18} />} 
            progress={stats.usage_pct}
            limit={`Limit: $${stats.budget_limit_usd ?? 1000}`}
         />
         <EliteCostCard 
            label="Fleet Burn Rate" 
            val={`$${(totalBurnRate ?? 0).toFixed(2)}`} 
            subtitle="Aggregate / Hour" 
            icon={<TrendingUp size={18} />} 
            accent="text-red-400"
         />
         <EliteCostCard 
            label="Scale Efficiency" 
            val="98.1%" 
            subtitle="Resource Optimization" 
            icon={<Zap size={18} />} 
            accent="text-[var(--primary)]"
         />
         <div className="glass-panel p-10 rounded-[2.5rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.03] to-transparent flex flex-col items-center justify-center text-center group relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:opacity-[0.06] transition-opacity">
               <Lock size={120} />
            </div>
            <div className={`p-4 rounded-2xl bg-black/40 border border-white/5 mb-4 group-hover:scale-110 transition-transform duration-500 ${stats.usage_pct > 90 ? 'text-red-500' : 'text-[var(--primary)]'}`}>
               <Lock size={28} />
            </div>
            <span className="text-white font-black text-xs uppercase tracking-widest group-hover:text-[var(--primary)] transition-colors">Guardrails Locked</span>
            <span className="text-[9px] text-gray-700 font-bold uppercase tracking-[0.2em] mt-2 italic">L1-L4 Policy Engaged</span>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* LEFT COLUMN: Project Economics List */}
        <div className="lg:col-span-12 xl:col-span-7">
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <Server size={240} />
              </div>
              
              <div className="flex items-center justify-between mb-12 relative z-10 px-2">
                 <div className="flex items-center gap-4">
                    <div className="p-4 bg-emerald-500/10 rounded-[1.5rem] border border-emerald-500/20 shadow-xl">
                       <Activity className="text-emerald-400" size={24} />
                    </div>
                    <div>
                       <h2 className="text-2xl font-black text-white italic uppercase tracking-tighter">Autonomous Spend Units</h2>
                       <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.3em] mt-1">Real-time Budget Drain Analysis</p>
                    </div>
                 </div>
                 <div className="flex items-center gap-6">
                    <div className="flex items-center gap-4 text-[10px] font-mono text-gray-700 bg-black/40 px-6 py-3 rounded-2xl border border-white/5">
                       <Globe size={16} className="text-[var(--primary)]" />
                       GLOBAL_SYNDICATE_ACTIVE
                    </div>
                 </div>
              </div>

              <div className="space-y-4 relative z-10 custom-scrollbar pr-2 max-h-[600px] overflow-y-auto">
                 {isProjectsLoading ? <Skeleton className="h-96 rounded-3xl" /> : (
                   projects.map((proj: any) => (
                     <div key={proj.id} className="p-6 rounded-[2rem] bg-white/[0.015] border border-white/5 hover:bg-white/[0.025] hover:border-[var(--primary)]/30 transition-all group/unit cursor-pointer">
                        <div className="flex justify-between items-center mb-6 px-2">
                           <div className="flex items-center gap-5">
                              <div className="w-10 h-10 rounded-xl bg-black/40 flex items-center justify-center border border-white/5 text-gray-600 group-hover/unit:text-[var(--primary)] group-hover/unit:border-[var(--primary)]/20 transition-all">
                                 <Zap size={20} />
                              </div>
                              <div>
                                 <h4 className="text-white font-black text-sm uppercase tracking-tight group-hover/unit:text-[var(--primary)] transition-colors">{proj.title}</h4>
                                 <p className="text-[9px] text-gray-700 font-mono tracking-widest mt-1 uppercase">NODE_ID: {proj.id.substring(0,8)}</p>
                              </div>
                           </div>
                           <div className="text-right">
                              <p className={`text-xs font-black font-mono tracking-tighter ${(proj.hourly_burn_rate ?? 0) > 5 ? 'text-red-400' : 'text-green-400'}`}>${(proj.hourly_burn_rate ?? 0).toFixed(2)}/HR</p>
                              <p className="text-[9px] text-gray-800 font-black uppercase mt-1 tracking-widest">Aggregate Burn</p>
                           </div>
                        </div>
                        
                        <div className="flex items-center gap-6 p-5 rounded-2xl bg-[#060a12]/80 border border-white/5 group-hover/unit:border-[var(--primary)]/20 transition-all">
                           <div className="flex-grow">
                              <div className="flex justify-between items-baseline mb-2">
                                 <span className="text-[9px] text-gray-700 font-black uppercase tracking-widest">Budget Remaining</span>
                                 <span className="text-[10px] font-mono font-black text-white italic">${(proj.current_budget_usd ?? 0).toFixed(0)} LEFT</span>
                              </div>
                              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
                                 <div 
                                   className="h-full bg-gradient-to-r from-[var(--primary)] to-emerald-500 shadow-[0_0_10px_rgba(102,252,241,0.2)]"
                                   style={{ width: `${Math.min((proj.current_budget_usd / 100) * 100, 100)}%` }}
                                 />
                              </div>
                           </div>
                           <button className="p-3 bg-white/5 rounded-xl text-gray-600 hover:text-white hover:bg-white/10 transition-all">
                              <ChevronRight size={18} />
                           </button>
                        </div>
                     </div>
                   ))
                 )}
              </div>
           </section>
        </div>

        {/* RIGHT COLUMN: Expense Drivers & Analysis */}
        <div className="lg:col-span-12 xl:col-span-5 flex flex-col gap-10">
           {/* Spend Density */}
           <section className="glass-panel p-10 rounded-[3rem] border-white/[0.03] bg-[#060a12]/50 relative overflow-hidden group shadow-xl">
              <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:opacity-[0.08] transition-opacity">
                 <PieChart size={140} className="text-[var(--primary)]" />
              </div>
              <div className="flex items-center justify-between mb-10 relative z-10">
                 <div className="flex items-center gap-3">
                    <PieChart size={20} className="text-[var(--primary)]" />
                    <h3 className="text-xs font-black text-white uppercase tracking-[0.3em]">Spend Density Radar</h3>
                 </div>
                 <button className="p-2.5 bg-white/5 border border-white/10 rounded-xl text-gray-600 hover:text-white transition-all">
                    <ArrowUpRight size={16} />
                 </button>
              </div>

              <div className="space-y-4 relative z-10">
                 {isAnalyticsLoading ? <Skeleton className="h-64 rounded-2xl" /> : (
                   stats.top_projects?.map((proj: any, idx: number) => (
                     <div key={proj.id} className="flex justify-between items-center p-6 rounded-[1.5rem] bg-white/[0.015] border border-white/5 hover:border-white/10 hover:bg-white/[0.025] transition-all group/driver">
                        <div className="flex items-center gap-5">
                           <span className="text-[10px] font-mono text-gray-700 font-black">0{idx + 1}.</span>
                           <h3 className="text-white font-black text-xs uppercase tracking-tight group-hover/driver:text-[var(--primary)] transition-colors">{proj.title}</h3>
                        </div>
                        <div className="flex items-center gap-5">
                           <span className="text-white font-black font-mono text-sm tracking-tighter">${(proj.cost_usd ?? 0).toFixed(2)}</span>
                           <div className="w-1.5 h-1.5 rounded-full bg-gray-900 group-hover/driver:bg-[var(--primary)] shadow-[0_0_8px_currentColor] transition-colors" />
                        </div>
                     </div>
                   )) || <div className="text-center py-10 text-gray-500 text-[11px] font-black uppercase tracking-widest">No exposure detected.</div>
                 )}
              </div>
           </section>

           {/* Autonomous Recommendation HUD */}
           <section className="glass-panel p-10 rounded-[3rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.05] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="absolute -bottom-10 -right-10 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-1000">
                 <Zap size={200} className="text-yellow-400" />
              </div>
              <h3 className="text-xs font-black text-white mb-8 flex items-center gap-3 uppercase tracking-[0.3em] relative z-10 italic">
                 <Zap size={20} className="text-yellow-400 animate-pulse" />
                 Tactical Economics
              </h3>
              
              <div className="p-8 rounded-[2rem] bg-black/40 border border-white/5 relative z-10 mb-8">
                 <p className="text-[11px] text-gray-500 font-bold leading-loose uppercase tracking-widest mb-6">
                    Sistem otonom olarak `Cluster eu-central-1` üzerindeki kaynak kullanımını %12 optimize ederek aylık $45 tasarruf öngörüyor.
                 </p>
                 <button className="w-full flex items-center justify-center gap-3 py-5 bg-[var(--primary)] text-[#060a12] font-black text-xs uppercase tracking-[0.2em] hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all rounded-2xl active:scale-95 group/btn">
                    Optimization Apply
                    <ArrowRight size={16} className="group-hover/btn:translate-x-2 transition-transform" />
                 </button>
              </div>
              
              <div className="flex items-center justify-between px-2 relative z-10 opacity-60">
                 <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Decision Confidence</span>
                 <span className="text-[10px] font-mono text-yellow-500">94.2%</span>
              </div>
           </section>
        </div>
      </div>
    </div>
  );
}

function EliteCostCard({ label, val, subtitle, icon, progress, accent = "text-white", limit }: any) {
  return (
    <div className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-white/[0.012] group hover:border-white/10 hover:bg-white/[0.025] transition-all relative overflow-hidden">
       <div className="flex justify-between items-center mb-10">
          <span className="text-[10px] text-gray-600 font-black uppercase tracking-[0.2em]">{label}</span>
          <div className="p-3 bg-black/40 rounded-xl border border-white/5 text-gray-600 group-hover:text-white group-hover:border-white/20 transition-all shadow-xl">
             {icon}
          </div>
       </div>
       <div className="flex flex-col mb-8">
          <h2 className={`text-4xl font-black tracking-tighter ${accent} transition-colors`}>{val}</h2>
          <span className="text-[9px] text-gray-700 font-black uppercase tracking-[0.3em] mt-3 italic">{subtitle}</span>
       </div>
       
       {progress !== undefined && (
         <div className="mt-4 pt-10 border-t border-white/[0.03]">
            <div className="flex justify-between items-baseline mb-2">
               <span className="text-[10px] font-mono text-[var(--primary)] font-black">{progress.toFixed(1)}% Usage</span>
               <span className="text-[9px] text-gray-700 font-black uppercase tracking-widest leading-none">{limit}</span>
            </div>
            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
               <div 
                 className={`h-full transition-all duration-1000 ${progress > 80 ? 'bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.4)]' : 'bg-[var(--primary)] shadow-[0_0_12px_rgba(102,252,241,0.4)]'}`}
                 style={{ width: `${Math.min(progress, 100)}%` }}
               />
            </div>
         </div>
       )}
    </div>
  );
}


