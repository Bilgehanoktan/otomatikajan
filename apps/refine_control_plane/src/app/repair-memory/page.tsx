"use client";

import React, { useState, useEffect } from "react";
import { 
  Activity, 
  Brain, 
  ShieldCheck, 
  AlertTriangle, 
  Clock, 
  BarChart3, 
  ChevronRight, 
  Zap, 
  Binary, 
  Fingerprint,
  RotateCcw,
  Search,
  Filter,
  Cpu
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";

export default function RepairMemoryPage() {
  const [isClient, setIsClient] = useState(false);
  const [subsystems, setSubsystems] = useState<any[]>([]);
  const [details, setDetails] = useState<any[]>([]);
  const [selectedSS, setSelectedSS] = useState<string | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setIsClient(true);
    const fetchMemory = async () => {
      try {
        const data = await safeFetchJson('/api/v1/repair-lab/memory/heatmaps');
        setSubsystems(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Tamir hafızası alınamadı", err);
      } finally {
        setLoading(false);
      }
    };
    fetchMemory();
  }, []);

  const fetchDetails = async (ss: string) => {
    setSelectedSS(ss);
    setDetailsLoading(true);
    try {
      const data = await safeFetchJson(`/api/v1/repair-lab/memory/details?subsystem=${encodeURIComponent(ss)}`);
      setDetails(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Detaylar alınamadı", err);
    } finally {
      setDetailsLoading(false);
    }
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden relative">
      
      <ResourceHeader 
        title="Repair Memory" 
        subtitle="Cognitive Risk Heatmaps & Subsystem Reliability Ledger" 
        icon={<Brain size={32} />}
        badge="Neural-V3 Active"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Experience Layer</span>
                <span className="text-sm font-black text-orange-500 mt-2 font-mono tracking-tighter italic">RELIABLE</span>
             </div>
             <button 
                onClick={() => window.location.reload()}
                className="p-4 bg-white/5 border border-white/5 rounded-2xl text-gray-500 hover:text-white transition-all active:scale-95"
             >
                <RotateCcw size={18} />
             </button>
          </div>
        }
      />

      {/* METRICS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
         <EliteMemoryMetric label="Resolved Patterns" val={subsystems.length > 0 ? subsystems.reduce((acc, s) => acc + (s.failure || 0), 0) : 0} icon={<Binary size={16} />} accent="text-orange-500" />
         <EliteMemoryMetric label="Avg. Reliability" val="94.2%" icon={<ShieldCheck size={16} />} accent="text-green-500" />
         <EliteMemoryMetric label="Learning Cycles" val="12.4k" icon={<Activity size={16} />} accent="text-[var(--primary)]" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
        {loading ? (
          [1,2,3,4,5,6,7,8].map(i => <Skeleton key={i} className="h-64 rounded-[2rem]" />)
        ) : subsystems.length === 0 ? (
          <div className="col-span-full py-40 text-center opacity-30 flex flex-col items-center gap-6">
             <div className="p-10 bg-white/5 rounded-full border border-white/5">
                <Brain size={64} className="text-gray-700" />
             </div>
             <p className="font-black text-gray-700 uppercase tracking-[0.3em] italic max-w-xs leading-loose">
                Hafızada henüz kayıtlı tamir deseni bulunmuyor. Sistem öğrendikçe burası dolacaktır.
             </p>
          </div>
        ) : (
          subsystems.map((sub: any, idx: number) => (
            <EliteMemoryNode 
              key={idx} 
              subsystem={sub} 
              index={idx + 1} 
              onAnalyze={() => fetchDetails(sub.subsystem)}
            />
          ))
        )}
      </div>

      {/* DETAIL SIDE PANEL */}
      {selectedSS && (
        <>
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity animate-in fade-in" 
            onClick={() => setSelectedSS(null)}
          />
          <div className="fixed right-0 top-0 bottom-0 w-full max-w-2xl bg-[#0a0f1a] border-l border-white/10 z-50 p-10 overflow-y-auto animate-in slide-in-from-right duration-500 shadow-2xl">
            <div className="flex justify-between items-center mb-10">
               <div>
                  <h2 className="text-3xl font-black text-white italic uppercase tracking-tighter">
                    <span className="text-orange-500">Analysis:</span> {selectedSS}
                  </h2>
                  <p className="text-[10px] text-gray-600 font-mono tracking-[0.3em] mt-2 italic">HISTORICAL EXPERIENCE LEDGER</p>
               </div>
               <button 
                 onClick={() => setSelectedSS(null)}
                 className="p-4 bg-white/5 rounded-2xl border border-white/5 text-gray-500 hover:text-white transition-all"
               >
                 <RotateCcw size={20} />
               </button>
            </div>

            {detailsLoading ? (
              <div className="space-y-6">
                 {[1,2,3,4].map(i => <Skeleton key={i} className="h-32 rounded-3xl" />)}
              </div>
            ) : details.length === 0 ? (
              <div className="py-20 text-center opacity-20 italic uppercase tracking-widest text-sm">No detail records found.</div>
            ) : (
              <div className="space-y-6">
                 {details.map((d, idx) => (
                   <div key={idx} className="glass-panel p-6 rounded-3xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-all group">
                      <div className="flex justify-between items-start mb-4">
                         <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${d.outcome === 'success' ? 'bg-green-500 glow-teal' : 'bg-red-500 glow-red'}`} />
                            <span className="text-xs font-black text-white uppercase tracking-wider">{d.outcome}</span>
                         </div>
                         <span className="text-[10px] text-gray-600 font-mono italic">
                            {new Date(d.recorded_at).toLocaleString()}
                         </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 mb-4">
                         <div className="p-3 bg-black/40 rounded-xl border border-white/5">
                            <span className="text-[9px] text-gray-700 font-black uppercase block mb-1">Incident ID</span>
                            <span className="text-xs font-mono text-gray-400">{d.incident_id?.substring(0, 16)}...</span>
                         </div>
                         <div className="p-3 bg-black/40 rounded-xl border border-white/5">
                            <span className="text-[9px] text-gray-700 font-black uppercase block mb-1">Reliability Score</span>
                            <span className="text-xs font-mono text-white font-bold">{(d.score * 100).toFixed(1)}%</span>
                         </div>
                      </div>

                      {d.failure_reason && d.failure_reason !== 'N/A' && (
                        <div className="p-4 bg-red-500/5 border border-red-500/10 rounded-2xl mb-4">
                           <span className="text-[9px] text-red-500/60 font-black uppercase mb-2 block tracking-widest">Failure Diagnosis</span>
                           <p className="text-xs text-red-100/70 italic leading-relaxed">{d.failure_reason}</p>
                        </div>
                      )}

                      {d.rejections && d.rejections.length > 0 && (
                        <div>
                           <span className="text-[9px] text-gray-700 font-black uppercase mb-2 block tracking-widest">Verifier Rejections</span>
                           <div className="flex flex-wrap gap-2">
                              {d.rejections.map((v: string, i: number) => (
                                <span key={i} className="px-2 py-0.5 bg-red-500/10 border border-red-500/20 text-red-500 text-[9px] font-bold uppercase rounded-md tracking-tighter">
                                  {v}
                                </span>
                              ))}
                           </div>
                        </div>
                      )}
                   </div>
                 ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function EliteMemoryMetric({ label, val, icon, accent }: any) {
  return (
    <div className="glass-panel p-8 rounded-[2rem] border-white/5 bg-white/[0.01] hover:bg-white/[0.02] transition-all relative overflow-hidden group">
       <div className="flex justify-between items-center mb-6">
          <span className="text-[10px] text-gray-600 font-black uppercase tracking-widest">{label}</span>
          <div className="p-3 bg-black/40 rounded-xl border border-white/5 text-gray-600 group-hover:text-white transition-colors">
            {icon}
          </div>
       </div>
       <h3 className={`text-4xl font-black tracking-tighter ${accent}`}>{val}</h3>
    </div>
  );
}

function EliteMemoryNode({ subsystem, index, onAnalyze }: { subsystem: any, index: number, onAnalyze: () => void }) {
  const risk = 1 - (subsystem.rate || 0);

  return (
    <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5 bg-white/[0.015] hover:bg-white/[0.035] hover:border-orange-500/30 transition-all group relative overflow-hidden shadow-xl">
       <div 
         className="absolute -top-10 -right-10 w-32 h-32 bg-orange-500/10 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"
         style={{ opacity: 0.1 + risk * 0.4 }}
       />
       
       <div className="relative z-10 flex flex-col h-full">
          <div className="flex justify-between items-start mb-8">
             <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center font-black text-orange-500 text-xs shadow-xl">
                   {index < 10 ? `0${index}` : index}
                </div>
                <div>
                   <h3 className="text-sm font-black text-white uppercase tracking-tight group-hover:text-orange-400 transition-colors truncate max-w-[120px]">
                     {subsystem.subsystem}
                   </h3>
                   <p className="text-[8px] text-gray-700 font-mono tracking-[0.2em] mt-1 uppercase">NODE_ACTIVE</p>
                </div>
             </div>
             <div className="p-2 bg-black/40 rounded-lg border border-white/5">
                <Fingerprint size={12} className="text-gray-700" />
             </div>
          </div>

          <div className="flex-1 flex flex-col justify-end gap-6">
             <div className="flex justify-between items-end">
                <div>
                   <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest block mb-1">Success Rate</span>
                   <span className={`text-4xl font-black tracking-tighter italic ${
                     subsystem.rate > 0.8 ? 'text-green-500' : subsystem.rate > 0.5 ? 'text-orange-500' : 'text-red-500'
                   }`}>
                      {(subsystem.rate * 100).toFixed(0)}%
                   </span>
                </div>
                <div className="text-right">
                   <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest block mb-1">Risk Factor</span>
                   <span className="text-xl font-black text-white font-mono tracking-tighter">{(risk * 100).toFixed(0)}</span>
                </div>
             </div>

             <div className="space-y-3">
                <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden border border-white/[0.03]">
                   <div 
                     className={`h-full transition-all duration-[2000ms] shadow-[0_0_10px_rgba(255,255,255,0.1)]
                        ${risk > 0.7 ? 'bg-gradient-to-r from-red-600 to-red-400' : 
                          risk > 0.4 ? 'bg-gradient-to-r from-orange-600 to-orange-400' : 
                          'bg-gradient-to-r from-green-600 to-green-400'}
                     `}
                     style={{ width: `${risk * 100}%` }}
                   />
                </div>
                <div className="flex justify-between items-center text-[9px] font-black uppercase tracking-widest text-gray-700">
                   <span>{subsystem.failure} Logged Failures</span>
                   <span 
                     onClick={onAnalyze}
                     className="text-orange-500/80 cursor-pointer hover:text-orange-400 transition-colors italic group-hover:translate-x-1 duration-500 translate-all"
                   >
                      Analyze →
                   </span>
                </div>
             </div>
          </div>
       </div>
    </div>
  );
}
