"use client";

import { useState, useEffect } from "react";
import { useList } from "@refinedev/core";
import { 
  FileText, 
  ShieldCheck, 
  Activity, 
  Cpu, 
  Zap, 
  ChevronRight,
  Plus,
  Clock,
  ExternalLink,
  Lock,
  Hash,
  Fingerprint,
  Share2,
  CheckCircle2,
  Users
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function AuditPage() {
  const [isClient, setIsClient] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<any>(null);

  useEffect(() => { setIsClient(true); }, []);

  const { query: { data: improvementsData, isLoading: isImprovementsLoading, isError: isImprovementsError } } = useList({
    resource: "improvements",
    sorters: [{ field: "created_at", order: "desc" }],
    queryOptions: {
      enabled: isClient
    }
  });

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  const improvements = improvementsData?.data ?? [];

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Audit Ledger" 
        subtitle="Immutable Verification & Multi-Operator Quorum" 
        icon={<FileText size={32} />}
        badge="Institutional Grade"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex items-center gap-4 border-r border-white/5 pr-8">
                <div className="text-right">
                   <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Lineage State</p>
                   <p className="text-[11px] text-green-400 font-black mt-2">SEALED & SYNCED</p>
                </div>
                <div className="p-3 bg-green-500/10 rounded-full animate-pulse border border-green-500/20">
                   <Lock size={16} className="text-green-400" />
                </div>
             </div>
             
             <button className="flex items-center gap-2 px-8 py-3 bg-[var(--primary)] text-[#060a12] text-[10px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95">
                <Share2 size={14} />
                <span>Export Proof</span>
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* TIMELINE SECTION - Main Stream */}
        <div className="xl:col-span-8">
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.01] to-transparent relative overflow-hidden">
              {/* Holographic Seal Sub-layer */}
              <div className="absolute -top-20 -right-20 opacity-[0.03] rotate-12 pointer-events-none">
                 <ShieldCheck size={400} className="text-[var(--primary)]" />
              </div>

              <div className="flex items-center justify-between mb-12 relative z-10">
                <div className="flex items-center gap-4">
                   <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-ping" />
                   <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">Live Verification Stream</h2>
                </div>
                <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500 bg-black/40 px-4 py-2 rounded-xl border border-white/5">
                   <Fingerprint size={14} className="text-[var(--primary)]" />
                   SHA-256 PARITY VERIFIED
                </div>
              </div>

              <div className="relative pl-12 space-y-12 before:absolute before:left-[17px] before:top-4 before:bottom-4 before:w-px before:bg-gradient-to-b before:from-[var(--primary)]/60 before:via-white/5 before:to-transparent">
                 {isImprovementsLoading ? (
                    <div className="space-y-12">
                       {[1,2,3].map(i => <Skeleton key={i} className="h-40 w-full rounded-3xl" />)}
                    </div>
                 ) : (
                    improvements.map((item: any) => (
                       <div 
                         key={item.id} 
                         onClick={() => setSelectedEvent(item)}
                         className={`relative group cursor-pointer transition-all duration-500 ${selectedEvent?.id === item.id ? 'translate-x-2' : ''}`}
                       >
                          {/* Timeline Dot */}
                          <div className={`absolute -left-[45px] top-2 w-6 h-6 rounded-full bg-[#060a12] border-2 transition-all duration-500 z-10 
                            ${selectedEvent?.id === item.id ? 'border-[var(--primary)] scale-125 shadow-[0_0_15px_var(--primary)]' : 'border-gray-800 group-hover:border-[var(--primary)]/60 shadow-xl'}
                          `}>
                             <div className="absolute inset-1 rounded-full bg-[var(--primary)]/10 animate-pulse" />
                          </div>
                          
                          <div className="flex flex-col gap-5">
                             <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                   <span className="text-[10px] font-mono text-gray-600 tracking-widest uppercase">{new Date(item.created_at).toLocaleString()}</span>
                                   <div className={`px-3 py-1 rounded-lg text-[9px] font-black tracking-widest uppercase border ${
                                      item.status === 'applied' || item.status === 'completed' 
                                        ? 'bg-green-400/5 text-green-400 border-green-400/20 shadow-[0_0_10px_rgba(34,197,94,0.1)]' 
                                        : 'bg-amber-400/5 text-amber-400 border-amber-400/20'
                                   }`}>
                                      {item.status}
                                   </div>
                                </div>
                                <div className="flex items-center gap-2 group-hover:text-[var(--primary)] transition-colors">
                                   <Hash size={12} className="text-gray-700" />
                                   <span className="text-[10px] font-mono text-gray-700 font-bold uppercase tracking-widest">{String(item.id).substring(0,12)}</span>
                                </div>
                             </div>

                             <div className={`p-8 rounded-[2rem] border transition-all duration-500 relative overflow-hidden ${
                               selectedEvent?.id === item.id 
                                 ? 'bg-white/[0.04] border-[var(--primary)]/40 shadow-2xl' 
                                 : 'bg-white/[0.012] border-white/5 hover:border-white/10 hover:bg-white/[0.02]'
                             }`}>
                                <div className="flex justify-between items-start mb-6">
                                   <h4 className="text-white font-black text-base tracking-tight leading-snug max-w-xl">
                                      {item.instruction}
                                   </h4>
                                   <div className="flex -space-x-2">
                                      {[1, 2, 3].map(i => (
                                         <div key={i} className="w-7 h-7 rounded-full bg-gray-800 border-2 border-[#060a12] flex items-center justify-center">
                                            <Users size={12} className="text-gray-500" />
                                         </div>
                                      ))}
                                      <div className="w-7 h-7 rounded-full bg-[var(--primary)] border-2 border-[#060a12] flex items-center justify-center">
                                         <ShieldCheck size={12} className="text-[#060a12]" />
                                      </div>
                                   </div>
                                </div>

                                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 pt-6 border-t border-white/[0.03]">
                                   <EvidenceItem label="Cortex Layer" val="v13.4-PRO" icon={<Cpu size={12}/>} />
                                   <EvidenceItem label="Quorum Level" val="L-4 ADVISORY" icon={<Users size={12}/>} />
                                   <EvidenceItem label="Drift Scan" status="NOMINAL" icon={<Activity size={12}/>} />
                                   <EvidenceItem label="Auth Hash" val="7F8A..91" icon={<Lock size={12}/>} />
                                </div>
                                
                                {selectedEvent?.id === item.id && (
                                  <div className="mt-8 pt-8 border-t border-white/5 flex items-center justify-between animate-in slide-in-from-top-4 duration-500">
                                     <div className="flex flex-col gap-1">
                                        <span className="text-[8px] font-black text-gray-600 uppercase tracking-widest">Parent Lineage</span>
                                        <span className="text-[10px] font-mono text-gray-500 leading-none">0x72a...8e11</span>
                                     </div>
                                     <div className="flex items-center gap-4">
                                        <button className="text-[10px] font-black text-[var(--primary)] uppercase tracking-widest flex items-center gap-2 hover:translate-x-1 transition-transform">
                                           Full Decision Proof <ExternalLink size={12} />
                                        </button>
                                     </div>
                                  </div>
                                )}
                             </div>
                          </div>
                       </div>
                    ))
                 )}
              </div>
           </section>
        </div>

        {/* SIDEBAR - Elite Evidence Panel */}
        <div className="xl:col-span-4 space-y-8">
           {/* Governance Snapshot Card */}
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/50 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity">
                 <ShieldCheck size={160} />
              </div>
              
              <div className="flex items-center gap-4 mb-10 relative z-10">
                 <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-[0_0_20px_rgba(102,252,241,0.15)]">
                    <ShieldCheck size={24} className="text-[var(--primary)]" />
                 </div>
                 <div>
                    <h3 className="text-xl font-black text-white tracking-tighter uppercase">Governance</h3>
                    <p className="text-[9px] text-[var(--primary)] font-black tracking-[0.2em] uppercase mt-1">Audit Policy v9.2</p>
                 </div>
              </div>

              <div className="space-y-5 relative z-10">
                 {[
                   { label: "Autonomy Tier", val: "TIER-4 REGULATED", status: "text-white" },
                   { label: "Consensus Mode", val: "MAJORITY QUORUM", status: "text-white" },
                   { label: "Lineage Sealing", val: "ACTIVE (REAL-TIME)", status: "text-green-400" },
                   { label: "Retraction Window", val: "15 MINUTES", status: "text-[var(--primary)]" },
                 ].map(item => (
                    <div key={item.label} className="p-5 rounded-3xl bg-white/[0.015] border border-white/5 hover:border-[var(--primary)]/20 transition-all">
                       <p className="text-[9px] text-gray-600 font-black uppercase tracking-widest mb-1.5">{item.label}</p>
                       <p className={`text-xs font-black uppercase tracking-tight ${item.status}`}>{item.val}</p>
                    </div>
                 ))}
              </div>
           </section>

           {/* Proof of Integrity Card */}
           <section className="glass-panel p-10 rounded-[2.5rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.03] to-transparent">
              <div className="flex items-center justify-between mb-8">
                 <div className="flex items-center gap-3">
                    <CheckCircle2 size={18} className="text-green-400" />
                    <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Integrity Check</h3>
                 </div>
                 <span className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">99.9% Parity</span>
              </div>
              
              <div className="space-y-6">
                 <div className="h-44 w-full flex items-end gap-1.5 px-2 py-4 border-b border-white/5 relative">
                    {[40, 70, 45, 90, 65, 80, 50, 85, 95, 60, 40, 75, 55, 90].map((h, i) => (
                       <div 
                         key={i} 
                         className="flex-1 bg-[var(--primary)]/10 hover:bg-[var(--primary)] group transition-all rounded-t-sm relative cursor-pointer" 
                         style={{ height: `${h}%` }}
                       >
                          <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-black px-2 py-1 rounded text-[7px] font-mono text-[var(--primary)] border border-[var(--primary)]/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                             H-{i}: {h}%
                          </div>
                       </div>
                    ))}
                    {/* Floating Label */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center pointer-events-none">
                       <span className="text-[3rem] font-black text-white/5 leading-none">SEALED</span>
                    </div>
                 </div>
                 
                 <div className="flex items-center gap-4 p-5 rounded-2xl bg-black/40 border border-white/5">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                    <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest leading-relaxed">
                       Sistem her 120 saniyede bir otonom kanıtları mühürleyerek değişmezlik zincirine ekler.
                    </p>
                 </div>
              </div>
           </section>
        </div>
      </div>
    </div>
  );
}

function EvidenceItem({ label, val, status, icon }: { label: string, val?: string, status?: string, icon: any }) {
  return (
    <div className="flex flex-col gap-2">
       <div className="flex items-center gap-2 text-gray-600">
          {icon}
          <span className="text-[8px] font-black uppercase tracking-widest">{label}</span>
       </div>
       {status ? (
         <span className="text-[10px] font-black text-blue-400 tracking-widest uppercase">{status}</span>
       ) : (
         <span className="text-[10px] font-black text-gray-400 tracking-tight uppercase truncate">{val}</span>
       )}
    </div>
  );
}
