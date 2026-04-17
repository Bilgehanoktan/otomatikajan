"use client";

import { useList } from "@refinedev/core";
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
  FlaskConical
} from "lucide-react";
import { useState } from "react";

export default function TrainingDrillsPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [isAutoActive, setIsAutoActive] = useState(false);
  
  const { data: drillsData } = useList({
    resource: "governance/drills"
  });

  const { mutate } = useCustomMutation();

  const toggleAutoDrills = () => {
    setIsAutoActive(!isAutoActive);
    // In real usage, this would call /governance/drills/automation/toggle
  };

  const triggerDrill = async (scenario: string) => {
    setIsRunning(true);
    mutate({
       url: `/governance/drills/trigger`,
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

  const drills = drillsData?.data ?? [
     { id: "1", scenario: "Simulated Regional Failure", status: "COMPLETED", outcome: "SUCCESS", duration: "14m", date: new Date().toISOString() },
     { id: "2", scenario: "Economic Budget Exhaustion", status: "FAILED", outcome: "POLICY_BREACH", duration: "3m", date: new Date().toISOString() },
     { id: "3", scenario: "Cascading Repair Loop", status: "COMPLETED", outcome: "STABILIZED", duration: "22m", date: new Date().toISOString() },
  ];

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-red-500/10 rounded-xl backdrop-blur-md border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]">
            <Target className="w-8 h-8 text-red-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#c5c6c7]">
              Tatbikat Merkezi (Training & Drills)
            </h1>
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">Sovereign Resilience Simulations | Phase 30</p>
          </div>
        </div>

        <button 
           onClick={() => triggerDrill("manual")}
           disabled={isRunning}
           className={`flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl font-bold transition-all shadow-[0_0_20px_rgba(220,38,38,0.3)] ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}>
          <Play size={18} fill="currentColor" />
          {isRunning ? "TATBİKAT BAŞLATILIYOR..." : "YENİ TATBİKAT BAŞLAT"}
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* ACTIVE SCENARIOS */}
        <div className="lg:col-span-2 space-y-8">
           <section className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/40 backdrop-blur-xl">
              <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-3">
                 <History size={20} className="text-red-400" />
                 Tatbikat Geçmişi
              </h2>

              <div className="space-y-4">
                 {drills.map((drill: any) => (
                    <div key={drill.id} className="p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/[0.08] transition-all flex items-center justify-between">
                       <div className="flex items-center gap-4">
                          <div className={`p-2 rounded-lg 
                             ${drill.outcome === 'SUCCESS' ? 'bg-green-500/10 text-green-400' : 
                               drill.outcome === 'POLICY_BREACH' ? 'bg-red-500/10 text-red-400' : 
                               'bg-blue-500/10 text-blue-400'}`}>
                             <Activity size={18} />
                          </div>
                          <div>
                             <h3 className="text-sm font-bold text-white">{drill.scenario}</h3>
                             <p className="text-[10px] text-gray-500 uppercase tracking-widest">{drill.date.split('T')[0]} | {drill.duration}</p>
                          </div>
                       </div>
                       <div className="flex items-center gap-4">
                          <span className={`text-[10px] font-black px-2 py-0.5 rounded
                             ${drill.outcome === 'SUCCESS' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                             {drill.outcome}
                          </span>
                          <button className="text-gray-500 hover:text-white transition-colors">
                             <ChevronRight size={16} />
                          </button>
                       </div>
                    </div>
                 ))}
              </div>
           </section>

           <section className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-gradient-to-r from-red-500/5 to-transparent">
              <div className="flex items-start gap-4">
                 <AlertOctagon className="text-red-500 shrink-0" size={24} />
                 <div>
                    <h3 className="text-white font-bold mb-1 italic">Stress Test Mode</h3>
                    <p className="text-xs text-gray-400 leading-relaxed">
                       Sistemi gerçek dünya krizlerine (Chaos Engineering) karşı hazırlamak için "Tatbikat Modu"nu aktif edebilirsiniz. Bu modda otonom korumalar ekstra hassas düzeye çekilir.
                    </p>
                 </div>
              </div>
           </section>
        </div>

        {/* STATS & QUICK ACTIONS */}
        <div className="flex flex-col gap-8">
           <section className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60">
              <h3 className="text-white font-bold mb-6 text-sm flex items-center gap-2">
                 <Flame size={16} className="text-orange-500" />
                 Simülasyon Parametreleri
              </h3>
              <div className="space-y-4">
                 <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                    <span className="text-[10px] text-gray-500 uppercase font-black block mb-2">Chaos Injection Level</span>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                       <div className="h-full bg-red-500 w-[65%]" />
                    </div>
                 </div>
                 <div className="flex justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                    <span className="text-xs text-gray-400 uppercase">Resilience Score</span>
                    <span className="text-xs text-green-400 font-black">0.88</span>
                 </div>
                 <div className="flex justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                    <span className="text-xs text-gray-400 uppercase">Mean Time to Recover</span>
                    <span className="text-xs text-white font-mono">2m 45s</span>
                 </div>
              </div>
           </section>

            <div className={`p-6 rounded-2xl border ${isAutoActive ? 'border-teal-500/30 bg-teal-500/5' : 'border-dashed border-white/10'} text-center transition-all`}>
               <Target size={32} className={`mx-auto mb-4 ${isAutoActive ? 'text-teal-400' : 'text-gray-700'}`} />
               <h4 className={`text-xs font-bold uppercase ${isAutoActive ? 'text-teal-400' : 'text-gray-400'}`}>
                 {isAutoActive ? "Otonom Motor Aktif" : "Game-Day Planner"}
               </h4>
               <p className="text-[10px] text-gray-600 mt-2">
                 {isAutoActive ? "Sistem rastgele aralıklarla stres testi yapmaktadır." : "Gelecek planlı tatbikat: 27 Nisan 2026"}
               </p>
               <button 
                 onClick={toggleAutoDrills}
                 className={`mt-4 px-4 py-1.5 rounded-lg text-[10px] uppercase font-black tracking-widest transition-all
                   ${isAutoActive ? 'bg-teal-500 text-black' : 'bg-white/5 text-gray-400 border border-white/10'}`}>
                 {isAutoActive ? "OTOMATİK MODU KAPAT" : "OTOMATİK MODU AÇ"}
               </button>
            </div>
        </div>
      </div>
    </div>
  );
}
