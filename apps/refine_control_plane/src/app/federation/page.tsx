"use client";

import React, { useState } from "react";
import { Network, Cpu, GitBranch, Gavel, Database, Activity, ShieldCheck, Zap, TrendingUp, Info } from "lucide-react";

export default function FederationPage() {
  const [activeTask, setActiveTask] = useState<string | null>(null);

  const clusters = [
    { id: "sec-overwatch", name: "Security Cluster", status: "Active", trust: 0.98, load: 12, color: "text-red-400" },
    { id: "logic-cortex", name: "Domain Logic", status: "Active", trust: 0.94, load: 45, color: "text-[#66fcf1]" },
    { id: "ops-reflex", name: "Infra & Ops", status: "Active", trust: 0.97, load: 8, color: "text-blue-400" },
    { id: "cost-guardian", name: "Cost Economy", status: "Idle", trust: 0.99, load: 0, color: "text-green-400" },
  ];

  const arbitrations = [
    { id: "ARB-102", type: "Conflict", target: "libs/auth/rbac.py", winner: "Security Cluster", reason: "Priority Precedence (10 > 5)", time: "10m ago" },
    { id: "ARB-101", type: "Consensus", target: "workflow_api/main.py", winner: "Logic Cortex", reason: "Single Proposer", time: "45m ago" },
  ];

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 rounded-xl backdrop-blur-md border border-purple-500/20 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
            <Network className="w-8 h-8 text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#c5c6c7]">
              Global Federation Hub
            </h1>
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">Multi-Agent Orchestration & Consolidation</p>
          </div>
        </div>

        <div className="flex gap-4">
           <div className="px-4 py-2 bg-purple-600/10 border border-purple-500/20 rounded-lg text-purple-400 text-xs font-mono font-bold flex items-center gap-2">
              <Zap size={14} className="animate-pulse" />
              MODE: SHADOW FEDERATION
           </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 mb-8">
         {clusters.map((c) => (
            <div key={c.id} className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl hover:translate-y-[-4px] transition-all cursor-pointer">
               <div className="flex justify-between items-start mb-6">
                  <div className={`p-2 rounded-lg bg-white/5 ${c.color}`}>
                     <Cpu size={20} />
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${c.status === 'Active' ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/10 text-gray-400'}`}>
                     {c.status}
                  </span>
               </div>
               <h3 className="text-white font-medium text-sm mb-1">{c.name}</h3>
               <p className="text-[10px] text-gray-500 font-mono mb-4">{c.id}</p>
               
               <div className="grid grid-cols-2 gap-4 border-t border-white/5 pt-4">
                  <div>
                     <p className="text-[10px] text-gray-500 uppercase tracking-tighter mb-1">Trust Score</p>
                     <p className="text-[#66fcf1] font-bold text-lg">{(c.trust * 100).toFixed(0)}%</p>
                  </div>
                  <div>
                     <p className="text-[10px] text-gray-500 uppercase tracking-tighter mb-1">Load</p>
                     <p className="text-white font-bold text-lg">{c.load}%</p>
                  </div>
               </div>
            </div>
         ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         {/* ARBITRATION LOG */}
         <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 overflow-hidden">
            <div className="flex items-center gap-3 mb-8">
               <Gavel className="text-purple-400" size={20} />
               <h2 className="text-xl font-semibold text-white">Federation Arbitration Log</h2>
            </div>
            
            <div className="space-y-4">
               {arbitrations.map(a => (
                  <div key={a.id} className="p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                     <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-3">
                           <span className="text-[10px] font-mono p-1 bg-purple-500/20 text-purple-300 rounded leading-none">{a.id}</span>
                           <h4 className="text-gray-200 font-medium text-sm">{a.target}</h4>
                        </div>
                        <span className="text-[10px] text-gray-500">{a.time}</span>
                     </div>
                     <div className="flex items-center gap-4 mt-4">
                        <div className="flex items-center gap-2 bg-green-500/10 text-green-400 px-3 py-1 rounded text-[10px] font-bold">
                           <ShieldCheck size={12} />
                           WINNER: {a.winner}
                        </div>
                        <p className="text-xs text-gray-500 italic">" {a.reason} "</p>
                     </div>
                  </div>
               ))}
            </div>
         </div>

         {/* FEDERATION STATS & TOPOLOGY */}
         <div className="flex flex-col gap-8">
            <div className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/40">
               <h3 className="text-white font-semibold mb-6 flex items-center gap-2">
                  <Activity size={18} className="text-[#66fcf1]" />
                  Global Task Distribution
               </h3>
               <div className="space-y-6">
                  <div>
                     <div className="flex justify-between text-[10px] text-gray-400 mb-2 uppercase tracking-widest">
                        <span>Logic Processing</span>
                        <span>45%</span>
                     </div>
                     <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-[#66fcf1] h-full" style={{ width: '45%' }}></div>
                     </div>
                  </div>
                  <div>
                     <div className="flex justify-between text-[10px] text-gray-400 mb-2 uppercase tracking-widest">
                        <span>Security Audits</span>
                        <span>25%</span>
                     </div>
                     <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-red-400 h-full" style={{ width: '25%' }}></div>
                     </div>
                  </div>
                  <div>
                     <div className="flex justify-between text-[10px] text-gray-400 mb-2 uppercase tracking-widest">
                        <span>Ops Rollbacks</span>
                        <span>10%</span>
                     </div>
                     <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-blue-400 h-full" style={{ width: '10%' }}></div>
                     </div>
                  </div>
               </div>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-purple-500/20 bg-purple-500/5">
               <h3 className="text-purple-400 font-semibold mb-4 flex items-center gap-2">
                  <Info size={18} />
                  Federation Contracts (v19.1)
               </h3>
               <ul className="space-y-3 text-xs text-gray-400">
                  <li className="flex gap-2">
                     <span className="text-purple-400 font-mono">•</span>
                     <span>Multi-agent consensus required for P0 patches.</span>
                  </li>
                  <li className="flex gap-2">
                     <span className="text-purple-400 font-mono">•</span>
                     <span>Evidence-trace sharing via FSB (Service Bus).</span>
                  </li>
                  <li className="flex gap-2">
                     <span className="text-purple-400 font-mono">•</span>
                     <span>Daily cluster budget: 1.5M tokens (Pooled).</span>
                  </li>
               </ul>
            </div>
         </div>
      </div>
    </div>
  );
}
