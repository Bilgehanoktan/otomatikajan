"use client";

import React, { useState } from "react";
import { ShieldAlert, Zap, Lock, Activity, RefreshCcw, AlertOctagon, Power, Heart, DollarSign } from "lucide-react";

export default function SafetyPage() {
  const [systemState, setSystemState] = useState("NORMAL");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleStateChange = (newState: string) => {
     setIsProcessing(true);
     setTimeout(() => {
        setSystemState(newState);
        setIsProcessing(false);
     }, 1500);
  };

  const metrics = [
    { name: "Health Index", value: 92, threshold: 70, icon: <Heart className="text-red-400" /> },
    { name: "Error Rate", value: 0.8, threshold: 5.0, icon: <Activity className="text-cyan-400" />, unit: "%" },
    { name: "Daily Projection", value: 142, threshold: 500, icon: <DollarSign className="text-green-400" />, unit: "$" },
  ];

  const activePolicies = [
    { id: 1, name: "Automatic Canary Rollback", status: "Enabled", type: "P1" },
    { id: 2, name: "Cost Throttling", status: "Enabled", type: "P2" },
    { id: 3, name: "Security Hardening (RBAC)", status: "Active", type: "Global" },
  ];

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-xl backdrop-blur-md border shadow-lg transition-all
            ${systemState === 'NORMAL' ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.3)]'}`}>
            <ShieldAlert className={`w-8 h-8 ${systemState === 'NORMAL' ? 'text-green-400' : 'text-red-400'}`} />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#c5c6c7]">
              Live Operations Safety
            </h1>
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">Autonomous Guardrails & Controls</p>
          </div>
        </div>

        <div className="flex gap-4">
           {systemState === 'NORMAL' ? (
              <button 
                onClick={() => handleStateChange("SAFETY_FREEZE")}
                className="flex items-center gap-2 px-6 py-3 bg-red-600/20 hover:bg-red-600/40 text-red-100 border border-red-500/30 rounded-xl font-bold transition-all animate-pulse"
              >
                <Power size={20} />
                FORCE SAFETY FREEZE
              </button>
           ) : (
              <button 
                onClick={() => handleStateChange("NORMAL")}
                className="flex items-center gap-2 px-6 py-3 bg-green-600/20 hover:bg-green-600/40 text-green-100 border border-green-500/30 rounded-xl font-bold transition-all"
              >
                <RefreshCcw size={20} />
                RESET TO NORMAL
              </button>
           )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* SAFETY STATUS CARD */}
        <div className="lg:col-span-2 flex flex-col gap-8">
          <div className="glass-panel p-8 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl">
             <div className="flex justify-between items-start mb-8">
                <div>
                   <h2 className="text-xl font-semibold text-white mb-2">System Autonomy State</h2>
                   <p className="text-gray-400 text-sm">Governed by EmergencyPolicyEngine v18</p>
                </div>
                <div className={`px-4 py-2 rounded-lg font-mono font-bold text-sm
                  ${systemState === 'NORMAL' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-500/20 text-red-500 border border-red-500/30'}`}>
                   {systemState}
                </div>
             </div>

             <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {metrics.map((m) => (
                   <div key={m.name} className="p-4 rounded-xl bg-white/5 border border-white/10">
                      <div className="flex items-center gap-3 mb-4">
                         {m.icon}
                         <span className="text-gray-300 text-sm font-medium">{m.name}</span>
                      </div>
                      <div className="flex items-end gap-2">
                         <span className="text-3xl font-bold text-white">{m.value}{m.unit}</span>
                         <span className="text-gray-500 text-xs mb-1">/ {m.threshold}{m.unit}</span>
                      </div>
                      <div className="mt-4 w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                         <div 
                           className={`h-full rounded-full transition-all duration-1000 ${m.value > m.threshold ? 'bg-red-500' : 'bg-[#66fcf1]'}`}
                           style={{ width: `${Math.min((m.value / (m.threshold * 1.5)) * 100, 100)}%` }}
                         ></div>
                      </div>
                   </div>
                ))}
             </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/40">
             <h3 className="text-lg font-medium text-white mb-6 flex items-center gap-2">
                <AlertOctagon size={18} className="text-[#66fcf1]" />
                Recent Safety Logs
             </h3>
             <div className="space-y-4">
                <div className="flex gap-4 p-4 rounded-lg bg-white/5 border-l-4 border-[#66fcf1]">
                   <div className="text-[#66fcf1] font-mono text-xs pt-1">23:02:15</div>
                   <div>
                      <p className="text-sm text-gray-200">Policy Calibration Complete. Applied thresholds from Phase 17 evidence.</p>
                      <span className="text-[10px] text-gray-500 uppercase font-bold">SOURCE: GovernanceEngine</span>
                   </div>
                </div>
                <div className="flex gap-4 p-4 rounded-lg bg-white/5 border-l-4 border-orange-500/50">
                   <div className="text-orange-400 font-mono text-xs pt-1">22:45:01</div>
                   <div>
                      <p className="text-sm text-gray-200">Minor Latency Spike detected in Project X. Throttling non-critical connectors.</p>
                      <span className="text-[10px] text-gray-500 uppercase font-bold">MODE: Degraded</span>
                   </div>
                </div>
             </div>
          </div>
        </div>

        {/* SIDEBAR: POLICIES & FALLBACKS */}
        <div className="flex flex-col gap-8">
           <div className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl">
              <h3 className="text-white font-semibold mb-6">Active Safety Policies</h3>
              <div className="space-y-4">
                 {activePolicies.map(p => (
                    <div key={p.id} className="flex justify-between items-center p-3 rounded-lg bg-[#1f2833]/30 border border-white/5">
                       <div>
                          <p className="text-sm text-gray-200 font-medium">{p.name}</p>
                          <span className="text-[10px] text-[#45a29e] font-bold">{p.type} Priority</span>
                       </div>
                       <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
                    </div>
                 ))}
              </div>
           </div>

           <div className="glass-panel p-6 rounded-2xl border border-red-500/20 bg-red-500/5">
              <h3 className="text-red-400 font-semibold mb-4 flex items-center gap-2">
                 <Lock size={18} />
                 Emergency Fallback Routes
              </h3>
              <ul className="space-y-3 text-xs text-gray-400">
                 <li className="flex gap-2">
                    <span className="text-[#66fcf1]">01</span>
                    <span>Switch to <b>gpt-4o-mini</b> for all autonomous cycles.</span>
                 </li>
                 <li className="flex gap-2">
                    <span className="text-[#66fcf1]">02</span>
                    <span>Isolate external tool execution (Read-Only).</span>
                 </li>
                 <li className="flex gap-2">
                    <span className="text-[#66fcf1]">03</span>
                    <span>Immediate Rollback to Git Stable Hash (RC1.7).</span>
                 </li>
              </ul>
           </div>
        </div>
      </div>
    </div>
  );
}
