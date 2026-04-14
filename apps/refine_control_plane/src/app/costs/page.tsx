"use client";

import { useOne } from "@refinedev/core";
import { BarChart3, TrendingUp, DollarSign, PieChart, ArrowUpRight, ShieldAlert } from "lucide-react";

export default function CostsPage() {
  const { query: { data, isLoading, isError } } = useOne({
    resource: "analytics/costs",
    id: "summary", // Dummy ID since it's a singleton stat
  });

  const stats = data?.data ?? {
    total_cost_usd: 0,
    budget_limit_usd: 1000,
    usage_pct: 0,
    top_projects: []
  };

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
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">Autonomous Spend Guardrails</p>
          </div>
        </div>
      </header>

      {/* OVERVIEW CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
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
              <span className="text-gray-400 text-sm font-medium">Auto-Scale Efficiency</span>
              <TrendingUp className="text-green-400" size={20} />
           </div>
           <h2 className="text-4xl font-bold text-white">94.2%</h2>
           <p className="text-xs text-gray-500 mt-2">Resource allocation vs Idle time</p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/40 backdrop-blur-xl flex flex-col justify-center items-center">
            <ShieldAlert className={stats.usage_pct > 90 ? 'text-red-500 animate-bounce' : 'text-[#45a29e]'} size={40} />
            <span className="mt-4 text-white font-bold uppercase tracking-widest text-xs">Guardrails Active</span>
            <span className="text-[10px] text-gray-500 mt-1">L1-L4 Autonomy Locked</span>
        </div>
      </div>

      {/* TOP PROJECTS LIST */}
      <section className="glass-panel rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-[#1f2833] flex justify-between items-center bg-gradient-to-b from-transparent to-[#0b0c10]/40">
          <h2 className="text-xl font-semibold text-white">Top Expense Drivers</h2>
          <PieChart className="text-gray-500" size={20} />
        </div>
        
        <div className="p-6">
          {isLoading ? (
            <div className="h-40 flex items-center justify-center">
               <div className="w-6 h-6 border-2 border-[#66fcf1] border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {stats.top_projects.map((proj: any, idx: number) => (
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
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
