"use client";

import React from "react";
import {
  Zap, ShieldCheck, TrendingUp, Trophy, AlertTriangle, Fingerprint, Activity, Binary, Cpu, FlaskConical,
  GitPullRequest, FileSearch, Bug, CheckCircle2, Clock, Image, ExternalLink, ChevronRight, Search
} from "lucide-react";

export const PatchTournamentBoard = ({ data }: { data: any }) => {
  if (!data) return (
    <div className="glass-panel p-10 rounded-[2.5rem] border-white/[0.05] bg-white/[0.01] animate-pulse">
      <div className="h-6 w-48 bg-white/5 rounded-lg mb-8"></div>
      <div className="space-y-6">
        {[1, 2, 3].map(i => <div key={i} className="h-28 bg-white/5 rounded-3xl"></div>)}
      </div>
    </div>
  );

  return (
    <div className="glass-panel p-10 rounded-[2.5rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.02] to-transparent relative overflow-hidden group shadow-2xl">
      <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
         <FlaskConical size={200} />
      </div>

      <div className="flex items-center justify-between mb-12 relative z-10 px-2">
        <div className="flex items-center gap-4">
          <div className="p-3.5 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-[0_0_24px_rgba(102,252,241,0.1)]">
            <Trophy size={24} className="text-[var(--primary)]" />
          </div>
          <div>
            <h3 className="text-xl font-black text-white uppercase tracking-tight">Patch Tournament Rankings</h3>
            <p className="text-[9px] font-black text-gray-500 uppercase tracking-[0.2em] mt-1">Autonomous Strategy Selection Matrix</p>
          </div>
        </div>
        <div className="flex items-center gap-3 bg-black/40 px-5 py-2.5 rounded-2xl border border-white/5">
           <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
           <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Active Tournament</span>
        </div>
      </div>

      <div className="space-y-6 relative z-10">
        {(!data?.candidates || data.candidates.length === 0) && (
          <div className="py-32 text-center flex flex-col items-center gap-8 opacity-40">
             <div className="p-10 rounded-full bg-white/[0.02] border border-dashed border-white/10">
                <Binary size={48} className="text-gray-700" />
             </div>
             <p className="text-xs font-black text-gray-700 font-mono uppercase tracking-[0.3em] leading-loose italic max-w-xs text-center">
               Awaiting Candidates... <br/>Execute Benchmark to trigger generation.
             </p>
          </div>
        )}
        {data?.candidates?.map((candidate: any, idx: number) => {
          const isWinner = candidate.status === 'winner';
          const isRejected = candidate.status === 'rejected';

          return (
            <div
              key={idx}
              className={`p-6 rounded-[2rem] border transition-all duration-700 hover:translate-x-2 group/card relative overflow-hidden
                ${isWinner
                  ? 'bg-[var(--primary)]/[0.04] border-[var(--primary)]/40 shadow-[0_12px_48px_rgba(102,252,241,0.1)] ring-1 ring-[var(--primary)]/20'
                  : isRejected
                  ? 'bg-red-500/[0.02] border-red-500/10 opacity-30 grayscale'
                  : 'bg-white/[0.015] border-white/5 hover:border-white/10 hover:bg-white/[0.025]'}
              `}
            >
              <div className="flex flex-col xl:flex-row justify-between items-center gap-10 relative z-10">
                <div className="flex items-center gap-8 flex-1">
                   <div className={`w-16 h-16 rounded-2xl flex items-center justify-center border transition-all duration-500 shadow-xl
                     ${isWinner ? 'bg-[var(--primary)] text-[#060a12] border-[var(--primary)] scale-110' : 'bg-black/40 text-gray-600 border-white/5 group-hover/card:text-white group-hover/card:border-white/20'}
                   `}>
                     {isWinner ? <Trophy size={28} /> : <Zap size={24} />}
                   </div>
                   <div>
                     <div className="flex flex-wrap items-center gap-4 mb-3">
                       <h3 className="text-xl font-black text-white uppercase tracking-tight group-hover/card:text-[var(--primary)] transition-colors">
                         {candidate.strategy} Strategy
                       </h3>
                       {isWinner && (
                         <span className="text-[9px] font-black bg-[var(--primary)]/20 text-[var(--primary)] px-3 py-1 rounded-lg border border-[var(--primary)]/20 shadow-[0_0_12px_rgba(102,252,241,0.2)]">OPERATIONAL CHAMPION</span>
                       )}
                     </div>
                     <div className="flex items-center gap-6 font-mono text-[9px] text-gray-700 tracking-[0.2em] uppercase font-black">
                        <span className="flex items-center gap-2"><ShieldCheck size={14} className={isWinner ? 'text-[var(--primary)]' : 'text-gray-800'} /> VERIFIED GENOME</span>
                        <span className="flex items-center gap-2 italic">ENCODING: {candidate.type}</span>
                     </div>
                   </div>
                </div>

                <div className="flex items-center gap-10">
                   <div className="flex flex-col items-end">
                      <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest mb-2">Resilience Factor</span>
                      <div className="text-3xl font-black tracking-tighter italic font-mono transition-colors group-hover/card:scale-110 duration-700">
                         <span className={isWinner ? 'text-[var(--primary)]' : 'text-white'}>
                            {(candidate.score * 100).toFixed(1)}
                         </span>
                         <span className="text-xs text-gray-700 ml-1.5">%</span>
                      </div>
                   </div>
                   <button className={`p-4 rounded-2xl transition-all ${isWinner ? 'bg-[var(--primary)]/10 text-[var(--primary)]' : 'bg-white/5 text-gray-700 hover:text-white'}`}>
                      <Binary size={20} />
                   </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const VerifierMatrix = ({ matrix }: { matrix: any }) => {
  if (!matrix || !matrix.verifiers || matrix.verifiers.length === 0) return (
    <div className="glass-panel p-32 rounded-[3.5rem] border-white/5 bg-white/[0.015] text-center flex flex-col items-center gap-8 shadow-2xl relative overflow-hidden group">
       <div className="absolute inset-0 bg-gradient-to-br from-violet-500/[0.02] to-transparent" />
       <div className="p-10 rounded-full bg-white/[0.02] border border-dashed border-white/10 relative z-10">
          <Activity size={64} className="text-gray-800 animate-pulse" />
       </div>
       <p className="text-xs font-black text-gray-700 font-mono uppercase tracking-[0.4em] relative z-10 italic max-w-sm leading-loose">
         Select tournament to <br/>synthesize matrix evidence layers.
       </p>
    </div>
  );

  return (
    <div className="glass-panel p-10 rounded-[3rem] border-white/[0.03] bg-gradient-to-br from-white/[0.01] to-transparent overflow-hidden shadow-2xl relative">
      <div className="absolute top-0 left-0 p-8 opacity-[0.02] pointer-events-none">
         <ShieldCheck size={150} />
      </div>

      <div className="flex items-center justify-between mb-12 relative z-10 px-2">
        <div className="flex items-center gap-5">
          <div className="p-3.5 bg-violet-500/10 rounded-2xl border border-violet-500/20 shadow-[0_0_24px_rgba(139,92,246,0.1)]">
            <ShieldCheck size={24} className="text-violet-400" />
          </div>
          <div>
            <h3 className="text-xl font-black text-white uppercase tracking-tight">Scientific Evidence Matrix</h3>
            <p className="text-[9px] font-black text-gray-500 uppercase tracking-[0.2em] mt-1">Multi-Layer Strategy Validation</p>
          </div>
        </div>
        <div className="flex items-center gap-6 bg-black/40 px-6 py-3 rounded-2xl border border-white/5 text-[10px] font-mono text-gray-600 font-black tracking-widest">
           <span className="text-violet-400">QUORUM: ACTIVE</span>
           <div className="w-px h-3 bg-white/10" />
           <span>LAYERS: {matrix.verifiers.length}</span>
        </div>
      </div>

      <div className="overflow-x-auto pr-4 relative z-10">
        <table className="w-full text-left border-separate border-spacing-y-4">
          <thead>
            <tr className="text-gray-700">
              <th className="py-2 px-8 text-[10px] font-black uppercase tracking-[0.25em]">Strategic Candidate</th>
              {matrix.verifiers.map((v: string) => (
                <th key={v} className="py-2 px-6 text-[10px] font-black uppercase tracking-[0.25em] text-center">{v}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.candidates.map((c: any, idx: number) => (
              <tr key={idx} className="group/row transition-all">
                <td className="py-6 px-8 bg-white/[0.015] border-l border-y border-white/5 rounded-l-[1.5rem] group-hover/row:bg-white/[0.03] transition-colors">
                  <div className="flex flex-col">
                    <span className="text-[13px] font-black text-white uppercase tracking-tight group-hover/row:text-violet-400 transition-colors">{c.name}</span>
                    <span className="text-[8px] font-mono font-black text-gray-700 mt-1 uppercase tracking-widest">ENCODED STRAND</span>
                  </div>
                </td>
                {c.results.map((res: number, i: number) => (
                  <td key={i} className={`py-6 px-6 bg-white/[0.015] border-y border-white/5 group-hover/row:bg-white/[0.03] transition-colors last:border-r last:rounded-r-[1.5rem] text-center`}>
                    <div className="flex flex-col items-center gap-3 relative group/cell">
                       <div className="w-24 h-2 bg-black/40 rounded-full overflow-hidden border border-white/[0.03] relative">
                          <div
                            className={`h-full rounded-full transition-all duration-1000 shadow-[0_0_12px_rgba(255,255,255,0.1)]
                              ${res > 0.9 ? 'bg-green-500 shadow-green-500/20' :
                                res > 0.75 ? 'bg-[var(--primary)] shadow-[var(--primary)]/20' :
                                res > 0.5 ? 'bg-amber-500 shadow-amber-500/20' :
                                'bg-red-500 shadow-red-500/20'}
                            `}
                            style={{ width: `${res * 100}%` }}
                          />
                       </div>
                       <span className="text-[10px] font-mono font-black text-gray-700 opacity-60 group-hover/cell:opacity-100 transition-opacity">{(res * 100).toFixed(0)}%</span>

                       {/* Floating Evidence Tooltip */}
                       <div className="absolute bottom-full mb-4 px-4 py-3 bg-black/95 border border-white/10 rounded-2xl text-[9px] font-mono text-white opacity-0 group-hover/cell:opacity-100 transition-all pointer-events-none scale-75 group-hover/cell:scale-100 z-50 shadow-2xl backdrop-blur-xl min-w-[150px]">
                          <div className="flex justify-between items-center mb-2 pb-2 border-b border-white/5">
                             <span className="text-gray-600 font-black">VALIDITY</span>
                             <span className="text-[var(--primary)]">{(res * 100).toFixed(2)}%</span>
                          </div>
                          <div className="text-gray-400 leading-relaxed uppercase tracking-tighter font-bold">
                             Evidence chain verified by layer core 0{i+1}.
                          </div>
                          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-black rotate-45 border-r border-b border-white/10" />
                       </div>
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const PRAgentGovernancePanel = ({ caseId, prUrl, onAction }: { caseId: string, prUrl?: string, onAction?: (action: string) => void }) => {
  const [showDiff, setShowDiff] = React.useState(false);
  const [diffContent, setDiffContent] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const fetchDiff = async () => {
    if (diffContent) {
      setShowDiff(!showDiff);
      return;
    }
    setLoading(true);
    try {
      const baseUrl = window.location.origin.replace(':3100', ':8000');
      const res = await fetch(`${baseUrl}/repair-lab/cases/${caseId}/patch`);
      const data = await res.json();
      setDiffContent(data.diff);
      setShowDiff(true);
    } catch (err) {
      console.error("Failed to fetch diff", err);
    } finally {
      setLoading(false);
    }
  };

  if (!prUrl) return (
    <div className="glass-panel p-10 rounded-[2.5rem] border-white/5 bg-white/[0.01] opacity-40">
      <div className="flex flex-col items-center gap-6 py-10">
        <GitPullRequest size={48} className="text-gray-700" />
        <p className="text-[10px] font-black text-gray-700 uppercase tracking-[0.3em]">Awaiting PR Generation</p>
      </div>
    </div>
  );

  const actions = [
    { id: 'describe', name: 'AI Describe', icon: <FileSearch size={18} />, color: 'var(--primary)' },
    { id: 'review', name: 'AI Review', icon: <ShieldCheck size={18} />, color: '#8b5cf6' },
    { id: 'improve', name: 'AI Improve', icon: <Zap size={18} />, color: '#f59e0b' },
    { id: 'full-review', name: 'Full Governance Cycle', icon: <GitPullRequest size={18} />, color: '#ec4899', highlight: true },
    { id: 'preview', name: 'Preview Patch', icon: <Binary size={18} />, color: '#3b82f6', onClick: fetchDiff },
    { id: 'apply', name: 'Approve & Apply', icon: <CheckCircle2 size={18} />, color: '#22c55e', highlight: true }
  ];

  return (
    <div className="glass-panel p-10 rounded-[2.5rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.02] to-transparent relative overflow-hidden group shadow-2xl">
      <div className="flex items-center justify-between mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-[var(--primary)]/10 rounded-xl border border-[var(--primary)]/20">
            <GitPullRequest size={20} className="text-[var(--primary)]" />
          </div>
          <div>
            <h3 className="text-lg font-black text-white uppercase tracking-tight">PR Governance Gate</h3>
            <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mt-1">Autonomous PR-Agent Integration</p>
          </div>
        </div>
        <div className="flex gap-2">
           <a href={prUrl} target="_blank" className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 transition-all text-[10px] font-black text-gray-400 uppercase tracking-widest">
              View PR <ExternalLink size={12} />
           </a>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {actions.map(action => (
          <button
            key={action.id}
            onClick={() => action.onClick ? action.onClick() : onAction?.(action.id)}
            className={`p-5 rounded-3xl border transition-all duration-500 flex flex-col items-center gap-4 group/btn relative overflow-hidden
              ${action.highlight ? 'bg-white/[0.03] border-white/10' : 'bg-transparent border-white/5'}
            `}
          >
            <div className={`p-3 rounded-2xl transition-all group-hover/btn:scale-110`} style={{ color: action.color, backgroundColor: `${action.color}10` }}>
              {action.icon}
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest text-center">{action.name}</span>
          </button>
        ))}
      </div>

      {showDiff && diffContent && (
        <div className="mt-8 p-6 bg-black/60 rounded-[2rem] border border-white/5 animate-in slide-in-from-top duration-500">
           <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Unified Diff Preview</span>
              <button onClick={() => setShowDiff(false)} className="text-[10px] font-black text-red-500 uppercase">Close</button>
           </div>
           <pre className="text-[10px] font-mono text-gray-400 overflow-x-auto whitespace-pre p-4 bg-black/40 rounded-xl leading-relaxed">
              {diffContent}
           </pre>
        </div>
      )}
    </div>
  );
};

export const UIRepairTimeline = ({ steps }: { steps: any[] }) => {
  return (
    <div className="glass-panel p-10 rounded-[2.5rem] border-white/5 bg-white/[0.015] shadow-2xl">
      <div className="flex items-center gap-4 mb-12">
        <div className="p-3 bg-white/5 rounded-xl border border-white/10">
          <Clock size={20} className="text-gray-400" />
        </div>
        <div>
          <h3 className="text-lg font-black text-white uppercase tracking-tight">Repair Life-Cycle</h3>
          <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mt-1">Traceability Feed</p>
        </div>
      </div>

      <div className="space-y-12 ml-4">
        {steps.map((step, idx) => (
          <div key={idx} className="relative pl-12 group/step">
            {idx !== steps.length - 1 && (
              <div className="absolute left-[11px] top-8 w-[2px] h-20 bg-gradient-to-b from-white/10 to-transparent group-hover/step:from-[var(--primary)]/40 transition-all duration-700" />
            )}
            <div className="absolute left-0 top-0 w-6 h-6 rounded-lg border flex items-center justify-center transition-all duration-500">
              {step.status === 'completed' ? <CheckCircle2 size={12} /> : idx + 1}
            </div>
            <div>
              <h4 className="text-xs font-black uppercase tracking-widest mb-2">
                {step.name}
              </h4>
              <p className="text-[10px] text-gray-600 font-medium leading-relaxed max-w-md">
                {step.description}
              </p>
              {step.artifact && (
                <div className="mt-4 flex items-center gap-3">
                   <div className="px-3 py-1.5 rounded-lg bg-black/40 border border-white/5 flex items-center gap-2">
                      <Binary size={10} className="text-gray-500" />
                      <span className="text-[8px] font-black text-gray-500 uppercase tracking-widest">Artifact: {step.artifact}</span>
                   </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const EvidenceGallery = ({ evidence }: { evidence: any[] }) => {
  return (
    <div className="glass-panel p-10 rounded-[2.5rem] border-white/5 bg-white/[0.015] shadow-2xl relative overflow-hidden">
       <div className="absolute top-0 right-0 p-8 opacity-[0.02] pointer-events-none">
          <Image size={150} />
       </div>

      <div className="flex items-center justify-between mb-10 relative z-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-violet-500/10 rounded-xl border border-violet-500/20">
            <Image size={20} className="text-violet-400" />
          </div>
          <div>
            <h3 className="text-lg font-black text-white uppercase tracking-tight">Visual Evidence</h3>
            <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mt-1">Playwright Trace Frames</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 relative z-10">
        {evidence.length === 0 && (
          <div className="col-span-2 py-20 text-center flex flex-col items-center gap-4 opacity-30">
            <Search size={32} className="text-gray-700" />
            <p className="text-[9px] font-black text-gray-700 uppercase tracking-[0.2em]">No Evidence Found</p>
          </div>
        )}
        {evidence.map((item, idx) => (
          <div key={idx} className="group/img relative rounded-2xl overflow-hidden border border-white/5 aspect-video hover:border-[var(--primary)]/40 transition-all cursor-zoom-in">
             <div className="absolute inset-0 bg-black/40 group-hover/img:bg-transparent transition-all z-10" />
             <img src={item.url} alt="evidence" className="w-full h-full object-cover transition-transform duration-1000 group-hover/img:scale-105" />
             <div className="absolute bottom-4 left-4 z-20 px-3 py-1.5 bg-black/80 backdrop-blur-xl border border-white/10 rounded-xl opacity-0 group-hover/img:opacity-100 transition-all translate-y-4 group-hover/img:translate-y-0">
                <span className="text-[8px] font-black text-white uppercase tracking-[0.2em]">{item.timestamp}</span>
             </div>
          </div>
        ))}
      </div>
    </div>
  );
};
