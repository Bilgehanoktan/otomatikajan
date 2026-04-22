"use client";

import React, { useState, useEffect } from "react";
import { 
  Shield, 
  GitBranch, 
  CheckCircle, 
  Eye, 
  Plus, 
  Search, 
  Filter, 
  GitGraph, 
  Lock, 
  Fingerprint, 
  Activity, 
  ChevronRight,
  Gavel,
  ShieldCheck,
  History,
  FileText,
  Share2,
  ExternalLink
} from "lucide-react";
import { useCustomMutation, useList } from "@refinedev/core";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function PolicyProposalsPage() {
  const [isClient, setIsClient] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => setIsClient(true), []);

  const { data: proposalData, isLoading: isProposalsLoading, isError, refetch } = useList({
    resource: "governance/proposals",
    queryOptions: { enabled: isClient }
  });

  const { mutate } = useCustomMutation();

  const handleApprove = (id: string) => {
    mutate({
      url: `/api/v1/governance/proposals/${id}/approve`,
      method: "post",
      values: {},
      successNotification: {
        message: "Onay Kaydedildi",
        description: "Politika teklifi için onayınız işlendi.",
        type: "success",
      },
    });
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  const proposals = proposalData?.data ?? [];

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Policy Proposals" 
        subtitle="Constitutional Governance & Automated Directive Ratification" 
        icon={<Gavel size={32} />}
        badge="Governance Core"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Statute Version</span>
                <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono italic tracking-tighter">v9.4.2-STABLE</span>
             </div>
              <button 
                onClick={() => setIsModalOpen(true)}
                className="flex items-center gap-2 px-8 py-3 bg-[var(--primary)] text-[#060a12] text-[10px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95 group"
              >
                 <Plus size={14} className="group-hover:rotate-90 transition-transform" />
                 <span>New Amendment</span>
              </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* PROPOSAL STREAM - Main Column */}
        <div className="xl:col-span-8">
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl min-h-[700px]">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <History size={300} />
              </div>

              <div className="flex items-center justify-between mb-12 relative z-10 px-2">
                 <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-ping shadow-[0_0_12px_rgba(102,252,241,0.6)]" />
                    <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">Legislative Proposal Stream</h2>
                 </div>
                 <div className="flex items-center gap-6">
                    <div className="relative">
                       <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                       <input 
                         type="text" 
                         placeholder="TEKLİF ARA..."
                         className="bg-black/40 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-[10px] font-black text-white focus:outline-none focus:border-[var(--primary)]/20 transition-all w-48"
                       />
                    </div>
                    <button className="p-2.5 bg-white/5 border border-white/5 rounded-xl text-gray-500 hover:text-white transition-all">
                       <Filter size={18} />
                    </button>
                 </div>
              </div>

              <div className="space-y-6 relative z-10">
                 {isProposalsLoading ? (
                    <div className="space-y-6">
                       {[1,2,3].map(i => <Skeleton key={i} className="h-44 rounded-3xl" />)}
                    </div>
                 ) : isError ? (
                    <div className="py-20 text-center flex flex-col items-center gap-6">
                       <p className="font-mono text-[10px] uppercase text-red-500 tracking-[0.2em]">Consensus Connection Lost</p>
                       <button onClick={() => refetch()} className="text-[10px] font-black text-white px-4 py-2 border border-white/10 rounded-xl">Retry Sync</button>
                    </div>
                 ) : (
                    proposals.map((proposal: any) => (
                       <div 
                         key={proposal.id} 
                         onClick={() => setSelectedProposal(proposal)}
                         className={`p-8 rounded-[2rem] border transition-all duration-500 group/item relative overflow-hidden cursor-pointer
                           ${selectedProposal?.id === proposal.id ? 'bg-white/[0.04] border-[var(--primary)]/40 shadow-2xl translate-x-1' : 'bg-white/[0.012] border-white/5 hover:border-white/10'}
                         `}
                       >
                          <div className="flex justify-between items-start mb-6">
                             <div className="flex items-center gap-5">
                                <div className="p-4 bg-black/40 rounded-xl border border-white/5 text-gray-600 group-hover/item:text-[var(--primary)] transition-colors">
                                   <Shield size={20} />
                                </div>
                                <div>
                                   <h3 className="text-base font-black text-white uppercase tracking-tight group-hover/item:text-[var(--primary)] transition-colors">{proposal.title}</h3>
                                   <div className="flex items-center gap-3 mt-1">
                                      <span className="text-[9px] font-black bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded tracking-widest">{proposal.scope}</span>
                                      <span className="w-1 h-1 rounded-full bg-gray-800" />
                                      <span className="text-[9px] text-gray-600 font-mono tracking-widest">{new Date(proposal.created_at).toLocaleDateString()}</span>
                                   </div>
                                </div>
                             </div>
                             <div className={`px-3 py-1 rounded-lg text-[9px] font-black tracking-widest uppercase border transition-all
                               ${proposal.status === 'COMMITTED' ? 'bg-green-500/10 text-green-500 border-green-500/20 shadow-[0_0_15px_rgba(34,197,94,0.1)]' : 'bg-amber-500/10 text-amber-500 border-amber-500/20'}
                             `}>
                                {proposal.status}
                             </div>
                          </div>

                          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-6 border-t border-white/[0.03]">
                             <StatBlock label="Quorum Level" val="2/3 SIGNED-OFF" icon={<Activity size={12}/>} />
                             <StatBlock label="Global Consensus" val="66%" icon={<CheckCircle size={12}/>} />
                             <StatBlock label="Git Lineage" val={proposal.git_commit_sha?.substring(0, 8) || "UNSEALED"} icon={<GitGraph size={12}/>} />
                          </div>
                       </div>
                    ))
                 )}
              </div>
           </section>
        </div>

        {/* SIDEBAR - Selection Detail & Statutes */}
        <div className="xl:col-span-4 space-y-8">
           {/* Detailed Context Module */}
           {selectedProposal ? (
             <section className="glass-panel p-10 rounded-[2.5rem] border-[var(--primary)]/20 bg-gradient-to-br from-[var(--primary)]/[0.05] to-transparent relative overflow-hidden animate-in slide-in-from-right-10 duration-500">
                <div className="flex items-center gap-4 mb-8">
                   <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-xl">
                      <ShieldCheck size={24} className="text-[var(--primary)]" />
                   </div>
                   <h3 className="text-xl font-black text-white tracking-tighter uppercase">Amendment Detail</h3>
                </div>
                
                <div className="space-y-6">
                   <div className="p-6 rounded-3xl bg-black/40 border border-white/5">
                      <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-3">Constitutional Impact</h4>
                      <p className="text-xs text-white leading-relaxed font-bold tracking-tight">{selectedProposal.description}</p>
                   </div>
                   
                   <div className="space-y-4">
                      <div className="flex justify-between items-center p-4 rounded-2xl bg-white/[0.02] border border-white/5">
                         <span className="text-[9px] text-gray-600 font-black uppercase tracking-widest">Amendment ID</span>
                         <span className="text-[11px] font-mono font-black text-white">{selectedProposal.id.substring(0, 16)}</span>
                      </div>
                      <div className="flex justify-between items-center p-4 rounded-2xl bg-white/[0.02] border border-white/5">
                         <span className="text-[9px] text-gray-600 font-black uppercase tracking-widest">Author</span>
                         <span className="text-[11px] font-black text-[var(--primary)] uppercase">{selectedProposal.author_id}</span>
                      </div>
                   </div>

                   <button 
                     onClick={() => handleApprove(selectedProposal.id)}
                     disabled={selectedProposal.status !== "PROPOSED"}
                     className="w-full flex items-center justify-center gap-3 py-5 bg-[var(--primary)] text-[#060a12] font-black text-[11px] uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.4)] transition-all active:scale-95 disabled:opacity-40"
                   >
                      <CheckCircle size={18} />
                      <span>Kurumsal Sign-off Ver</span>
                   </button>
                </div>
             </section>
           ) : (
             <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/50 flex flex-col items-center justify-center text-center opacity-60 h-[400px]">
                <div className="p-6 bg-white/[0.02] rounded-full border border-white/5 mb-6">
                   <FileText size={32} className="text-gray-700" />
                </div>
                <p className="text-[11px] font-black text-gray-600 uppercase tracking-widest max-w-[180px]">
                   Analiz etmek istediğiniz teklifi akıştan seçiniz.
                </p>
             </section>
           )}

           {/* Constitutional Status */}
           <section className="glass-panel p-10 rounded-[3rem] border-white/[0.03] bg-gradient-to-br from-white/[0.01] to-transparent relative overflow-hidden group">
              <div className="flex items-center gap-3 mb-8 relative z-10">
                 <Lock size={18} className="text-orange-500" />
                 <h3 className="text-xs font-black text-white uppercase tracking-[0.2em]">Global Statutes</h3>
              </div>
              
              <div className="space-y-4 relative z-10 text-gray-500">
                 <StatuteItem label="Autonomy Level" val="TIER-4 REGULATED" />
                 <StatuteItem label="Quorum Threshold" val="MAJORITY (66%)" />
                 <StatuteItem label="Safety Baseline" val="STRICT ISO-42001" />
              </div>
              
              <button className="mt-10 w-full py-4 bg-white/[0.02] border border-white/5 rounded-2xl text-[9px] font-black text-gray-600 uppercase hover:text-white transition-all tracking-widest flex items-center justify-center gap-3">
                 View Constitution <ExternalLink size={12} />
              </button>
           </section>
        </div>
      </div>

      {/* NEW AMENDMENT MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-8 animate-in fade-in zoom-in duration-300">
           <div 
             className="absolute inset-0 bg-[#060a12]/90 backdrop-blur-xl"
             onClick={() => setIsModalOpen(false)}
           />
           <div className="glass-panel w-full max-w-xl p-10 rounded-[3rem] border-[var(--primary)]/20 bg-gradient-to-br from-[#0b0c10] to-[#060a12] relative z-10 shadow-[0_32px_128px_rgba(0,0,0,0.8)]">
              <div className="flex items-center gap-4 mb-10">
                 <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20">
                    <Gavel size={24} className="text-[var(--primary)]" />
                 </div>
                 <div>
                    <h3 className="text-2xl font-black text-white uppercase tracking-tighter">New Amendment</h3>
                    <p className="text-[9px] text-[var(--primary)] font-black uppercase tracking-widest mt-1">Legislative Proposal Draft</p>
                 </div>
              </div>
              
              <form onSubmit={(e) => { e.preventDefault(); setIsModalOpen(false); }} className="space-y-8">
                 <div className="space-y-3">
                    <label className="text-[9px] font-black text-gray-600 uppercase tracking-widest ml-1">Statute Title</label>
                    <input 
                      required
                      placeholder="e.g. DATA_RETENTION_POLICY_REVISION"
                      className="w-full bg-black/40 border border-white/10 rounded-2xl py-4 px-8 text-[11px] font-black text-white focus:outline-none focus:border-[var(--primary)]/50 transition-all font-mono"
                    />
                 </div>

                 <div className="space-y-3">
                    <label className="text-[9px] font-black text-gray-600 uppercase tracking-widest ml-1">Constitutional Impact Statement</label>
                    <textarea 
                      required
                      rows={4}
                      placeholder="Describe the regulatory and operational changes..."
                      className="w-full bg-black/40 border border-white/10 rounded-2xl py-5 px-8 text-[11px] font-black text-white focus:outline-none focus:border-[var(--primary)]/50 transition-all resize-none font-mono"
                    />
                 </div>
                 
                 <div className="pt-6 flex gap-6">
                    <button 
                      type="button"
                      onClick={() => setIsModalOpen(false)}
                      className="flex-1 py-5 text-[10px] font-black uppercase text-gray-500 hover:text-white transition-all"
                    >
                       Discard Draft
                    </button>
                    <button 
                      type="submit"
                      className="flex-[2] py-5 bg-[var(--primary)] text-[#060a12] rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] hover:shadow-[0_8px_32px_rgba(102,252,241,0.4)] transition-all active:scale-95"
                    >
                       Seal and Propose
                    </button>
                 </div>
              </form>
           </div>
        </div>
      )}
    </div>
  );
}

function StatBlock({ label, val, icon }: any) {
  return (
    <div className="flex flex-col gap-2">
       <div className="flex items-center gap-2 text-gray-700 group-hover/item:text-[var(--primary)] transition-colors">
          {icon}
          <span className="text-[8px] font-black uppercase tracking-[0.2em]">{label}</span>
       </div>
       <span className="text-[11px] font-black text-gray-500 uppercase tracking-tight">{val}</span>
    </div>
  );
}

function StatuteItem({ label, val }: any) {
  return (
    <div className="flex justify-between items-baseline p-4 rounded-xl bg-white/[0.015] border border-white/5 hover:border-orange-500/20 transition-all">
       <span className="text-[8px] font-black uppercase tracking-widest">{label}</span>
       <span className="text-[10px] font-black text-white uppercase tracking-tight">{val}</span>
    </div>
  );
}
