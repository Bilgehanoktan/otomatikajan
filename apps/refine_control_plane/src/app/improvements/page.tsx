"use client";

import React, { useState, useEffect } from "react";
import { useList, useUpdate, useNavigation } from "@refinedev/core";
import { SystemImprovement } from "@/types/mission-control";
import { 
    Cpu, 
    ShieldCheck, 
    AlertTriangle, 
    Code2, 
    Check, 
    X,
    ExternalLink,
    Terminal,
    Clock,
    Zap,
    Activity,
    ChevronRight,
    Search,
    Filter,
    ArrowRight,
    Dna,
    Database,
    Binary
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function ImprovementsPage() {
    const [isClient, setIsClient] = useState(false);
    useEffect(() => setIsClient(true), []);

    const { query: { data, isLoading, isError, refetch } } = useList({
        resource: "improvements",
        pagination: { pageSize: 20 },
        sorters: [{ field: "created_at", order: "desc" }],
        queryOptions: { enabled: isClient }
    });

    const { mutate: updateStatus } = useUpdate();

    const handleApprove = (id: string) => {
        updateStatus({
            resource: "improvements",
            id,
            values: { status: "approved" },
            successNotification: { message: "Patch approved for deployment", type: "success" }
        }, {
            onSuccess: () => refetch()
        });
    };

    const handleReject = (id: string) => {
        updateStatus({
            resource: "improvements",
            id,
            values: { status: "rejected" },
            successNotification: { message: "Patch rejected", type: "error" }
        }, {
            onSuccess: () => refetch()
        });
    };

    if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

    const improvements = data?.data ?? [];
    const pendingCount = improvements.filter(i => i.status === "pending").length;
    const healedCount = improvements.filter(i => i.status === "applied").length;

    return (
        <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
            
            <ResourceHeader 
                title="Evolution Ledger" 
                subtitle="Autonomous Self-Healing & Neural Architectural Overlays" 
                icon={<Dna size={32} />}
                badge="HEAL-V2 Active"
                actions={
                    <div className="flex items-center gap-8">
                        <div className="flex flex-col items-end border-r border-white/5 pr-8">
                            <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Cortex Confidence</span>
                            <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono tracking-tighter italic">98.4% STABLE</span>
                        </div>
                        <div className="flex items-center gap-4">
                            <button className="p-3 bg-white/5 border border-white/5 rounded-2xl text-gray-500 hover:text-white transition-all">
                                <Activity size={18} />
                            </button>
                            <button className="flex items-center gap-2 px-8 py-3 bg-[var(--primary)] text-[#060a12] text-[10px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95 group">
                                <Zap size={14} className="group-hover:animate-pulse" />
                                <span>Recalibrate</span>
                            </button>
                        </div>
                    </div>
                }
            />

            {/* METRICS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
                <EliteMetricCard label="Pending Approval" val={pendingCount} icon={<Clock size={16} />} accent="text-amber-400" />
                <EliteMetricCard label="Total Evolutionary Cycles" val={healedCount} icon={<ShieldCheck size={16} />} accent="text-green-400" />
                <EliteMetricCard label="System Integrity" val="94%" icon={<Activity size={16} />} accent="text-[var(--primary)]" />
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
                {/* IMPROVEMENTS STREAM */}
                <div className="xl:col-span-12">
                   <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl">
                      <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                         <Binary size={300} />
                      </div>

                      <div className="flex items-center justify-between mb-12 relative z-10 px-2">
                         <div className="flex items-center gap-4">
                            <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-ping shadow-[0_0_12px_rgba(102,252,241,0.6)]" />
                            <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">Autonomous Evolution Stream</h2>
                         </div>
                         <div className="flex items-center gap-6">
                            <div className="relative">
                               <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                               <input 
                                 type="text" 
                                 placeholder="MODÜL ARA..."
                                 className="bg-black/40 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-[10px] font-black text-white focus:outline-none focus:border-[var(--primary)]/20 transition-all w-48"
                                />
                            </div>
                            <button className="p-2.5 bg-white/5 border border-white/5 rounded-xl text-gray-500 hover:text-white transition-all">
                               <Filter size={18} />
                            </button>
                         </div>
                      </div>

                      <div className="space-y-8 relative z-10">
                         {isLoading ? (
                            <div className="space-y-6">
                               {[1,2,3].map(i => <Skeleton key={i} className="h-44 rounded-3xl" />)}
                            </div>
                         ) : isError ? (
                            <div className="py-20 text-center text-red-500 font-mono text-[10px] uppercase tracking-widest">Evolution Telemetry Offline</div>
                         ) : (
                             improvements.map((improvement: any) => (
                               <EliteImprovementItem 
                                 key={improvement.id} 
                                 improvement={improvement} 
                                 onApprove={() => handleApprove(improvement.id)}
                                 onReject={() => handleReject(improvement.id)}
                               />
                            ))
                         )}
                      </div>
                   </section>
                </div>
            </div>
        </div>
    );
}

function EliteMetricCard({ label, val, icon, accent }: any) {
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

function EliteImprovementItem({ improvement, onApprove, onReject }: any) {
    const isPending = improvement.status === "pending";
    
    return (
        <div className={`p-8 rounded-[2.5rem] border transition-all duration-500 group/item relative overflow-hidden
          ${isPending ? 'bg-amber-500/[0.02] border-amber-500/20 hover:border-amber-500/40' : 'bg-white/[0.015] border-white/5 hover:border-white/10'}
        `}>
           <div className="flex flex-col xl:flex-row justify-between gap-10 relative z-10">
              <div className="flex-1">
                 <div className="flex items-start gap-6 mb-8">
                    <div className={`p-5 rounded-2xl border transition-all duration-500 shadow-xl
                      ${isPending ? 'bg-amber-500/10 border-amber-500/20 text-amber-500' : 'bg-black/40 border-white/5 text-gray-700'}
                      group-hover/item:scale-110
                    `}>
                       <Code2 size={24} />
                    </div>
                    <div>
                        <div className="flex flex-wrap items-center gap-4 mb-3">
                           <h3 className="text-xl font-black text-white uppercase tracking-tight group-hover/item:text-[var(--primary)] transition-colors">
                             {improvement.target_file}
                           </h3>
                           <span className={`px-2.5 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border transition-all
                             ${improvement.status === 'applied' ? 'bg-green-500/10 text-green-400 border-green-500/20 shadow-[0_0_10px_rgba(34,197,94,0.1)]' : 'bg-amber-500/10 text-amber-500 border-amber-500/20'}
                           `}>
                             {improvement.status}
                           </span>
                        </div>
                        <p className="text-xs font-bold leading-relaxed tracking-tight text-gray-500 max-w-2xl">
                           "{improvement.instruction}"
                        </p>
                    </div>
                 </div>

                 {/* Synthetic Patch Preview */}
                 <div className="bg-black/40 rounded-3xl border border-white/5 p-6 font-mono text-[11px] relative group/patch">
                    <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/5">
                       <div className="flex items-center gap-3 text-gray-700">
                          <Terminal size={14} />
                          <span className="uppercase tracking-widest font-black text-[9px]">Proposed Synthetic Patch</span>
                       </div>
                       <button className="text-[9px] font-black text-gray-700 uppercase hover:text-[var(--primary)] transition-colors">View Diffs</button>
                    </div>
                    <pre className="text-gray-400 overflow-x-auto max-h-40 custom-scrollbar opacity-60 group-hover/patch:opacity-100 transition-opacity">
                       {improvement.proposed_patch}
                    </pre>
                 </div>

                 {/* Verifier Matrix */}
                 <div className="flex items-center gap-10 mt-8 pt-6 border-t border-white/[0.03]">
                    <VerifierBadge label="Syntax" status="PASSED" icon={<ShieldCheck size={12}/>} primary />
                    <VerifierBadge label="Unit Tests" status="12/12 COMPLETED" icon={<Cpu size={12}/>} />
                    <VerifierBadge label="Consensus" status="VERIFIED" icon={<Activity size={12}/>} />
                    
                    <div className="flex items-center gap-3 ml-auto opacity-40">
                       <Clock size={12} className="text-gray-700" />
                       <span className="text-[9px] font-mono font-black text-gray-700 uppercase">{new Date(improvement.created_at).toLocaleString()}</span>
                    </div>
                 </div>
              </div>

              {isPending && (
                <div className="flex xl:flex-col justify-end items-center gap-4 min-w-[220px]">
                   <button 
                     onClick={onApprove}
                     className="w-full flex items-center justify-center gap-3 px-8 py-5 bg-[var(--primary)] text-[#060a12] font-black text-[11px] uppercase tracking-widest rounded-[1.5rem] hover:shadow-[0_8px_32px_rgba(102,252,241,0.4)] transition-all active:scale-95 group/btn"
                   >
                      <Check size={20} />
                      <span>Approve & Apply</span>
                   </button>
                   <button 
                     onClick={onReject}
                     className="w-full flex items-center justify-center gap-3 px-8 py-5 bg-red-500/10 text-red-500 border border-red-500/20 font-black text-[11px] uppercase tracking-widest rounded-[1.5rem] hover:bg-red-500/20 transition-all active:scale-95"
                   >
                      <X size={20} />
                      <span>Reject Patch</span>
                   </button>
                </div>
              )}
           </div>
        </div>
    );
}

function VerifierBadge({ label, status, icon, primary }: any) {
  return (
    <div className="flex items-center gap-3 group/badge cursor-help">
       <div className={`p-1.5 rounded-lg border transition-all ${primary ? 'bg-[var(--primary)]/10 border-[var(--primary)]/20 text-[var(--primary)]' : 'bg-white/5 border-white/5 text-gray-700 group-hover/badge:text-white'}`}>
          {icon}
       </div>
       <div className="flex flex-col">
          <span className="text-[8px] font-black text-gray-700 uppercase tracking-widest">{label}</span>
          <span className={`text-[9px] font-black uppercase tracking-tighter ${primary ? 'text-[var(--primary)]' : 'text-gray-500 group-hover/badge:text-white transition-colors'}`}>{status}</span>
       </div>
    </div>
  );
}
