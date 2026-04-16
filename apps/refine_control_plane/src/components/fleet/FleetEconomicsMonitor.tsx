"use client";

import React from 'react';

interface EconomicsData {
  global_burn_rate: number;
  mesh_concurrency_total: number;
  forecast_window_hours: number;
}

export const FleetEconomicsMonitor: React.FC<{ data: EconomicsData }> = ({ data }) => {
  return (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl hover:bg-white/10 transition-all duration-300">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span className="w-2 h-6 bg-emerald-500 rounded-full inline-block"></span>
            Fleet Economics Monitor
          </h3>
          <p className="text-white/40 text-xs font-mono mt-1">REAL-TIME BURN & LOAD FORECASTING</p>
        </div>
        <div className="text-right">
          <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-[10px] font-bold tracking-widest uppercase">
            ACTIVE FORECAST
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* KPI: Global Burn Rate */}
        <div className="p-4 rounded-xl bg-black/20 border border-white/5">
          <p className="text-white/40 text-[10px] font-bold uppercase tracking-wider mb-1">Global Burn Rate</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-white">${data.global_burn_rate.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            <span className="text-xs text-white/20 font-mono">/HR</span>
          </div>
          <div className="mt-3 h-1 w-full bg-white/5 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 w-[65%]" />
          </div>
        </div>

        {/* KPI: Predictive Capacity */}
        <div className="p-4 rounded-xl bg-black/20 border border-white/5">
          <p className="text-white/40 text-[10px] font-bold uppercase tracking-wider mb-1">Forecast Load ({data.forecast_window_hours}H)</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-blue-400">+{Math.round(data.mesh_concurrency_total * 0.25)}</span>
            <span className="text-xs text-white/20 font-mono">TASKS</span>
          </div>
          <p className="text-[10px] text-blue-400/60 font-medium mt-2 flex items-center gap-1">
             <span className="animate-pulse">▲</span> TRENDING UPWARDS
          </p>
        </div>

        {/* KPI: Efficiency Score */}
        <div className="p-4 rounded-xl bg-black/20 border border-white/5">
          <p className="text-white/40 text-[10px] font-bold uppercase tracking-wider mb-1">Economic Efficiency</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-amber-500">92.4%</span>
          </div>
          <p className="text-[10px] text-white/30 font-medium mt-2">
            VS. PERFORMANCE BASELINE
          </p>
        </div>
      </div>

      {/* Region Cost Map Simulation (Simplified) */}
      <div className="mt-8">
        <div className="flex justify-between items-center mb-4">
            <h4 className="text-[10px] font-bold text-white/60 uppercase tracking-widest">Regional Cost Arbitrage</h4>
            <span className="text-[9px] text-white/20 font-mono underline cursor-help">REBALANCE POLICY: TIER-3 PRIORITY</span>
        </div>
        <div className="space-y-3">
            {[
                { name: 'us-east-1', cost: '$0.005', status: 'Optimal', color: 'bg-emerald-500' },
                { name: 'eu-central-1', cost: '$0.007', status: 'High Energy', color: 'bg-amber-500' },
                { name: 'ap-southeast-1', cost: '$0.008', status: 'Drained', color: 'bg-red-500' }
            ].map(r => (
                <div key={r.name} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5 hover:bg-white/[0.05] transition-all">
                    <div className="flex items-center gap-3">
                        <div className={`w-1.5 h-1.5 rounded-full ${r.color}`}></div>
                        <span className="text-xs font-bold text-white/80">{r.name}</span>
                    </div>
                    <div className="flex items-center gap-6">
                        <span className="text-[10px] font-mono text-white/40 uppercase">{r.status}</span>
                        <span className="text-xs font-black text-white">{r.cost}</span>
                    </div>
                </div>
            ))}
        </div>
      </div>
    </div>
  );
};
