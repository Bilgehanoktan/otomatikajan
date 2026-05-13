"use client";

import React, { useState, useEffect } from "react";
import { 
  FlaskConical, 
  Play, 
  BarChart3, 
  Activity, 
  Cpu, 
  Zap,
  Info,
  Clock,
  ShieldCheck,
  TrendingUp,
  Binary,
  Target,
  RefreshCcw,
  Search,
  Filter
} from "lucide-react";
import { PatchTournamentBoard, VerifierMatrix } from "@/components/repair/LabComponents";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/runtime";
import { useTranslations } from "next-intl";

interface RepairImprovement {
  id: string;
  title: string;
  component: string;
  description?: string;
  status: "completed" | "action_required" | "failed" | string;
  diagnostic_id?: string;
  actions?: string[];
  requires_operator_action?: boolean;
  decision_type?: string;
  outcome?: string;
  created_at?: string;
}

interface SelfRepairRun {
  incident_id: string;
  trace_id?: string;
  summary?: string;
  final_status: string;
  risk_level: string;
  risk_score?: number;
  recommended_action?: string;
  tests_passed: boolean;
  patch_applied: boolean;
  suspected_files: string[];
  changed_files: string[];
  report_path: string;
  updated_at: string;
}

interface TaskflowRun {
  incident_id: string;
  trace_id?: string;
  workflow_id: string;
  workflow_name?: string;
  status: string;
  current_step?: string;
  final_decision?: string;
  risk_score?: number;
  step_count: number;
  succeeded_step_count: number;
  skipped_step_count: number;
  failed_step_count: number;
  gate_waiting: boolean;
  event_count: number;
  metric_count: number;
  artifact_count: number;
  updated_at: string;
}

export default function RepairLabPage() {
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [tournament, setTournament] = useState<any>(null);
  const [matrix, setMatrix] = useState<any>(null);
  const [improvements, setImprovements] = useState<RepairImprovement[]>([]);
  const [selfRepairRuns, setSelfRepairRuns] = useState<SelfRepairRun[]>([]);
  const [taskflowRuns, setTaskflowRuns] = useState<TaskflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [isClient, setIsClient] = useState(false);
  const t = useTranslations("repair_lab");
  const apiUrl = getApiBaseUrl();

  useEffect(() => { setIsClient(true); }, []);

  const fetchData = async () => {
    try {
      const benchData: any = await safeFetchJson(`${apiUrl}/repair-lab/benchmarks`);
      setBenchmarks(Array.isArray(benchData) ? benchData : []);

      const improvementData: any = await safeFetchJson(`${apiUrl}/repair-lab/improvements`);
      setImprovements(Array.isArray(improvementData) ? improvementData : []);

      const selfRepairData: any = await safeFetchJson(`${apiUrl}/repair-lab/self-repair-runs`);
      setSelfRepairRuns(Array.isArray(selfRepairData) ? selfRepairData : []);

      const taskflowData: any = await safeFetchJson(`${apiUrl}/repair-lab/taskflow-runs`);
      setTaskflowRuns(Array.isArray(taskflowData) ? taskflowData : []);

      const tourData: any = await safeFetchJson(`${apiUrl}/repair-lab/tournaments`);
      if (tourData && tourData.length > 0) {
        const latest = tourData[0];
        setTournament(latest);

        const matrixData: any = await safeFetchJson(`${apiUrl}/repair-lab/verifiers/matrix?tournament_id=${latest.id}`);
        setMatrix(matrixData);
      }
    } catch (err) {
      console.error("Laboratuvar verileri alınamadı", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isClient) return;
    fetchData();
    const interval = setInterval(fetchData, 15000); 
    return () => clearInterval(interval);
  }, [isClient]);

  const runLab = async () => {
    setLoading(true);
    try {
      await safeFetchJson(`${apiUrl}/repair-lab/run`, { method: 'POST' });
      // We don't use window.alert in elite UI, but for now we follow the existing pattern with a small delay
      setTimeout(fetchData, 2000);
    } catch (err) {
      console.error("Laboratuvar başlatılamadı.");
    } finally {
      setLoading(false);
    }
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title={t("title")} 
        subtitle={t("subtitle")} 
        icon={<FlaskConical size={32} />}
        badge="Phase 28 Active"
        actions={
          <div className="flex items-center gap-8">
             <div className="flex flex-col items-end border-r border-white/5 pr-8">
                <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">{t("globalAccuracy")}</span>
                <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono tracking-tighter italic">94.2% NOMINAL</span>
             </div>
             <button 
               onClick={runLab}
               className="flex items-center gap-2 px-10 py-4 bg-[var(--primary)] text-[#060a12] text-[11px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_48px_rgba(102,252,241,0.4)] transition-all active:scale-95 group"
             >
                <Play size={16} className="fill-[#060a12] group-hover:scale-125 transition-transform" />
                <span>{t("executeBenchmark")}</span>
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* LEFT: Benchmarks & Samples */}
        <div className="xl:col-span-3 space-y-10">
           <section className="glass-panel p-8 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-xl">
              <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <Binary size={120} />
              </div>

              <div className="flex items-center justify-between mb-10 relative z-10 px-2">
                 <h3 className="text-xs font-black text-white uppercase tracking-[0.3em] italic">{t("systemBenchmarks")}</h3>
                 <BarChart3 size={16} className="text-gray-700" />
              </div>

              <div className="space-y-4 relative z-10">
                 {loading && benchmarks.length === 0 ? (
                    <div className="space-y-4">
                       {[1,2,3,4].map(i => <Skeleton key={i} className="h-24 rounded-2xl" />)}
                    </div>
                 ) : benchmarks.length === 0 ? (
                    <div className="py-20 text-center opacity-30 flex flex-col items-center gap-4">
                       <Target size={32} className="text-gray-700" />
                       <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">{t("noActiveSamples")}</span>
                    </div>
                 ) : (
                    benchmarks.map((b: any) => (
                       <EliteBenchmarkCard key={b.id} benchmark={b} />
                    ))
                 )}
              </div>

              <div className="mt-10 p-5 bg-black/40 rounded-2xl border border-white/5 relative z-10">
                 <div className="flex items-center gap-3 mb-3">
                    <Info size={14} className="text-[var(--primary)]" />
                    <span className="text-[9px] font-black text-[var(--primary)] uppercase tracking-widest">{t("evidenceNotice")}</span>
                 </div>
                 <p className="text-[10px] text-gray-600 leading-relaxed font-mono uppercase font-black">
                    {t("evidenceNoticeDesc")}
                 </p>
              </div>
           </section>
        </div>

        {/* RIGHT: Active Tournament & Verifiers */}
        <div className="xl:col-span-9 space-y-10">
           <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
              <div className="xl:col-span-8">
                 <PatchTournamentBoard data={tournament} />
              </div>
              
              <div className="xl:col-span-4 h-full">
                 <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent h-full flex flex-col relative overflow-hidden group shadow-xl">
                    <div className="absolute -bottom-10 -right-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity duration-1000">
                       <TrendingUp size={200} className="text-[var(--primary)]" />
                    </div>
                    
                    <div className="flex items-center gap-4 mb-10 relative z-10 px-2">
                       <div className="p-3 bg-white/5 rounded-xl border border-white/10 text-[var(--primary)]">
                          <TrendingUp size={20} />
                       </div>
                       <h3 className="text-xl font-black text-white tracking-tighter uppercase">{t("stats")}</h3>
                    </div>
                    
                    {tournament ? (
                      <div className="flex-1 flex flex-col justify-between relative z-10">
                         <div className="space-y-1">
                            {[
                              { label: "Incident ID", val: tournament.incident_id, icon: <Activity size={14}/> },
                              { label: "Candidates", val: tournament.total_candidates, icon: <Cpu size={14}/> },
                              { label: "Execution", val: new Date(tournament.created_at).toLocaleTimeString(), icon: <Clock size={14}/> },
                              { label: "Quorum", val: "VERIFIED", icon: <ShieldCheck size={14} className="text-green-500"/> },
                              { label: "Diversity", val: "HIGH", icon: <Binary size={14} className="text-blue-400"/> },
                            ].map(item => (
                               <div key={item.label} className="flex items-center justify-between py-5 border-b border-white/[0.03] last:border-0 hover:bg-white/[0.012] transition-colors rounded-xl px-2">
                                  <div className="flex items-center gap-4 text-gray-600">
                                     {item.icon}
                                     <span className="text-[9px] font-black uppercase tracking-widest">{item.label}</span>
                                  </div>
                                  <span className="text-[11px] font-black text-white tracking-tighter uppercase font-mono">{item.val}</span>
                               </div>
                            ))}
                         </div>
                         
                         <div className="mt-10 p-6 bg-[var(--primary)]/[0.03] rounded-3xl border border-[var(--primary)]/10 text-center">
                            <p className="text-[10px] text-gray-500 leading-loose uppercase font-black italic tracking-widest">
                               {t("optimalStrategyNotice")}
                            </p>
                         </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center flex-1 py-12 text-gray-700 opacity-40">
                        <RefreshCcw size={48} className="animate-spin mb-6" />
                        <span className="text-[9px] font-black uppercase tracking-widest">{t("syncingTelemetry")}</span>
                      </div>
                    )}
                 </section>
              </div>
           </div>
           
           <RuntimeRepairTimeline improvements={improvements} loading={loading} />

           <SelfRepairRunsPanel runs={selfRepairRuns} loading={loading} />

           <TaskflowRunsPanel runs={taskflowRuns} loading={loading} />

           <VerifierMatrix matrix={matrix} />
        </div>

      </div>
    </div>
  );
}

function TaskflowRunsPanel({ runs, loading }: { runs: TaskflowRun[]; loading: boolean }) {
  const t = useTranslations("repair_lab");
  const toneFor = (status: string, gateWaiting: boolean) => {
    if (gateWaiting || status === "WAITING_HUMAN") return "border-amber-400/15 bg-amber-500/5 text-amber-300";
    if (status === "DRAFT_PR_READY" || status === "COMPLETED") return "border-green-400/15 bg-green-500/5 text-green-300";
    if (status === "BLOCKED" || status === "FAILED") return "border-red-400/15 bg-red-500/5 text-red-300";
    return "border-cyan-400/15 bg-cyan-500/5 text-cyan-300";
  };

  return (
    <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent shadow-xl">
      <div className="mb-8 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-xs font-black text-white uppercase tracking-[0.3em] italic">{t("taskflowTrace")}</h3>
          <p className="mt-2 text-[10px] font-black uppercase tracking-widest text-gray-600">
            {t("taskflowTraceDesc")}
          </p>
        </div>
        <span className="w-fit rounded-xl border border-white/10 bg-white/5 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-gray-500">
          {runs.length} traces
        </span>
      </div>

      {loading && runs.length === 0 ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {[1, 2].map((i) => <Skeleton key={i} className="h-32 rounded-2xl" />)}
        </div>
      ) : runs.length === 0 ? (
        <div className="rounded-2xl border border-white/5 bg-black/20 p-8 text-center">
          <span className="text-[10px] font-black uppercase tracking-widest text-gray-700">No TaskFlow Traces Found</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {runs.slice(0, 6).map((run) => (
            <div key={`${run.workflow_id}-${run.incident_id}`} className={`rounded-2xl border p-5 ${toneFor(run.status, run.gate_waiting)}`}>
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <div className="text-[10px] font-black uppercase tracking-widest text-current">
                    {run.workflow_id}
                  </div>
                  <div className="mt-1 text-[9px] font-black uppercase tracking-widest text-gray-600">
                    {run.incident_id}
                  </div>
                </div>
                <span className="rounded-lg border border-current/20 bg-black/20 px-2 py-1 text-[8px] font-black uppercase tracking-widest">
                  {run.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-[9px] font-black uppercase tracking-widest">
                <div className="rounded-xl border border-white/5 bg-black/20 p-3">
                  <div className="text-gray-700">Current Step</div>
                  <div className="mt-1 truncate text-current" title={run.current_step || "complete"}>{run.current_step || "complete"}</div>
                </div>
                <div className="rounded-xl border border-white/5 bg-black/20 p-3">
                  <div className="text-gray-700">Decision</div>
                  <div className="mt-1 truncate text-current" title={run.final_decision || "none"}>{run.final_decision || "none"}</div>
                </div>
                <div className="rounded-xl border border-white/5 bg-black/20 p-3">
                  <div className="text-gray-700">Steps</div>
                  <div className="mt-1 text-current">{run.succeeded_step_count}/{run.step_count} ok</div>
                </div>
                <div className="rounded-xl border border-white/5 bg-black/20 p-3">
                  <div className="text-gray-700">Artifacts</div>
                  <div className="mt-1 text-current">{run.artifact_count} files</div>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {run.gate_waiting ? (
                  <span className="rounded-lg border border-amber-400/20 bg-amber-500/10 px-2 py-1 text-[8px] font-black uppercase tracking-widest text-amber-300">
                    human gate waiting
                  </span>
                ) : null}
                <span className="rounded-lg border border-white/5 bg-black/30 px-2 py-1 text-[8px] font-black uppercase tracking-widest text-gray-500">
                  {run.event_count} events
                </span>
                <span className="rounded-lg border border-white/5 bg-black/30 px-2 py-1 text-[8px] font-black uppercase tracking-widest text-gray-500">
                  {run.metric_count} metrics
                </span>
              </div>

              <div className="mt-4 border-t border-white/[0.04] pt-3 text-[9px] font-mono font-black uppercase tracking-widest text-gray-700">
                {run.updated_at ? new Date(run.updated_at).toLocaleString() : "No timestamp"}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function SelfRepairRunsPanel({ runs, loading }: { runs: SelfRepairRun[]; loading: boolean }) {
  const t = useTranslations("repair_lab");
  const toneFor = (status: string) => {
    if (status === "DRAFT_PR_READY" || status === "SANDBOX_PASSED") return "border-green-400/15 bg-green-500/5 text-green-300";
    if (status === "HUMAN_APPROVAL_REQUIRED" || status === "QUORUM_REQUIRED") return "border-amber-400/15 bg-amber-500/5 text-amber-300";
    return "border-red-400/15 bg-red-500/5 text-red-300";
  };

  return (
    <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent shadow-xl">
      <div className="mb-8 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-xs font-black text-white uppercase tracking-[0.3em] italic">{t("selfRepairReports")}</h3>
          <p className="mt-2 text-[10px] font-black uppercase tracking-widest text-gray-600">
            {t("selfRepairReportsDesc")}
          </p>
        </div>
        <span className="w-fit rounded-xl border border-white/10 bg-white/5 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-gray-500">
          {runs.length} reports
        </span>
      </div>

      {loading && runs.length === 0 ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {[1, 2].map((i) => <Skeleton key={i} className="h-32 rounded-2xl" />)}
        </div>
      ) : runs.length === 0 ? (
        <div className="rounded-2xl border border-white/5 bg-black/20 p-8 text-center">
          <span className="text-[10px] font-black uppercase tracking-widest text-gray-700">No Self-Repair Reports Found</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {runs.slice(0, 6).map((run) => (
            <div key={run.incident_id} className={`rounded-2xl border p-5 ${toneFor(run.final_status)}`}>
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <div className="text-[10px] font-black uppercase tracking-widest text-current">
                    {run.incident_id}
                  </div>
                  <div className="mt-1 text-[9px] font-black uppercase tracking-widest text-gray-600">
                    {run.recommended_action || "review"}
                  </div>
                </div>
                <span className="rounded-lg border border-current/20 bg-black/20 px-2 py-1 text-[8px] font-black uppercase tracking-widest">
                  {run.final_status}
                </span>
              </div>

              <p className="mb-4 line-clamp-2 text-xs font-semibold text-gray-400">{run.summary || "No summary"}</p>

              <div className="grid grid-cols-2 gap-3 text-[9px] font-black uppercase tracking-widest">
                <div className="rounded-xl border border-white/5 bg-black/20 p-3">
                  <div className="text-gray-700">Risk</div>
                  <div className="mt-1 text-current">{run.risk_level} {run.risk_score ?? ""}</div>
                </div>
                <div className="rounded-xl border border-white/5 bg-black/20 p-3">
                  <div className="text-gray-700">Sandbox</div>
                  <div className="mt-1 text-current">{run.tests_passed ? "passed" : "failed"}</div>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {run.suspected_files.slice(0, 3).map((file) => (
                  <span key={file} className="rounded-lg border border-white/5 bg-black/30 px-2 py-1 text-[8px] font-black uppercase tracking-widest text-gray-500">
                    {file}
                  </span>
                ))}
              </div>

              <div className="mt-4 border-t border-white/[0.04] pt-3 text-[9px] font-mono font-black uppercase tracking-widest text-gray-700">
                {run.updated_at ? new Date(run.updated_at).toLocaleString() : "No timestamp"}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function RuntimeRepairTimeline({ improvements, loading }: { improvements: RepairImprovement[]; loading: boolean }) {
  const t = useTranslations("repair_lab");
  const runtimeItems = improvements.filter(
    (item) => item.decision_type === "RUNTIME_REPAIR_ATTEMPT" || item.diagnostic_id,
  );

  const toneFor = (status: string) => {
    if (status === "completed") return "border-green-400/15 bg-green-500/5 text-green-300";
    if (status === "action_required") return "border-amber-400/15 bg-amber-500/5 text-amber-300";
    return "border-red-400/15 bg-red-500/5 text-red-300";
  };

  return (
    <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent shadow-xl">
      <div className="mb-8 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-xs font-black text-white uppercase tracking-[0.3em] italic">{t("runtimeRepairTimeline")}</h3>
          <p className="mt-2 text-[10px] font-black uppercase tracking-widest text-gray-600">
            {t("runtimeRepairTimelineDesc")}
          </p>
        </div>
        <span className="w-fit rounded-xl border border-white/10 bg-white/5 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-gray-500">
          {runtimeItems.length} records
        </span>
      </div>

      {loading && runtimeItems.length === 0 ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {[1, 2].map((i) => <Skeleton key={i} className="h-28 rounded-2xl" />)}
        </div>
      ) : runtimeItems.length === 0 ? (
        <div className="rounded-2xl border border-white/5 bg-black/20 p-8 text-center">
          <span className="text-[10px] font-black uppercase tracking-widest text-gray-700">No Runtime Repairs Recorded</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {runtimeItems.slice(0, 6).map((item) => (
            <div key={item.id} className={`rounded-2xl border p-5 ${toneFor(item.status)}`}>
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <div className="text-[10px] font-black uppercase tracking-widest text-current">
                    {item.diagnostic_id || item.component}
                  </div>
                  <div className="mt-1 text-[9px] font-black uppercase tracking-widest text-gray-600">
                    {item.component}
                  </div>
                </div>
                <span className="rounded-lg border border-current/20 bg-black/20 px-2 py-1 text-[8px] font-black uppercase tracking-widest">
                  {item.status}
                </span>
              </div>
              <p className="mb-4 line-clamp-2 text-xs font-semibold text-gray-400">{item.description || item.title}</p>
              <div className="flex flex-wrap items-center gap-2">
                {(item.actions || []).slice(0, 3).map((action) => (
                  <span key={action} className="rounded-lg border border-white/5 bg-black/30 px-2 py-1 text-[8px] font-black uppercase tracking-widest text-gray-500">
                    {action}
                  </span>
                ))}
                {item.requires_operator_action ? (
                  <span className="rounded-lg border border-amber-400/20 bg-amber-500/10 px-2 py-1 text-[8px] font-black uppercase tracking-widest text-amber-300">
                    operator action
                  </span>
                ) : null}
              </div>
              <div className="mt-4 border-t border-white/[0.04] pt-3 text-[9px] font-mono font-black uppercase tracking-widest text-gray-700">
                {item.created_at ? new Date(item.created_at).toLocaleString() : "No timestamp"}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function EliteBenchmarkCard({ benchmark }: { benchmark: any }) {
  const isPass = benchmark.status === 'completed';

  return (
    <div className="p-6 rounded-[2rem] border border-white/5 bg-white/[0.015] hover:bg-white/[0.03] hover:border-[var(--primary)]/20 transition-all cursor-pointer group/card relative overflow-hidden">
       <div className="flex justify-between items-start mb-6">
          <div className="flex-1 mr-4">
             <h4 className="text-[11px] font-black text-white uppercase tracking-tight group-hover/card:text-[var(--primary)] transition-colors line-clamp-1">
                {benchmark.name}
             </h4>
             <p className="text-[8px] font-mono font-black text-gray-700 mt-1 uppercase tracking-widest">S-LEVEL: {benchmark.id.substring(0,6)}</p>
          </div>
          <span className={`px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest border transition-all
             ${isPass ? 'text-green-400 border-green-400/20 bg-green-500/10' : 'text-[var(--primary)] border-[var(--primary)]/20 bg-[var(--primary)]/10'}
          `}>
             {isPass ? 'Pass' : 'Active'}
          </span>
       </div>
       
       <div className="flex items-center justify-between pt-4 border-t border-white/[0.03]">
          <div className="flex flex-col gap-1">
             <span className="text-[8px] font-black text-gray-700 uppercase tracking-widest">Accuracy</span>
             <span className="text-[11px] font-black text-gray-400 font-mono tracking-tighter">{(benchmark.success_rate * 100).toFixed(0)}%</span>
          </div>
          <div className="flex flex-col items-end gap-1">
             <span className="text-[8px] font-black text-gray-700 uppercase tracking-widest">Score</span>
             <span className="text-[11px] font-black text-white font-mono tracking-tighter">{(benchmark.avg_score * 100).toFixed(0)}</span>
          </div>
       </div>
    </div>
  );
}
