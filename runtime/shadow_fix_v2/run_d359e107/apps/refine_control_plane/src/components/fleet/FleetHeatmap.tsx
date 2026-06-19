"use client";

import React from "react";

interface FleetProject {
  id: string;
  name: string;
  status: "healthy" | "warning" | "error" | "idle";
  load_pct: number; // 0-100
  tier: number;
}

interface FleetHeatmapProps {
  projects: FleetProject[];
}

export default function FleetHeatmap({ projects }: FleetHeatmapProps) {
  return (
    <div className="p-6 rounded-2xl bg-[#1f2833]/20 border border-[#45a29e]/20 backdrop-blur-xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-black text-white tracking-tighter uppercase">Global Fleet Heatmap</h3>
          <p className="text-[10px] text-[#45a29e] font-bold uppercase tracking-widest mt-1">Multi-Project Real-time state (n={projects.length})</p>
        </div>
        <div className="flex gap-4">
           <LegendItem color="bg-green-500" label="Healthy" />
           <LegendItem color="bg-yellow-500" label="Warning" />
           <LegendItem color="bg-red-500" label="Error" />
        </div>
      </div>

      <div className="grid grid-cols-10 sm:grid-cols-20 md:grid-cols-30 lg:grid-cols-40 gap-1.5 min-h-[120px]">
        {projects.map((p) => (
          <div key={p.id} className="group relative">
             <div 
               className={`w-4 h-4 rounded-sm transition-all duration-300 cursor-pointer 
                 ${p.status === 'healthy' ? 'bg-green-500/60 shadow-[0_0_5px_rgba(34,197,94,0.3)] hover:bg-green-400' : 
                   p.status === 'warning' ? 'bg-yellow-500/60 shadow-[0_0_5px_rgba(234,179,8,0.3)] hover:bg-yellow-400' : 
                   p.status === 'error' ? 'bg-red-500/60 shadow-[0_0_5px_rgba(239,68,68,0.3)] hover:bg-red-400 animate-pulse' : 
                   'bg-[#1f2833]/50 border border-[#45a29e]/10'}
                 ${p.load_pct > 80 ? 'brightness-150' : ''}
               `}
               style={{ opacity: 0.3 + (p.load_pct / 100) * 0.7 }}
             />
             {/* Simple Custom Tooltip (since we can't be sure of AntD setup) */}
             <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-3 bg-[#0b0c10] border border-[#66fcf1]/30 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 shadow-2xl">
                <div className="text-[10px] font-black text-[#66fcf1] mb-1">{p.name.toUpperCase()}</div>
                <div className="flex justify-between text-[9px] text-[#c5c6c7] font-mono">
                   <span>ID: {String(p.id).substring(0,8)}</span>
                   <span>Tier: {p.tier}</span>
                </div>
                <div className="mt-2 h-1 bg-[#1f2833] rounded-full overflow-hidden">
                   <div className="h-full bg-[#66fcf1]" style={{ width: `${p.load_pct}%` }} />
                </div>
                <div className="mt-1 text-right text-[8px] font-bold text-[#45a29e]">{p.load_pct}% Capacity</div>
             </div>
          </div>
        ))}
        
        {/* Fill empty spots to maintain grid if needed */}
        {Array.from({ length: Math.max(0, 100 - projects.length) }).map((_, i) => (
           <div key={`empty-${i}`} className="w-4 h-4 rounded-sm bg-[#1f2833]/10 border border-[#1f2833]/20" />
        ))}
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string, label: string }) {
  return (
    <div className="flex items-center gap-1.5">
       <div className={`w-2 h-2 rounded-full ${color}`} />
       <span className="text-[8px] font-black text-[#45a29e] uppercase tracking-tighter">{label}</span>
    </div>
  );
}
