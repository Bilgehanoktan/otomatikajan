"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldCheck, 
  Activity, 
  Cpu, 
  Zap, 
  Terminal, 
  Clock, 
  ChevronRight, 
  Search, 
  Filter, 
  Layers, 
  Gavel,
  AlertTriangle,
  Fingerprint,
  Target,
  BarChart3,
  SearchCode
} from "lucide-react";
import { useTranslations } from "next-intl";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";

export default function VerifiersPage() {
  const t = useTranslations("verifiers");
  const [isClient, setIsClient] = useState(false);
  const [verifiers, setVerifiers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setIsClient(true);
    const fetchVerifiers = async () => {
      try {
        const data = await safeFetchJson('/api/v1/repair-lab/verifiers');
        setVerifiers(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Doğrulayıcı verileri alınamadı", err);
      } finally {
        setLoading(false);
      }
    };
    fetchVerifiers();
  }, []);

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Verifier Mesh" 
        subtitle="Multi-Layer Quality Assurance & Precision Reliability Matrix" 
        icon={<ShieldCheck size={32} />}
        badge="MESH-V5 Active"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Global Precision</span>
                <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono italic tracking-tighter">0.992 NOMINAL</span>
             </div>
             <button className="flex items-center gap-2 px-8 py-3 bg-[var(--primary)] text-[#060a12] text-[10px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95 group">
                <Target size={14} className="group-hover:scale-125 transition-transform" />
                <span>Optimize Mesh</span>
             </button>
          </div>
        }
      />

      {/* VITAL SIGNS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
         <EliteMeshMetric label="Aggregated Precision" val="99.2%" icon={<Activity size={16} />} accent="text-[var(--primary)]" />
         <EliteMeshMetric label="Average Latency" val="1.5s" icon={<Clock size={16} />} accent="text-blue-400" />
         <EliteMeshMetric label="Active Layers" val={verifiers.length || 5} icon={<Layers size={16} />} accent="text-purple-400" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* VERIFIER GRID - Main Column */}
        <div className="xl:col-span-12">
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none text-purple-400">
                 <ShieldCheck size={300} />
              </div>

              <div className="flex items-center justify-between mb-12 relative z-10 px-2">
                 <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-purple-500 animate-ping shadow-[0_0_12px_rgba(168,85,247,0.6)]" />
                    <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">Active Verifier Matrix</h2>
                 </div>
                 <div className="flex items-center gap-6">
                    <div className="relative">
                       <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                       <input 
                         type="text" 
                         placeholder={t("activeLayers")}
                         className="bg-black/40 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-[10px] font-black text-white focus:outline-none focus:border-purple-500/20 transition-all w-48"
                       />
                    </div>
                    <button className="p-2.5 bg-white/5 border border-white/5 rounded-xl text-gray-500 hover:text-white transition-all">
                       <Filter size={18} />
                    </button>
                 </div>
              </div>

              <div className="space-y-6 relative z-10">
                 {loading ? (
                    <div className="space-y-6">
                       {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-32 rounded-3xl" />)}
                    </div>
                 ) : verifiers.length === 0 ? (
                    <div className="py-32 text-center text-gray-700 font-black uppercase tracking-[0.3em] italic">
                       Henüz mesh verisi toplanmadı. Doğu Katmanları bekleniyor...
                    </div>
                 ) : (
                    verifiers.map((v, idx) => (
                       <EliteVerifierItem key={idx} verifier={v} index={idx + 1} />
                    ))
                 )}
              </div>
           </section>
        </div>
      </div>
    </div>
  );
}

function EliteMeshMetric({ label, val, icon, accent }: any) {
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

function EliteVerifierItem({ verifier, index }: { verifier: any, index: number }) {
  return (
    <div className="p-8 rounded-[2rem] border border-white/5 bg-white/[0.015] hover:bg-white/[0.025] hover:border-purple-500/30 transition-all group/item relative overflow-hidden">
       <div className="flex flex-col xl:flex-row justify-between items-center gap-10 relative z-10">
          
          {/* Identity */}
          <div className="flex items-center gap-6 flex-1 min-w-[300px]">
             <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center font-black text-purple-400 text-xl group-hover/item:scale-110 group-hover/item:bg-purple-500/20 transition-all shadow-xl">
                {index < 10 ? `0${index}` : index}
             </div>
             <div>
                <h3 className="text-xl font-black text-white uppercase tracking-tight group-hover/item:text-purple-400 transition-colors">
                  {verifier.name}
                </h3>
                <p className="text-[9px] text-gray-700 font-mono tracking-[0.2em] mt-1 uppercase">INTERNAL_HASH: {verifier.name.toUpperCase()}_V5_STABLE</p>
             </div>
          </div>

          {/* Reliability Gauge */}
          <div className="flex flex-col gap-3 min-w-[200px]">
             <div className="flex justify-between items-end px-1">
                <span className="text-[10px] font-black text-gray-700 uppercase tracking-widest">Reliability</span>
                <span className="text-xs font-mono font-black text-white">{(verifier.reliability * 100).toFixed(0)}%</span>
             </div>
             <div className="w-48 h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/[0.03]">
                <div 
                  className="h-full bg-gradient-to-r from-purple-600 to-blue-400 shadow-[0_0_12px_rgba(168,85,247,0.4)] transition-all duration-1000" 
                  style={{ width: `${verifier.reliability * 100}%` }}
                />
             </div>
          </div>

          {/* Precision & Latency */}
          <div className="grid grid-cols-2 gap-8 min-w-[240px]">
             <div className="flex flex-col gap-2">
                <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Precision</span>
                <span className={`text-[11px] font-black font-mono tracking-tighter ${verifier.precision > 0.9 ? 'text-green-500' : 'text-gray-500'}`}>
                   {(verifier.precision * 100).toFixed(1)}%
                </span>
             </div>
             <div className="flex flex-col gap-2">
                <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Latency</span>
                <span className="text-[11px] font-black font-mono text-gray-500 italic">{verifier.latency}</span>
             </div>
          </div>

          {/* Blocked Errors / Actions */}
          <div className="flex items-center gap-6 min-w-[180px]">
             <div className="px-5 py-2.5 bg-red-500/10 border border-red-500/20 rounded-xl">
                <div className="text-[11px] font-black text-red-500 tracking-tighter uppercase whitespace-nowrap">
                   {verifier.detected_errors} CRITV_FLAGS
                </div>
             </div>
             <button className="p-3 bg-white/5 rounded-xl text-gray-700 hover:text-white transition-all">
                <ChevronRight size={18} />
             </button>
          </div>
       </div>
    </div>
  );
}
