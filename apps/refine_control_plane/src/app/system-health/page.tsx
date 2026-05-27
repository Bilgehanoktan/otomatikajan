"use client";

import React, { useState, useEffect } from "react";
import { useCustom, useApiUrl, useTranslate } from "@refinedev/core";
import { useTranslations } from "next-intl";
import {
  Activity,
  ShieldCheck,
  Cpu,
  HeartPulse,
  Database,
  Zap,
  Globe,
  Binary,
  Fingerprint,
  Layers,
  Server,
  AlertOctagon,
  ArrowUpRight,
  Timer,
  BarChart3,
  Lock
} from "lucide-react";
import { Button, Progress, Card, Tag, Skeleton, Tooltip, message } from "antd";
import { safeFetchJson } from "@/lib/api";
import {
  compactRuntimeDiagnosticLabel,
  RuntimeDiagnostic,
  RuntimeDiagnosticsResponse,
} from "@/lib/runtimeDiagnostics";

interface HealthData {
  status: string;
  uptime_pct: number;
  latency_ms: number;
  cpu_load_pct: number;
  memory_usage_pct: number;
  services: {
    name: string;
    status: "healthy" | "degraded" | "down";
    latency: number;
    version: string;
  }[];
}

const LOAD_PROFILE_HEIGHTS = Array.from({ length: 40 }, (_, index) => {
  const wave = Math.sin(index * 1.7) * 28;
  const pulse = ((index * 17) % 31);
  return Math.round(Math.max(20, Math.min(98, 56 + wave + pulse)));
});

export default function SystemHealthPage() {
  const t = useTranslations("system_health");
  const tDash = useTranslations("dashboard");
  const translate = useTranslate();
  const apiUrl = useApiUrl();
  const [isClient, setIsClient] = useState(false);
  const [repairingId, setRepairingId] = useState<string | null>(null);
  const [repairResults, setRepairResults] = useState<Record<string, string>>({});

  useEffect(() => {
    setIsClient(true);
  }, []);

  const { query: healthQuery } = useCustom<any>({
    url: `${apiUrl}/health/dashboard`,
    method: "get",
    queryOptions: {
      enabled: isClient,
      refetchInterval: 5000,
    },
  });
  const { data: healthRaw, isLoading } = healthQuery;
  const { query: diagnosticsQuery } = useCustom<RuntimeDiagnosticsResponse>({
    url: `${apiUrl}/health/runtime-diagnostics`,
    method: "get",
    queryOptions: {
      enabled: isClient,
      refetchInterval: 10000,
    },
  });

  const health = healthRaw?.data || {};
  const diagnostics = diagnosticsQuery.data?.data?.diagnostics || [];

  const { query: queueQuery } = useCustom<any>({
    url: `${apiUrl}/health/queue-detailed`,
    method: "get",
    queryOptions: {
      enabled: isClient,
      refetchInterval: 3000,
    },
  });
  const queueData = queueQuery.data?.data || { status: "offline", concurrency: 2, active_workers: 0, queue_size: 0, stats: {} };

  const diagnosticTone = (item: RuntimeDiagnostic) => {
    if (item.severity === "error") return "border-red-500/20 bg-red-500/5 text-red-400";
    if (item.severity === "warning") return "border-amber-500/20 bg-amber-500/5 text-amber-400";
    return "border-cyan-500/20 bg-cyan-500/5 text-cyan-300";
  };

  const runRepair = async (item: RuntimeDiagnostic) => {
    setRepairingId(item.id);
    try {
      const result = await safeFetchJson<{ status: string; actions?: string[]; recommended_action?: string }>(
        `${apiUrl}/health/runtime-diagnostics/${item.id}/repair`,
        {
          method: "POST",
          body: "{}",
          useOfflineFallback: false,
        },
      );
      const summary = result.actions?.length
        ? `${result.status}: ${result.actions.join(", ")}`
        : result.recommended_action || result.status;
      setRepairResults((current) => ({ ...current, [item.id]: summary }));
      if (result.status === "repaired" || result.status === "noop") {
        message.success(`Runtime repair: ${summary}`);
      } else {
        message.warning(summary);
      }
      await diagnosticsQuery.refetch?.();
    } catch (err) {
      const detail = err instanceof Error ? err.message : "Repair failed";
      setRepairResults((current) => ({ ...current, [item.id]: detail }));
      message.error(detail);
    } finally {
      setRepairingId(null);
    }
  };

  const metrics = [
    { label: tDash("resilience.nodes.api"), val: "99.99%", status: tDash("resilience.status"), metric: `${health.api_latency_ms || 24}ms RT`, icon: <Globe size={24}/>, color: "text-blue-500" },
    { label: tDash("resilience.nodes.db"), val: "98.5%", status: tDash("resilience.status"), metric: "24 ACTIVE", icon: <Database size={24}/>, color: "text-green-500" },
    { label: tDash("resilience.nodes.cache"), val: "100%", status: tDash("resilience.status"), metric: "3.2GB MEM", icon: <Zap size={24}/>, color: "text-amber-500" },
    { label: tDash("resilience.nodes.vector"), val: tDash("resilience.synced"), status: tDash("resilience.status"), metric: "OPTIMIZED", icon: <Binary size={24}/>, color: "text-violet-500" },
    { label: tDash("resilience.nodes.cortex"), val: tDash("resilience.ready"), status: tDash("resilience.idle"), metric: "v14.02", icon: <HeartPulse size={24}/>, color: "text-rose-500" },
    { label: tDash("resilience.nodes.audit"), val: "14.2TB", status: tDash("resilience.ok"), metric: "92% FREE", icon: <ShieldCheck size={24}/>, color: "text-emerald-500" },
    { label: tDash("resilience.nodes.celery"), val: "8/8", status: tDash("resilience.status"), metric: "0 PENDING", icon: <Cpu size={24}/>, color: "text-indigo-500" },
    { label: tDash("resilience.nodes.security"), val: tDash("resilience.synced"), status: tDash("resilience.status"), metric: "GLOBAL", icon: <Fingerprint size={24}/>, color: "text-cyan-500" },
  ];

  return (
    <div className="min-h-screen bg-[#060a12] text-white p-4 lg:p-12 font-sans selection:bg-[var(--primary)] selection:text-black">
      {/* Header Area */}
      <header className="mb-12 flex flex-col lg:flex-row lg:items-end justify-between gap-8">
        <div className="space-y-4">
          <div className="flex items-center gap-4 text-[var(--primary)] mb-2">
            <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-[0_0_20px_rgba(102,252,241,0.1)]">
              <Activity size={28} className="animate-pulse" />
            </div>
            <div className="h-px w-12 bg-gradient-to-r from-[var(--primary)]/50 to-transparent" />
            <span className="text-[10px] font-black uppercase tracking-[0.5em] italic opacity-70">Infrastructure Pulse</span>
          </div>
          <h1 className="text-5xl lg:text-7xl font-black tracking-tighter italic uppercase text-white">
            Kernel <span className="text-[var(--primary)]">Health</span>
          </h1>
          <p className="text-gray-500 max-w-2xl text-lg font-medium leading-relaxed italic border-l-4 border-white/5 pl-6">
            {t("subtitle")}
          </p>
        </div>

        <div className="flex gap-4">
            <div className="glass-panel px-8 py-4 rounded-2xl border-white/5 bg-white/[0.02] flex items-center gap-6">
               <div className="flex flex-col items-end">
                  <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest italic">{t("uptime")}</span>
                  <span className="text-xl font-black text-green-500 italic">99.999%</span>
               </div>
               <div className="w-px h-8 bg-white/10" />
               <div className="flex flex-col items-end">
                  <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest italic">{t("version")}</span>
                  <span className="text-xl font-black text-[var(--primary)] italic">v4.12.0-S</span>
               </div>
            </div>
        </div>
      </header>

      <section className="mb-12 rounded-[2rem] border border-white/5 bg-white/[0.015] p-8 shadow-2xl">
        <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-[11px] font-black uppercase tracking-[0.4em] text-[var(--primary)]">
              Runtime Diagnostics
            </h2>
            <p className="mt-2 text-sm font-medium text-gray-500">
              Active runtime causes behind degraded health and safe repair boundaries.
            </p>
          </div>
          <Tag className="w-fit border-white/10 bg-white/5 font-black uppercase tracking-widest text-gray-300">
            {diagnostics.length} signals
          </Tag>
        </div>
        {diagnosticsQuery.isLoading ? (
          <Skeleton active paragraph={{ rows: 3 }} />
        ) : diagnostics.length === 0 ? (
          <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-5 text-sm font-bold text-emerald-400">
            No runtime diagnostics are currently active.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {diagnostics.map((item) => (
              <div key={item.id} className={`rounded-xl border p-5 ${diagnosticTone(item)}`}>
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-black uppercase tracking-widest">
                      {compactRuntimeDiagnosticLabel(item)}
                    </span>
                    {item.id === "observer_write_denied" && (
                      <Tooltip title="Permission Locked">
                        <Lock size={12} className="text-red-500/50" />
                      </Tooltip>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Tag className="m-0 border-current bg-transparent text-current">{item.severity}</Tag>
                    {item.auto_repairable ? (
                      <Tag className="m-0 border-cyan-400/20 bg-cyan-400/10 text-cyan-300">repairable</Tag>
                    ) : item.requires_operator_action ? (
                      <Tag className="m-0 border-amber-400/20 bg-amber-400/10 text-amber-300">operator action</Tag>
                    ) : null}
                  </div>
                </div>
                <p className="mb-3 text-sm font-semibold text-gray-200">{item.impact}</p>
                <p className="text-xs font-medium leading-relaxed text-gray-500">{item.recommended_action}</p>
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-600">
                    {repairResults[item.id] || (item.auto_repairable ? "Safe repair available" : "Manual operator action")}
                  </span>
                  {item.auto_repairable ? (
                    <Button
                      size="small"
                      type="default"
                      loading={repairingId === item.id}
                      onClick={() => void runRepair(item)}
                      className="border-cyan-400/20 bg-cyan-400/10 text-cyan-200"
                    >
                      Repair
                    </Button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Asenkron Kuyruk Gözlemlenebilirlik HUD'ı (Queue & Performance HUD) */}
      <section className="mb-12 rounded-[2rem] border border-white/5 bg-white/[0.015] p-8 shadow-2xl">
        <div className="mb-8 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[var(--primary)] shadow-[0_0_10px_rgba(102,252,241,0.6)] animate-ping" />
              <h2 className="text-[11px] font-black uppercase tracking-[0.4em] text-[var(--primary)]">
                Asenkron Kuyruk Gözlemlenebilirlik HUD'ı
              </h2>
            </div>
            <p className="mt-2 text-sm font-medium text-gray-500">
              SQLite-backed Huey JobQueue active workers, pending jobs, and autonomous incident consensus trigger.
            </p>
          </div>
          <Tag className={`w-fit border-white/10 font-black uppercase tracking-widest ${queueData.status === "online" ? "bg-green-500/10 text-green-400 border-green-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"}`}>
            {queueData.status === "online" ? "AKTİF" : "DEGRADED"}
          </Tag>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Worker Status Grid */}
          <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-white/[0.01] flex flex-col justify-between">
            <div className="mb-4">
              <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Aktif İşçiler (Workers)</span>
              <div className="mt-2 text-3xl font-black text-white italic">
                {queueData.active_workers} / {queueData.concurrency} <span className="text-xs font-mono font-bold text-gray-600">aktif</span>
              </div>
            </div>
            <div className="flex gap-2">
              {Array.from({ length: queueData.concurrency || 2 }).map((_, i) => (
                <div 
                  key={i} 
                  className={`flex-1 p-3 rounded-lg border text-center transition-all ${
                    i < queueData.active_workers 
                      ? "border-green-500/20 bg-green-500/5 text-green-400" 
                      : "border-white/5 bg-white/[0.01] text-gray-600"
                  }`}
                >
                  <Cpu size={16} className={`mx-auto mb-1 ${i < queueData.active_workers ? "animate-pulse text-green-400" : ""}`} />
                  <span className="text-[9px] font-black tracking-widest">W-{i+1}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Queue Size & Telemetry */}
          <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-white/[0.01] flex flex-col justify-between">
            <div className="mb-4">
              <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Kuyruk Boyutu & Biriken İşler</span>
              <div className="mt-2 text-3xl font-black text-amber-500 italic">
                {queueData.queue_size || 0} <span className="text-xs font-mono font-bold text-gray-600">bekleyen iş</span>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[9px] font-black text-gray-500 uppercase mb-1">
                <span>SQLite-Backed queue</span>
                <span>{queueData.backend || "inprocess"}</span>
              </div>
              <Progress 
                percent={Math.min(100, ((queueData.queue_size || 0) / 20) * 100)} 
                showInfo={false} 
                strokeColor="#f59e0b" 
                trailColor="rgba(255,255,255,0.05)" 
                size="small" 
              />
            </div>
          </div>

          {/* Autonomous Incident Consensus Widget */}
          <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-white/[0.01] flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Consensus Debate Trigger</span>
              <div className="mt-2 flex items-center gap-2 text-xl font-black text-emerald-400 italic">
                <Zap size={18} className="text-emerald-400 animate-bounce" />
                NOMİNAL <span className="text-[10px] font-bold text-gray-600 tracking-widest not-italic">AKTİF</span>
              </div>
            </div>
            <p className="text-[10px] font-bold text-gray-500 mt-2 leading-relaxed border-t border-white/5 pt-4">
              ⚡ Otonom anomali tespit motoru devrededir. Yeni bir olay yakalandığında tartışma konsensüsü otomatik tetiklenir.
            </p>
          </div>
        </div>
      </section>

      {/* Main Stats Grid */}
      <section className="grid grid-cols-1 lg:grid-cols-4 gap-8 mb-12">
        <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((node, i) => (
            <div 
              key={node.label} 
              className="group p-8 rounded-[2.5rem] border border-white/5 bg-white/[0.012] hover:bg-white/[0.03] hover:border-[var(--primary)]/30 transition-all flex flex-col justify-between h-56 shadow-xl relative overflow-hidden"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className={`absolute -top-8 -right-8 opacity-[0.02] group-hover:opacity-[0.08] transition-opacity duration-1000 ${node.color}`}>
                 {React.cloneElement(node.icon as any, { size: 120 })}
              </div>
              
              <div className="flex items-center justify-between relative z-10">
                  <div className="flex items-center gap-4">
                     <div className={`p-4 bg-black/40 rounded-2xl border border-white/5 group-hover:border-[var(--primary)]/20 transition-colors ${node.color}`}>
                        {node.icon}
                     </div>
                     <div className="flex flex-col gap-0.5">
                        <span className="text-[11px] font-black text-gray-500 uppercase tracking-tighter group-hover:text-white transition-colors">{node.label}</span>
                        <div className="flex items-center gap-2">
                           <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.6)]" />
                           <span className="text-[9px] font-black text-green-500 tracking-widest uppercase">{node.status}</span>
                        </div>
                     </div>
                  </div>
              </div>

              <div className="flex items-end justify-between relative z-10 pt-8 border-t border-white/[0.03]">
                  <div className="text-4xl font-black text-white tracking-tighter italic group-hover:text-[var(--primary)] transition-colors">{node.val}</div>
                  <div className="text-[10px] font-mono font-black text-gray-600 uppercase tracking-widest">{node.metric}</div>
              </div>
            </div>
          ))}
        </div>

        {/* System Load Panel */}
        <aside className="space-y-6">
           <div className="glass-panel p-8 rounded-[3rem] border-white/5 bg-white/[0.02] shadow-2xl space-y-8">
              <h3 className="text-[11px] font-black text-[var(--primary)] uppercase tracking-[0.4em] mb-4 italic flex items-center gap-3">
                <Layers size={14} />
                {t("resourceUsage")}
              </h3>
              
              <div className="space-y-6">
                 <div>
                    <div className="flex justify-between text-[11px] font-black uppercase tracking-tight italic mb-2">
                       <span className="text-gray-400">Compute Load</span>
                       <span className="text-white">42%</span>
                    </div>
                    <Progress percent={42} showInfo={false} strokeColor="var(--primary)" trailColor="rgba(255,255,255,0.05)" size={4} />
                 </div>
                 <div>
                    <div className="flex justify-between text-[11px] font-black uppercase tracking-tight italic mb-2">
                       <span className="text-gray-400">Memory Cluster</span>
                       <span className="text-white">68%</span>
                    </div>
                    <Progress percent={68} showInfo={false} strokeColor="#f59e0b" trailColor="rgba(255,255,255,0.05)" size={4} />
                 </div>
                 <div>
                    <div className="flex justify-between text-[11px] font-black uppercase tracking-tight italic mb-2">
                       <span className="text-gray-400">Network Latency</span>
                       <span className="text-white">12%</span>
                    </div>
                    <Progress percent={12} showInfo={false} strokeColor="#10b981" trailColor="rgba(255,255,255,0.05)" size={4} />
                 </div>
              </div>

              <div className="pt-6 border-t border-white/5">
                 <div className="flex items-center gap-3 p-4 bg-amber-500/5 border border-amber-500/20 rounded-2xl">
                    <AlertOctagon size={18} className="text-amber-500 animate-pulse" />
                    <span className="text-[10px] font-black text-amber-500 uppercase tracking-widest italic">Node-3 memory drift detected</span>
                 </div>
              </div>
           </div>

           <div className="glass-panel p-8 rounded-[3rem] border-white/5 bg-white/[0.02] shadow-xl flex items-center justify-between">
              <div className="flex items-center gap-4">
                 <div className="p-3 bg-blue-500/10 rounded-xl text-blue-500">
                    <Server size={20} />
                 </div>
                 <div>
                    <div className="text-[10px] font-black text-gray-600 uppercase tracking-widest italic">Global Nodes</div>
                    <div className="text-xl font-black text-white italic">12 / 12 <span className="text-green-500 text-xs ml-1">OK</span></div>
                 </div>
              </div>
              <ArrowUpRight size={20} className="text-gray-700" />
           </div>
        </aside>
      </section>

      {/* Advanced Telemetry Section (Placeholders for charts) */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         <div className="lg:col-span-2 glass-panel p-10 rounded-[3.5rem] border-white/5 bg-white/[0.01] shadow-2xl relative overflow-hidden group">
            <div className="flex items-center justify-between mb-10">
               <div>
                  <h3 className="text-[11px] font-black text-gray-500 uppercase tracking-[0.4em] italic mb-2">{t("telemetry.latencyTitle")}</h3>
                  <div className="flex items-center gap-4">
                     <div className="text-4xl font-black text-white italic tracking-tighter">14ms</div>
                     <Tag className="bg-green-500/10 border-green-500/20 text-green-500 font-black italic">-2.4ms Today</Tag>
                  </div>
               </div>
               <div className="flex gap-2">
                  <div className="p-2 bg-white/5 rounded-lg text-gray-600 hover:text-white transition-colors cursor-pointer">
                     <Timer size={18} />
                  </div>
                  <div className="p-2 bg-white/5 rounded-lg text-gray-600 hover:text-white transition-colors cursor-pointer">
                     <BarChart3 size={18} />
                  </div>
               </div>
            </div>
            
            <div className="h-64 w-full flex items-end gap-1 px-4 mb-4">
               {LOAD_PROFILE_HEIGHTS.map((height, i) => (
                  <div 
                    key={i} 
                    className="flex-1 bg-[var(--primary)] opacity-20 hover:opacity-100 transition-opacity rounded-t-sm" 
                    style={{ height: `${height}%` }}
                  />
               ))}
            </div>
            <div className="flex justify-between text-[9px] font-black text-gray-700 uppercase tracking-[0.3em] px-4">
               <span>00:00 UTC</span>
               <span>SYSTEM REAL-TIME LOAD PROFILE</span>
               <span>23:59 UTC</span>
            </div>
         </div>

         <div className="glass-panel p-10 rounded-[3.5rem] border-white/5 bg-white/[0.01] shadow-2xl">
            <h3 className="text-[11px] font-black text-gray-500 uppercase tracking-[0.4em] italic mb-8">{t("telemetry.recentIncidents")}</h3>
            <div className="space-y-6">
               {[
                  { time: "2m ago", type: "DB_SYNC", severity: "low", msg: "Replication lag exceeded 500ms" },
                  { time: "14m ago", type: "API_TIMEOUT", severity: "high", msg: "Worker-4 failed to respond in time" },
                  { time: "1h ago", type: "AUTH_GATED", severity: "med", msg: "Unauthorized access attempt from Node-X" },
                  { time: "4h ago", type: "KERNEL_UP", severity: "low", msg: "Kernel patch v4.11.9 deployed" },
               ].map((inc, i) => (
                  <div key={i} className="flex gap-4 group cursor-default">
                     <div className="flex flex-col items-center">
                        <div className={`w-2 h-2 rounded-full mt-1 ${inc.severity === 'high' ? 'bg-rose-500' : inc.severity === 'med' ? 'bg-amber-500' : 'bg-blue-500'} shadow-[0_0_10px_currentColor]`} />
                        <div className="w-px flex-1 bg-white/5 mt-2" />
                     </div>
                     <div className="flex-1 pb-6">
                        <div className="flex items-center justify-between mb-1">
                           <span className="text-[10px] font-black text-white uppercase tracking-tight italic">{inc.type}</span>
                           <span className="text-[9px] font-bold text-gray-700 italic">{inc.time}</span>
                        </div>
                        <p className="text-[11px] text-gray-500 font-bold leading-relaxed">{inc.msg}</p>
                     </div>
                  </div>
               ))}
            </div>
         </div>
      </section>
    </div>
  );
}
