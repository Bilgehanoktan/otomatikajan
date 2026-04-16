"use client";

import React, { useState } from "react";
import { 
  Network, 
  Cpu, 
  Gavel, 
  Activity, 
  ShieldCheck, 
  Zap, 
  Info, 
  Server, 
  Flame, 
  CheckCircle2,
  AlertOctagon,
  Globe,
  Waves
} from "lucide-react";

export default function FederationPage() {
  const [hoveredCluster, setHoveredCluster] = useState<string | null>(null);

  const clusters = [
    { id: "sec-overwatch", name: "Security Cluster", status: "Active", trust: 0.98, load: 12, region: "us-east-1", color: "text-red-400", bg: "bg-red-400" },
    { id: "logic-cortex", name: "Domain Logic", status: "Active", trust: 0.95, load: 68, region: "eu-central-1", color: "text-[#66fcf1]", bg: "bg-[#66fcf1]" },
    { id: "ops-reflex", name: "Infra & Ops", status: "Active", trust: 0.97, load: 24, region: "ap-southeast-1", color: "text-blue-400", bg: "bg-blue-400" },
    { id: "cost-guardian", name: "Cost Economy", status: "Active", trust: 0.99, load: 2, region: "us-west-1", color: "text-green-400", bg: "bg-green-400" },
  ];

  const arbitrations = [
    { id: "ARB-102", type: "Conflict", target: "libs/auth/rbac.py", winner: "Security Cluster", reason: "Priority Precedence (10 > 5)", time: "10m ago", complexity: "High" },
    { id: "ARB-101", type: "Consensus", target: "workflow_api/main.py", winner: "Logic Cortex", reason: "Single Proposer", time: "45m ago", complexity: "Low" },
  ];

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10] text-[#c5c6c7]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-12">
        <div className="flex items-center gap-6">
          <div className="p-4 bg-purple-500/10 rounded-2xl backdrop-blur-xl border border-purple-500/20 shadow-[0_0_30px_rgba(168,85,247,0.25)]">
            <Network className="w-10 h-10 text-purple-400 animate-pulse" />
          </div>
          <div>
            <h1 className="text-4xl font-black text-white tracking-tighter uppercase italic">Federation.Hub</h1>
            <p className="text-[#45a29e] tracking-[0.4em] text-[10px] font-black uppercase mt-1.5 opacity-60">Consolidated Intelligence Matrix • Phase 19</p>
          </div>
        </div>

        <div className="flex items-center gap-8">
           <div className="flex flex-col items-end">
              <span className="text-[10px] text-purple-400 font-black uppercase tracking-[0.2em]">Consensus Quorum</span>
              <div className="flex items-center gap-2 mt-1">
                 <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map(i => (
                       <div key={i} className={`w-3 h-3 rounded-sm ${i <= 5 ? 'bg-purple-500 shadow-[0_0_8px_#a855f7]' : 'bg-white/5'}`}></div>
                    ))}
                 </div>
                 <span className="text-white font-black text-sm ml-2">5/5</span>
              </div>
           </div>
           <div className="w-[1px] h-12 bg-white/10"></div>
           <div className="px-5 py-3 bg-white/5 border border-white/10 rounded-2xl flex items-center gap-4">
              <div className="flex flex-col">
                 <span className="text-[9px] text-gray-500 font-black uppercase">Active Clusters</span>
                 <span className="text-xl font-black text-[#66fcf1]">04</span>
              </div>
              <Waves className="text-[#66fcf1] animate-bounce" size={20} />
           </div>
        </div>
      </header>

      {/* CLUSTER MONITOR GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 mb-12">
         {clusters.map((c) => (
            <div 
               key={c.id} 
               onMouseEnter={() => setHoveredCluster(c.id)}
               onMouseLeave={() => setHoveredCluster(null)}
               className="glass-panel p-8 rounded-[2.5rem] border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-2xl hover:border-purple-500/40 transition-all group relative overflow-hidden"
            >
               <div className={`absolute top-0 right-0 p-10 opacity-5 group-hover:opacity-10 transition-opacity ${c.color}`}>
                  <Cpu size={120} />
               </div>

               <div className="flex justify-between items-start mb-8 relative z-10">
                  <div className={`p-4 rounded-2xl bg-white/5 ${c.color} border border-white/10 shadow-xl group-hover:scale-110 transition-transform`}>
                     <Cpu size={24} />
                  </div>
                  <div className="flex flex-col items-end">
                     <span className={`text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-tighter ${c.status === 'Active' ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/10 text-gray-400'}`}>
                        {c.status}
                     </span>
                     <span className="text-[8px] text-gray-600 font-mono mt-1">{c.region}</span>
                  </div>
               </div>

               <div className="relative z-10">
                  <h3 className="text-white font-black text-lg mb-1 group-hover:text-purple-400 transition-colors uppercase">{c.name}</h3>
                  <p className="text-[10px] text-gray-500 font-mono mb-8 tracking-widest">{c.id}</p>
                  
                  <div className="grid grid-cols-2 gap-8 border-t border-white/5 pt-8">
                     <div>
                        <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-2 flex items-center gap-2">
                           <ShieldCheck size={12} className={c.color} />
                           Trust
                        </p>
                        <p className={`${c.color} font-black text-2xl font-mono tracking-tighter`}>{(c.trust * 100).toFixed(0)}%</p>
                     </div>
                     <div>
                        <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-2 flex items-center gap-2">
                           <Activity size={12} className={c.color} />
                           Load
                        </p>
                        <p className="text-white font-black text-2xl font-mono tracking-tighter">{c.load}%</p>
                     </div>
                  </div>

                  <div className="mt-6">
                     <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                        <div className={`h-full ${c.bg} transition-all duration-1000`} style={{ width: `${c.load}%` }}></div>
                     </div>
                  </div>
               </div>
            </div>
         ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
         {/* ARBITRATION LOG */}
         <div className="lg:col-span-3 glass-panel p-8 rounded-[2.5rem] border border-[#1f2833] bg-[#0b0c10]/40 overflow-hidden relative">
            <div className="absolute top-0 right-0 p-8 opacity-[0.03] pointer-events-none">
               <Gavel size={200} />
            </div>
            
            <div className="flex items-center justify-between mb-10 relative z-10">
               <div className="flex items-center gap-4">
                  <div className="p-3 bg-purple-500/10 rounded-xl border border-purple-500/20">
                     <Gavel className="text-purple-400" size={24} />
                  </div>
                  <div>
                     <h2 className="text-2xl font-black text-white italic uppercase tracking-tighter">Arbitration Ledger</h2>
                     <p className="text-[9px] text-[#45a29e] font-black uppercase tracking-[0.3em]">Decision Integrity Stream</p>
                  </div>
               </div>
               <button className="px-5 py-2 bg-white/5 border border-white/10 rounded-xl text-[10px] font-black text-gray-400 hover:text-white transition-colors uppercase tracking-widest">
                  View Full History
               </button>
            </div>
            
            <div className="space-y-4 relative z-10">
               {arbitrations.map(a => (
                  <div key={a.id} className="p-6 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.05] hover:border-[#66fcf1]/30 transition-all group/item">
                     <div className="flex justify-between items-start mb-6">
                        <div className="flex items-center gap-4">
                           <span className="text-[11px] font-black font-mono p-1.5 bg-purple-500/20 text-purple-300 rounded-lg tracking-tighter border border-purple-500/20">{a.id}</span>
                           <div>
                              <h4 className="text-white font-black text-sm tracking-tight">{a.target}</h4>
                              <span className="text-[10px] text-gray-500 font-mono">{a.type} Detected</span>
                           </div>
                        </div>
                        <div className="text-right">
                           <span className="text-[10px] text-gray-600 font-black block uppercase mb-1">{a.time}</span>
                           <span className={`text-[9px] font-black border px-2 py-0.5 rounded ${a.complexity === 'High' ? 'text-orange-400 border-orange-500/20 bg-orange-500/5' : 'text-blue-400 border-blue-500/20 bg-blue-500/5'}`}>
                              Complexity: {a.complexity}
                           </span>
                        </div>
                     </div>
                     <div className="flex items-center justify-between gap-6 mt-4 p-4 rounded-2xl bg-[#0b0c10]/60 border border-white/5">
                        <div className="flex items-center gap-4">
                           <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center text-green-400 shadow-[0_0_15px_rgba(34,197,94,0.1)]">
                              <ShieldCheck size={20} />
                           </div>
                           <div>
                              <p className="text-[10px] text-gray-500 font-black uppercase mb-1">Winning Cluster</p>
                              <p className="text-white font-black text-sm uppercase tracking-tight">{a.winner}</p>
                           </div>
                        </div>
                        <div className="flex-1 text-right">
                           <p className="text-[10px] text-gray-500 font-black uppercase mb-1">Resolution Logic</p>
                           <p className="text-xs text-[#66fcf1] italic font-mono">" {a.reason} "</p>
                        </div>
                     </div>
                  </div>
               ))}
            </div>
         </div>

         {/* SIDEBAR: SPECIALIZATION HEATMAP */}
         <div className="flex flex-col gap-8">
            <section className="glass-panel p-8 rounded-[2.5rem] border border-[#1f2833] bg-[#0b0c10]/40 relative overflow-hidden group">
               <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
               <h3 className="text-white font-black text-xs mb-8 flex items-center gap-3 uppercase tracking-widest relative z-10">
                  <Flame size={18} className="text-orange-500 animate-pulse" />
                  Specialization Heatmap
               </h3>
               <div className="space-y-8 relative z-10">
                  <HeatmapBar label="Logic Synapse" value={88} color="bg-[#66fcf1]" shadow="shadow-[#66fcf1]/30" />
                  <HeatmapBar label="Security Gate" value={94} color="bg-red-500" shadow="shadow-red-500/30" />
                  <HeatmapBar label="Economic Steering" value={42} color="bg-green-500" shadow="shadow-green-500/30" />
                  <HeatmapBar label="Infrastructure" value={76} color="bg-blue-400" shadow="shadow-blue-400/30" />
               </div>
            </section>

            <section className="p-8 rounded-[2rem] border border-purple-500/20 bg-purple-500/[0.03] backdrop-blur-3xl">
               <h3 className="text-purple-400 font-black text-xs mb-6 flex items-center gap-3 uppercase tracking-widest">
                  <Info size={18} />
                  Cluster Protocols
               </h3>
               <ul className="space-y-4">
                  <li className="flex gap-4 group cursor-help">
                     <CheckCircle2 size={16} className="text-[#66fcf1] shrink-0" />
                     <p className="text-[11px] text-gray-400 leading-relaxed group-hover:text-white transition-colors uppercase tracking-tighter">Consensus required for all resource mutations in P0 zones.</p>
                  </li>
                  <li className="flex gap-4 group cursor-help">
                     <CheckCircle2 size={16} className="text-[#66fcf1] shrink-0" />
                     <p className="text-[11px] text-gray-400 leading-relaxed group-hover:text-white transition-colors uppercase tracking-tighter">Heartbeat telemetry broadcasting every 400ms via mesh-bus.</p>
                  </li>
                  <li className="flex gap-4 group cursor-help">
                     <AlertOctagon size={16} className="text-orange-500 shrink-0 animate-pulse" />
                     <p className="text-[11px] text-gray-400 leading-relaxed group-hover:text-white transition-colors uppercase tracking-tighter">Drift limit: 0.2% variance allowed before cluster quarantine.</p>
                  </li>
               </ul>
            </section>
         </div>
      </div>
    </div>
  );
}

function HeatmapBar({ label, value, color, shadow }: any) {
  return (
    <div className="group cursor-help">
       <div className="flex justify-between items-end mb-2">
          <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest group-hover:text-white transition-colors">{label}</span>
          <span className={`text-[11px] font-black font-mono tracking-tighter ${color.replace('bg-', 'text-')}`}>{value}%</span>
       </div>
       <div className="w-full bg-white/5 h-2.5 rounded-sm overflow-hidden border border-white/5">
          <div className={`h-full ${color} ${shadow} transition-all duration-1000 shadow-[0_0_10px_currentColor]`} style={{ width: `${value}%` }}></div>
       </div>
    </div>
  );
}
