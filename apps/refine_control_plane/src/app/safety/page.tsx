"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, 
  Zap, 
  Lock, 
  Activity, 
  RefreshCcw, 
  AlertOctagon, 
  Power, 
  Heart, 
  DollarSign,
  ShieldCheck,
  ChevronRight,
  Target,
  Terminal,
  Clock,
  Unlock,
  Radio
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function SafetyPage() {
  const [isClient, setIsClient] = useState(false);
  const [systemState, setSystemState] = useState("NORMAL");
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => setIsClient(true), []);

  const handleStateChange = (newState: string) => {
     setIsProcessing(true);
     setTimeout(() => {
        setSystemState(newState);
        setIsProcessing(false);
     }, 1500);
  };

  const metrics = [
    { name: "Health Index", value: 92, threshold: 70, icon: <Heart size={16} /> },
    { name: "Error Rate", value: 0.8, threshold: 5.0, icon: <Activity size={16} />, unit: "%" },
    { name: "Daily Exposure", value: 142, threshold: 500, icon: <DollarSign size={16} />, unit: "$" },
  ];

  const activePolicies = [
    { id: 1, name: "Automatic Canary Rollback", status: "Enabled", type: "P1 CITICAL" },
    { id: 2, name: "Cost Throttling", status: "Enabled", type: "P2 STANDBY" },
    { id: 3, name: "Security Hardening (RBAC)", status: "Active", type: "GLOBAL" },
  ];

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Safety Control" 
        subtitle="Autonomous Guardrails & Emergency Response Protocols" 
        icon={<ShieldAlert size={32} />}
        badge="Regulatory Grade"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Status</span>
                <div className="flex items-center gap-2 mt-2">
                   <div className={`w-2.5 h-2.5 rounded-full ${systemState === 'NORMAL' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.6)] animate-pulse'}`} />
                   <span className={`text-sm font-black transition-colors ${systemState === 'NORMAL' ? 'text-green-400' : 'text-red-400 uppercase'}`}>{systemState}</span>
                </div>
             </div>
             
             {systemState === 'NORMAL' ? (
                <button 
                  onClick={() => handleStateChange("SAFETY_FREEZE")}
                  disabled={isProcessing}
                  className="flex items-center gap-3 px-8 py-3 bg-red-500/10 text-red-500 border border-red-500/20 text-[10px] font-black uppercase tracking-widest rounded-2xl hover:bg-red-500/20 transition-all active:scale-95 group shadow-xl"
                >
                  <Power size={14} className="group-hover:rotate-180 transition-transform duration-500" />
                  <span>Force Safety Freeze</span>
                </button>
             ) : (
                <button 
                  onClick={() => handleStateChange("NORMAL")}
                  disabled={isProcessing}
                  className="flex items-center gap-3 px-8 py-3 bg-green-500/10 text-green-400 border border-green-500/20 text-[10px] font-black uppercase tracking-widest rounded-2xl hover:bg-green-500/20 transition-all active:scale-95 shadow-xl"
                >
                  <RefreshCcw size={14} className={isProcessing ? 'animate-spin' : ''} />
                  <span>Reset to Normal</span>
                </button>
             )}
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* SAFETY MONITORS - Main Column */}
        <div className="xl:col-span-8 space-y-10">
           {/* Autonomy State & Metrics */}
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <ShieldCheck size={300} />
              </div>
              
              <div className="flex items-center justify-between mb-12 relative z-10">
                 <div>
                    <h2 className="text-xl font-black text-white uppercase tracking-tighter mb-2 italic">Integrated Guardrails</h2>
                    <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.3em]">Governed by EmergencyPolicyEngine v18</p>
                 </div>
                 <div className="flex items-center gap-4 text-[10px] font-mono text-gray-700 bg-black/40 px-6 py-3 rounded-2xl border border-white/5">
                    <Radio size={16} className={systemState === 'NORMAL' ? "text-green-500 animate-pulse" : "text-red-500 animate-ping"} />
                    REAL-TIME_SHIELD_ACTIVE
                 </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
                 {metrics.map((m) => (
                    <div key={m.name} className="p-8 rounded-[2rem] bg-white/[0.015] border border-white/5 hover:border-[var(--primary)]/20 transition-all group/stat">
                       <div className="flex items-center justify-between mb-8">
                          <div className="p-3 bg-black/40 rounded-xl text-gray-600 group-hover/stat:text-[var(--primary)] transition-colors">
                            {m.icon}
                          </div>
                          <span className="text-[9px] text-gray-700 font-black uppercase tracking-widest">{m.name}</span>
                       </div>
                       <div className="flex items-baseline gap-2 mb-4 px-2">
                          <span className="text-4xl font-black text-white tracking-tighter">{m.value}{m.unit}</span>
                          <span className="text-gray-700 text-[10px] font-black uppercase italic">/ {m.threshold}{m.unit}</span>
                       </div>
                       <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden border border-white/5">
                          <div 
                            className={`h-full opacity-60 transition-all duration-1000 ${m.value > m.threshold ? 'bg-red-500' : 'bg-[var(--primary)]'}`}
                            style={{ width: `${Math.min((m.value / (m.threshold * 1.5)) * 100, 100)}%` }}
                          ></div>
                       </div>
                    </div>
                 ))}
              </div>
           </section>

           {/* Safety Logs */}
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-[#060a12]/50 relative overflow-hidden group shadow-2xl">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <Terminal size={240} />
              </div>
              <div className="flex items-center gap-3 mb-12 relative z-10">
                 <AlertOctagon size={18} className="text-[var(--primary)]" />
                 <h3 className="text-xs font-black text-white uppercase tracking-[0.4em]">Integrated Safety Ledger</h3>
              </div>
              
              <div className="space-y-4 relative z-10 custom-scrollbar pr-2 max-h-[300px] overflow-y-auto">
                 <SafetyLogItem time="23:02:15" msg="Policy Calibration Complete. Applied thresholds from Phase 17 evidence." source="GovernanceEngine" type="primary" />
                 <SafetyLogItem time="22:45:01" msg="Minor Latency Spike detected in Project X. Throttling non-critical connectors." source="OperationalShield" type="warning" />
                 <SafetyLogItem time="18:30:12" msg="Sanity check failure in Verifier matrix. Regional isolation protocol engaged." source="SafetySentinel" type="danger" />
              </div>
           </section>
        </div>

        {/* SIDEBAR - Policies & Emergency */}
        <div className="xl:col-span-4 flex flex-col gap-10">
           {/* Active Policies */}
           <section className="glass-panel p-10 rounded-[3rem] border-white/[0.05] bg-[#060a12]/50 relative overflow-hidden group shadow-xl">
              <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
                 <ShieldCheck size={140} className="text-[var(--primary)]" />
              </div>
              
              <div className="flex items-center gap-4 mb-10 relative z-10">
                 <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-xl">
                    <ShieldCheck size={24} className="text-[var(--primary)]" />
                 </div>
                 <div>
                    <h3 className="text-xl font-black text-white tracking-tighter uppercase">Policies</h3>
                    <p className="text-[9px] text-[var(--primary)] font-black tracking-[0.2em] uppercase mt-1">L1-L4 Active</p>
                 </div>
              </div>

              <div className="space-y-5 relative z-10">
                 {activePolicies.map(p => (
                    <div key={p.id} className="flex justify-between items-center p-5 rounded-2xl bg-white/[0.015] border border-white/5 hover:border-[var(--primary)]/20 transition-all group/item">
                       <div>
                          <p className="text-[11px] font-black text-white uppercase tracking-tight group-hover/item:text-[var(--primary)] transition-colors">{p.name}</p>
                          <span className="text-[9px] text-gray-700 font-black uppercase tracking-widest mt-1 block">{p.type}</span>
                       </div>
                       <div className="w-2.5 h-2.5 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.4)] transition-all group-hover/item:scale-125" />
                    </div>
                 ))}
              </div>
           </section>

           {/* Emergency Fallbacks */}
           <section className="glass-panel p-10 rounded-[3rem] border-red-500/10 bg-gradient-to-br from-red-500/[0.05] to-transparent relative group overflow-hidden shadow-2xl">
              <div className="absolute -bottom-10 -right-10 opacity-[0.04] group-hover:opacity-[0.08] transition-opacity duration-1000">
                 <Lock size={200} className="text-red-500" />
              </div>
              <h3 className="text-xs font-black text-red-400 mb-8 flex items-center gap-3 uppercase tracking-[0.3em] relative z-10">
                 <Lock size={20} />
                 Emergency Fallbacks
              </h3>
              
              <ul className="space-y-6 relative z-10 mb-10">
                 {[
                   { id: "01", text: "Switch to gpt-4o-mini for all autonomous cycles." },
                   { id: "02", text: "Isolate external tool execution (Read-Only)." },
                   { id: "03", text: "Immediate Rollback to Git Stable Hash (RC1.7)." }
                 ].map((route) => (
                    <li key={route.id} className="flex gap-5 group/li cursor-help">
                       <span className="text-[10px] font-mono font-black text-red-500/60 group-hover/li:text-red-400 transition-colors uppercase">{route.id}</span>
                       <p className="text-[11px] text-gray-500 font-bold leading-relaxed group-hover/li:text-red-200 transition-colors uppercase tracking-tight">{route.text}</p>
                    </li>
                 ))}
              </ul>

              <button className="w-full flex items-center justify-center gap-3 py-5 bg-red-500/10 border border-red-500/20 text-red-500 text-[10px] font-black uppercase tracking-widest rounded-2xl hover:bg-red-500/20 transition-all active:scale-95 group/btn">
                 Execute Global Freeze
                 <AlertOctagon size={16} className="group-hover/btn:rotate-12 transition-transform shadow-[0_0_10px_currentColor]" />
              </button>
           </section>
        </div>
      </div>
    </div>
  );
}

function SafetyLogItem({ time, msg, source, type }: any) {
  const accent = type === 'danger' ? 'border-red-500/40 text-red-400 bg-red-500/[0.02]' : type === 'warning' ? 'border-orange-500/40 text-orange-400' : 'border-[var(--primary)]/40 text-[var(--primary)]';

  return (
    <div className={`p-6 rounded-[2rem] bg-white/[0.015] border border-white/5 hover:bg-white/[0.025] transition-all flex gap-6 items-start group`}>
       <div className="flex flex-col items-center gap-2 pt-1 border-r border-white/10 pr-6 min-w-[100px]">
          <span className="text-[10px] font-mono font-black text-gray-700 uppercase tracking-widest">{time}</span>
          <div className={`w-1 h-1 rounded-full ${type === 'danger' ? 'bg-red-500' : type === 'warning' ? 'bg-orange-500' : 'bg-[var(--primary)]'}`} />
       </div>
       <div className="flex-1">
          <p className="text-[11px] font-bold leading-relaxed mb-3 text-gray-400 group-hover:text-white transition-colors">{msg}</p>
          <div className="flex items-center justify-between">
             <span className="text-[8px] font-black text-gray-700 uppercase tracking-widest">Source: {source}</span>
             <ChevronRight size={12} className="text-gray-800 opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0" />
          </div>
       </div>
    </div>
  );
}
