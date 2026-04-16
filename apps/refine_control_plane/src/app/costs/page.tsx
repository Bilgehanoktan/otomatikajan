"use client";

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
  Activity
} from "lucide-react";

export default function CostsPage() {
  // Global Analytics
  const { query: { data: analyticsData, isLoading: isAnalyticsLoading } } = useOne({
    resource: "analytics/costs",
    id: "summary",
  });

  // Project-level Economics
  const { query: { data: projectsData, isLoading: isProjectsLoading } } = useList({
    resource: "projects",
    pagination: { pageSize: 100 },
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

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-[#66fcf1]/10 rounded-xl backdrop-blur-md border border-[#66fcf1]/20 shadow-[0_0_15px_rgba(102,252,241,0.2)]">
            <BarChart3 className="w-8 h-8 text-[#66fcf1]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#c5c6c7]">
              Cost Governance
            </h1>
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">Autonomous Spend Guardrails (Phase 24)</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
           <div className="px-4 py-2 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center gap-3">
              <Clock className="w-4 h-4 text-orange-400" />
              <div className="flex flex-col">
                 <span className="text-[10px] text-orange-400 font-black uppercase leading-none">Sovereignty Countdown</span>
                 <span className="text-white font-bold">{daysLeft} Days Remaining</span>
              </div>
           </div>
        </div>
      </header>

      {/* OVERVIEW CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <div className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/40 backdrop-blur-xl">
           <div className="flex justify-between items-center mb-6">
              <span className="text-gray-400 text-sm font-medium">Total Consumption</span>
              <DollarSign className="text-[#66fcf1]" size={20} />
           </div>
           <div className="flex items-baseline gap-2">
              <h2 className="text-4xl font-bold text-white">${stats.total_cost_usd.toFixed(2)}</h2>
              <span className="text-[#45a29e] text-xs">MTD</span>
           </div>
           <div className="mt-6 w-full h-2 bg-white/5 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-1000 ${stats.usage_pct > 80 ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-[#66fcf1] shadow-[0_0_10px_rgba(102,252,241,0.5)]'}`}
                style={{ width: `${Math.min(stats.usage_pct, 100)}%` }}
              ></div>
           </div>
           <div className="flex justify-between mt-2 text-[10px] uppercase font-bold tracking-tighter">
              <span className="text-[#45a29e]">{stats.usage_pct.toFixed(1)}% Usage</span>
              <span className="text-gray-500">Limit: ${stats.budget_limit_usd}</span>
           </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/40 backdrop-blur-xl">
           <div className="flex justify-between items-center mb-6">
              <span className="text-gray-400 text-sm font-medium">Fleet Burn Rate</span>
              <TrendingUp className="text-red-400" size={20} />
           </div>
           <div className="flex items-baseline gap-2">
              <h2 className="text-4xl font-bold text-white">${totalBurnRate.toFixed(2)}</h2>
              <span className="text-red-400 text-xs">/HR</span>
           </div>
           <p className="text-xs text-gray-500 mt-2">Aggregate across {projects.length} nodes</p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/40 backdrop-blur-xl">
           <div className="flex justify-between items-center mb-6">
              <span className="text-gray-400 text-sm font-medium">Auto-Scale Efficiency</span>
              <Zap className="text-yellow-400" size={20} />
           </div>
           <h2 className="text-4xl font-bold text-white">98.1%</h2>
           <p className="text-xs text-gray-500 mt-2">Resource allocation vs Idle time</p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/40 backdrop-blur-xl flex flex-col justify-center items-center">
            <ShieldAlert className={stats.usage_pct > 90 ? 'text-red-500 animate-bounce' : 'text-[#66fcf1]'} size={40} />
            <span className="mt-4 text-white font-bold uppercase tracking-widest text-xs">Guardrails Active</span>
            <span className="text-[10px] text-gray-500 mt-1">L1-L4 Autonomy Locked</span>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* PROJECT ECONOMIC LIST */}
        <section className="glass-panel rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl overflow-hidden shadow-2xl">
          <div className="p-6 border-b border-[#1f2833] flex justify-between items-center bg-gradient-to-b from-transparent to-[#0b0c10]/40">
            <h2 className="text-xl font-semibold text-white">Project Economics</h2>
            <Activity className="text-[#66fcf1]" size={20} />
          </div>
          
          <div className="p-6">
            {isProjectsLoading ? (
              <div className="h-40 flex items-center justify-center">
                 <div className="w-6 h-6 border-2 border-[#66fcf1] border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {projects.map((proj: any) => (
                  <div key={proj.id} className="group flex flex-col p-4 rounded-xl bg-white/5 border border-white/5 hover:border-[#66fcf1]/30 transition-all">
                    <div className="flex justify-between items-center mb-3">
                      <h3 className="text-white font-bold text-sm tracking-tight">{proj.title}</h3>
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-black ${proj.hourly_burn_rate > 5 ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
                        ${proj.hourly_burn_rate?.toFixed(2)}/hr
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                       <div className="flex-grow bg-white/5 h-1.5 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-[#66fcf1] to-blue-500"
                            style={{ width: `${Math.min((proj.current_budget_usd / 100) * 100, 100)}%` }}
                          ></div>
                       </div>
                       <span className="text-[10px] font-mono text-gray-500 font-bold">${proj.current_budget_usd?.toFixed(0)} LEFT</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* TOP EXPENSE DRIVERS */}
        <section className="glass-panel rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl overflow-hidden shadow-2xl">
          <div className="p-6 border-b border-[#1f2833] flex justify-between items-center bg-gradient-to-b from-transparent to-[#0b0c10]/40">
            <h2 className="text-xl font-semibold text-white">Global Spend Density</h2>
            <PieChart className="text-gray-500" size={20} />
          </div>
          
          <div className="p-6">
            {isAnalyticsLoading ? (
              <div className="h-40 flex items-center justify-center">
                 <div className="w-6 h-6 border-2 border-[#66fcf1] border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {stats.top_projects?.map((proj: any, idx: number) => (
                  <div key={proj.id} className="flex justify-between items-center p-4 rounded-lg bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                    <div className="flex items-center gap-4">
                      <span className="text-xs font-mono text-gray-600">{idx + 1}.</span>
                      <h3 className="text-white font-medium text-sm">{proj.title}</h3>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-[#66fcf1] font-bold font-mono">${proj.cost_usd.toFixed(2)}</span>
                      <ArrowUpRight size={14} className="text-gray-600" />
                    </div>
                  </div>
                )) || <div className="text-center py-10 text-gray-500">No data available.</div>}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
