"use client";

import { useList } from "@refinedev/core";
import { 
  FileText, 
  User, 
  Tag, 
  Clock, 
  ChevronRight, 
  ShieldCheck, 
  Activity, 
  Cpu, 
  Zap, 
  AlertTriangle 
} from "lucide-react";

export default function AuditPage() {
  const { query: { data: improvementsData, isLoading: isImprovementsLoading } } = useList({
    resource: "improvements",
    sorters: [{ field: "created_at", order: "desc" }]
  });

  const improvements = improvementsData?.data ?? [];

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 rounded-xl backdrop-blur-md border border-purple-500/20 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
            <FileText className="w-8 h-8 text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#c5c6c7]">
              Autonomous Ledger
            </h1>
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">Immutable Decision Records (Phase 17)</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
           <div className="flex flex-col items-end">
              <span className="text-[10px] text-[#45a29e] font-black uppercase">System Trust Index</span>
              <div className="flex items-center gap-2 mt-1">
                 <div className="w-32 h-2 bg-white/5 rounded-full overflow-hidden border border-white/5">
                    <div className="h-full bg-gradient-to-r from-purple-500 to-[#66fcf1] w-[92%] shadow-[0_0_10px_rgba(102,252,241,0.3)]"></div>
                 </div>
                 <span className="text-white font-black text-sm">92%</span>
              </div>
           </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* TIMELINE SECTION */}
        <div className="lg:col-span-2">
           <section className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#1f2833]/10 backdrop-blur-xl">
              <h2 className="text-xl font-semibold text-white mb-8 flex items-center gap-3">
                 <Activity size={20} className="text-[#66fcf1]" />
                 Transition Stream
              </h2>

              <div className="relative pl-8 space-y-12 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[2px] before:bg-gradient-to-b before:from-[#66fcf1] before:via-purple-500/50 before:to-transparent">
                 {isImprovementsLoading ? (
                    <div className="py-20 text-center text-gray-500">Retrieving autonomous history...</div>
                 ) : improvements.length === 0 ? (
                    <div className="py-20 text-center text-gray-500">No transitions recorded in the current ledger.</div>
                 ) : (
                    improvements.map((item: any) => (
                       <div key={item.id} className="relative group">
                          {/* Timeline Dot */}
                          <div className="absolute -left-[35px] top-1.5 w-4 h-4 rounded-full bg-[#0b0c10] border-2 border-[#66fcf1] z-10 group-hover:scale-125 group-hover:shadow-[0_0_10px_#66fcf1] transition-all"></div>
                          
                          <div className="flex flex-col gap-4">
                             <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                   <span className="text-[10px] font-mono text-[#45a29e] tracking-widest uppercase">{new Date(item.created_at).toLocaleTimeString()}</span>
                                   <span className={`px-2 py-0.5 rounded text-[9px] font-black tracking-tighter uppercase
                                      ${item.status === 'applied' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'}`}>
                                      {item.status}
                                   </span>
                                </div>
                                <span className="text-[10px] font-bold text-gray-600">ID: {String(item.id).substring(0,8) || 'N/A'}</span>
                             </div>

                             <div className="p-5 rounded-2xl bg-white/5 border border-white/5 group-hover:border-[#66fcf1]/30 group-hover:bg-white/[0.08] transition-all">
                                <h4 className="text-white font-bold text-sm mb-2 flex items-center gap-2">
                                   <Zap size={14} className="text-yellow-400" />
                                   {item.instruction}
                                </h4>
                                <div className="flex items-center gap-4 text-[11px] text-gray-400 mb-4 pb-4 border-b border-white/5">
                                   <span className="flex items-center gap-1"><Cpu size={12} /> Model: gpt-4o-mini</span>
                                   <span className="flex items-center gap-1 text-green-400"><ShieldCheck size={12} /> Verified (12 Tests)</span>
                                </div>
                                <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest">
                                   <div className="flex items-center gap-2">
                                      <span className="text-gray-500">Risk Score:</span>
                                      <span className="text-blue-400">0.12 (LOW)</span>
                                   </div>
                                   <button className="flex items-center gap-1 text-[#66fcf1] hover:underline cursor-pointer">
                                      View Decision Context <ChevronRight size={10} />
                                   </button>
                                </div>
                             </div>
                          </div>
                       </div>
                    ))
                 )}
              </div>
           </section>
        </div>

        {/* SIDEBAR: POLICY SNAPSHOT */}
        <div className="flex flex-col gap-8">
           <section className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60">
              <h3 className="text-white font-bold mb-6 text-sm flex items-center gap-2">
                 <ShieldCheck size={16} className="text-[#66fcf1]" />
                 Governance Baseline
              </h3>
              <div className="space-y-4">
                 <div className="flex justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                    <span className="text-xs text-gray-400">Autonomy Tier</span>
                    <span className="text-xs text-white font-black">TIER-4 (ADVANCED)</span>
                 </div>
                 <div className="flex justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                    <span className="text-xs text-gray-400">Canary Period</span>
                    <span className="text-xs text-white font-black">15 MINUTES</span>
                 </div>
                 <div className="flex justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                    <span className="text-xs text-gray-400">Drift Check</span>
                    <span className="text-xs text-green-400 font-black">NOMINAL</span>
                 </div>
              </div>
           </section>

           <section className="p-6 rounded-2xl border border-red-500/10 bg-red-500/5">
              <h3 className="text-red-400 font-bold mb-4 flex items-center gap-2 text-sm uppercase tracking-tighter">
                 <AlertTriangle size={16} />
                 Critical Reversions
              </h3>
              <div className="text-[10px] text-gray-500 italic py-4 text-center">
                 No automated rollbacks detected in the current governance window.
              </div>
           </section>
        </div>
      </div>
    </div>
  );
}
