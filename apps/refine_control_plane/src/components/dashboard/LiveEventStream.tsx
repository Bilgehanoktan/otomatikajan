"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Zap } from "lucide-react";
import { Skeleton } from "./Skeleton";
import { buildWebSocketCandidates } from "@/lib/runtime";
import { useTranslations } from "next-intl";
import { safeFetchJson } from "@/lib/api";
import { getStoredAccessToken } from "@/lib/auth";

interface SystemEvent {
  seq: number;
  timestamp: string;
  type: string;
  severity: "info" | "warning" | "critical";
  category: string;
  message: string;
}

const CATEGORY_FILTERS = [
  { key: "all", label: "all", icon: "" },
  { key: "alert", label: "Alert", icon: "⚠" },
  { key: "failover", label: "Failover", icon: "⚡" },
  { key: "repair", label: "Repair", icon: "🔧" },
  { key: "budget", label: "Budget", icon: "💰" },
  { key: "quorum", label: "Quorum", icon: "🗳" },
  { key: "governance", label: "Governance", icon: "🏦" },
  { key: "workflow", label: "Workflow", icon: "⚙" },
];

const SEV_STYLES: Record<string, { bg: string; text: string; border: string; label: string }> = {
  info:     { bg: "bg-[#66fcf1]/[0.08]",  text: "text-[#66fcf1]",  border: "border-l-[#66fcf1]/40", label: "INFO" },
  warning:  { bg: "bg-amber-500/[0.08]",   text: "text-amber-400",  border: "border-l-amber-400/50", label: "WARN" },
  critical: { bg: "bg-red-500/[0.12]",     text: "text-red-400",    border: "border-l-red-400/70",   label: "CRIT" },
};

export function LiveEventStream({ apiUrl, height }: { apiUrl: string, height?: string }) {
  const t = useTranslations("dashboard.telemetry");
  const [events, setEvents] = useState<SystemEvent[]>([]);
  const [filter, setFilter] = useState("all");
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "polling" | "offline">("connecting");
  const terminalRef = useRef<HTMLDivElement>(null);
  const lastSeqRef = useRef(0);
  const seenRef = useRef(new Set<number>());
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const MAX_WS_RETRIES = 5;

  const pushEvent = useCallback((ev: SystemEvent) => {
    if (seenRef.current.has(ev.seq) && ev.seq > 0) return;
    seenRef.current.add(ev.seq);
    if (seenRef.current.size > 500) {
      const arr = [...seenRef.current];
      arr.slice(0, 100).forEach((s) => seenRef.current.delete(s));
    }
    if (ev.seq > lastSeqRef.current) lastSeqRef.current = ev.seq;
    setEvents((prev) => {
      const next = [...prev, ev];
      return next.length > 200 ? next.slice(-200) : next;
    });
  }, []);

  useEffect(() => {
    let mounted = true;
    let reconnectTimer: ReturnType<typeof setTimeout>;
    const wsCandidates = buildWebSocketCandidates("/ws/events");

    function connect(candidateIndex = 0) {
      if (!mounted) return;
      if (reconnectCountRef.current >= MAX_WS_RETRIES) {
        setWsStatus("polling");
        return;
      }

      if (candidateIndex >= wsCandidates.length) {
        reconnectCountRef.current++;
        setWsStatus("polling");
        const delay = Math.min(3000 * Math.pow(2, reconnectCountRef.current - 1), 30000);
        reconnectTimer = setTimeout(() => connect(0), delay);
        return;
      }

      try {
        const wsUrl = wsCandidates[candidateIndex];
        const token = getStoredAccessToken();
        const finalWsUrl = token ? `${wsUrl}${wsUrl.includes("?") ? "&" : "?"}token=${token}` : wsUrl;
        
        console.debug(`[WS] Connecting to ${finalWsUrl}`);
        const ws = new WebSocket(finalWsUrl);
        wsRef.current = ws;


        const openTimeout = setTimeout(() => { if (ws.readyState !== WebSocket.OPEN) ws.close(); }, 8000);

        ws.onopen = () => {
          clearTimeout(openTimeout);
          if (!mounted) return;
          reconnectCountRef.current = 0;
          setWsStatus("connected");
          pushEvent({
            seq: -Date.now(), timestamp: new Date().toISOString(), type: "SYSTEM_INFO",
            severity: "info", category: "alert",
            message: t("connectionActive"),
          });
        };

        ws.onmessage = (e) => {
          try { pushEvent(JSON.parse(e.data) as SystemEvent); } catch { /* ignore malformed */ }
        };

        ws.onclose = () => {
          clearTimeout(openTimeout);
          if (!mounted) return;
          if (candidateIndex + 1 < wsCandidates.length) {
            connect(candidateIndex + 1);
            return;
          }
          reconnectCountRef.current++;
          setWsStatus("polling");
          const delay = Math.min(3000 * Math.pow(2, reconnectCountRef.current - 1), 30000);
          reconnectTimer = setTimeout(() => connect(0), delay);
        };

        ws.onerror = () => ws.close();
      } catch {
        connect(candidateIndex + 1);
      }
    }

    connect();
    return () => {
      mounted = false;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [pushEvent, t]);

  useEffect(() => {
    if (wsStatus === "connected") return;

    const timer = setInterval(async () => {
      try {
        const data = await safeFetchJson(
          `/health/events/stream?since_seq=${lastSeqRef.current}&limit=50`,
          { signal: AbortSignal.timeout(5000) }
        );
        (data.events || []).forEach((ev: SystemEvent) => pushEvent(ev));
      } catch { /* fail silently */ }
    }, 5000);
    return () => clearInterval(timer);
  }, [apiUrl, wsStatus, pushEvent]);

  useEffect(() => {
    const el = terminalRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    if (isNearBottom) el.scrollTop = el.scrollHeight;
  }, [events]);

  const filtered = filter === "all" ? events : events.filter((e) => e.category === filter);
  const isConnecting = wsStatus === "connecting" && events.length === 0;

  return (
    <div className="rounded-2xl border border-white/[0.05] bg-[#0b0c10]/80 overflow-hidden shadow-2xl backdrop-blur-3xl h-full flex flex-col transition-all duration-500 hover:border-white/[0.12]">
      {/* Header bar */}
      <div className="flex flex-wrap items-center gap-3 px-6 py-4 border-b border-white/[0.04] bg-black/40">
        <div className="flex items-center gap-2.5 mr-4">
          <div className="relative">
             <div className={`w-2 h-2 rounded-full ${
                wsStatus === "connected" ? "bg-[var(--primary)] shadow-[0_0_8px_var(--primary)]" :
                wsStatus === "offline"   ? "bg-red-400 shadow-[0_0_8px_rgba(244,63,94,0.4)]" : "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]"
              }`} style={{ animation: wsStatus !== "offline" ? "pulse-ring 2s infinite" : "none" }} />
          </div>
          <span className="text-[10px] font-black tracking-[0.25em] uppercase text-white font-mono">
            {t("title")}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto no-scrollbar">
          {CATEGORY_FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`text-[9px] font-bold tracking-[0.05em] uppercase px-2.5 py-1 rounded-lg border font-mono transition-all duration-300 ${
                filter === f.key
                  ? "bg-[var(--primary)]/10 border-[var(--primary)]/30 text-[var(--primary)] shadow-[0_0_12px_var(--primary-glow)]"
                  : "bg-transparent border-white/[0.05] text-[#4a5568] hover:border-white/10 hover:text-[#a0aec0]"
              }`}
            >
              {f.icon ? <span className="mr-1">{f.icon}</span> : ""}{f.key === "all" ? t("all") : t(`categories.${f.key}`)}
            </button>
          ))}
        </div>

        <div className={`ml-auto px-2.5 py-1 rounded-lg border text-[8px] font-black tracking-[0.1em] font-mono transition-colors duration-500 ${
          wsStatus === "connected" ? "bg-green-500/[0.08] text-green-400 border-green-500/15" :
          wsStatus === "offline"   ? "bg-red-500/[0.08] text-red-100 border-red-500/20" :
                                     "bg-amber-500/[0.08] text-amber-300 border-amber-500/15"
        }`}>
          {wsStatus === "connected" ? t("status.stable") : wsStatus === "connecting" ? t("status.sync") : wsStatus === "offline" ? t("status.lost") : t("status.fallback")}
        </div>
      </div>

      {/* Terminal */}
      <div
        ref={terminalRef}
        className="flex-1 min-h-[400px] overflow-y-auto px-4 py-5 font-mono text-[11px] leading-relaxed bg-black/40 scrollbar-premium"
      >
        {isConnecting ? (
          <div className="space-y-3 px-2">
            {[90, 70, 85, 60, 80, 50, 75].map((w, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-2.5 w-14" />
                <Skeleton className="h-4 w-10 rounded-md" />
                <Skeleton className="h-4 w-16 rounded-md" />
                <Skeleton className={`h-2.5 w-[${w}%] opacity-60`} />
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full opacity-30 grayscale gap-3">
            <Zap size={32} className="animate-pulse text-gray-500" />
            <span className="text-[10px] text-gray-400 font-mono tracking-[0.2em] uppercase">
              {wsStatus === "offline" ? t("connectionLost") : t("waitingEvents")}
            </span>
          </div>
        ) : (
          <div className="space-y-[3px]">
            {filtered.map((ev, i) => {
              const sev = SEV_STYLES[ev.severity] || SEV_STYLES.info;
              const ts = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString("tr-TR", { hour12: false }) : "--:--:--";
              const catIcon = CATEGORY_FILTERS.find((f) => f.key === ev.category)?.icon || "•";

              return (
                <div
                  key={`${ev.seq}-${i}`}
                  className={`flex items-start gap-4 py-1.5 px-4 rounded-xl border-l-[3px] transition-all duration-300 hover:bg-white/[0.03] group ${sev.border} ${
                    ev.severity === "critical" ? "bg-red-500/[0.02]" : ""
                  }`}
                >
                  <span className="text-[10px] text-gray-600 flex-shrink-0 min-w-[55px] font-medium">{ts}</span>
                  <span className={`text-[9px] font-black tracking-widest px-1.5 py-0.5 rounded-md flex-shrink-0 min-w-[36px] text-center shadow-sm ${sev.bg} ${sev.text}`}>
                    {sev.label}
                  </span>
                  <span className="text-[9px] font-bold tracking-widest px-1.5 py-0.5 rounded-md bg-white/[0.05] text-gray-500 flex-shrink-0 min-w-[70px] text-center uppercase border border-white/[0.02]">
                    {catIcon} {ev.category}
                  </span>
                  <span className={`flex-1 break-words transition-colors duration-300 ${
                    ev.severity === "critical" ? "text-red-300 font-semibold" :
                    ev.severity === "warning" ? "text-amber-300" : "text-gray-400 group-hover:text-gray-200"
                  }`}>
                    {ev.message}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
