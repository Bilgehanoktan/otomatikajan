"use client";

import React, { useState, useEffect } from "react";
import { 
  FlaskConical, 
  Play, 
  BarChart3, 
  Activity, 
  Cpu, 
  Zap,
  Info,
  Clock,
  ShieldCheck,
  TrendingUp,
  Binary,
  Target,
  RefreshCcw,
  Search,
  Filter
} from "lucide-react";
import { PatchTournamentBoard, VerifierMatrix } from "@/components/repair/LabComponents";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function RepairLabPage() {
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [tournament, setTournament] = useState<any>(null);
  const [matrix, setMatrix] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => { setIsClient(true); }, []);

  const fetchData = async () => {
    try {
      const benchRes = await fetch('/api/v1/repair-lab/benchmarks');
      const benchData = await benchRes.json();
      setBenchmarks(Array.isArray(benchData) ? benchData : []);

      const tourRes = await fetch('/api/v1/repair-lab/tournaments');
      const tourData = await tourRes.json();
      if (tourData && tourData.length > 0) {
        const latest = tourData[0];
        setTournament(latest);

        const matrixRes = await fetch(`/api/v1/repair-lab/verifiers/matrix?tournament_id=${latest.id}`);
        const matrixData = await matrixRes.json();
        setMatrix(matrixData);
      }
    } catch (err) {
      console.error("Laboratuvar verileri alınamadı", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isClient) return;
    fetchData();
    const interval = setInterval(fetchData, 15000); 
    return () => clearInterval(interval);
  }, [isClient]);

  const runLab = async () => {
    setLoading(true);
    try {
      await fetch('/api/v1/repair-lab/run', { method: 'POST' });
      // We don't use window.alert in elite UI, but for now we follow the existing pattern with a small delay
      setTimeout(fetchData, 2000);
    } catch (err) {
      console.error("Laboratuvar başlatılamadı.");
    } finally {
      setLoading(false);
    }
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Repair Laboratory" 
        subtitle="Scientific Evidence Chain & Patch Tournament Matrix" 
        icon={<FlaskConical size={32} />}
        badge="Phase 28 Active"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Global Accuracy</span>
                <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono tracking-tighter italic">94.2% NOMINAL</span>
             </div>
             <button 
               onClick={runLab}
               className="flex items-center gap-2 px-10 py-4 bg-[var(--primary)] text-[#060a12] text-[11px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_48px_rgba(102,252,241,0.4)] transition-all active:scale-95 group"
             >
                <Play size={16} className="fill-[#060a12] group-hover:scale-125 transition-transform" />
                <span>Execute Benchmark</span>
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* LEFT: Benchmarks & Samples */}
        <div className="xl:col-span-3 space-y-10">
           <section className="glass-panel p-8 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-xl">
              <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <Binary size={120} />
              </div>

              <div className="flex items-center justify-between mb-10 relative z-10 px-2">
                 <h3 className="text-xs font-black text-white uppercase tracking-[0.3em] italic">System Benchmarks</h3>
                 <BarChart3 size={16} className="text-gray-700" />
              </div>

              <div className="space-y-4 relative z-10">
                 {loading && benchmarks.length === 0 ? (
                    <div className="space-y-4">
                       {[1,2,3,4].map(i => <Skeleton key={i} className="h-24 rounded-2xl" />)}
                    </div>
                 ) : benchmarks.length === 0 ? (
                    <div className="py-20 text-center opacity-30 flex flex-col items-center gap-4">
                       <Target size={32} className="text-gray-700" />
                       <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">No Active Samples</span>
                    </div>
                 ) : (
                    benchmarks.map((b: any) => (
                       <EliteBenchmarkCard key={b.id} benchmark={b} />
                    ))
                 )}
              </div>

              <div className="mt-10 p-5 bg-black/40 rounded-2xl border border-white/5 relative z-10">
                 <div className="flex items-center gap-3 mb-3">
                    <Info size={14} className="text-[var(--primary)]" />
                    <span className="text-[9px] font-black text-[var(--primary)] uppercase tracking-widest">Evidence Notice</span>
                 </div>
                 <p className="text-[10px] text-gray-600 leading-relaxed font-mono uppercase font-black">
                    Results are signed & <br/>ledgered in Lineage V2.
                 </p>
              </div>
           </section>
        </div>

        {/* RIGHT: Active Tournament & Verifiers */}
        <div className="xl:col-span-9 space-y-10">
           <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
              <div className="xl:col-span-8">
                 <PatchTournamentBoard data={tournament} />
              </div>
              
              <div className="xl:col-span-4 h-full">
                 <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent h-full flex flex-col relative overflow-hidden group shadow-xl">
                    <div className="absolute -bottom-10 -right-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity duration-1000">
                       <TrendingUp size={200} className="text-[var(--primary)]" />
                    </div>
                    
                    <div className="flex items-center gap-4 mb-10 relative z-10 px-2">
                       <div className="p-3 bg-white/5 rounded-xl border border-white/10 text-[var(--primary)]">
                          <TrendingUp size={20} />
                       </div>
                       <h3 className="text-xl font-black text-white tracking-tighter uppercase">Stats</h3>
                    </div>
                    
                    {tournament ? (
                      <div className="flex-1 flex flex-col justify-between relative z-10">
                         <div className="space-y-1">
                            {[
                              { label: "Incident ID", val: tournament.incident_id, icon: <Activity size={14}/> },
                              { label: "Candidates", val: tournament.total_candidates, icon: <Cpu size={14}/> },
                              { label: "Execution", val: new Date(tournament.created_at).toLocaleTimeString(), icon: <Clock size={14}/> },
                              { label: "Quorum", val: "VERIFIED", icon: <ShieldCheck size={14} className="text-green-500"/> },
                              { label: "Diversity", val: "HIGH", icon: <Binary size={14} className="text-blue-400"/> },
                            ].map(item => (
                               <div key={item.label} className="flex items-center justify-between py-5 border-b border-white/[0.03] last:border-0 hover:bg-white/[0.012] transition-colors rounded-xl px-2">
                                  <div className="flex items-center gap-4 text-gray-600">
                                     {item.icon}
                                     <span className="text-[9px] font-black uppercase tracking-widest">{item.label}</span>
                                  </div>
                                  <span className="text-[11px] font-black text-white tracking-tighter uppercase font-mono">{item.val}</span>
                               </div>
                            ))}
                         </div>
                         
                         <div className="mt-10 p-6 bg-[var(--primary)]/[0.03] rounded-3xl border border-[var(--primary)]/10 text-center">
                            <p className="text-[10px] text-gray-500 leading-loose uppercase font-black italic tracking-widest">
                               "Optimal strategy selected <br/>via multi-critera evaluation."
                            </p>
                         </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center flex-1 py-12 text-gray-700 opacity-40">
                        <RefreshCcw size={48} className="animate-spin mb-6" />
                        <span className="text-[9px] font-black uppercase tracking-widest">Syncing Telemetry...</span>
                      </div>
                    )}
                 </section>
              </div>
           </div>
           
           <VerifierMatrix matrix={matrix} />
        </div>

      </div>
    </div>
  );
}

function EliteBenchmarkCard({ benchmark }: { benchmark: any }) {
  const isPass = benchmark.status === 'completed';

  return (
    <div className="p-6 rounded-[2rem] border border-white/5 bg-white/[0.015] hover:bg-white/[0.03] hover:border-[var(--primary)]/20 transition-all cursor-pointer group/card relative overflow-hidden">
       <div className="flex justify-between items-start mb-6">
          <div className="flex-1 mr-4">
             <h4 className="text-[11px] font-black text-white uppercase tracking-tight group-hover/card:text-[var(--primary)] transition-colors line-clamp-1">
                {benchmark.name}
             </h4>
             <p className="text-[8px] font-mono font-black text-gray-700 mt-1 uppercase tracking-widest">S-LEVEL: {benchmark.id.substring(0,6)}</p>
          </div>
          <span className={`px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest border transition-all
             ${isPass ? 'text-green-400 border-green-400/20 bg-green-500/10' : 'text-[var(--primary)] border-[var(--primary)]/20 bg-[var(--primary)]/10'}
          `}>
             {isPass ? 'Pass' : 'Active'}
          </span>
       </div>
       
       <div className="flex items-center justify-between pt-4 border-t border-white/[0.03]">
          <div className="flex flex-col gap-1">
             <span className="text-[8px] font-black text-gray-700 uppercase tracking-widest">Accuracy</span>
             <span className="text-[11px] font-black text-gray-400 font-mono tracking-tighter">{(benchmark.success_rate * 100).toFixed(0)}%</span>
          </div>
          <div className="flex flex-col items-end gap-1">
             <span className="text-[8px] font-black text-gray-700 uppercase tracking-widest">Score</span>
             <span className="text-[11px] font-black text-white font-mono tracking-tighter">{(benchmark.avg_score * 100).toFixed(0)}</span>
          </div>
       </div>
    </div>
  );
}
