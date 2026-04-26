"use client";

import React, { useState, useEffect } from "react";
import { useList, useCustomMutation } from "@refinedev/core";
import { 
  Dna, 
  Target, 
  Play, 
  History, 
  Trash2, 
  AlertOctagon, 
  ShieldCheck, 
  Zap,
  Activity,
  ChevronRight,
  Flame,
  Terminal,
  FlaskConical,
  Clock,
  Radio,
  Calendar,
  Lock,
  ChevronDown,
  Info
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function TrainingDrillsPage() {
  const [isClient, setIsClient] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isAutoActive, setIsAutoActive] = useState(false);

  useEffect(() => setIsClient(true), []);

  const { query: { data: drillsData, isLoading: isDrillsLoading, isError } } = useList({
    resource: "governance/drills",
    queryOptions: { enabled: isClient }
  });

  const { mutate } = useCustomMutation();

  const toggleAutoDrills = () => {
    setIsAutoActive(!isAutoActive);
  };

  const triggerDrill = async (scenario: string) => {
    setIsRunning(true);
    mutate({
       url: "/governance/drills/trigger",
       method: "post",
       values: { scenario },
       successNotification: {
         message: "Tatbikat Başlatıldı",
         description: `${scenario} senaryosu için otonom döngü tetiklendi.`,
         type: "success",
       }
    });
    setTimeout(() => setIsRunning(false), 2000);
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  const drills = drillsData?.data ?? [
     { id: "1", scenario: "Simulated Regional Failure", status: "COMPLETED", outcome: "SUCCESS", duration: "14m", date: new Date().toISOString() },
     { id: "2", scenario: "Economic Budget Exhaustion", status: "FAILED", outcome: "POLICY_BREACH", duration: "3m", date: new Date().toISOString() },
     { id: "3", scenario: "Cascading Repair Loop", status: "COMPLETED", outcome: "STABILIZED", duration: "22m", date: new Date().toISOString() },
  ];

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Training Hub" 
        subtitle="Resilience Simulations & Autonomous Chaos Engineering" 
        icon={<Target size={32} />}
        badge="Resilience Tier-1"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Resilience Score</span>
                <span className="text-sm font-black text-green-400 mt-2 font-mono tracking-tighter italic">0.88 / 1.0</span>
             </div>
             
             <button 
                onClick={() => triggerDrill("manual")}
                disabled={isRunning}
                className="flex items-center gap-3 px-8 py-3 bg-red-500/10 text-red-500 border border-red-500/20 text-[10px] font-black uppercase tracking-widest rounded-2xl hover:bg-red-500/20 transition-all active:scale-95 group shadow-xl disabled:opacity-50"
             >
                <Play size={14} className={isRunning ? 'animate-ping' : 'group-hover:scale-125 transition-transform'} fill="currentColor" />
                <span>{isRunning ? "Simulating..." : "Initialize Drill"}</span>
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* DRILL HISTORY - Main Column */}
        <div className="xl:col-span-8">
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <History size={300} />
              </div>

              <div className="flex items-center justify-between mb-12 relative z-10 px-2">
                 <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-ping shadow-[0_0_12px_rgba(239,68,68,0.6)]" />
                    <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">Resilience Simulation Ledger</h2>
                 </div>
                 <div className="flex items-center gap-6">
                    <button className="flex items-center gap-2 text-[10px] font-black text-gray-700 uppercase hover:text-white transition-colors">
                       Filter <ChevronDown size={14} />
                    </button>
                 </div>
              </div>

              <div className="space-y-6 relative z-10 custom-scrollbar pr-3 max-h-[700px] overflow-y-auto">
                 {isDrillsLoading ? (
                    <div className="space-y-6">
                       {[1,2,3].map(i => <Skeleton key={i} className="h-40 rounded-3xl" />)}
                    </div>
                 ) : (
                    drills.map((drill: any) => (
                       <div key={drill.id} className="p-8 rounded-[2rem] bg-white/[0.015] border border-white/5 hover:bg-white/[0.025] hover:border-white/10 transition-all group/item">
                          <div className="flex justify-between items-center px-2">
                             <div className="flex items-center gap-6">
                                <div className={`p-5 rounded-2xl border transition-all duration-500 shadow-xl
                                  ${drill.outcome === 'SUCCESS' ? 'bg-green-500/10 border-green-500/20 text-green-500' : 
                                    drill.outcome === 'POLICY_BREACH' ? 'bg-red-500/10 border-red-500/20 text-red-500' : 
                                    'bg-blue-500/10 border-blue-500/20 text-blue-400'}
                                  group-hover/item:scale-110
                                `}>
                                   <Activity size={24} />
                                </div>
                                <div>
                                   <h3 className="text-lg font-black text-white uppercase tracking-tight group-hover/item:text-[var(--primary)] transition-colors">
                                     {drill.scenario}
                                   </h3>
                                   <div className="flex items-center gap-4 mt-2">
                                      <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">{new Date(drill.date).toLocaleDateString()}</span>
                                      <span className="w-1.5 h-1.5 rounded-full bg-gray-900" />
                                      <div className="flex items-center gap-2">
                                         <Clock size={12} className="text-gray-700" />
                                         <span className="text-[9px] font-mono font-black text-gray-700 uppercase">{drill.duration}</span>
                                      </div>
                                   </div>
                                </div>
                             </div>
                             
                             <div className="flex items-center gap-6">
                                <span className={`px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border transition-all
                                  ${drill.outcome === 'SUCCESS' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}
                                `}>
                                   {drill.outcome}
                                </span>
                                <button className="p-3 bg-white/5 rounded-xl text-gray-700 hover:text-white transition-all">
                                   <ChevronRight size={18} />
                                </button>
                             </div>
                          </div>
                       </div>
                    ))
                 )}
              </div>
           </section>
        </div>

        {/* SIDEBAR - Parameters & Automation */}
        <div className="xl:col-span-4 flex flex-col gap-10">
           {/* Simulation Parameters */}
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/50 relative overflow-hidden group shadow-xl">
              <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
                 <Flame size={140} className="text-orange-500" />
              </div>
              
              <div className="flex items-center gap-4 mb-10 relative z-10">
                 <div className="p-3 bg-orange-500/10 rounded-2xl border border-orange-500/20 shadow-xl">
                    <Flame size={24} className="text-orange-500" />
                 </div>
                 <div>
                    <h3 className="text-xl font-black text-white tracking-tighter uppercase">Parameters</h3>
                    <p className="text-[9px] text-orange-400 font-black tracking-[0.2em] uppercase mt-1">Chaos Injectors</p>
                 </div>
              </div>

              <div className="space-y-8 relative z-10">
                 <div>
                    <div className="flex justify-between items-end mb-3">
                       <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest leading-none">Chaos Density</span>
                       <span className="text-xs font-mono font-black text-white">65%</span>
                    </div>
                    <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden border border-white/[0.03]">
                       <div className="h-full bg-gradient-to-r from-orange-500 to-red-500 shadow-[0_0_12px_rgba(249,115,22,0.4)] transition-all duration-1000" style={{ width: '65%' }} />
                    </div>
                 </div>

                 <div className="grid grid-cols-1 gap-4">
                    <StatItem label="Mean Recovery" val="2m 45s" icon={<Clock size={12}/>} />
                    <StatItem label="Error Tolerance" val="5.0% EXT" icon={<AlertOctagon size={12}/>} />
                 </div>
              </div>
           </section>

           {/* Automated Drills */}
           <section className={`glass-panel p-10 rounded-[3rem] border-white/[0.03] transition-all duration-700 relative overflow-hidden group shadow-2xl
             ${isAutoActive ? 'bg-emerald-500/[0.02] border-emerald-500/20' : 'bg-gradient-to-br from-white/[0.01] to-transparent'}
           `}>
              <div className="absolute -bottom-10 -right-10 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-1000">
                 <Target size={200} className={isAutoActive ? 'text-emerald-500' : 'text-gray-700'} />
              </div>
              
              <div className="flex flex-col items-center text-center relative z-10">
                 <div className={`p-5 rounded-2xl border mb-6 transition-all duration-500
                   ${isAutoActive ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500 animate-pulse' : 'bg-black/40 border-white/5 text-gray-700'}
                 `}>
                    <Target size={32} />
                 </div>
                 
                 <h4 className={`text-xs font-black uppercase tracking-[0.3em] mb-3 transition-colors ${isAutoActive ? 'text-emerald-400' : 'text-white'}`}>
                    {isAutoActive ? "Otonom Motor Aktif" : "Game-Day Planner"}
                 </h4>
                 <p className="text-[11px] text-gray-700 font-bold leading-relaxed uppercase tracking-tighter mb-10 max-w-[200px]">
                    {isAutoActive ? "Sistem rastgele aralıklarla stres testi yapmaktadır." : "Gelecek planlı tatbikat: 27 Nisan 2026"}
                 </p>

                 <button 
                   onClick={toggleAutoDrills}
                   className={`w-full py-5 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all active:scale-95
                     ${isAutoActive ? 'bg-emerald-500 text-[#060a12] hover:shadow-[0_8px_32px_rgba(16,185,129,0.3)]' : 'bg-white/5 text-gray-600 border border-white/10 hover:text-white hover:border-white/20'}`}
                 >
                    {isAutoActive ? "Terminate Auto-Mode" : "Initialize Auto-Mode"}
                 </button>
              </div>
           </section>

           {/* Quick Disclaimer/Info */}
           <div className="px-10 flex gap-4 opacity-40">
              <Info size={14} className="text-gray-700 shrink-0" />
              <p className="text-[9px] text-gray-700 font-black uppercase leading-tight tracking-widest">
                 Tüm simülasyonlar izole edilmiş gölge kopyalar (Shadow Clusters) üzerinde gerçekleştirilir.
              </p>
           </div>
        </div>
      </div>
    </div>
  );
}

function StatItem({ label, val, icon }: any) {
  return (
    <div className="flex justify-between items-center p-5 rounded-xl bg-white/[0.012] border border-white/5 hover:border-white/10 transition-all">
       <div className="flex items-center gap-3 text-gray-700">
          {icon}
          <span className="text-[9px] font-black uppercase tracking-widest">{label}</span>
       </div>
       <span className="text-[11px] font-black text-white font-mono tracking-tighter uppercase">{val}</span>
    </div>
  );
}
