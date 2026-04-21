"use client";

import { useState, useEffect } from "react";
import { useList, useUpdate } from "@refinedev/core";
import { 
  CheckSquare, 
  XSquare, 
  Cpu, 
  Clock, 
  AlertCircle, 
  Plus,
  ShieldCheck,
  UserCheck,
  Zap,
  ChevronRight,
  Lock,
  Target,
  Gavel,
  Scale
} from "lucide-react";
import { App } from "antd";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function ApprovalsPage() {
  const { notification } = App.useApp();
  const [isClient, setIsClient] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => setIsClient(true), []);

  const { query: { data, isLoading, isError, refetch } } = useList({
    resource: "approvals",
    filters: [
      {
        field: "status",
        operator: "eq",
        value: "pending",
      },
    ],
    queryOptions: {
      enabled: isClient
    }
  });

  const { mutate: updateApproval } = useUpdate();
  
  const handleDecision = (id: string, status: "approved" | "rejected") => {
    updateApproval({
       resource: "approvals",
       id,
       values: { status, comment: `Actioned via Elite Control Plane at ${new Date().toISOString()}` },
    }, {
       onSuccess: () => refetch(),
    });
  };

  const handleCreateDirective = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    notification.success({
       message: "Directive Broadcasted",
       description: "The emergency directive has been propagated across the mesh network.",
       placement: "topRight"
    });
    setIsModalOpen(false);
  };

  const requests = data?.data ?? [];
  const staleMeta = (requests as any).__sqv_meta;

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Quorum Center" 
        subtitle="Multi-Operator Governance Gates & Manual Intervention" 
        icon={<CheckSquare size={32} />}
        badge="L3-L4 Gates"
        staleMeta={staleMeta}
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Decision Integrity</span>
                <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono italic tracking-tighter">99.9% VERIFIED</span>
             </div>
              <button 
                onClick={() => setIsModalOpen(true)}
                className="flex items-center gap-2 px-8 py-3 bg-[var(--primary)] text-[#060a12] text-[10px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95 group"
              >
                 <Plus size={14} className="group-hover:rotate-90 transition-transform" />
                 <span>New Directive</span>
              </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* APPROVAL FEED - Main Column */}
        <div className="xl:col-span-8">
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl min-h-[600px]">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <Gavel size={300} />
              </div>

              <div className="flex items-center justify-between mb-12 relative z-10 px-2">
                 <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-ping shadow-[0_0_12px_rgba(102,252,241,0.6)]" />
                    <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">Pending Sign-Off Quorum</h2>
                 </div>
                 <div className="flex items-center gap-6">
                    <span className="text-[10px] font-black text-gray-700 uppercase tracking-widest">Active Requests: {requests.length}</span>
                 </div>
              </div>

              <div className="space-y-6 relative z-10">
                 {isLoading ? (
                    <div className="space-y-6">
                       {[1,2,3].map(i => <Skeleton key={i} className="h-44 rounded-3xl" />)}
                    </div>
                 ) : isError ? (
                    <div className="py-20 text-center flex flex-col items-center gap-6">
                       <p className="font-mono text-[10px] uppercase text-red-500 tracking-[0.2em]">Quorum Synchronization Lost</p>
                       <button onClick={() => refetch()} className="text-[10px] font-black text-white px-4 py-2 border border-white/10 rounded-xl hover:bg-white/5 transition-all">Retry Consensus</button>
                    </div>
                 ) : requests.length === 0 ? (
                    <div className="py-32 text-center flex flex-col items-center gap-6">
                       <div className="p-8 bg-white/[0.02] rounded-full border border-white/5 opacity-40">
                          <ShieldCheck size={48} className="text-[var(--primary)]" />
                       </div>
                       <p className="font-black text-gray-600 uppercase tracking-[0.3em] italic">
                          Tüm kapılar açık. Bekleyen onay yok.
                       </p>
                    </div>
                 ) : (
                    requests.map((req: any) => (
                       <EliteApprovalCard 
                         key={req.id} 
                         request={req} 
                         onApprove={() => handleDecision(req.id, "approved")}
                         onReject={() => handleDecision(req.id, "rejected")}
                       />
                    ))
                 )}
              </div>
           </section>
        </div>

        {/* SIDEBAR - Quorum Status */}
        <div className="xl:col-span-4 space-y-8">
           {/* Decision Matrix */}
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/50 relative overflow-hidden group shadow-xl">
              <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
                 <Scale size={140} className="text-[var(--primary)]" />
              </div>
              
              <div className="flex items-center gap-4 mb-10 relative z-10">
                 <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-xl">
                    <UserCheck size={24} className="text-[var(--primary)]" />
                 </div>
                 <div>
                    <h3 className="text-xl font-black text-white tracking-tighter uppercase">Quorum State</h3>
                    <p className="text-[9px] text-[var(--primary)] font-black tracking-[0.2em] uppercase mt-1">Institutional Consensus</p>
                 </div>
              </div>

              <div className="space-y-6 relative z-10">
                 <div className="p-6 rounded-2xl bg-white/[0.015] border border-white/5 group-hover:border-[var(--primary)]/20 transition-all">
                    <div className="flex justify-between items-center mb-4">
                       <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest leading-none">Global Threshold</span>
                       <span className="text-sm font-black text-white">4 / 5 SYNC</span>
                    </div>
                    <div className="flex gap-2">
                       {[1,2,3,4,5].map(i => (
                         <div key={i} className={`h-1.5 flex-1 rounded-full transition-all duration-1000 ${i <= 4 ? 'bg-[var(--primary)] shadow-[0_0_8px_var(--primary)]' : 'bg-white/5'}`} />
                       ))}
                    </div>
                 </div>
                 
                 <div className="p-6 rounded-2xl bg-black/40 border border-white/5 group-hover:border-white/10 transition-all">
                    <p className="text-[9px] text-gray-500 font-bold leading-relaxed uppercase tracking-widest mb-6 italic opacity-60">
                       L3+ yetkili işlemler için en az 3 operatör mührü veya 1 yüksek güvenli AI yetkisi gerekmektedir.
                    </p>
                    <div className="flex items-center justify-between">
                       <span className="text-[10px] font-black text-[var(--primary)] uppercase tracking-widest">Protocol Active</span>
                       <Lock size={12} className="text-gray-700" />
                    </div>
                 </div>
              </div>
           </section>

           {/* Quick Stats */}
           <section className="glass-panel p-10 rounded-[3rem] border-white/[0.03] bg-gradient-to-br from-white/[0.01] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="flex flex-col gap-6 relative z-10">
                 <div className="flex justify-between items-center border-b border-white/[0.03] pb-6">
                    <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">Decision Time (Avg)</span>
                    <span className="text-xs font-mono font-black text-white">12.4m</span>
                 </div>
                 <div className="flex justify-between items-center border-b border-white/[0.03] pb-6">
                    <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">Rejection Rate</span>
                    <span className="text-xs font-mono font-black text-red-400">2.1%</span>
                 </div>
                 <div className="flex justify-between items-center">
                    <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">Consensus Drift</span>
                    <span className="text-xs font-mono font-black text-green-400">NOMINAL</span>
                 </div>
              </div>
           </section>
        </div>
      </div>

      {/* NEW DIRECTIVE MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-8 animate-in fade-in zoom-in duration-300">
           <div 
             className="absolute inset-0 bg-[#060a12]/90 backdrop-blur-xl"
             onClick={() => setIsModalOpen(false)}
           />
           <div className="glass-panel w-full max-w-xl p-10 rounded-[3rem] border-[var(--primary)]/20 bg-gradient-to-br from-[#0b0c10] to-[#060a12] relative z-10 shadow-[0_32px_128px_rgba(0,0,0,0.8)]">
              <div className="flex items-center gap-4 mb-10">
                 <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20">
                    <Target size={24} className="text-[var(--primary)]" />
                 </div>
                 <div>
                    <h3 className="text-2xl font-black text-white uppercase tracking-tighter">Emergency Directive</h3>
                    <p className="text-[9px] text-[var(--primary)] font-black uppercase tracking-widest mt-1">Manual Governance Override</p>
                 </div>
              </div>
              
              <form onSubmit={handleCreateDirective} className="space-y-8">
                 <div className="space-y-3">
                    <label className="text-[9px] font-black text-gray-600 uppercase tracking-widest ml-1">Directive Scope</label>
                    <div className="grid grid-cols-2 gap-4">
                       <button type="button" className="p-4 rounded-2xl bg-[var(--primary)]/10 border border-[var(--primary)]/20 text-[var(--primary)] text-[10px] font-black uppercase">Fleet-Wide</button>
                       <button type="button" className="p-4 rounded-2xl bg-white/5 border border-white/10 text-gray-500 text-[10px] font-black uppercase">Local Node</button>
                    </div>
                 </div>

                 <div className="space-y-3">
                    <label className="text-[9px] font-black text-gray-600 uppercase tracking-widest ml-1">Executive Order</label>
                    <textarea 
                      required
                      rows={4}
                      placeholder="Enter directive parameters (e.g. HALT_ALL_TRADES, REBOOT_MESH)..."
                      className="w-full bg-black/40 border border-white/10 rounded-2xl py-5 px-8 text-[11px] font-black text-white focus:outline-none focus:border-[var(--primary)]/50 transition-all resize-none font-mono"
                    />
                 </div>
                 
                 <div className="pt-6 flex gap-6">
                    <button 
                      type="button"
                      onClick={() => setIsModalOpen(false)}
                      className="flex-1 py-5 text-[10px] font-black uppercase text-gray-500 hover:text-white transition-all"
                    >
                       Abort
                    </button>
                    <button 
                      type="submit"
                      className="flex-[2] py-5 bg-[var(--primary)] text-[#060a12] rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] hover:shadow-[0_8px_32px_rgba(102,252,241,0.4)] transition-all active:scale-95"
                    >
                       Broadcast Directive
                    </button>
                 </div>
              </form>
           </div>
        </div>
      )}
    </div>
  );
}

function EliteApprovalCard({ request, onApprove, onReject }: { request: any, onApprove: () => void, onReject: () => void }) {
  const isBudget = request.request_type === 'budget';

  return (
    <div className="p-8 rounded-[2rem] border border-white/5 bg-white/[0.015] hover:bg-white/[0.025] hover:border-[var(--primary)]/30 transition-all group/item relative overflow-hidden">
       <div className="flex flex-col md:flex-row justify-between gap-10 relative z-10">
          <div className="flex items-start gap-6">
             <div className={`p-5 rounded-2xl border transition-all duration-500 shadow-xl
               ${isBudget ? 'bg-amber-500/10 border-amber-500/20 text-amber-500' : 'bg-[var(--primary)]/10 border-[var(--primary)]/20 text-[var(--primary)]'}
               group-hover/item:scale-110
             `}>
                <Zap size={24} className={isBudget ? 'animate-pulse' : ''} />
             </div>
             
             <div>
                <div className="flex flex-wrap items-center gap-4 mb-3">
                   <h3 className="text-xl font-black text-white uppercase tracking-tighter group-hover/item:text-[var(--primary)] transition-colors">
                     {request.request_type} GATE INTERVENTION
                   </h3>
                   <span className="px-2.5 py-1 rounded-lg text-[9px] font-mono font-black bg-black/40 text-gray-600 border border-white/5 uppercase tracking-widest leading-none">
                     TX_ID: {String(request.id).substring(0,12)}
                   </span>
                </div>
                <p className="text-xs font-bold leading-relaxed tracking-tight text-gray-500 max-w-2xl mb-8">
                   "{request.reason}"
                </p>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-8 pt-8 border-t border-white/[0.03]">
                   <div className="flex flex-col gap-2">
                      <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Project Scope</span>
                      <span className="text-[11px] font-black text-white truncate max-w-[140px] uppercase tracking-tight">{String(request.project_id).substring(0,13)}...</span>
                   </div>
                   <div className="flex flex-col gap-2">
                      <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Step Context</span>
                      <span className="text-[11px] font-black text-[var(--primary)] uppercase tracking-tight">{request.step_id || "GLOBAL_OPS"}</span>
                   </div>
                   <div className="flex flex-col gap-2">
                      <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Requested Time</span>
                      <div className="flex items-center gap-2">
                         <Clock size={12} className="text-gray-700" />
                         <span className="text-[11px] font-mono font-black text-gray-500 uppercase">{new Date(request.created_at).toLocaleTimeString()}</span>
                      </div>
                   </div>
                </div>
             </div>
          </div>

          <div className="flex md:flex-col justify-end items-center gap-4 min-w-[200px]">
             <button 
               onClick={onApprove}
               className="w-full flex items-center justify-center gap-3 px-8 py-4 bg-[var(--primary)] text-[#060a12] font-black text-[11px] uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.4)] transition-all active:scale-95 group/approve"
             >
                <CheckSquare size={18} className="group-hover/approve:scale-125 transition-transform" />
                <span>Onayla</span>
             </button>
             <button 
               onClick={onReject}
               className="w-full flex items-center justify-center gap-3 px-8 py-4 bg-red-500/10 text-red-500 border border-red-500/20 font-black text-[11px] uppercase tracking-widest rounded-2xl hover:bg-red-500/20 transition-all active:scale-95"
             >
                <XSquare size={18} />
                <span>Reddet</span>
             </button>
          </div>
       </div>
    </div>
  );
}
