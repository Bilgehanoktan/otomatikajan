"use client";

import React from "react";
import { App } from "antd";
import {
  AlertTriangle,
  CheckCircle2,
  Flame,
  Clock,
  Filter,
  Activity,
  ShieldAlert,
  Radio,
  ChevronRight,
  Zap,
  Target,
  Terminal,
  Search,
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/runtime";

interface Incident {
  id: string;
  incident_type: string;
  status: string;
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  project_id?: string;
  created_at: string;
  payload?: Record<string, unknown>;
}

export default function IncidentsPage() {
  const { notification } = App.useApp();
  const [isClient, setIsClient] = React.useState(false);
  const [incidents, setIncidents] = React.useState<Incident[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isError, setIsError] = React.useState(false);
  const [staleMeta, setStaleMeta] = React.useState<unknown>(null);

  React.useEffect(() => setIsClient(true), []);

  const apiBase = React.useMemo(() => getApiBaseUrl(), []);

  const loadIncidents = React.useCallback(async () => {
    setIsLoading(true);
    setIsError(false);

    try {
      const response = await safeFetchJson<Incident[] | { data?: Incident[]; __sqv_meta?: unknown }>(
        `${apiBase}/governance/incidents?_end=10&_order=desc&_sort=created_at&_start=0`,
        { useOfflineFallback: true },
      );

      const items = Array.isArray(response)
        ? response
        : Array.isArray(response?.data)
          ? response.data
          : [];

      setIncidents(items);
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
  }, [apiBase]);

  React.useEffect(() => {
    if (!isClient) return;
    void loadIncidents();
  }, [isClient, loadIncidents]);

  const handleResolve = React.useCallback(
    async (id: string) => {
      try {
        const identityName = (window as any).__SQV_IDENTITY__?.name || "mimari-operator";

        await safeFetchJson(`${apiBase}/governance/incidents/${id}/resolve`, {
          method: "POST",
          body: JSON.stringify({ 
            resolution_notes: "Resolved from control plane incidents page",
            operator_id: identityName
          }),
        });

        notification.success({
          message: "Action applied",
          description: "Incident has been marked as resolved.",
          placement: "topRight",
        });

        await loadIncidents();
      } catch (err) {
        notification.error({
          message: "Action failed",
          description: err instanceof Error ? err.message : "An unknown error occurred",
          placement: "topRight",
        });
      }
    },
    [apiBase, loadIncidents, notification],
  );

  const handleResolveAll = React.useCallback(async () => {
    if (incidents.length === 0) return;
    
    notification.info({
      message: "Processing Hub",
      description: `Resolving ${incidents.length} incidents. Please wait...`,
      placement: "topRight",
    });

    try {
      // Resolve sequentially to prevent network saturation
      for (const inc of incidents) {
        if (inc.status === "resolved") continue;
        const identityName = (window as any).__SQV_IDENTITY__?.name || "mimari-operator";
        
        await safeFetchJson(`${apiBase}/governance/incidents/${inc.id}/resolve`, {
          method: "POST",
          body: JSON.stringify({ 
            resolution_notes: "Bulk resolution from control plane",
            operator_id: identityName
          }),
        });
      }

      notification.success({
        message: "Fleet Stabilized",
        description: "All incidents have been cleared.",
        placement: "topRight",
      });

      await loadIncidents();
    } catch (err) {
      notification.error({
        message: "Bulk Action Partial Failure",
        description: err instanceof Error ? err.message : "Network error during bulk cleanup",
        placement: "topRight",
      });
      await loadIncidents();
    }
  }, [apiBase, incidents, loadIncidents, notification]);

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#060a12] p-8 text-gray-300 animate-in fade-in duration-1000">
      <ResourceHeader
        title="Incident Control"
        subtitle="Real-time Chaos Monitoring & Autonomous Mitigation"
        icon={<AlertTriangle size={32} />}
        badge="Critical Ops"
        staleMeta={staleMeta as never}
        actions={
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-4 border-r border-white/5 pr-8">
              <div className="text-right">
                <p className="text-[9px] font-black uppercase leading-none tracking-widest text-gray-500">
                  Global Pulse
                </p>
                <p className="mt-2 text-sm font-black text-blue-400">NOMINAL</p>
              </div>
              <div className="rounded-full border border-blue-500/20 bg-blue-500/10 p-3">
                <Radio size={16} className="animate-pulse text-blue-400" />
              </div>
            </div>

            <button className="flex items-center gap-2 rounded-2xl border border-red-500/20 bg-red-500/10 px-8 py-3 text-[10px] font-black uppercase tracking-widest text-red-500 shadow-xl transition-all hover:bg-red-500/20 active:scale-95">
              <Zap size={14} />
              <span>Chaos Protocol</span>
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-10 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <section className="glass-panel group relative overflow-hidden rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent p-10 shadow-2xl">
            <div className="pointer-events-none absolute right-0 top-0 p-10 opacity-[0.02] transition-opacity group-hover:opacity-[0.05]">
              <Terminal size={300} />
            </div>

            <div className="relative z-10 mb-12 flex items-center justify-between px-2">
              <div className="flex items-center gap-4">
                <div className="h-2 w-2 animate-ping rounded-full bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.6)]" />
                <h2 className="text-xs font-black uppercase tracking-[0.4em] text-white">Integrated Chaos Stream</h2>
              </div>
              <div className="flex items-center gap-6">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                  <input
                    type="text"
                    placeholder="OLAY ARA..."
                    className="w-48 rounded-xl border border-white/5 bg-black/40 py-2 pl-10 pr-4 text-[10px] font-black text-white transition-all focus:border-[var(--primary)]/20 focus:outline-none"
                  />
                </div>
                <button className="rounded-xl border border-white/5 bg-white/5 p-2.5 text-gray-500 transition-all hover:text-white">
                  <Filter size={18} />
                </button>
              </div>
            </div>

            <div className="custom-scrollbar relative z-10 max-h-[800px] space-y-6 overflow-y-auto pr-3">
              {isLoading ? (
                <div className="space-y-6">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-40 rounded-3xl" />
                  ))}
                </div>
              ) : isError ? (
                <div className="flex flex-col items-center gap-6 py-20 text-center">
                  <div className="rounded-full border border-red-500/20 bg-red-500/10 p-6 text-red-500">
                    <AlertTriangle size={32} />
                  </div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-gray-500">
                    Telemetry Connection Severed
                  </p>
                  <button
                    onClick={() => void loadIncidents()}
                    className="text-[10px] font-black uppercase tracking-widest text-[var(--primary)] hover:underline"
                  >
                    Re-establish Sync
                  </button>
                </div>
              ) : incidents.length === 0 ? (
                <div className="py-32 text-center font-black uppercase tracking-[0.3em] italic text-gray-600 opacity-40">
                  Aktif olay tespit edilmedi. Sistem otonom dengede.
                </div>
              ) : (
                incidents.map((inc) => (
                  <EliteIncidentItem key={inc.id} incident={inc} onResolve={() => void handleResolve(inc.id)} />
                ))
              )}
            </div>
          </section>
        </div>

        <div className="space-y-8 xl:col-span-4">
          <section className="glass-panel group relative overflow-hidden rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/50 p-10 shadow-xl">
            <div className="pointer-events-none absolute right-0 top-0 p-8 opacity-[0.03] transition-opacity group-hover:opacity-[0.08]">
              <ShieldAlert size={140} className="text-red-500" />
            </div>

            <div className="relative z-10 mb-10 flex items-center gap-4 text-red-500">
              <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-3 shadow-xl">
                <ShieldAlert size={24} />
              </div>
              <div>
                <h3 className="text-xl font-black uppercase tracking-tighter text-white">Severity Monitor</h3>
                <p className="mt-1 text-[9px] font-black uppercase tracking-[0.2em] text-red-400">Hazard Phase 3</p>
              </div>
            </div>

            <div className="relative z-10 space-y-6">
              <SeverityGauge label="Critical / P0" value={incidents.filter((i) => i.severity === "critical").length} color="bg-red-500" total={incidents.length} />
              <SeverityGauge label="High / P1" value={incidents.filter((i) => i.severity === "high").length} color="bg-orange-500" total={incidents.length} />
              <SeverityGauge label="Medium / P2" value={incidents.filter((i) => i.severity === "medium").length} color="bg-blue-500" total={incidents.length} />
            </div>
          </section>

          <section className="glass-panel group relative overflow-hidden rounded-[3rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.05] to-transparent p-10 shadow-2xl">
            <div className="absolute -bottom-10 -right-10 opacity-[0.03] transition-opacity duration-1000 group-hover:opacity-[0.08]">
              <Activity size={200} className="text-[var(--primary)]" />
            </div>
            <h3 className="relative z-10 mb-8 flex items-center gap-3 text-xs font-black uppercase tracking-[0.3em] italic text-white">
              <Activity size={20} className="text-[var(--primary)]" />
              Mitigation HUD
            </h3>

            <div className="relative z-10 space-y-6">
              <div className="rounded-2xl border border-white/5 bg-black/40 p-6 transition-all group-hover:border-[var(--primary)]/20">
                <p className="mb-4 text-[10px] font-bold uppercase tracking-widest leading-relaxed text-gray-500">
                  Otonom tamir motoru son 1 saatte düşük öncelikli olaylarda self-healing başarısı sağladı.
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-black text-green-400">92% SUCCESS</span>
                  <button className="text-[9px] font-black uppercase text-gray-700 transition-colors hover:text-white">
                    Details
                  </button>
                </div>
              </div>

              <button 
                onClick={() => void handleResolveAll()}
                disabled={incidents.length === 0}
                className="group/btn w-full rounded-2xl bg-[var(--primary)] py-5 text-[10px] font-black uppercase tracking-[0.2em] text-[#060a12] transition-all hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <span className="inline-flex items-center justify-center gap-3">
                  Tümünü Temizle
                  <ChevronRight size={14} className="transition-transform group-hover/btn:translate-x-2" />
                </span>
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function EliteIncidentItem({
  incident,
  onResolve,
}: {
  incident: Incident;
  onResolve: () => void;
}) {
  const isCritical = incident.severity === "critical";
  const isResolved = incident.status === "resolved";

  return (
    <div
      className={`group/item relative overflow-hidden rounded-[2rem] border p-8 transition-all duration-500 ${
        isCritical
          ? "border-red-500/20 bg-red-500/[0.02] hover:border-red-500/40"
          : "border-white/5 bg-white/[0.015] hover:border-white/10 hover:bg-white/[0.025]"
      }`}
    >
      <div className="relative z-10 flex items-start justify-between gap-8">
        <div className="flex items-start gap-6">
          <div
            className={`rounded-2xl border p-5 shadow-xl transition-all duration-500 ${
              isCritical
                ? "border-red-500/20 bg-red-500/10 text-red-500 group-hover/item:scale-110"
                : "border-white/5 bg-black/40 text-gray-600 group-hover/item:text-blue-400"
            }`}
          >
            {isCritical ? <Flame size={24} className="animate-pulse" /> : <ShieldAlert size={24} />}
          </div>

          <div>
            <div className="mb-2 flex flex-wrap items-center gap-4">
              <h3 className="text-lg font-black uppercase tracking-tight text-white transition-colors group-hover/item:text-[var(--primary)]">
                {(incident.incident_type || "UNKNOWN_INCIDENT").replace("_", " ")}
              </h3>
              <span
                className={`rounded-lg border px-2.5 py-1 text-[9px] font-black uppercase tracking-widest transition-all ${
                  isResolved
                    ? "border-green-500/20 bg-green-500/10 text-green-500"
                    : "border-[var(--primary)]/20 bg-[var(--primary)]/10 text-[var(--primary)] shadow-[0_0_10px_rgba(102,252,241,0.1)]"
                }`}
              >
                {incident.status}
              </span>
            </div>
            <p
              className={`mb-6 max-w-xl text-xs font-bold leading-relaxed tracking-tight ${
                isCritical ? "text-red-200 opacity-80" : "text-gray-500"
              }`}
            >
              {incident.message}
            </p>

            <div className="flex items-center gap-6 border-t border-white/[0.03] pt-6">
              <div className="flex items-center gap-2">
                <Clock size={12} className="text-gray-700" />
                <span className="text-[9px] font-mono font-black uppercase tracking-widest text-gray-700">
                  {new Date(incident.created_at).toLocaleTimeString()}
                </span>
              </div>
              {incident.project_id && (
                <div className="flex items-center gap-2">
                  <Target size={12} className="text-gray-700" />
                  <span className="text-[9px] font-black uppercase tracking-widest text-gray-700">
                    NODE_ID: {String(incident.project_id).substring(0, 8)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex min-w-[120px] flex-col items-end gap-3">
          {!isResolved ? (
            <button
              onClick={onResolve}
              className="rounded-xl border border-white/10 bg-white/5 px-6 py-2.5 text-[10px] font-black uppercase text-white transition-all hover:border-[var(--primary)] hover:bg-[var(--primary)] hover:text-[#060a12] active:scale-95"
            >
              Aksiyon Al
            </button>
          ) : (
            <div className="flex items-center gap-2 rounded-xl border border-green-500/20 bg-green-500/10 px-4 py-2 text-green-500">
              <CheckCircle2 size={16} />
              <span className="text-[9px] font-black uppercase tracking-widest">Çözüldü</span>
            </div>
          )}
        </div>
      </div>

      {isCritical && <div className="pointer-events-none absolute inset-0 bg-red-500/5 transition-all duration-1000 group-hover:bg-red-500/10" />}
    </div>
  );
}

function SeverityGauge({
  label,
  value,
  color,
  total,
}: {
  label: string;
  value: number;
  color: string;
  total: number;
}) {
  const pct = total > 0 ? (value / total) * 100 : 0;

  return (
    <div className="group cursor-help">
      <div className="mb-3 flex items-end justify-between px-1">
        <span className="text-[10px] font-black uppercase tracking-widest text-gray-600 transition-colors group-hover:text-white">
          {label}
        </span>
        <span className={`font-mono text-[11px] font-black tracking-tighter ${color.replace("bg-", "text-")}`}>{value}</span>
      </div>
      <div className="relative h-1.5 w-full overflow-hidden rounded-full border border-white/[0.03] bg-black/40 transition-all group-hover:border-white/10">
        <div className={`h-full opacity-60 shadow-[0_0_15px_currentColor] transition-all duration-1000 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
