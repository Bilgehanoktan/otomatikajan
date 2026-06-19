"use client";

import React, { useState, useEffect } from "react";
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
  Waves,
  Fingerprint,
  Lock,
  Share2,
  ExternalLink,
  ChevronRight
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function FederationPage() {
  const [isClient, setIsClient] = useState(false);
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);

  useEffect(() => setIsClient(true), []);

  const clusters = [
    { id: "sec-overwatch", name: "Güvenlik Kümesi", status: "Aktif", trust: 0.98, load: 12, region: "US-EAST", icon: <ShieldCheck size={20}/>, accent: "text-red-400" },
    { id: "logic-cortex", name: "Alan Mantığı", status: "Aktif", trust: 0.95, load: 68, region: "EU-CENTRAL", icon: <Cpu size={20}/>, accent: "text-[var(--primary)]" },
    { id: "ops-reflex", name: "Altyapı & Operasyon", status: "Aktif", trust: 0.97, load: 24, region: "AP-SOUTH", icon: <Server size={20}/>, accent: "text-blue-400" },
    { id: "cost-guardian", name: "Maliyet Ekonomisi", status: "Aktif", trust: 0.99, load: 2, region: "US-WEST", icon: <Activity size={20}/>, accent: "text-green-400" },
  ];

  const arbitrations = [
    { id: "ARB-102", type: "Çakışma", target: "libs/auth/rbac.py", winner: "Güvenlik Kümesi", reason: "Öncelik Üstünlüğü (10 > 5)", time: "10 dk önce", complexity: "Yüksek", hash: "0x7F2A...E1" },
    { id: "ARB-101", type: "Konsensüs", target: "workflow_api/main.py", winner: "Alan Mantığı", reason: "Teklif Veren Tek Kişi", time: "45 dk önce", complexity: "Düşük", hash: "0x3D1B...F4" },
  ];

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Federasyon Merkezi" 
        subtitle="Konsolide İstihbarat Matrisi & Küresel Konsensüs Quorumu" 
        icon={<Network size={32} />}
        badge="Çoklu Bölge"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest">Küresel Quorum</span>
                <div className="flex items-center gap-2 mt-2">
                   <div className="flex gap-1.5">
                      {[1, 2, 3, 4, 5].map(i => (
                         <div key={i} className="w-2.5 h-2.5 rounded-full bg-[var(--primary)] shadow-[0_0_8px_var(--primary)] animate-pulse" style={{ animationDelay: `${i*200}ms` }} />
                      ))}
                   </div>
                   <span className="text-white font-black text-xs ml-3">5 / 5 AKTİF</span>
                </div>
             </div>
             <button className="flex items-center gap-2 px-8 py-3 bg-[var(--primary)] text-[#060a12] text-[10px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95">
                <Share2 size={14} />
                <span>Matrisi Dışa Aktar</span>
             </button>
          </div>
        }
      />

      {/* CLUSTER MONITOR GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 mb-12">
         {clusters.map((c) => (
            <div 
               key={c.id} 
               onClick={() => setSelectedCluster(c.id)}
               className={`glass-panel p-8 rounded-[2.5rem] border transition-all duration-500 group relative overflow-hidden cursor-pointer
                 ${selectedCluster === c.id ? 'bg-white/[0.04] border-[var(--primary)]/40 shadow-2xl' : 'bg-white/[0.012] border-white/5 hover:border-white/10'}
               `}
            >
               <div className={`absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.06] transition-opacity ${c.accent}`}>
                  <Cpu size={140} />
               </div>

               <div className="flex justify-between items-start mb-8 relative z-10">
                  <div className={`p-4 rounded-2xl bg-black/40 border border-white/5 ${c.accent} shadow-xl group-hover:scale-110 transition-transform duration-500`}>
                     {c.icon}
                  </div>
                  <div className="flex flex-col items-end">
                     <span className={`text-[9px] font-black px-3 py-1 rounded-lg uppercase tracking-widest border ${c.status === 'Aktif' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-gray-500/10 text-gray-400'}`}>
                        {c.status}
                     </span>
                     <span className="text-[9px] text-gray-600 font-mono font-black mt-2 tracking-widest leading-none">{c.region}</span>
                  </div>
               </div>

               <div className="relative z-10">
                  <h3 className="text-white font-black text-base mb-1 transition-colors uppercase tracking-tight">{c.name}</h3>
                  <p className="text-[9px] text-gray-700 font-mono mb-8 tracking-widest uppercase">{c.id}</p>
                  
                  <div className="grid grid-cols-2 gap-8 border-t border-white/[0.03] pt-8">
                     <div>
                        <p className="text-[9px] text-gray-600 font-black uppercase tracking-[0.2em] mb-3 flex items-center gap-2">
                           <ShieldCheck size={12} className={c.accent} />
                           Güven
                        </p>
                        <p className={`${c.accent} font-black text-2xl font-mono tracking-tighter`}>{(c.trust * 100).toFixed(0)}%</p>
                     </div>
                     <div>
                        <p className="text-[9px] text-gray-600 font-black uppercase tracking-[0.2em] mb-3 flex items-center gap-2">
                           <Activity size={12} className={c.accent} />
                           Yük
                        </p>
                        <p className="text-white font-black text-2xl font-mono tracking-tighter">{c.load}%</p>
                     </div>
                  </div>

                  <div className="mt-8">
                     <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden border border-white/5">
                        <div className={`h-full opacity-60 bg-current transition-all duration-1000 ${c.accent.replace('text-', 'bg-')}`} style={{ width: `${c.load}%` }}></div>
                     </div>
                  </div>
               </div>
            </div>
         ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
         {/* ARBITRATION LOG */}
         <div className="xl:col-span-8">
            <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.015] to-transparent relative overflow-hidden group">
               <div className="absolute top-0 right-0 p-10 opacity-[0.02] pointer-events-none group-hover:opacity-[0.05] transition-opacity">
                  <Gavel size={240} />
               </div>
               
               <div className="flex items-center justify-between mb-12 relative z-10">
                  <div className="flex items-center gap-4">
                     <div className="p-4 bg-[var(--primary)]/10 rounded-[1.5rem] border border-[var(--primary)]/20 shadow-xl">
                        <Gavel className="text-[var(--primary)]" size={28} />
                     </div>
                     <div>
                        <h2 className="text-2xl font-black text-white italic uppercase tracking-tighter">Hakem Defteri</h2>
                        <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.3em] mt-1">Holografik Bütünlük Kanıtları</p>
                     </div>
                  </div>
                  <div className="flex items-center gap-4">
                     <div className="flex items-center gap-4 text-[10px] font-mono text-gray-700 bg-black/40 px-6 py-3 rounded-2xl border border-white/5">
                        <Fingerprint size={16} className="text-[var(--primary)]" />
                        KONSENSÜS_SENKRONİZE_AKTİF
                     </div>
                  </div>
               </div>
               
               <div className="space-y-6 relative z-10">
                  {arbitrations.map(a => (
                     <div key={a.id} className="p-8 rounded-[2rem] bg-white/[0.015] border border-white/5 hover:bg-white/[0.025] hover:border-[var(--primary)]/30 transition-all group/item cursor-pointer">
                        <div className="flex justify-between items-start mb-8">
                           <div className="flex items-center gap-5">
                              <span className="text-[10px] font-black font-mono p-2 bg-black/40 text-[var(--primary)] rounded-xl tracking-tighter border border-[var(--primary)]/20 shadow-xl">{a.id}</span>
                              <div>
                                 <h4 className="text-white font-black text-base tracking-tight mb-1 group-hover/item:text-[var(--primary)] transition-colors">{a.target}</h4>
                                 <div className="flex items-center gap-3">
                                   <span className="text-[10px] text-gray-600 font-black uppercase tracking-widest">{a.type} Tespit Edildi</span>
                                   <span className="w-1 h-1 rounded-full bg-gray-800" />
                                   <span className="text-[10px] text-gray-600 font-mono tracking-widest">{a.hash}</span>
                                 </div>
                              </div>
                           </div>
                           <div className="text-right">
                              <span className="text-[10px] text-gray-700 font-black block uppercase mb-2 tracking-widest italic">{a.time}</span>
                              <div className={`px-3 py-1 rounded-lg text-[9px] font-black tracking-widest uppercase border ${a.complexity === 'Yüksek' ? 'text-amber-500 border-amber-500/20 bg-amber-500/5 shadow-[0_0_10px_rgba(245,158,11,0.05)]' : 'text-blue-400 border-blue-500/20 bg-blue-500/5'}`}>
                                 KARMAŞIKLIK: {a.complexity === 'Yüksek' ? 'YÜKSEK' : 'DÜŞÜK'}
                              </div>
                         </div>
                        </div>
                        
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 rounded-[1.5rem] bg-[#060a12]/80 border border-white/5 group-hover/item:border-[var(--primary)]/20 transition-all">
                           <div className="flex items-center gap-5 border-r border-white/5 pr-6">
                              <div className="p-4 bg-green-500/10 rounded-2xl flex items-center justify-center text-green-400 border border-green-500/20">
                                 <ShieldCheck size={24} className="animate-pulse" />
                              </div>
                              <div>
                                 <p className="text-[10px] text-gray-700 font-black uppercase tracking-widest mb-1.5 leading-none">Zekâ Kararı</p>
                                 <p className="text-white font-black text-sm uppercase tracking-tight italic">KAZANAN: {a.winner}</p>
                              </div>
                           </div>
                           <div className="flex flex-col justify-center">
                              <p className="text-[10px] text-gray-700 font-black uppercase tracking-widest mb-1.5 leading-none">Mantıksal Çözümleme</p>
                              <p className="text-xs text-[var(--primary)] italic font-mono font-bold">" {a.reason} "</p>
                           </div>
                        </div>
                     </div>
                  ))}
               </div>
            </section>
         </div>

         {/* SIDEBAR: SPECIALIZATION HUD */}
         <div className="xl:col-span-4 flex flex-col gap-10">
            <section className="glass-panel p-10 rounded-[3rem] border-white/[0.03] bg-[#060a12]/50 relative overflow-hidden group">
               <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-[var(--primary)]/[0.03] to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
               <div className="flex items-center gap-4 mb-10 relative z-10">
                  <div className="p-3 bg-orange-500/10 rounded-2xl border border-orange-500/20">
                     <Flame size={20} className="text-orange-500 animate-pulse" />
                  </div>
                  <h3 className="text-base font-black text-white uppercase tracking-tighter italic">Bölgesel Durum</h3>
               </div>
               
               <div className="space-y-10 relative z-10">
                  <HeatmapBar label="Mantık Sinapsı" value={88} color="text-[var(--primary)]" />
                  <HeatmapBar label="Güvenlik Kapısı" value={94} color="text-red-500" />
                  <HeatmapBar label="Ekonomik Yönlendirme" value={42} color="text-green-500" />
                  <HeatmapBar label="Altyapı Durumu" value={76} color="text-blue-400" />
               </div>

               <div className="mt-12 pt-10 border-t border-white/[0.03] relative z-10">
                  <div className="flex items-center justify-between mb-4">
                     <div className="flex items-center gap-2">
                        <Waves size={16} className="text-[var(--primary)]" />
                        <span className="text-[10px] font-black text-white uppercase tracking-widest">Küresel Senk</span>
                     </div>
                     <span className="text-[10px] font-mono text-gray-700">92ms GECİKME</span>
                  </div>
                  <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                     <div className="h-full bg-[var(--primary)]/40 w-[92%] shadow-[0_0_8px_var(--primary)]" />
                  </div>
               </div>
            </section>

            <section className="glass-panel p-10 rounded-[3rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.05] to-transparent relative group overflow-hidden shadow-2xl">
               <div className="absolute -bottom-10 -right-10 opacity-[0.05] group-hover:opacity-10 transition-opacity">
                  <Info size={180} />
               </div>
               <h3 className="text-xs font-black text-[var(--primary)] mb-8 flex items-center gap-3 uppercase tracking-[0.3em] relative z-10">
                  <ShieldCheck size={20} />
                  Protokoller
               </h3>
               <ul className="space-y-6 relative z-10">
                  {[
                    "P0 bölgelerindeki tüm kaynak mutasyonları için konsensüs gereklidir.",
                    "mesh-bus üzerinden her 400ms'de bir kalp atışı telemetrisi yayını.",
                    "Sapma sınırı: Küme karantinasından önce %0.2 varyansa izin verilir."
                  ].map((text, i) => (
                    <li key={i} className="flex gap-4 group/li cursor-help">
                       <div className="mt-1 w-1.5 h-1.5 rounded-full bg-[var(--primary)] border shadow-[0_0_8px_var(--primary)] group-hover/li:scale-150 transition-transform" />
                       <p className="text-[11px] text-gray-500 font-bold leading-relaxed group-hover/li:text-white transition-colors uppercase tracking-tight">{text}</p>
                    </li>
                  ))}
               </ul>
               
               <button className="mt-10 w-full py-5 rounded-2xl bg-white/[0.03] border border-white/10 text-[10px] font-black text-gray-500 hover:text-white hover:border-[var(--primary)]/30 transition-all uppercase tracking-widest flex items-center justify-center gap-3">
                  Tam Protokol Özellikleri <ChevronRight size={14} />
               </button>
            </section>
         </div>
      </div>
    </div>
  );
}

function HeatmapBar({ label, value, color }: any) {
  return (
    <div className="group cursor-help">
       <div className="flex justify-between items-end mb-3">
          <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest group-hover:text-white transition-colors">{label}</span>
          <span className={`text-xs font-black font-mono tracking-tighter ${color}`}>{value}%</span>
       </div>
       <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden border border-white/[0.03] relative group-hover:border-[var(--primary)]/10 transition-all">
          <div className={`h-full opacity-60 transition-all duration-1000 ${color.replace('text-', 'bg-')} shadow-[0_0_15px_currentColor]`} style={{ width: `${value}%` }}></div>
       </div>
    </div>
  );
}
