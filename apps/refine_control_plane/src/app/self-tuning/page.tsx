"use client";

import React, { useState, useEffect } from "react";
import { 
  Zap, 
  Activity, 
  Settings, 
  ChevronRight, 
  ArrowRight, 
  RefreshCcw, 
  Cpu, 
  ShieldCheck, 
  BarChart3, 
  Radio, 
  Terminal, 
  Target,
  FlaskConical,
  Lock,
  Search,
  Filter,
  Dna,
  Binary,
  AlertTriangle
} from "lucide-react";
import { useTranslations } from "next-intl";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";

export default function SelfTuningPage() {
  const t = useTranslations("improvements");
  const [isClient, setIsClient] = useState(false);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [evolutionFeed, setEvolutionFeed] = useState<any[]>([]);
  const [evolutionStatus, setEvolutionStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [staleMeta, setStaleMeta] = useState<any>(null);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const fetchData = async () => {
    try {
      const sugData: any = await safeFetchJson(`/api/v1/repair-lab/tuning/suggestions`);
      setSuggestions(sugData || []);

      const feedData: any = await safeFetchJson(`/api/v1/repair-lab/evolution/feed`);
      setEvolutionFeed(feedData || []);

      const statusData: any = await safeFetchJson(`/api/v1/repair-lab/evolution/status`);
      setEvolutionStatus(statusData);

      // Check for stale metadata in any of the responses to trigger the global degraded label
      if (statusData?.__sqv_meta) {
        setStaleMeta(statusData.__sqv_meta);
      } else if (sugData?.__sqv_meta) {
        setStaleMeta(sugData.__sqv_meta);
      } else {
        setStaleMeta(null);
      }
    } catch (err) {
      console.error(t("errorFetch"), err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [isClient]);

  const handleAction = async (id: string, status: 'approved' | 'rejected') => {
    try {
      const response: any = await safeFetchJson(`/api/v1/repair-lab/tuning/suggestions/${id}/apply`, {
        method: 'POST',
        body: JSON.stringify({ status })
      });
      if (response.status || response.id) {
        setSuggestions(prev => prev.map(s => s.id === id ? { ...s, status } : s));
      }
    } catch (err) {
      console.error(t("errorAction"), err);
    }
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title={t("title")} 
        subtitle={t("subtitle")} 
        icon={<Dna size={32} />}
        badge="AGI ALPHA-v13"
        staleMeta={staleMeta}
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">{t("cycleState")}</span>
                <div className="flex items-center gap-2 mt-2">
                   <div className={`w-2 h-2 rounded-full ${evolutionStatus?.is_running ? 'bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500'}`} />
                   <span className="text-sm font-black text-white uppercase tracking-tighter">{evolutionStatus?.is_running ? t("running") : t("halted")}</span>
                </div>
             </div>
             <button onClick={() => fetchData()} className="p-4 bg-white/5 border border-white/5 rounded-2xl text-gray-500 hover:text-white transition-all active:scale-95">
                <RefreshCcw size={18} className={loading ? 'animate-spin' : ''} />
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* TUNING SUGGESTIONS - Main Column */}
        <div className="xl:col-span-8">
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl min-h-[700px]">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <Settings size={300} />
              </div>

              <div className="flex items-center justify-between mb-12 relative z-10 px-2">
                 <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-ping shadow-[0_0_12px_rgba(102,252,241,0.6)]" />
                    <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">Integrated Calibration Matrix</h2>
                 </div>
                 <div className="flex items-center gap-6">
                    <span className="text-[10px] font-black text-gray-700 uppercase tracking-widest">{suggestions.length} Active Suggestions</span>
                 </div>
              </div>

              <div className="space-y-8 relative z-10">
                 {loading ? (
                    <div className="space-y-6">
                       {[1,2,3].map(i => <Skeleton key={i} className="h-44 rounded-3xl" />)}
                    </div>
                 ) : suggestions.length === 0 ? (
                    <div className="py-32 text-center flex flex-col items-center gap-6 opacity-40">
                       <div className="p-8 bg-white/5 rounded-full border border-white/5">
                          <Target size={48} className="text-gray-700" />
                       </div>
                       <p className="font-black text-gray-700 uppercase tracking-[0.3em] italic max-w-xs leading-loose">
                          {t("noSuggestions")}
                       </p>
                    </div>
                 ) : (
                    suggestions.map((s: any) => (
                       <EliteCalibrationCard 
                         key={s.id} 
                         suggestion={s} 
                         onApprove={() => handleAction(s.id, 'approved')}
                         onReject={() => handleAction(s.id, 'rejected')}
                       />
                    ))
                 )}
              </div>
           </section>
        </div>

        {/* EVOLUTION FEED - Sidebar */}
        <div className="xl:col-span-4 flex flex-col gap-10">
           {/* Live Feed */}
           <section className="glass-panel p-10 rounded-[3rem] border-white/[0.05] bg-[#060a12]/50 relative overflow-hidden group shadow-xl">
              <div className="absolute top-0 right-0 p-8 opacity-[0.01] transition-opacity">
                 <Radio size={140} className="text-blue-400" />
              </div>
              
              <div className="flex items-center justify-between mb-10 relative z-10">
                 <div className="flex items-center gap-4 text-blue-400">
                    <div className="p-3 bg-blue-400/10 rounded-2xl border border-blue-400/20 shadow-xl">
                       <Radio size={24} className="animate-pulse" />
                    </div>
                    <div>
                       <h3 className="text-xl font-black text-white tracking-tighter uppercase">Evolution</h3>
                       <p className="text-[9px] font-black tracking-[0.2em] uppercase mt-1">Live Traces</p>
                    </div>
                 </div>
              </div>

              <div className="space-y-4 relative z-10 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                 {evolutionFeed.length === 0 ? (
                    <div className="py-20 text-center text-gray-700 font-black uppercase tracking-widest italic opacity-40">{t("gatheringData")}</div>
                 ) : (
                    evolutionFeed.map((item: any) => (
                       <div key={item.id} className={`p-6 rounded-[1.5rem] bg-white/[0.012] border transition-all hover:bg-white/[0.025]
                          ${item.success ? 'border-blue-500/10 shadow-[0_0_10px_rgba(59,130,246,0.02)]' : 'border-red-500/20'}
                       `}>
                          <div className="flex justify-between items-start mb-3">
                             <span className={`text-[8px] font-black px-2 py-0.5 rounded uppercase tracking-widest ${item.success ? 'bg-blue-500/10 text-blue-400' : 'bg-red-500/10 text-red-500'}`}>
                                {item.success ? 'Success' : 'Failed'}
                             </span>
                             <span className="text-[8px] text-gray-700 font-mono font-black">{new Date(item.created_at).toLocaleTimeString()}</span>
                          </div>
                          <p className="text-[10px] font-black text-white uppercase tracking-tight mb-2 truncate">{item.component}</p>
                          <p className="text-[9px] text-gray-600 leading-relaxed uppercase font-bold">{item.rationale}</p>
                       </div>
                    ))
                 )}
              </div>
           </section>

           {/* Failure Analysis / Stuck State */}
           <section className="glass-panel p-10 rounded-[3rem] border-red-500/10 bg-gradient-to-br from-red-500/[0.05] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="absolute -bottom-10 -right-10 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-1000">
                 <Zap size={200} className="text-red-500" />
              </div>
              <h3 className="text-xs font-black text-white mb-8 flex items-center gap-3 uppercase tracking-[0.3em] relative z-10 italic">
                 <AlertTriangle size={20} className="text-red-500" />
                 Resilience Stress
              </h3>
              
              <div className="space-y-4 relative z-10">
                 {Object.entries(evolutionStatus?.failure_counts || {}).map(([file, count]: [string, any]) => (
                   count > 0 && (
                     <div key={file} className="p-4 rounded-2xl bg-black/40 border border-white/5 flex items-center justify-between group/risk">
                        <div className="flex-1 mr-4">
                           <span className="text-[8px] font-mono text-gray-500 truncate block uppercase max-w-[150px]">{file}</span>
                           <div className="flex gap-1 mt-2">
                              {[...Array(evolutionStatus?.stuck_threshold || 5)].map((_, i) => (
                                <div key={i} className={`h-1 flex-1 rounded-full transition-all duration-1000 ${i < count ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]' : 'bg-white/5'}`} />
                              ))}
                           </div>
                        </div>
                        <span className={`text-[9px] font-black uppercase ${count >= (evolutionStatus?.stuck_threshold || 5) ? 'text-red-500' : 'text-gray-700'}`}>
                           {count >= (evolutionStatus?.stuck_threshold || 5) ? 'Stuck' : 'Risk'}
                        </span>
                     </div>
                   )
                 ))}
                 {(!evolutionStatus?.failure_counts || Object.values(evolutionStatus?.failure_counts).every(c => c === 0)) && (
                    <div className="text-center py-10 opacity-30 flex flex-col items-center gap-4">
                       <ShieldCheck size={32} className="text-green-500" />
                       <span className="text-[9px] font-black text-green-500 uppercase tracking-widest leading-loose">{t("noStuckState")}</span>
                    </div>
                 )}
              </div>
           </section>
        </div>
      </div>
    </div>
  );
}

function EliteCalibrationCard({ suggestion, onApprove, onReject }: any) {
  const isPending = suggestion.status === 'pending';

  return (
    <div className={`p-8 rounded-[2.5rem] border transition-all duration-500 group/item relative overflow-hidden
      ${isPending ? 'bg-white/[0.015] border-white/5 hover:border-[var(--primary)]/30' : 'bg-black/40 border-white/5 opacity-60'}
    `}>
       <div className="flex flex-col xl:flex-row justify-between gap-10 relative z-10">
          <div className="flex-1">
             <div className="flex items-start gap-6 mb-8">
                <div className={`p-5 rounded-2xl border transition-all duration-500 shadow-xl
                   ${isPending ? 'bg-[var(--primary)]/10 border-[var(--primary)]/20 text-[var(--primary)] group-hover/item:scale-110' : 'bg-white/5 border-white/5 text-gray-700'}
                `}>
                   <Cpu size={24} />
                </div>
                <div>
                   <div className="flex flex-wrap items-center gap-4 mb-3">
                      <h3 className="text-xl font-black text-white uppercase tracking-tight group-hover/item:text-[var(--primary)] transition-colors">
                        {suggestion.parameter}
                      </h3>
                      <span className="text-[9px] font-mono font-black text-gray-700 uppercase tracking-widest bg-black/40 px-2 py-0.5 rounded border border-white/5">
                        ID: {suggestion.id}
                      </span>
                   </div>
                   <p className="text-xs font-bold leading-relaxed tracking-tight text-gray-500 max-w-2xl mb-8">
                      "{suggestion.reason}"
                   </p>
                </div>
             </div>

             <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 pt-8 border-t border-white/[0.03]">
                <StatItem label="Current Value" val={suggestion.current_value} icon={<Activity size={12}/>} />
                <StatItem label="Proposed" val={suggestion.proposed_value} icon={<Zap size={12}/>} primary />
                <StatItem label="Confidence" val={`${(suggestion.confidence * 100).toFixed(0)}%`} icon={<ShieldCheck size={12}/>} />
                <StatItem label="Impact" val={suggestion.impact} icon={<BarChart3 size={12}/>} />
             </div>
          </div>

          <div className="flex xl:flex-col justify-end items-center gap-4 min-w-[200px]">
             {isPending ? (
                <>
                   <button 
                     onClick={onApprove}
                     className="w-full flex items-center justify-center gap-3 px-8 py-4 bg-[var(--primary)] text-[#060a12] font-black text-[11px] uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.4)] transition-all active:scale-95 group/btn"
                   >
                      <Check size={18} />
                      <span>Uygula</span>
                   </button>
                   <button 
                     onClick={onReject}
                     className="w-full flex items-center justify-center gap-3 px-8 py-4 bg-white/5 border border-white/10 text-gray-600 font-black text-[10px] uppercase tracking-widest rounded-2xl hover:bg-white/10 hover:text-white transition-all active:scale-95"
                   >
                      <X size={18} />
                      <span>Reddet</span>
                   </button>
                </>
             ) : (
                <div className={`flex items-center gap-2 px-6 py-3 rounded-xl border text-[9px] font-black uppercase tracking-widest shadow-xl
                  ${suggestion.status === 'approved' ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-500'}
                `}>
                   <ShieldCheck size={14} />
                   {suggestion.status === 'approved' ? 'Applied' : 'Rejected'}
                </div>
             )}
          </div>
       </div>
    </div>
  );
}

function StatItem({ label, val, icon, primary }: any) {
  return (
    <div className="flex flex-col gap-2">
       <div className="flex items-center gap-2 text-gray-700">
          {icon}
          <span className="text-[8px] font-black uppercase tracking-[0.2em]">{label}</span>
       </div>
       <span className={`text-[11px] font-black font-mono tracking-tighter uppercase ${primary ? 'text-[var(--primary)] ring-1 ring-[var(--primary)]/20 px-2 py-0.5 rounded bg-[var(--primary)]/5 w-fit' : 'text-white'}`}>{val}</span>
    </div>
  );
}

function Check({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

function X({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  );
}
