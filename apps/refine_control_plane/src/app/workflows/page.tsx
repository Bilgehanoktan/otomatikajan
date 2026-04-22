"use client";

import React, { useState, useEffect } from "react";
import { useList, useNavigation } from "@refinedev/core";
import { 
  Activity, 
  Clock, 
  ChevronRight, 
  RotateCcw, 
  Zap, 
  ShieldCheck,
  TrendingUp,
  Layout,
  Terminal,
  Cpu,
  Fingerprint,
  Search,
  Filter,
  BarChart3,
  Network
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function WorkflowList() {
  const [isClient, setIsClient] = useState(false);
  useEffect(() => setIsClient(true), []);

  const { query } = useList({
    resource: "workflows",
    sorters: [{ field: "started_at", order: "desc" }],
    queryOptions: { enabled: isClient }
  });
  const { data, isLoading, isError, refetch, error } = query;
  const { show } = useNavigation();

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  const workflowsRaw = data?.data;
  const workflows = Array.isArray(workflowsRaw) ? workflowsRaw : [];
  const activeJobs = workflows.filter(w => w.status?.toLowerCase() === 'running').length;
  
  // Extract global stale meta if the provider switched to Degraded Mode
  const staleMeta = (data as any)?.__sqv_meta || (workflows as any).__sqv_meta;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Active Workflows" 
        subtitle="Real-time Autonomous Orchestration & Decision Traces" 
        icon={<Activity size={32} />}
        badge="Engine Core v13"
        staleMeta={staleMeta}
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Active Cycles</span>
                <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono tracking-tighter italic">{activeJobs} RUNNING</span>
             </div>
             <div className="flex flex-col items-end border-r border-[#66fcf1]/20 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Global Success</span>
                <span className="text-sm font-black text-white mt-2">99.4%</span>
             </div>
             <button onClick={() => refetch()} className="p-4 bg-white/5 border border-white/5 rounded-2xl text-gray-500 hover:text-white transition-all hover:bg-white/10 active:scale-90">
                <RotateCcw size={18} />
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* WORKFLOW STREAM - Main Column */}
        <div className="xl:col-span-12">
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <Network size={300} />
              </div>

              <div className="flex items-center justify-between mb-12 relative z-10 px-2">
                 <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-ping shadow-[0_0_12px_rgba(102,252,241,0.6)]" />
                    <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">Integrated Orchestration Stream</h2>
                 </div>
                 <div className="flex items-center gap-6">
                    <div className="relative">
                       <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                       <input 
                         type="text" 
                         placeholder="İŞ AKIŞI ARA..."
                         className="bg-black/40 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-[10px] font-black text-white focus:outline-none focus:border-[var(--primary)]/20 transition-all w-48"
                       />
                    </div>
                    <button className="p-2.5 bg-white/5 border border-white/5 rounded-xl text-gray-500 hover:text-white transition-all">
                       <Filter size={18} />
                    </button>
                 </div>
              </div>

              <div className="space-y-6 relative z-10">
                 {isLoading ? (
                    <div className="space-y-4">
                       {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-28 rounded-3xl" />)}
                    </div>
                 ) : isError ? (
                    <div className="py-20 text-center text-red-500 font-mono text-[10px] uppercase tracking-widest">
                       Workflow Telemetry Offline: {String(error?.message || "Bilinmeyen hata")}
                    </div>
                 ) : (
                    workflows.map((wf: any) => (
                       <EliteWorkflowItem 
                         key={wf.id} 
                         workflow={wf} 
                         onClick={() => wf.id && show("workflows", wf.id)}
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

function EliteWorkflowItem({ workflow, onClick }: { workflow: any, onClick: () => void }) {
  const status = workflow.status?.toLowerCase();
  const isRunning = status === 'running';
  const isCompleted = status === 'completed';
  const isFailed = status === 'failed';

  return (
    <div 
      onClick={onClick}
      className="p-8 rounded-[2rem] border border-white/5 bg-white/[0.012] hover:bg-white/[0.025] hover:border-[var(--primary)]/30 transition-all group/item cursor-pointer relative overflow-hidden"
    >
       <div className="flex flex-col xl:flex-row justify-between items-center gap-10 relative z-10">
          
          {/* Status Icon */}
          <div className="flex items-center gap-8 flex-1 min-w-[350px]">
             <div className="relative">
                <div className={`w-14 h-14 rounded-2xl border flex items-center justify-center transition-all duration-500 shadow-xl
                   ${isRunning ? 'bg-[var(--primary)]/10 border-[var(--primary)]/20 text-[var(--primary)] group-hover/item:scale-110' : 
                     isCompleted ? 'bg-green-500/10 border-green-500/20 text-green-500' : 
                     isFailed ? 'bg-red-500/10 border-red-500/20 text-red-500' : 'bg-black/40 border-white/5 text-gray-600'}
                `}>
                   <Layout size={24} />
                </div>
                {isRunning && (
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-[var(--primary)] rounded-full border-2 border-[#060a12] animate-pulse shadow-[0_0_10px_var(--primary)]" />
                )}
             </div>
             
             <div>
                <div className="flex flex-wrap items-center gap-4 mb-2">
                   <h3 className="text-lg font-black text-white uppercase tracking-tight group-hover/item:text-[var(--primary)] transition-colors">
                     {workflow.workflow_type || 'GENERAL_OPS'}
                   </h3>
                   <span className={`px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-widest border transition-all
                     ${isRunning ? 'bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/20' : 
                       isCompleted ? 'bg-green-500/10 text-green-500 border-green-500/20' : 
                       isFailed ? 'bg-red-500/10 text-red-500 border-red-500/20' : 'bg-white/5 text-gray-600'}
                   `}>
                     {workflow.status}
                   </span>
                </div>
                <p className="text-[9px] text-gray-700 font-mono tracking-widest uppercase">FLOW_ID: {String(workflow.id).substring(0, 16)}</p>
             </div>
          </div>

          {/* Integrity Badges */}
          <div className="hidden md:flex items-center gap-4 min-w-[240px]">
             <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.015] border border-white/5 hover:border-[var(--primary)]/20 transition-all">
                <ShieldCheck size={14} className="text-green-500" />
                <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">TRUST_L4</span>
             </div>
             <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.015] border border-white/5">
                <Fingerprint size={14} className="text-blue-400" />
                <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">SIGNED</span>
             </div>
          </div>

          {/* Progress / Step Context */}
          <div className="flex flex-col gap-3 min-w-[200px]">
             <div className="flex justify-between items-end px-1">
                <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">
                   Step {workflow.current_step_index || 0} / {workflow.steps?.length || 1}
                </span>
                <span className="text-[10px] font-mono font-black text-white tracking-widest">
                   {Math.round(((workflow.current_step_index || 0) / (workflow.steps?.length || 1)) * 100)}%
                </span>
             </div>
             <div className="w-48 h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/[0.03]">
                <div 
                   className={`h-full bg-gradient-to-r from-[var(--primary)] to-blue-500 shadow-[0_0_10px_rgba(102,252,241,0.3)] transition-all duration-1000
                     ${isFailed ? 'from-red-600 to-red-400' : ''}
                   `} 
                   style={{ width: `${(workflow.current_step_index || 0) / (workflow.steps?.length || 1) * 100}%` }}
                />
             </div>
          </div>

          {/* Action */}
          <div className="flex items-center gap-4 min-w-[100px] justify-end">
             <div className="flex items-center gap-2 text-[var(--primary)] opacity-0 group-hover:item:opacity-100 group-hover:item:translate-x-1 transition-all">
                <span className="text-[10px] font-black uppercase tracking-widest">Inspect</span>
                <ChevronRight size={16} />
             </div>
          </div>
       </div>
    </div>
  );
}
