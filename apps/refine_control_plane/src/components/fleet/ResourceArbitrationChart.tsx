"use client";

import React from "react";
import { BarChart3, Fingerprint } from "lucide-react";

interface TierStats {
  tier: number;
  label: string;
  count: number;
  usage_pct: number;
  limit: number;
}

interface ResourceArbitrationChartProps {
  stats: TierStats[];
}

export default function ResourceArbitrationChart({ stats }: ResourceArbitrationChartProps) {
  return (
    <div className="p-6 rounded-2xl bg-[#1f2833]/20 border border-[#45a29e]/20 backdrop-blur-xl flex flex-col h-full">
      <div className="flex items-center gap-3 mb-6">
        <BarChart3 className="text-[#66fcf1] w-6 h-6" />
        <div>
          <h3 className="text-lg font-black text-white tracking-tighter uppercase">Resource Arbitration</h3>
          <p className="text-[10px] text-[#45a29e] font-bold uppercase tracking-widest mt-1">Global Quota distribution per Isolation Tier</p>
        </div>
      </div>

      <div className="space-y-6 flex-grow">
        {stats.map((s) => (
          <div key={s.tier} className="space-y-2 group">
            <div className="flex justify-between items-end px-1">
              <div className="flex items-center gap-2">
                 <span className={`w-1.5 h-1.5 rounded-full ${s.tier === 0 ? 'bg-red-500 shadow-[0_0_8px_red]' : 'bg-blue-400'}`} />
                 <span className="text-[10px] font-black text-white uppercase tracking-tight">{s.label}</span>
                 <span className="text-[8px] text-[#45a29e] font-mono font-bold">(Tier {s.tier})</span>
              </div>
              <div className="text-right">
                 <span className="text-[12px] font-black text-[#66fcf1] font-mono">{s.usage_pct}%</span>
                 <span className="text-[8px] text-[#45a29e] ml-1 uppercase font-bold">In Use</span>
              </div>
            </div>
            
            <div className="h-2.5 bg-[#0b0c10]/60 rounded-full border border-[#1f2833] overflow-hidden group-hover:border-[#66fcf1]/30 transition-all shadow-inner">
               <div 
                 className={`h-full transition-all duration-1000 ease-out rounded-full 
                   ${s.usage_pct > 90 ? 'bg-gradient-to-r from-red-500 to-orange-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 
                     s.usage_pct > 70 ? 'bg-gradient-to-r from-yellow-400 to-yellow-600' : 
                     'bg-gradient-to-r from-blue-400 to-[#66fcf1]'}`}
                 style={{ width: `${s.usage_pct}%` }} 
               />
            </div>

            <div className="flex justify-between text-[8px] font-bold text-[#45a29e] uppercase tracking-tighter px-1">
               <span>{s.count} Active Projects</span>
               <span>Limit: {s.limit} Global Threads</span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 pt-6 border-t border-[#1f2833]/50">
         <div className="flex items-start gap-3 p-3 rounded-xl bg-blue-500/5 border border-blue-500/10">
            <Fingerprint className="text-blue-400 w-5 h-5 mt-0.5 shrink-0" />
            <p className="text-[9px] text-blue-400/80 leading-relaxed font-medium italic">
               * Preemption logic is active. Tier-0 (Mission Critical) requests will automatically force-pause Tier-3 (Sandbox) workloads if global thread limit exceeds 85%.
            </p>
         </div>
      </div>
    </div>
  );
}
