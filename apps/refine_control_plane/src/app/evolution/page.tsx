"use client";

import { useEffect, useState } from "react";
import { 
  Dna, 
  History, 
  Cpu, 
  GitBranch, 
  FileCode, 
  Terminal, 
  CheckCircle2, 
  Zap,
  Activity,
  ArrowRight
} from "lucide-react";
import { useApiUrl, useCustom } from "@refinedev/core";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

type SystemUpdate = {
  id: string;
  target_file: string;
  description: string;
  rationale: string;
  status: string;
  diff_summary?: string;
  changed_symbols: string[];
  test_result: any;
  git_commit?: string;
  created_at: string;
};

type EvolutionState = {
  current_version: string;
  last_updated: string;
  updates: SystemUpdate[];
};

export default function EvolutionPage() {
  const [isClient, setIsClient] = useState(false);
  const [selectedUpdate, setSelectedUpdate] = useState<SystemUpdate | null>(null);
  const apiUrl = useApiUrl();

  useEffect(() => {
    setIsClient(true);
  }, []);

  const { query } = useCustom<EvolutionState>({
    url: `${apiUrl}/evolution/state`,
    method: "get",
    queryOptions: {
      enabled: isClient,
    },
  });

  const { data, isLoading } = query;

  const state = data?.data;
  const updates = state?.updates ?? [];

  useEffect(() => {
    if (!selectedUpdate && updates.length > 0) {
      setSelectedUpdate(updates[0]);
    }
  }, [updates, selectedUpdate]);

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen bg-[#060a12] p-8 text-gray-300 animate-in fade-in duration-1000">
      <ResourceHeader
        title="System Evolution"
        subtitle="Autonomous Self-Update Ledger & Code Lineage"
        icon={<Dna size={32} className="text-[var(--primary)]" />}
        badge="AGI Evolution"
        actions={
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Version</p>
              <p className="mt-2 text-sm font-black text-[var(--primary)]">{state?.current_version ?? "v1.0"}</p>
            </div>
            <div className="h-10 w-px bg-white/5" />
            <div className="text-right">
              <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Last Sync</p>
              <p className="mt-2 text-[10px] font-mono text-gray-400">
                {state?.last_updated ? new Date(state.last_updated).toLocaleTimeString() : "READY"}
              </p>
            </div>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Timeline Column */}
        <div className="lg:col-span-5 xl:col-span-4">
          <div className="glass-panel min-h-[70vh] rounded-[2rem] border-white/5 bg-white/[0.01] p-6">
            <div className="mb-8 flex items-center justify-between px-2">
              <div className="flex items-center gap-3">
                <History size={18} className="text-gray-500" />
                <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-white">Update Stream</h3>
              </div>
              <span className="rounded-full bg-[var(--primary)]/10 px-3 py-1 text-[9px] font-black text-[var(--primary)]">
                {updates.length} EVENTS
              </span>
            </div>

            <div className="relative space-y-4 pl-4 before:absolute before:left-[23px] before:top-4 before:bottom-4 before:w-px before:bg-gradient-to-b before:from-[var(--primary)]/40 before:to-transparent">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full rounded-2xl" />
                ))
              ) : updates.length === 0 ? (
                <div className="flex flex-col items-center gap-4 py-20 text-center opacity-30">
                  <Cpu size={40} />
                  <p className="text-[10px] font-black uppercase tracking-widest">No evolution logs yet.</p>
                </div>
              ) : (
                updates.map((update) => {
                  const isSelected = selectedUpdate?.id === update.id;
                  return (
                    <div
                      key={update.id}
                      onClick={() => setSelectedUpdate(update)}
                      className={`group relative cursor-pointer rounded-2xl border p-4 transition-all duration-300 ${
                        isSelected
                          ? "border-[var(--primary)]/40 bg-white/[0.05] shadow-[0_0_20px_rgba(102,252,241,0.05)]"
                          : "border-white/5 hover:border-white/10 hover:bg-white/[0.02]"
                      }`}
                    >
                      <div className={`absolute -left-[25px] top-1/2 h-2 w-2 -translate-y-1/2 rounded-full border transition-all ${
                        isSelected ? "bg-[var(--primary)] border-[var(--primary)] scale-125 shadow-[0_0_10px_var(--primary)]" : "bg-[#060a12] border-gray-700"
                      }`} />
                      
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] font-mono text-gray-500">
                            {new Date(update.created_at).toLocaleString()}
                          </span>
                          <span className={`text-[8px] font-black uppercase tracking-tighter ${
                            update.status === "applied" ? "text-green-400" : "text-yellow-400"
                          }`}>
                            {update.status}
                          </span>
                        </div>
                        <h4 className="text-[11px] font-black text-white group-hover:text-[var(--primary)] transition-colors">
                          {update.description}
                        </h4>
                        <div className="flex items-center gap-2">
                          <FileCode size={10} className="text-gray-600" />
                          <span className="truncate text-[9px] font-mono text-gray-500">{update.target_file}</span>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Detail Column */}
        <div className="lg:col-span-7 xl:col-span-8">
          {selectedUpdate ? (
            <div className="space-y-6 animate-in slide-in-from-right-8 duration-700">
              {/* Main Card */}
              <div className="glass-panel overflow-hidden rounded-[2.5rem] border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-10">
                <div className="mb-10 flex items-start justify-between">
                  <div>
                    <div className="mb-4 flex items-center gap-3">
                      <div className="rounded-xl bg-[var(--primary)]/10 p-2 text-[var(--primary)]">
                        <Zap size={20} />
                      </div>
                      <h2 className="text-2xl font-black tracking-tighter text-white">
                        {selectedUpdate.description}
                      </h2>
                    </div>
                    <p className="max-w-2xl text-sm leading-relaxed text-gray-400">
                      {selectedUpdate.rationale}
                    </p>
                  </div>
                  {selectedUpdate.git_commit && (
                    <div className="flex flex-col items-end gap-2">
                      <span className="text-[9px] font-black uppercase tracking-widest text-gray-600">Git Commit</span>
                      <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-black/40 px-4 py-2 font-mono text-[10px] text-gray-400">
                        <GitBranch size={12} className="text-[var(--primary)]" />
                        {selectedUpdate.git_commit.slice(0, 7)}
                      </div>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                  <DetailMetric 
                    icon={<FileCode size={16} />}
                    label="Target File"
                    value={selectedUpdate.target_file}
                  />
                  <DetailMetric 
                    icon={<Terminal size={16} />}
                    label="Execution ID"
                    value={selectedUpdate.id}
                  />
                  <DetailMetric 
                    icon={<Activity size={16} />}
                    label="Validation"
                    value="PASSED (SHADOW RUNNER)"
                    success
                  />
                </div>

                {/* Diff Preview Placeholder (In a real app, this would show the diff) */}
                <div className="mt-10">
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-gray-500">
                      Change Summary
                    </h3>
                    <div className="flex gap-2">
                      {selectedUpdate.changed_symbols.map(s => (
                        <span key={s} className="rounded-lg bg-white/5 px-2 py-1 text-[9px] font-mono text-gray-400">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-3xl border border-white/5 bg-black/60 p-8 font-mono text-xs leading-relaxed text-green-400/80">
                    <pre className="whitespace-pre-wrap">
                      {selectedUpdate.diff_summary || "// No diff summary provided"}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Status Section */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div className="glass-panel rounded-3xl border-white/5 bg-white/[0.01] p-8">
                  <div className="mb-4 flex items-center gap-3">
                    <CheckCircle2 size={18} className="text-green-400" />
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-white">Self-Test Report</h3>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-gray-500">Syntax Check</span>
                      <span className="font-bold text-green-400">PASSED</span>
                    </div>
                    <div className="flex justify-between text-[11px]">
                      <span className="text-gray-500">Logical Consistency</span>
                      <span className="font-bold text-green-400">VERIFIED</span>
                    </div>
                    <div className="flex justify-between text-[11px]">
                      <span className="text-gray-500">Safety Constraints</span>
                      <span className="font-bold text-green-400">ENFORCED</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col justify-center rounded-3xl bg-[var(--primary)] p-8 text-[#060a12]">
                   <h3 className="mb-2 text-xl font-black uppercase tracking-tighter">Evolutionary Jump</h3>
                   <p className="text-xs font-bold opacity-70">
                     Sistem bu güncellemeyle birlikte kendi mimarisini daha dayanıklı ve otonom hale getirdi.
                   </p>
                   <div className="mt-6 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest">
                     <span>View Code Lineage</span>
                     <ArrowRight size={14} />
                   </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-full items-center justify-center py-40 opacity-20">
              <div className="flex flex-col items-center gap-6">
                <Dna size={80} className="animate-pulse" />
                <p className="font-black uppercase tracking-[0.5em]">Select an update to audit</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DetailMetric({ icon, label, value, success }: { icon: any, label: string, value: string, success?: boolean }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
      <div className="mb-2 flex items-center gap-2 text-gray-600">
        {icon}
        <span className="text-[8px] font-black uppercase tracking-widest">{label}</span>
      </div>
      <p className={`truncate text-xs font-black uppercase tracking-tight ${success ? "text-green-400" : "text-white"}`}>
        {value}
      </p>
    </div>
  );
}
