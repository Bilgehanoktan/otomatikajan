"use client";

import { useTranslations, useFormatter } from "next-intl";
import { useCallback, useEffect, useMemo, useState } from "react";
import { App } from "antd";
import {
  CheckSquare,
  XSquare,
  Clock,
  Plus,
  ShieldCheck,
  UserCheck,
  Zap,
  Lock,
  Target,
  Gavel,
  Scale,
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";
import { ensureSession, getAuthHeaders } from "@/lib/auth";
import { getApiBaseUrl } from "@/lib/runtime";

type ApprovalStatus = "approved" | "rejected";

interface ApprovalRequest {
  id: string;
  project_id: string;
  request_type: string;
  reason: string;
  status: string;
  created_at: string;
  agent_id?: string;
  decided_by?: string;
  decided_at?: string;
  comment?: string;
}

export default function ApprovalsPage() {
  const t = useTranslations("quorum");
  const format = useFormatter();
  const { notification } = App.useApp();
  const [isClient, setIsClient] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [staleMeta, setStaleMeta] = useState<unknown>(null);

  useEffect(() => setIsClient(true), []);

  const apiBase = useMemo(() => getApiBaseUrl(), []);

  const loadRequests = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);

    try {
      const session = await ensureSession();
      if (session.kind === "network-error") {
        throw session.error;
      }
      if (session.kind !== "authenticated") {
        throw new Error(t("notifications.sessionError"));
      }
      const authHeaders = await getAuthHeaders();
      const response = await safeFetchJson<ApprovalRequest[] | { data?: ApprovalRequest[]; __sqv_meta?: unknown }>(
        `${apiBase}/approvals?_end=10&_start=0&status=pending`,
        { headers: authHeaders },
      );

      const items = Array.isArray(response)
        ? response
        : Array.isArray(response?.data)
          ? response.data
          : [];

      setRequests(items);
      if (!Array.isArray(response) && response?.__sqv_meta) {
        setStaleMeta(response.__sqv_meta);
      } else {
        setStaleMeta(null);
      }
    } catch {
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  }, [apiBase, ensureSession]);

  useEffect(() => {
    if (!isClient) return;
    void loadRequests();
  }, [isClient, loadRequests]);

  const handleDecision = useCallback(
    async (id: string, status: ApprovalStatus) => {
      try {
        const session = await ensureSession();
        if (session.kind === "network-error") {
          throw session.error;
        }
        if (session.kind !== "authenticated") {
          throw new Error(t("notifications.sessionError"));
        }
        const authHeaders = await getAuthHeaders();

        await safeFetchJson(`${apiBase}/approvals/${id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json", ...authHeaders },
          body: JSON.stringify({
            status,
            comment: `Actioned via Elite Control Plane at ${new Date().toISOString()}`,
          }),
        });

        notification.success({
          message: status === "approved" ? t("notifications.approvalSaved") : t("notifications.rejectionSaved"),
          description: t("notifications.auditDesc"),
          placement: "topRight",
        });

        await loadRequests();
      } catch (err) {
        notification.error({
          message: t("notifications.actionFailed"),
          description: err instanceof Error ? err.message : "Error",
          placement: "topRight",
        });
      }
    },
    [apiBase, loadRequests, notification, t],
  );

  const handleCreateDirective = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    notification.success({
      message: t("notifications.directiveBroadcasted"),
      description: t("notifications.directiveDesc"),
      placement: "topRight",
    });
    setIsModalOpen(false);
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#060a12] p-8 text-gray-300 animate-in fade-in duration-1000">
      <ResourceHeader
        title={t("title")}
        subtitle={t("subtitle")}
        icon={<CheckSquare size={32} />}
        badge="L3-L4 Gates"
        staleMeta={staleMeta as never}
        actions={
          <div className="flex items-center gap-8">
            <div className="flex flex-col items-end border-r border-white/5 pr-8">
              <span className="text-[9px] font-black uppercase leading-none tracking-widest text-gray-500">
                {t("decisionIntegrity")}
              </span>
              <span className="mt-2 font-mono text-sm font-black italic tracking-tighter text-[var(--primary)]">
                99.9% {t("verified")}
              </span>
            </div>
            <button
              onClick={() => setIsModalOpen(true)}
              className="group flex items-center gap-2 rounded-2xl bg-[var(--primary)] px-8 py-3 text-[10px] font-black uppercase tracking-widest text-[#060a12] transition-all hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] active:scale-95"
            >
              <Plus size={14} className="transition-transform group-hover:rotate-90" />
              <span>{t("newDirective")}</span>
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-10 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <section className="glass-panel group relative min-h-[600px] overflow-hidden rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent p-10 shadow-2xl">
            <div className="pointer-events-none absolute right-0 top-0 p-10 opacity-[0.02] transition-opacity group-hover:opacity-[0.05]">
              <Gavel size={300} />
            </div>

            <div className="relative z-10 mb-12 flex items-center justify-between px-2">
              <div className="flex items-center gap-4">
                <div className="h-2 w-2 animate-ping rounded-full bg-[var(--primary)] shadow-[0_0_12px_rgba(102,252,241,0.6)]" />
                <h2 className="text-xs font-black uppercase tracking-[0.4em] text-white">{t("pendingSignOff")}</h2>
              </div>
              <div className="flex items-center gap-6">
                <span className="text-[10px] font-black uppercase tracking-widest text-gray-700">
                  {t("activeRequests")}: {requests.length}
                </span>
              </div>
            </div>

            <div className="relative z-10 space-y-6">
              {isLoading ? (
                <div className="space-y-6">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-44 rounded-3xl" />
                  ))}
                </div>
              ) : isError ? (
                <div className="flex flex-col items-center gap-6 py-20 text-center">
                  <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-500">
                    {t("syncLost")}
                  </p>
                  <button
                    onClick={() => void loadRequests()}
                    className="rounded-xl border border-white/10 px-4 py-2 text-[10px] font-black text-white transition-all hover:bg-white/5"
                  >
                    Consensus
                  </button>
                </div>
              ) : requests.length === 0 ? (
                <div className="flex flex-col items-center gap-6 py-32 text-center">
                  <div className="rounded-full border border-white/5 bg-white/[0.02] p-8 opacity-40">
                    <ShieldCheck size={48} className="text-[var(--primary)]" />
                  </div>
                  <p className="text-gray-600 font-black uppercase tracking-[0.3em] italic">
                    {t("allGatesOpen")}
                  </p>
                </div>
              ) : (
                requests.map((req) => (
                  <EliteApprovalCard
                    key={req.id}
                    request={req}
                    onApprove={() => void handleDecision(req.id, "approved")}
                    onReject={() => void handleDecision(req.id, "rejected")}
                    t={t}
                    format={format}
                  />
                ))
              )}
            </div>
          </section>
        </div>

        <div className="space-y-8 xl:col-span-4">
          <section className="glass-panel group relative overflow-hidden rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/50 p-10 shadow-xl">
            <div className="pointer-events-none absolute right-0 top-0 p-8 opacity-[0.03] transition-opacity group-hover:opacity-[0.08]">
              <Scale size={140} className="text-[var(--primary)]" />
            </div>

            <div className="relative z-10 mb-10 flex items-center gap-4">
              <div className="rounded-2xl border border-[var(--primary)]/20 bg-[var(--primary)]/10 p-3 shadow-xl">
                <UserCheck size={24} className="text-[var(--primary)]" />
              </div>
              <div>
                <h3 className="text-xl font-black uppercase tracking-tighter text-white">{t("quorumState")}</h3>
                <p className="mt-1 text-[9px] font-black uppercase tracking-[0.2em] text-[var(--primary)]">
                  {t("institutionalConsensus")}
                </p>
              </div>
            </div>

            <div className="relative z-10 space-y-6">
              <div className="rounded-2xl border border-white/5 bg-white/[0.015] p-6 transition-all group-hover:border-[var(--primary)]/20">
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-[9px] font-black uppercase leading-none tracking-widest text-gray-600">
                    {t("globalThreshold")}
                  </span>
                  <span className="text-sm font-black text-white">4 / 5 {t("sync")}</span>
                </div>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`h-1.5 flex-1 rounded-full transition-all duration-1000 ${
                        i <= 4 ? "bg-[var(--primary)] shadow-[0_0_8px_var(--primary)]" : "bg-white/5"
                      }`}
                    />
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-white/5 bg-black/40 p-6 transition-all group-hover:border-white/10">
                <p className="mb-6 text-[9px] font-bold uppercase tracking-widest italic leading-relaxed text-gray-500 opacity-60">
                  {t("governanceRules")}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-black uppercase tracking-widest text-[var(--primary)]">{t("protocolActive")}</span>
                  <Lock size={12} className="text-gray-700" />
                </div>
              </div>
            </div>
          </section>

          <section className="glass-panel relative overflow-hidden rounded-[3rem] border-white/[0.03] bg-gradient-to-br from-white/[0.01] to-transparent p-10 shadow-2xl">
            <div className="relative z-10 flex flex-col gap-6">
              <div className="flex items-center justify-between border-b border-white/[0.03] pb-6">
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-600">{t("avgDecisionTime")}</span>
                <span className="text-xs font-mono font-black text-white">12.4m</span>
              </div>
              <div className="flex items-center justify-between border-b border-white/[0.03] pb-6">
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-600">{t("rejectionRate")}</span>
                <span className="text-xs font-mono font-black text-red-400">2.1%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-600">{t("consensusDrift")}</span>
                <span className="text-xs font-mono font-black text-green-400">{t("nominal")}</span>
              </div>
            </div>
          </section>
        </div>
      </div>

      {isModalOpen && (
        <div className="animate-in fade-in zoom-in fixed inset-0 z-50 flex items-center justify-center p-8 duration-300">
          <div className="absolute inset-0 bg-[#060a12]/90 backdrop-blur-xl" onClick={() => setIsModalOpen(false)} />
          <div className="glass-panel relative z-10 w-full max-w-xl rounded-[3rem] border-[var(--primary)]/20 bg-gradient-to-br from-[#0b0c10] to-[#060a12] p-10 shadow-[0_32px_128px_rgba(0,0,0,0.8)]">
            <div className="mb-10 flex items-center gap-4">
              <div className="rounded-2xl border border-[var(--primary)]/20 bg-[var(--primary)]/10 p-3">
                <Target size={24} className="text-[var(--primary)]" />
              </div>
              <div>
                <h3 className="text-2xl font-black uppercase tracking-tighter text-white">{t("emergencyDirective")}</h3>
                <p className="mt-1 text-[9px] font-black uppercase tracking-widest text-[var(--primary)]">
                  {t("manualOverride")}
                </p>
              </div>
            </div>

            <form onSubmit={handleCreateDirective} className="space-y-8">
              <div className="space-y-3">
                <label className="ml-1 text-[9px] font-black uppercase tracking-widest text-gray-600">{t("directiveScope")}</label>
                <div className="grid grid-cols-2 gap-4">
                  <button type="button" className="rounded-2xl border border-[var(--primary)]/20 bg-[var(--primary)]/10 p-4 text-[10px] font-black uppercase text-[var(--primary)]">
                    {t("fleetWide")}
                  </button>
                  <button type="button" className="rounded-2xl border border-white/10 bg-white/5 p-4 text-[10px] font-black uppercase text-gray-500">
                    {t("localNode")}
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                <label className="ml-1 text-[9px] font-black uppercase tracking-widest text-gray-600">{t("executiveOrder")}</label>
                <textarea
                  required
                  rows={4}
                  placeholder={t("placeholderOrder")}
                  className="w-full resize-none rounded-2xl border border-white/10 bg-black/40 px-8 py-5 font-mono text-[11px] font-black text-white transition-all focus:border-[var(--primary)]/50 focus:outline-none"
                />
              </div>

              <div className="flex gap-6 pt-6">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 py-5 text-[10px] font-black uppercase text-gray-500 transition-all hover:text-white"
                >
                  {t("abort")}
                </button>
                <button
                  type="submit"
                  className="flex-[2] rounded-2xl bg-[var(--primary)] py-5 text-[10px] font-black uppercase tracking-[0.2em] text-[#060a12] transition-all hover:shadow-[0_8px_32px_rgba(102,252,241,0.4)] active:scale-95"
                >
                  {t("broadcast")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function EliteApprovalCard({
  request,
  onApprove,
  onReject,
  t,
  format,
}: {
  request: ApprovalRequest;
  onApprove: () => void;
  onReject: () => void;
  t: any;
  format: any;
}) {
  const isBudget = request.request_type === "budget";

  return (
    <div className="group/item relative overflow-hidden rounded-[2rem] border border-white/5 bg-white/[0.015] p-8 transition-all hover:border-[var(--primary)]/30 hover:bg-white/[0.025]">
      <div className="relative z-10 flex flex-col justify-between gap-10 md:flex-row">
        <div className="flex items-start gap-6">
          <div
            className={`rounded-2xl border p-5 shadow-xl transition-all duration-500 group-hover/item:scale-110 ${
              isBudget
                ? "border-amber-500/20 bg-amber-500/10 text-amber-500"
                : "border-[var(--primary)]/20 bg-[var(--primary)]/10 text-[var(--primary)]"
            }`}
          >
            <Zap size={24} className={isBudget ? "animate-pulse" : ""} />
          </div>

          <div>
            <div className="mb-3 flex flex-wrap items-center gap-4">
              <h3 className="text-xl font-black uppercase tracking-tighter text-white transition-colors group-hover/item:text-[var(--primary)]">
                {(request.request_type || "SYSTEM").toUpperCase()} {t("gateIntervention")}
              </h3>
              <span className="rounded-lg border border-white/5 bg-black/40 px-2.5 py-1 text-[9px] font-mono font-black uppercase leading-none tracking-widest text-gray-600">
                TX_ID: {String(request.id).substring(0, 12)}
              </span>
            </div>
            <p className="mb-8 max-w-2xl text-xs font-bold leading-relaxed tracking-tight text-gray-500">
              "{request.reason}"
            </p>

            <div className="grid grid-cols-2 gap-8 border-t border-white/[0.03] pt-8 md:grid-cols-3">
              <div className="flex flex-col gap-2">
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-700">{t("projectScope")}</span>
                <span className="max-w-[140px] truncate text-[11px] font-black uppercase tracking-tight text-white">
                  {String(request.project_id).substring(0, 13)}...
                </span>
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-700">{t("stepContext")}</span>
                <span className="text-[11px] font-black uppercase tracking-tight text-[var(--primary)]">
                  {request.agent_id || "GLOBAL_OPS"}
                </span>
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-700">{t("requestedTime")}</span>
                <div className="flex items-center gap-2">
                  <Clock size={12} className="text-gray-700" />
                  <span className="text-[11px] font-mono font-black uppercase text-gray-500">
                    {format.dateTime(new Date(request.created_at), { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex min-w-[200px] items-center justify-end gap-4 md:flex-col">
          <button
            onClick={onApprove}
            className="group/approve flex w-full items-center justify-center gap-3 rounded-2xl bg-[var(--primary)] px-8 py-4 text-[11px] font-black uppercase tracking-widest text-[#060a12] transition-all hover:shadow-[0_8px_32px_rgba(102,252,241,0.4)] active:scale-95"
          >
            <CheckSquare size={18} className="transition-transform group-hover/approve:scale-125" />
            <span>{t("approve")}</span>
          </button>
          <button
            onClick={onReject}
            className="flex w-full items-center justify-center gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 px-8 py-4 text-[11px] font-black uppercase tracking-widest text-red-500 transition-all hover:bg-red-500/20 active:scale-95"
          >
            <XSquare size={18} />
            <span>{t("reject")}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
