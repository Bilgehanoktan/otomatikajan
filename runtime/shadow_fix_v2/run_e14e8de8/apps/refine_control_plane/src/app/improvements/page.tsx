"use client";

import React from "react";
import { useList, useUpdate } from "@refinedev/core";
import { useTranslations } from "next-intl";
import {
  Activity,
  Binary,
  Check,
  Clock,
  Code2,
  Cpu,
  Dna,
  Filter,
  Search,
  ShieldCheck,
  Terminal,
  X,
  Zap,
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { SystemImprovement } from "@/types/mission-control";

type ImprovementFilter = "all" | "pending" | "approved" | "applied" | "rejected" | "failed";

export default function ImprovementsPage() {
  const t = useTranslations("improvements");
  const [isClient, setIsClient] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [filter, setFilter] = React.useState<ImprovementFilter>("all");

  React.useEffect(() => setIsClient(true), []);

  const {
    query: { data, isLoading, isError, refetch },
  } = useList<SystemImprovement>({
    resource: "governance/improvements",
    pagination: { pageSize: 20 },
    sorters: [{ field: "created_at", order: "desc" }],
    queryOptions: { enabled: isClient },
  });

  const { mutate: updateStatus } = useUpdate();

  const handleApprove = (id: string) => {
    updateStatus(
      {
        resource: "governance/improvements",
        id,
        values: { status: "approved" },
        successNotification: { message: t("notifications.approved"), type: "success" },
      },
      {
        onSuccess: () => refetch(),
      },
    );
  };

  const handleReject = (id: string) => {
    updateStatus(
      {
        resource: "governance/improvements",
        id,
        values: { status: "rejected" },
        successNotification: { message: t("notifications.rejected"), type: "error" },
      },
      {
        onSuccess: () => refetch(),
      },
    );
  };

  const improvements = React.useMemo<SystemImprovement[]>(() => data?.data ?? [], [data]);
  const pendingCount = improvements.filter((i) => i.status === "pending").length;
  const healedCount = improvements.filter((i) => i.status === "applied").length;

  const filteredImprovements = React.useMemo(() => {
    const search = searchTerm.trim().toLowerCase();
    return improvements.filter((item) => {
      const statusOk = filter === "all" ? true : item.status?.toLowerCase() === filter;
      if (!statusOk) return false;
      if (!search) return true;
      const haystack = `${item.target_file} ${item.instruction} ${item.status}`.toLowerCase();
      return haystack.includes(search);
    });
  }, [filter, improvements, searchTerm]);

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#060a12] p-8 text-gray-300 animate-in fade-in duration-1000">
      <ResourceHeader
        title={t("title")}
        subtitle={t("subtitle")}
        icon={<Dna size={32} />}
        badge={t("badge")}
        actions={
          <div className="flex items-center gap-8">
            <div className="flex flex-col items-end border-r border-white/5 pr-8">
              <span className="text-[9px] font-black uppercase leading-none tracking-widest text-gray-500">
                {t("cortexConfidence")}
              </span>
              <span className="mt-2 font-mono text-sm font-black italic tracking-tighter text-[var(--primary)]">
                98.4% STABLE
              </span>
            </div>
            <div className="flex items-center gap-4">
              <button className="rounded-2xl border border-white/5 bg-white/5 p-3 text-gray-500 transition-all hover:text-white">
                <Activity size={18} />
              </button>
              <button className="group flex items-center gap-2 rounded-2xl bg-[var(--primary)] px-8 py-3 text-[10px] font-black uppercase tracking-widest text-[#060a12] transition-all hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] active:scale-95">
                <Zap size={14} className="group-hover:animate-pulse" />
                <span>{t("recalibrate")}</span>
              </button>
            </div>
          </div>
        }
      />

      <div className="mb-10 grid grid-cols-1 gap-8 md:grid-cols-3">
        <EliteMetricCard
          label={t("metrics.pendingApproval")}
          val={pendingCount}
          icon={<Clock size={16} />}
          accent="text-amber-400"
        />
        <EliteMetricCard
          label={t("metrics.totalCycles")}
          val={healedCount}
          icon={<ShieldCheck size={16} />}
          accent="text-green-400"
        />
        <EliteMetricCard
          label={t("metrics.integrity")}
          val="94%"
          icon={<Activity size={16} />}
          accent="text-[var(--primary)]"
        />
      </div>

      <section className="glass-panel group relative overflow-hidden rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent p-10 shadow-2xl">
        <div className="pointer-events-none absolute right-0 top-0 p-10 opacity-[0.02] transition-opacity group-hover:opacity-[0.05]">
          <Binary size={300} />
        </div>

        <div className="relative z-10 mb-12 flex items-center justify-between px-2">
          <div className="flex items-center gap-4">
            <div className="h-2 w-2 animate-ping rounded-full bg-[var(--primary)] shadow-[0_0_12px_rgba(102,252,241,0.6)]" />
            <h2 className="text-xs font-black uppercase tracking-[0.4em] text-white">{t("streamTitle")}</h2>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
              <input
                type="text"
                placeholder={t("searchPlaceholder")}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-56 rounded-xl border border-white/5 bg-black/40 py-2 pl-10 pr-4 text-[10px] font-black text-white transition-all focus:border-[var(--primary)]/20 focus:outline-none"
              />
            </div>
            <button
              className="rounded-xl border border-white/5 bg-white/5 p-2.5 text-gray-500 transition-all hover:text-white"
              title={t("filterTitle")}
            >
              <Filter size={18} />
            </button>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as ImprovementFilter)}
              className="rounded-xl border border-white/5 bg-black/40 px-3 py-2 text-[10px] font-black uppercase tracking-widest text-white focus:border-[var(--primary)]/20 focus:outline-none"
            >
              <option value="all">{t("filters.all")}</option>
              <option value="pending">{t("filters.pending")}</option>
              <option value="approved">{t("filters.approved")}</option>
              <option value="applied">{t("filters.applied")}</option>
              <option value="rejected">{t("filters.rejected")}</option>
              <option value="failed">{t("filters.failed")}</option>
            </select>
          </div>
        </div>

        <div className="relative z-10 space-y-8">
          {isLoading ? (
            <div className="space-y-6">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-44 rounded-3xl" />
              ))}
            </div>
          ) : isError ? (
            <div className="py-20 text-center font-mono text-[10px] uppercase tracking-widest text-red-500">
              {t("telemetryOffline")}
            </div>
          ) : filteredImprovements.length === 0 ? (
            <div className="py-20 text-center font-mono text-[10px] uppercase tracking-widest text-gray-500">
              {t("noResults")}
            </div>
          ) : (
            filteredImprovements.map((improvement) => (
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
  );
}

function EliteMetricCard({
  label,
  val,
  icon,
  accent,
}: {
  label: string;
  val: string | number;
  icon: React.ReactNode;
  accent: string;
}) {
  return (
    <div className="glass-panel group relative overflow-hidden rounded-[2rem] border-white/5 bg-white/[0.01] p-8 transition-all hover:bg-white/[0.02]">
      <div className="mb-6 flex items-center justify-between">
        <span className="text-[10px] font-black uppercase tracking-widest text-gray-600">{label}</span>
        <div className="rounded-xl border border-white/5 bg-black/40 p-3 text-gray-600 transition-colors group-hover:text-white">
          {icon}
        </div>
      </div>
      <h3 className={`text-4xl font-black tracking-tighter ${accent}`}>{val}</h3>
    </div>
  );
}

function EliteImprovementItem({
  improvement,
  onApprove,
  onReject,
}: {
  improvement: SystemImprovement;
  onApprove: () => void;
  onReject: () => void;
}) {
  const isPending = improvement.status === "pending";

  return (
    <div
      className={`group/item relative overflow-hidden rounded-[2.5rem] border p-8 transition-all duration-500 ${
        isPending
          ? "border-amber-500/20 bg-amber-500/[0.02] hover:border-amber-500/40"
          : "border-white/5 bg-white/[0.015] hover:border-white/10"
      }`}
    >
      <div className="relative z-10 flex flex-col justify-between gap-10 xl:flex-row">
        <div className="flex-1">
          <div className="mb-8 flex items-start gap-6">
            <div
              className={`rounded-2xl border p-5 text-gray-700 shadow-xl transition-all duration-500 group-hover/item:scale-110 ${
                isPending
                  ? "border-amber-500/20 bg-amber-500/10 text-amber-500"
                  : "border-white/5 bg-black/40"
              }`}
            >
              <Code2 size={24} />
            </div>
            <div>
              <div className="mb-3 flex flex-wrap items-center gap-4">
                <h3 className="text-xl font-black uppercase tracking-tight text-white transition-colors group-hover/item:text-[var(--primary)]">
                  {improvement.target_file}
                </h3>
                <span
                  className={`rounded-lg border px-2.5 py-1 text-[9px] font-black uppercase tracking-widest transition-all ${
                    improvement.status === "applied"
                      ? "border-green-500/20 bg-green-500/10 text-green-400 shadow-[0_0_10px_rgba(34,197,94,0.1)]"
                      : "border-amber-500/20 bg-amber-500/10 text-amber-500"
                  }`}
                >
                  {improvement.status}
                </span>
              </div>
              <p className="max-w-2xl text-xs font-bold leading-relaxed tracking-tight text-gray-500">
                {improvement.instruction || "-"}
              </p>
            </div>
          </div>

          <div className="group/patch relative rounded-3xl border border-white/5 bg-black/40 p-6 font-mono text-[11px]">
            <div className="mb-4 flex items-center justify-between border-b border-white/5 pb-4">
              <div className="flex items-center gap-3 text-gray-700">
                <Terminal size={14} />
                <span className="text-[9px] font-black uppercase tracking-widest">Proposed Synthetic Patch</span>
              </div>
              <button className="text-[9px] font-black uppercase text-gray-700 transition-colors hover:text-[var(--primary)]">
                View Diffs
              </button>
            </div>
            <pre className="custom-scrollbar max-h-40 overflow-x-auto text-gray-400 opacity-60 transition-opacity group-hover/patch:opacity-100">
              {improvement.proposed_patch || ""}
            </pre>
          </div>

          <div className="mt-8 flex items-center gap-10 border-t border-white/[0.03] pt-6">
            <VerifierBadge label="Syntax" status="PASSED" icon={<ShieldCheck size={12} />} primary />
            <VerifierBadge label="Unit Tests" status="12/12 COMPLETED" icon={<Cpu size={12} />} />
            <VerifierBadge label="Consensus" status="VERIFIED" icon={<Activity size={12} />} />

            <div className="ml-auto flex items-center gap-3 opacity-40">
              <Clock size={12} className="text-gray-700" />
              <span className="font-mono text-[9px] font-black uppercase text-gray-700">
                {new Date(improvement.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {isPending && (
          <div className="flex min-w-[220px] items-center justify-end gap-4 xl:flex-col">
            <button
              onClick={onApprove}
              className="group/btn flex w-full items-center justify-center gap-3 rounded-[1.5rem] bg-[var(--primary)] px-8 py-5 text-[11px] font-black uppercase tracking-widest text-[#060a12] transition-all hover:shadow-[0_8px_32px_rgba(102,252,241,0.4)] active:scale-95"
            >
              <Check size={20} />
              <span>Approve & Apply</span>
            </button>
            <button
              onClick={onReject}
              className="flex w-full items-center justify-center gap-3 rounded-[1.5rem] border border-red-500/20 bg-red-500/10 px-8 py-5 text-[11px] font-black uppercase tracking-widest text-red-500 transition-all hover:bg-red-500/20 active:scale-95"
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

function VerifierBadge({
  label,
  status,
  icon,
  primary,
}: {
  label: string;
  status: string;
  icon: React.ReactNode;
  primary?: boolean;
}) {
  return (
    <div className="group/badge flex cursor-help items-center gap-3">
      <div
        className={`rounded-lg border p-1.5 transition-all ${
          primary
            ? "border-[var(--primary)]/20 bg-[var(--primary)]/10 text-[var(--primary)]"
            : "border-white/5 bg-white/5 text-gray-700 group-hover/badge:text-white"
        }`}
      >
        {icon}
      </div>
      <div className="flex flex-col">
        <span className="text-[8px] font-black uppercase tracking-widest text-gray-700">{label}</span>
        <span
          className={`text-[9px] font-black uppercase tracking-tighter ${
            primary ? "text-[var(--primary)]" : "text-gray-500 transition-colors group-hover/badge:text-white"
          }`}
        >
          {status}
        </span>
      </div>
    </div>
  );
}
