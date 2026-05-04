"use client";

import React from "react";
import { useNavigation } from "@refinedev/core";
import { useTranslations, useFormatter } from "next-intl";
import {
  Activity,
  ChevronRight,
  Filter,
  Fingerprint,
  Layout,
  Network,
  Plus,
  RotateCcw,
  Search,
  ShieldCheck,
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/runtime";

interface WorkflowListItem {
  id: string;
  title: string;
  workflow_type: string;
  status: string;
  progress_pct: number;
  total_steps: number;
  completed_steps: number;
  failed_steps: number;
}

interface WorkflowSummary {
  total: number;
  running: number;
  pending_approval: number;
  __sqv_meta?: unknown;
}

export default function WorkflowList() {
  const t = useTranslations("workflows");
  const tStatus = useTranslations("status");
  const { show, create } = useNavigation();
  const [workflows, setWorkflows] = React.useState<WorkflowListItem[]>([]);
  const [summary, setSummary] = React.useState<WorkflowSummary>({
    total: 0,
    running: 0,
    pending_approval: 0,
  });
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const apiBase = React.useMemo(() => getApiBaseUrl(), []);

  const load = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [workflowResp, summaryResp] = await Promise.all([
        safeFetchJson<WorkflowListItem[] | { data?: WorkflowListItem[] }>(
          `${apiBase}/workflows?_end=10&_order=desc&_sort=started_at&_start=0`,
        ),
        safeFetchJson<WorkflowSummary>(`${apiBase}/workflows/stats/summary`),
      ]);

      const workflowItems = Array.isArray(workflowResp)
        ? workflowResp
        : Array.isArray(workflowResp?.data)
          ? workflowResp.data
          : [];

      setWorkflows(workflowItems);
      setSummary({
        total: summaryResp?.total ?? workflowItems.length,
        running:
          summaryResp?.running ??
          workflowItems.filter((w) => w.status?.toLowerCase() === "running").length,
        pending_approval:
          summaryResp?.pending_approval ??
          workflowItems.filter((w) => w.status?.toLowerCase() === "pending_approval").length,
        __sqv_meta: summaryResp?.__sqv_meta,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bilinmeyen hata");
    } finally {
      setIsLoading(false);
    }
  }, [apiBase]);

  React.useEffect(() => {
    void load();
  }, [load]);

  const activeJobs = summary.running;
  const staleMeta = summary.__sqv_meta;

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#060a12] p-8 text-gray-300 animate-in fade-in duration-1000">
      <ResourceHeader
        title={t("listTitle")}
        subtitle={t("listSubtitle")}
        icon={<Activity size={32} />}
        badge="Engine Core v13"
        staleMeta={staleMeta as never}
        actions={
          <div className="flex items-center gap-8">
            <div className="flex flex-col items-end border-r border-white/5 pr-8">
              <span className="text-[9px] font-black uppercase leading-none tracking-widest text-gray-500">
                {t("activeCycles")}
              </span>
              <span className="mt-2 font-mono text-sm font-black italic tracking-tighter text-[var(--primary)]">
                {activeJobs} {tStatus("running").toUpperCase()}
              </span>
            </div>
            <div className="flex flex-col items-end border-r border-[#66fcf1]/20 pr-8">
              <span className="text-[9px] font-black uppercase leading-none tracking-widest text-gray-500">
                {t("pendingApproval")}
              </span>
              <span className="mt-2 text-sm font-black text-white">{summary.pending_approval}</span>
            </div>
            <button
              onClick={() => create("workflows")}
              className="flex items-center gap-2 rounded-2xl border-none bg-gradient-to-r from-[var(--primary)] to-blue-500 p-4 font-black italic tracking-widest text-[#060a12] transition-all hover:scale-105 active:scale-95"
            >
              <Plus size={18} />
              <span className="hidden text-[10px] uppercase xl:inline">{t("create")}</span>
            </button>
            <button
              onClick={() => void load()}
              className="rounded-2xl border border-white/5 bg-white/5 p-4 text-gray-500 transition-all hover:bg-white/10 hover:text-white active:scale-90"
            >
              <RotateCcw size={18} />
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-10 xl:grid-cols-12">
        <div className="xl:col-span-12">
          <section className="glass-panel group relative overflow-hidden rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent p-10 shadow-2xl">
            <div className="pointer-events-none absolute right-0 top-0 p-10 opacity-[0.02] transition-opacity group-hover:opacity-[0.05]">
              <Network size={300} />
            </div>

            <div className="relative z-10 mb-12 flex items-center justify-between px-2">
              <div className="flex items-center gap-4">
                <div className="h-2 w-2 animate-ping rounded-full bg-[var(--primary)] shadow-[0_0_12px_rgba(102,252,241,0.6)]" />
                <h2 className="text-xs font-black uppercase tracking-[0.4em] text-white">
                  {t("streamTitle")}
                </h2>
              </div>
              <div className="flex items-center gap-6">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                  <input
                    type="text"
                    placeholder={t("searchPlaceholder")}
                    className="w-48 rounded-xl border border-white/5 bg-black/40 py-2 pl-10 pr-4 text-[10px] font-black text-white transition-all focus:border-[var(--primary)]/20 focus:outline-none"
                  />
                </div>
                <button className="rounded-xl border border-white/5 bg-white/5 p-2.5 text-gray-500 transition-all hover:text-white">
                  <Filter size={18} />
                </button>
              </div>
            </div>

            <div className="relative z-10 space-y-6">
              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-28 rounded-3xl" />
                  ))}
                </div>
              ) : error ? (
                <div className="py-20 text-center font-mono text-[10px] uppercase tracking-widest text-red-500">
                  {t("notifications.networkError")}: {error}
                </div>
              ) : workflows.length === 0 ? (
                <div className="py-20 text-center">
                  <div className="text-sm font-black uppercase tracking-[0.3em] text-white">
                    {t("noWorkflows")}
                  </div>
                  <div className="mt-3 text-xs text-gray-500">
                    {t("demoWarning")}
                  </div>
                </div>
              ) : (
                workflows.map((wf) => (
                  <WorkflowCard key={wf.id} workflow={wf} onClick={() => show("workflows", wf.id)} />
                ))
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function WorkflowCard({
  workflow,
  onClick,
}: {
  workflow: WorkflowListItem;
  onClick: () => void;
}) {
  const t = useTranslations("workflows");
  const tStatus = useTranslations("status");
  const format = useFormatter();
  
  const statusKey = workflow.status?.toLowerCase() || "pending_approval";
  const isRunning = statusKey === "running";
  const isCompleted = statusKey === "completed";
  const isFailed = statusKey === "failed" || statusKey === "error";
  const progress = workflow.progress_pct ?? 0;

  return (
    <div
      onClick={onClick}
      className="group/item relative cursor-pointer overflow-hidden rounded-[2rem] border border-white/5 bg-white/[0.012] p-8 transition-all hover:border-[var(--primary)]/30 hover:bg-white/[0.025]"
    >
      <div className="relative z-10 flex flex-col items-center justify-between gap-10 xl:flex-row">
        <div className="flex min-w-[350px] flex-1 items-center gap-8">
          <div className="relative">
            <div
              className={`flex h-14 w-14 items-center justify-center rounded-2xl border shadow-xl transition-all duration-500 ${
                isRunning
                  ? "border-[var(--primary)]/20 bg-[var(--primary)]/10 text-[var(--primary)] group-hover/item:scale-110"
                  : isCompleted
                    ? "border-green-500/20 bg-green-500/10 text-green-500"
                    : isFailed
                      ? "border-red-500/20 bg-red-500/10 text-red-500"
                      : "border-white/5 bg-black/40 text-gray-600"
              }`}
            >
              <Layout size={24} />
            </div>
            {isRunning && (
              <div className="absolute -right-1 -top-1 h-4 w-4 animate-pulse rounded-full border-2 border-[#060a12] bg-[var(--primary)] shadow-[0_0_10px_var(--primary)]" />
            )}
          </div>

          <div>
            <div className="mb-2 flex flex-wrap items-center gap-4">
              <h3 className="text-lg font-black uppercase tracking-tight text-white transition-colors group-hover/item:text-[var(--primary)]">
                {workflow.title}
              </h3>
              <span
                className={`rounded-lg border px-2 py-0.5 text-[9px] font-black uppercase tracking-widest transition-all ${
                  isRunning
                    ? "border-[var(--primary)]/20 bg-[var(--primary)]/10 text-[var(--primary)]"
                    : isCompleted
                      ? "border-green-500/20 bg-green-500/10 text-green-500"
                      : isFailed
                        ? "border-red-500/20 bg-red-500/10 text-red-500"
                        : "bg-white/5 text-gray-300"
                }`}
              >
                {tStatus(statusKey as any)}
              </span>
              <span className="rounded-lg border border-white/5 bg-white/[0.02] px-2 py-0.5 text-[9px] font-black uppercase tracking-widest text-gray-500">
                {workflow.workflow_type}
              </span>
            </div>
            <p className="font-mono text-[9px] uppercase tracking-widest text-gray-700">
              FLOW_ID: {String(workflow.id).substring(0, 16)}
            </p>
          </div>
        </div>

        <div className="hidden min-w-[240px] items-center gap-4 md:flex">
          <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.015] px-4 py-2 transition-all hover:border-[var(--primary)]/20">
            <ShieldCheck size={14} className="text-green-500" />
            <span className="text-[9px] font-black uppercase tracking-widest text-gray-600">TRUST_L4</span>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.015] px-4 py-2">
            <Fingerprint size={14} className="text-blue-400" />
            <span className="text-[9px] font-black uppercase tracking-widest text-gray-600">SIGNED</span>
          </div>
        </div>

        <div className="flex min-w-[200px] flex-col gap-3">
          <div className="flex items-end justify-between px-1">
            <span className="text-[9px] font-black uppercase tracking-widest text-gray-700">
              {t("step")} {workflow.completed_steps} / {workflow.total_steps || 1}
            </span>
            <span className="font-mono text-[10px] font-black tracking-widest text-white">
              {format.number(progress / 100, { style: 'percent' })}
            </span>
          </div>
          <div className="h-1.5 w-48 overflow-hidden rounded-full border border-white/[0.03] bg-black/40">
            <div
              className={`h-full bg-gradient-to-r from-[var(--primary)] to-blue-500 shadow-[0_0_10px_rgba(102,252,241,0.3)] transition-all duration-1000 ${
                isFailed ? "from-red-600 to-red-400" : ""
              }`}
              style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
            />
          </div>
        </div>

        <div className="flex min-w-[100px] items-center justify-end gap-4">
          <div className="flex items-center gap-2 text-[var(--primary)] opacity-0 transition-all group-hover/item:translate-x-1 group-hover/item:opacity-100">
            <span className="text-[10px] font-black uppercase tracking-widest">{t("inspect")}</span>
            <ChevronRight size={16} />
          </div>
        </div>
      </div>
    </div>
  );
}
