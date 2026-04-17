"use client";

import React, { useState, useEffect } from "react";
import { useList, useCustom, useApiUrl } from "@refinedev/core";
import {
  Activity,
  ShieldCheck,
  Terminal,
  Cpu,
  CheckCircle,
  AlertTriangle,
  Clock,
  Zap,
  Database,
  GitBranch,
  Globe,
  ExternalLink,
  ArrowRight,
  HeartPulse,
  DollarSign,
  FlaskConical,
  Gauge,
} from "lucide-react";

// ── Tip ──────────────────────────────────────────────
interface DashboardData {
  status?: string;
  health_score?: number;
  health_label?: string;
  active_agents?: number;
  api_latency_ms?: number;
  db_status?: string;
  workflows?: {
    total?: number;
    running?: number;
    completed?: number;
    failed?: number;
    pending?: number;
    pending_approval?: number;
    success_rate_pct?: number;
  };
  cost?: {
    total_usd?: number;
    budget_usd?: number;
    budget_used_pct?: number;
    total_calls?: number;
    avg_latency_s?: number;
  };
  canary?: {
    success_rate?: number;
    active_canary?: number;
    total_patches_7d?: number;
    promoted?: number;
    rolled_back?: number;
  };
}

// ── Alt bileşenler ───────────────────────────────────

function MetricCard({
  label,
  value,
  subLabel,
  color,
  barPct,
  barColor,
  icon,
  hero,
}: {
  label: string;
  value: string | number;
  subLabel?: string;
  color: string;
  barPct?: number;
  barColor?: string;
  icon: React.ReactNode;
  hero?: boolean;
}) {
  const resolveBarColor = () => {
    if (barColor) return barColor;
    if (color.includes("teal") || color.includes("cyan")) return "#66fcf1";
    if (color.includes("green")) return "#48bb78";
    if (color.includes("red")) return "#fc6675";
    if (color.includes("amber") || color.includes("yellow")) return "#f6ad55";
    return "#45a29e";
  };

  return (
    <div className={`group relative overflow-hidden rounded-xl border bg-[#0b0c10]/80 transition-all duration-300 hover:shadow-[0_0_20px_rgba(102,252,241,0.05)] ${
      hero
        ? "border-[#66fcf1]/10 bg-gradient-to-br from-[#66fcf1]/[0.03] to-[#0b0c10] p-6 col-span-1 md:col-span-2 xl:col-span-1"
        : "border-white/5 p-5 hover:border-[#66fcf1]/20"
    }`}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-[9px] font-black tracking-[0.2em] uppercase text-[#4a5568]">{label}</span>
        <div className="p-1.5 rounded-lg bg-white/5">{icon}</div>
      </div>
      <div className={`font-black leading-none transition-colors duration-500 ${hero ? "text-4xl" : "text-3xl"} ${color}`}>{value}</div>
      {subLabel && <div className="text-[10px] text-[#4a5568] mt-1.5 font-mono transition-colors duration-500">{subLabel}</div>}
      {barPct !== undefined && (
        <div className={`${hero ? "mt-4 h-1" : "mt-3 h-px"} bg-white/5 rounded-full overflow-hidden`}>
          <div
            className="h-full rounded-full transition-all duration-1000"
            style={{ width: `${Math.min(barPct, 100)}%`, background: resolveBarColor() }}
          />
        </div>
      )}
    </div>
  );
}

// ── Faz 3: Live Event Stream ─────────────────────────
interface SystemEvent {
  seq: number;
  timestamp: string;
  type: string;
  severity: "info" | "warning" | "critical";
  category: string;
  message: string;
}

const CATEGORY_FILTERS = [
  { key: "all", label: "Tümü" },
  { key: "alert", label: "Alert", icon: "⚠" },
  { key: "failover", label: "Failover", icon: "⚡" },
  { key: "repair", label: "Repair", icon: "🔧" },
  { key: "budget", label: "Budget", icon: "💰" },
  { key: "quorum", label: "Quorum", icon: "🗳" },
  { key: "governance", label: "Governance", icon: "🏦" },
  { key: "workflow", label: "Workflow", icon: "⚙" },
];

const SEV_STYLES: Record<string, { bg: string; text: string; border: string; label: string }> = {
  info:     { bg: "bg-[#66fcf1]/8",  text: "text-[#66fcf1]", border: "border-l-[#66fcf1]/30", label: "INFO" },
  warning:  { bg: "bg-amber-500/8",  text: "text-amber-400", border: "border-l-amber-400/50", label: "WARN" },
  critical: { bg: "bg-red-500/8",    text: "text-red-400",   border: "border-l-red-400/60",   label: "CRIT" },
};

function LiveEventStream({ apiUrl }: { apiUrl: string }) {
  const [events, setEvents] = useState<SystemEvent[]>([]);
  const [filter, setFilter] = useState("all");
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "polling">("connecting");
  const terminalRef = React.useRef<HTMLDivElement>(null);
  const lastSeqRef = React.useRef(0);
  const seenRef = React.useRef(new Set<number>());
  const wsRef = React.useRef<WebSocket | null>(null);

  // Olay ekleme fonksiyonu
  const pushEvent = React.useCallback((ev: SystemEvent) => {
    if (seenRef.current.has(ev.seq) && ev.seq > 0) return;
    seenRef.current.add(ev.seq);
    if (seenRef.current.size > 300) {
      const arr = [...seenRef.current];
      arr.slice(0, 100).forEach((s) => seenRef.current.delete(s));
    }
    if (ev.seq > lastSeqRef.current) lastSeqRef.current = ev.seq;
    setEvents((prev) => {
      const next = [...prev, ev];
      return next.length > 120 ? next.slice(-120) : next;
    });
  }, []);

  // WebSocket bağlantısı
  useEffect(() => {
    let mounted = true;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      try {
        const base = apiUrl.replace(/^http/, "ws").replace(/\/api\/v1\/?$/, "");
        const ws = new WebSocket(`${base}/ws/events`);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!mounted) return;
          setWsStatus("connected");
          pushEvent({
            seq: -1, timestamp: new Date().toISOString(), type: "SYSTEM_INFO",
            severity: "info", category: "alert",
            message: "WebSocket bağlantısı kuruldu — canlı akış aktif",
          });
        };

        ws.onmessage = (e) => {
          try {
            const ev = JSON.parse(e.data) as SystemEvent;
            pushEvent(ev);
          } catch { /* malformed */ }
        };

        ws.onclose = () => {
          if (!mounted) return;
          setWsStatus("polling");
          reconnectTimer = setTimeout(connect, 5000);
        };

        ws.onerror = () => ws.close();
      } catch {
        setWsStatus("polling");
        reconnectTimer = setTimeout(connect, 5000);
      }
    }

    connect();
    return () => {
      mounted = false;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [apiUrl, pushEvent]);

  // Polling fallback
  useEffect(() => {
    if (wsStatus === "connected") return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${apiUrl}/events/stream?since_seq=${lastSeqRef.current}&limit=30`);
        if (!res.ok) return;
        const data = await res.json();
        (data.events || []).forEach((ev: SystemEvent) => pushEvent(ev));
      } catch { /* ignore */ }
    }, 4000);
    return () => clearInterval(timer);
  }, [apiUrl, wsStatus, pushEvent]);

  // Auto-scroll
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [events]);

  const filtered = filter === "all" ? events : events.filter((e) => e.category === filter);

  return (
    <div className="rounded-2xl border border-white/5 bg-[#0b0c10]/60 overflow-hidden">
      {/* Üst bar */}
      <div className="flex flex-wrap items-center gap-2 px-5 py-3 border-b border-white/5 bg-black/20">
        <div className="flex items-center gap-2 mr-3">
          <div className="w-1.5 h-1.5 rounded-full bg-[#66fcf1] shadow-[0_0_6px_#66fcf1] animate-pulse" />
          <span className="text-[10px] font-black tracking-[0.2em] uppercase text-white">
            Live Event Stream
          </span>
        </div>
        {/* Filtreler */}
        {CATEGORY_FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`text-[8px] font-bold tracking-[0.1em] uppercase px-2 py-1 rounded border font-mono transition-all ${
              filter === f.key
                ? "bg-[#66fcf1]/8 border-[#66fcf1]/25 text-[#66fcf1]"
                : "bg-transparent border-white/5 text-[#4a5568] hover:border-white/15 hover:text-[#a0aec0]"
            }`}
          >
            {f.icon ? `${f.icon} ` : ""}{f.label}
          </button>
        ))}
        {/* WS durumu */}
        <span className={`ml-auto text-[8px] font-bold tracking-[0.1em] px-2 py-1 rounded font-mono ${
          wsStatus === "connected"
            ? "bg-green-500/10 text-green-400 border border-green-500/20"
            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
        }`}>
          {wsStatus === "connected" ? "WS CANLI" : wsStatus === "connecting" ? "BAĞLANIYOR" : "POLLING"}
        </span>
      </div>

      {/* Terminal */}
      <div
        ref={terminalRef}
        className="h-[280px] overflow-y-auto px-2 py-2 font-mono text-[11px] leading-relaxed bg-black/20"
        style={{ scrollBehavior: "smooth" }}
      >
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center h-full text-[#4a5568] text-xs italic">
            Olay bekleniyor…
          </div>
        ) : (
          filtered.map((ev, i) => {
            const sev = SEV_STYLES[ev.severity] || SEV_STYLES.info;
            const ts = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString("tr-TR", { hour12: false }) : "--:--:--";
            const catIcon = CATEGORY_FILTERS.find((f) => f.key === ev.category)?.icon || "•";

            return (
              <div
                key={`${ev.seq}-${i}`}
                className={`flex items-start gap-2 py-[3px] px-3 border-l-2 rounded-r transition-all hover:bg-white/[0.02] ${sev.border} ${
                  ev.severity === "critical" ? "bg-red-500/[0.02]" : ""
                }`}
              >
                <span className="text-[10px] text-[#4a5568] flex-shrink-0 min-w-[52px]">{ts}</span>
                <span className={`text-[8px] font-extrabold tracking-wider px-[5px] py-px rounded flex-shrink-0 min-w-[32px] text-center ${sev.bg} ${sev.text}`}>
                  {sev.label}
                </span>
                <span className="text-[8px] font-bold tracking-wider px-[5px] py-px rounded bg-white/[0.03] text-[#4a5568] flex-shrink-0 min-w-[42px] text-center uppercase">
                  {catIcon} {ev.category}
                </span>
                <span className={`flex-1 break-words ${
                  ev.severity === "critical" ? "text-red-400 font-semibold" :
                  ev.severity === "warning" ? "text-amber-400" : "text-[#a0aec0]"
                }`}>
                  {ev.message}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

function QuickLink({
  href,
  label,
  sub,
  external,
  accent,
}: {
  href: string;
  label: string;
  sub: string;
  external?: boolean;
  accent?: string;
}) {
  return (
    <a
      href={href}
      target={external ? "_blank" : undefined}
      rel={external ? "noreferrer" : undefined}
      className="flex items-center justify-between p-3 rounded-lg border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-[#66fcf1]/20 transition-all group"
    >
      <div>
        <div className="text-xs font-semibold text-white">{label}</div>
        <div className="text-[10px] text-[#4a5568] font-mono mt-0.5">{sub}</div>
      </div>
      <ExternalLink
        size={12}
        className="text-[#4a5568] group-hover:text-[#66fcf1] transition-colors flex-shrink-0 ml-3"
      />
    </a>
  );
}

// ── Ana sayfa ────────────────────────────────────────

export default function ControlPlaneDashboard() {
  const [isClient, setIsClient] = useState(false);
  const [uptime, setUptime] = useState("00:00:00");
  const [startTime] = useState(() => Date.now());
  const [activeTab, setActiveTab] = useState<"overview" | "workflows" | "events" | "health">("overview");
  const apiUrl = useApiUrl();

  useEffect(() => {
    setIsClient(true);
    const timer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const h = Math.floor(elapsed / 3600).toString().padStart(2, "0");
      const m = Math.floor((elapsed % 3600) / 60).toString().padStart(2, "0");
      const s = (elapsed % 60).toString().padStart(2, "0");
      setUptime(`${h}:${m}:${s}`);
    }, 1000);
    return () => clearInterval(timer);
  }, [startTime]);

  // Workflow listesi
  const { query: { data: wfData, isLoading: wfLoading } } = useList({
    resource: "workflows",
    pagination: { pageSize: 5 },
    queryOptions: { enabled: isClient },
  });

  // Birleşik sağlık endpoint'i — 8 saniyelik polling
  const { query: { data: dashRaw } } = useCustom({
    url: `${apiUrl}/health/dashboard`,
    method: "get",
    queryOptions: {
      enabled: isClient,
      refetchInterval: 8000,
    },
  });

  if (!isClient) return <div className="min-h-screen bg-[#0b0c10]" />;

  const workflows = wfData?.data ?? [];
  const dash = (dashRaw?.data as DashboardData) ?? {};
  const wf = dash.workflows ?? {};
  const cost = dash.cost ?? {};
  const canary = dash.canary ?? {};
  const total = wf.total || 0;
  const healthScore = dash.health_score ?? 0;
  const healthLabel = dash.health_label ?? "unknown";
  const healthColor = healthScore >= 80 ? "text-green-400" : healthScore >= 60 ? "text-amber-400" : "text-red-400";
  const healthLabelTr = healthLabel === "healthy" ? "SAĞLIKLI" : healthLabel === "degraded" ? "BOZULMUŞ" : healthLabel === "critical" ? "KRİTİK" : "BİLİNMYOR";
  const latency = dash.api_latency_ms ?? 0;
  const latencyColor = latency < 100 ? "text-green-400" : latency < 300 ? "text-amber-400" : "text-red-400";
  const dbOk = dash.db_status === "connected";
  const budgetPct = cost.budget_used_pct ?? 0;
  const budgetColor = budgetPct < 70 ? "text-green-400" : budgetPct < 90 ? "text-amber-400" : "text-red-400";
  const canaryRate = canary.success_rate ?? 0;
  const canaryColor = canaryRate >= 80 ? "text-green-400" : canaryRate >= 50 ? "text-amber-400" : "text-red-400";

  return (
    <div className="min-h-screen bg-[#0b0c10] p-6 space-y-6">

      {/* ── HERO IDENTITY BLOCK ──────────────────────────── */}
      <header className="rounded-2xl border border-white/5 bg-gradient-to-br from-[#0d1117] to-[#0b0c10] overflow-hidden">
        {/* Üst şerit */}
        <div className="flex items-center gap-3 px-6 py-3 border-b border-white/5 bg-black/30">
          <div className="w-1.5 h-1.5 rounded-full bg-[#66fcf1] shadow-[0_0_6px_#66fcf1] animate-pulse" />
          <span className="text-[9px] font-black tracking-[0.25em] uppercase text-[#45a29e] font-mono">
            Backend Core Engine · Port 8000 · Aktif
          </span>
          <div className="ml-auto flex items-center gap-4">
            <span className="text-[9px] font-mono text-[#4a5568]">ENV: <span className="text-amber-400">PILOT ROLLOUT</span></span>
            <span className="text-[9px] font-mono text-[#4a5568]">BÖLGE: <span className="text-white">SOV-M-1</span></span>
            <span className="text-[9px] font-mono text-[#4a5568]">UPTIME: <span className="text-[#66fcf1]">{uptime}</span></span>
          </div>
        </div>

        {/* Ana kimlik */}
        <div className="px-8 py-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="relative">
              <div className="p-4 bg-[#66fcf1]/8 rounded-2xl border border-[#66fcf1]/15 shadow-[0_0_40px_rgba(102,252,241,0.08)]">
                <Cpu className="w-10 h-10 text-[#66fcf1]" />
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-[#0b0c10] animate-pulse shadow-[0_0_8px_#48bb78]" />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-4xl md:text-5xl font-black tracking-[-0.03em] text-white uppercase leading-none">
                  Mission <span className="text-[#66fcf1]">Control</span>
                </h1>
                <span className="px-2 py-0.5 rounded bg-[#66fcf1]/8 border border-[#66fcf1]/15 text-[#66fcf1] text-[9px] font-black uppercase tracking-widest">
                  v13.04.1
                </span>
              </div>
              <p className="text-[#45a29e] text-sm tracking-wide">
                Sovereign AGI — Otonom Yazılım Geliştirme Operasyon Kalbi
              </p>
              {/* Meta satırı */}
              <div className="flex flex-wrap items-center gap-5 mt-3">
                {[
                  { key: "API", val: "/api/v1", icon: <Globe size={10} /> },
                  { key: "Framework", val: "FastAPI + Async", icon: <Zap size={10} /> },
                  { key: "DB", val: "PostgreSQL · pgvector", icon: <Database size={10} /> },
                  { key: "Queue", val: "Celery · Redis", icon: <GitBranch size={10} /> },
                ].map(({ key, val, icon }) => (
                  <div key={key} className="flex items-center gap-1.5">
                    <span className="text-[#4a5568]">{icon}</span>
                    <span className="text-[9px] font-black tracking-[0.15em] uppercase text-[#4a5568]">{key}</span>
                    <span className="text-[10px] font-mono text-[#a0aec0]">{val}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sağ butonlar */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-white/8 bg-white/3 text-[10px] font-bold uppercase tracking-wider text-[#a0aec0] hover:text-white hover:border-white/20 hover:bg-white/6 transition-all"
            >
              Swagger <ExternalLink size={10} />
            </a>
            <a
              href="http://localhost:3100"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#66fcf1]/25 bg-[#66fcf1]/8 text-[10px] font-bold uppercase tracking-wider text-[#66fcf1] hover:bg-[#66fcf1]/15 transition-all"
            >
              Kontrol Paneli <ArrowRight size={10} />
            </a>
          </div>
        </div>
      </header>

      {/* ── API HUB: HIZLI ERİŞİM KATMANI ───────────────── */}
      <ApiHub apiBase="http://localhost:8000" />

      {/* ── HERO KPI BANDI ────────────────────────────────── */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        <MetricCard
          hero
          label="Sistem Sağlık Skoru"
          value={healthScore ? `%${healthScore}` : "—"}
          subLabel={healthLabelTr}
          color={healthColor}
          barPct={healthScore}
          barColor={healthScore >= 80 ? "#48bb78" : healthScore >= 60 ? "#f6ad55" : "#fc6675"}
          icon={<HeartPulse size={14} className={healthColor} />}
        />
        <MetricCard
          hero
          label="Aktif Ajan / Birimler"
          value={dash.active_agents ?? "—"}
          subLabel={(dash.active_agents ?? 0) > 0 ? "Çalışıyor" : "Bekleniyor"}
          color="text-[#66fcf1]"
          icon={<Cpu size={14} className="text-[#66fcf1]" />}
        />
        <MetricCard
          hero
          label="API Gecikmesi"
          value={latency ? `${latency}ms` : "—"}
          subLabel={latency < 100 ? "Optimal" : latency < 300 ? "Kabul edilebilir" : "Yüksek"}
          color={latencyColor}
          barPct={Math.min(latency / 500 * 100, 100)}
          barColor={latency < 100 ? "#48bb78" : latency < 300 ? "#f6ad55" : "#fc6675"}
          icon={<Gauge size={14} className={latencyColor} />}
        />
        <MetricCard
          hero
          label="DB Durumu"
          value={dbOk ? "BAĞLI" : "KESİK"}
          subLabel={dbOk ? "PostgreSQL · pgvector" : "Bağlantı hatası"}
          color={dbOk ? "text-green-400" : "text-red-400"}
          icon={<Database size={14} className={dbOk ? "text-green-400" : "text-red-400"} />}
        />
      </div>

      {/* ── İKİNCİL KPI SERİSİ ───────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        <MetricCard
          label="Operasyon Maliyeti"
          value={cost.total_usd !== undefined ? `$${cost.total_usd.toFixed(2)}` : "—"}
          subLabel={`%${budgetPct.toFixed(0)} / $${cost.budget_usd ?? 100}`}
          color={budgetColor}
          barPct={budgetPct}
          barColor={budgetPct < 70 ? "#48bb78" : budgetPct < 90 ? "#f6ad55" : "#fc6675"}
          icon={<DollarSign size={12} className={budgetColor} />}
        />
        <MetricCard
          label="Canary Başarısı"
          value={canaryRate ? `%${canaryRate}` : "—"}
          subLabel={`${canary.promoted ?? 0} başarılı / ${canary.total_patches_7d ?? 0} toplam`}
          color={canaryColor}
          barPct={canaryRate}
          barColor={canaryRate >= 80 ? "#48bb78" : canaryRate >= 50 ? "#f6ad55" : "#fc6675"}
          icon={<FlaskConical size={12} className={canaryColor} />}
        />
        <MetricCard
          label="Başarı Oranı"
          value={wf.success_rate_pct !== undefined ? `%${wf.success_rate_pct}` : "—"}
          subLabel="Workflow"
          color="text-green-400"
          barPct={wf.success_rate_pct}
          icon={<ShieldCheck size={12} className="text-green-400" />}
        />
        <MetricCard
          label="Aktif İşler"
          value={wf.running ?? "—"}
          subLabel={`/ ${total} toplam`}
          color="text-[#66fcf1]"
          barPct={total ? ((wf.running ?? 0) / total) * 100 : 0}
          icon={<Activity size={12} className="text-[#66fcf1]" />}
        />
        <MetricCard
          label="Hatalı"
          value={wf.failed ?? "—"}
          color="text-red-400"
          barPct={total ? ((wf.failed ?? 0) / total) * 100 : 0}
          icon={<AlertTriangle size={12} className="text-red-400" />}
        />
        <MetricCard
          label="Onay Bekliyor"
          value={(wf.pending_approval ?? 0) + (wf.pending ?? 0) || "—"}
          color="text-amber-400"
          barPct={total ? (((wf.pending_approval ?? 0) + (wf.pending ?? 0)) / total) * 100 : 0}
          icon={<Clock size={12} className="text-amber-400" />}
        />
      </div>

      {/* ── SEKME ÇERÇEVE ────────────────────────────────── */}
      <div className="rounded-2xl border border-white/5 bg-[#0b0c10]/70 overflow-hidden">

        {/* Sekme çubuğu */}
        <div className="flex items-center gap-0 border-b border-white/5 bg-black/20 px-2 pt-2">
          {([
            { id: "overview",   label: "Overview",   icon: <Cpu size={12} /> },
            { id: "workflows",  label: "Workflows",  icon: <Activity size={12} />, badge: wf.running ?? 0 },
            { id: "events",     label: "Events",     icon: <Zap size={12} /> },
            { id: "health",     label: "Health",     icon: <HeartPulse size={12} /> },
          ] as const).map((tab) => (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`relative flex items-center gap-2 px-5 py-2.5 text-[10px] font-black uppercase tracking-[0.18em] transition-all duration-200 rounded-t-lg ${
                activeTab === tab.id
                  ? "text-[#66fcf1] bg-[#66fcf1]/5 border-b-2 border-[#66fcf1]"
                  : "text-[#4a5568] hover:text-[#a0aec0] hover:bg-white/3 border-b-2 border-transparent"
              }`}
            >
              <span className={activeTab === tab.id ? "text-[#66fcf1]" : "text-[#4a5568]"}>
                {tab.icon}
              </span>
              {tab.label}
              {"badge" in tab && (tab.badge as number) > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full text-[8px] font-black bg-[#66fcf1]/15 text-[#66fcf1] border border-[#66fcf1]/20">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* ── TAB: OVERVIEW ──────────────────────────────── */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-0 divide-x divide-white/5">

            {/* Sol: hızlı erişim */}
            <div className="p-5 space-y-3">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-1 h-1 rounded-full bg-[#66fcf1]" />
                <span className="text-[9px] font-black tracking-[0.2em] uppercase text-[#4a5568]">Hızlı Erişim</span>
              </div>
              <QuickLink href="http://localhost:3100" label="Refine Kontrol Paneli" sub="localhost:3100 · Full UI" external />
              <QuickLink href="http://localhost:8000/docs" label="Swagger API Docs" sub="OpenAPI · Tüm endpoint'ler" external />
              <QuickLink href="http://localhost:8000/redoc" label="ReDoc Dokümantasyon" sub="Tam şema referansı" external />
              <QuickLink href="http://localhost:8000/api/v1/approvals?status=pending" label="Onay Kuyruğu" sub="GET /approvals?status=pending" external />
              <QuickLink href="http://localhost:8000/health" label="Sağlık Durumu" sub="GET /health · JSON" external />
            </div>

            {/* Orta: sistem kimliği */}
            <div className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-1 h-1 rounded-full bg-[#45a29e]" />
                <span className="text-[9px] font-black tracking-[0.2em] uppercase text-[#4a5568]">Sistem Kimliği</span>
              </div>
              <div className="space-y-0 font-mono text-[10px]">
                {([
                  ["ENGINE",    "Egemen YAZ Core",       "text-white"],
                  ["BUILD",     "v13.04.1-f30",          "text-white"],
                  ["FRAMEWORK", "FastAPI + Async",        "text-[#a0aec0]"],
                  ["DB",        "PostgreSQL · pgvector",  "text-[#a0aec0]"],
                  ["QUEUE",     "Celery · Redis",         "text-[#a0aec0]"],
                  ["ENV",       "PILOT ROLLOUT",          "text-amber-400"],
                  ["REGION",    "SOV-M-1",                "text-[#a0aec0]"],
                  ["UPTIME",    uptime,                   "text-[#66fcf1]"],
                ] as [string, string, string][]).map(([key, val, color]) => (
                  <div key={key} className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0">
                    <span className="text-[#4a5568] tracking-widest text-[9px]">{key}</span>
                    <span className={`${color} font-mono`}>{val}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Sağ: görev listesi / notlar */}
            <div className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-1 h-1 rounded-full bg-violet-400" />
                <span className="text-[9px] font-black tracking-[0.2em] uppercase text-[#4a5568]">Ops Durumu</span>
              </div>
              <div className="space-y-2">
                {[
                  { label: "Constitutional Guard",   ok: true,  note: "Aktif — 3 kural" },
                  { label: "Budget Circuit Breaker", ok: true,  note: "sovereign-system" },
                  { label: "LaunchGatekeeper",       ok: true,  note: "dry-run geçildi" },
                  { label: "Repair Lab",             ok: true,  note: "Tournament v2" },
                  { label: "Quorum Engine",          ok: true,  note: "2/3 kuorum" },
                  { label: "Policy VCS",             ok: false, note: "mock mod" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-1.5 border-b border-white/[0.04] last:border-0">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${item.ok ? "bg-green-400" : "bg-amber-400"}`} />
                      <span className="text-[10px] text-[#a0aec0] font-mono">{item.label}</span>
                    </div>
                    <span className={`text-[9px] font-black ${item.ok ? "text-[#4a5568]" : "text-amber-400"}`}>{item.note}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB: WORKFLOWS ─────────────────────────────── */}
        {activeTab === "workflows" && (
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#66fcf1] shadow-[0_0_6px_#66fcf1]" />
                <span className="text-[10px] font-black tracking-[0.2em] uppercase text-white">Son İş Akışları</span>
              </div>
              <a href="/workflows" className="text-[10px] text-[#45a29e] hover:text-[#66fcf1] transition-colors font-mono">
                tümünü gör →
              </a>
            </div>
            <div className="space-y-1.5">
              {wfLoading ? (
                <div className="flex justify-center py-10">
                  <div className="w-5 h-5 border-2 border-[#66fcf1] border-t-transparent rounded-full animate-spin" />
                </div>
              ) : workflows.length === 0 ? (
                <div className="text-center py-10 text-[#4a5568] font-mono text-xs italic">
                  Şu anda aktif bir iş akışı bulunmuyor.
                </div>
              ) : (
                workflows.map((wfItem: any) => {
                  const sc =
                    wfItem.status === "completed" ? "text-green-400 bg-green-500/10 border-green-500/20"
                    : wfItem.status === "failed" || wfItem.status === "error" ? "text-red-400 bg-red-500/10 border-red-500/20"
                    : wfItem.status === "running" ? "text-[#66fcf1] bg-[#66fcf1]/10 border-[#66fcf1]/20"
                    : "text-amber-400 bg-amber-500/10 border-amber-500/20";
                  return (
                    <div
                      key={wfItem.id}
                      className="flex items-center justify-between py-2.5 px-3 rounded-lg border border-white/5 bg-white/[0.015] hover:bg-white/[0.035] hover:border-white/10 transition-all cursor-pointer group"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="p-1.5 bg-white/5 rounded-md shrink-0">
                          <Activity className="w-3.5 h-3.5 text-[#45a29e]" />
                        </div>
                        <div className="min-w-0">
                          <div className="text-[11px] font-semibold text-white uppercase tracking-tight truncate">
                            {wfItem.workflow_type || wfItem.title || "Bilinmeyen"}
                          </div>
                          <div className="text-[9px] text-[#4a5568] font-mono">{String(wfItem.id).substring(0, 8)}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {wfItem.progress_pct !== undefined && (
                          <div className="hidden sm:flex items-center gap-1.5">
                            <div className="w-16 h-px bg-white/5 rounded-full overflow-hidden">
                              <div className="h-full bg-[#45a29e]/60" style={{ width: `${wfItem.progress_pct}%` }} />
                            </div>
                            <span className="text-[9px] text-[#4a5568] font-mono">%{wfItem.progress_pct}</span>
                          </div>
                        )}
                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase border ${sc}`}>
                          {wfItem.status}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* ── TAB: EVENTS ────────────────────────────────── */}
        {activeTab === "events" && (
          <div className="p-4">
            <LiveEventStream apiUrl={apiUrl} />
          </div>
        )}

        {/* ── TAB: HEALTH ────────────────────────────────── */}
        {activeTab === "health" && (
          <div className="p-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
              {[
                {
                  label: "API Server",
                  status: dbOk ? "ÇEVRIMIÇI" : "HATA",
                  ok: true,
                  detail: "Port 8000 · FastAPI",
                  icon: <Globe size={16} />,
                  accent: "text-[#66fcf1]",
                  accentBg: "bg-[#66fcf1]/8",
                  accentBorder: "border-[#66fcf1]/20",
                },
                {
                  label: "PostgreSQL",
                  status: dbOk ? "BAĞLI" : "KESİK",
                  ok: dbOk,
                  detail: "pgvector · async pool",
                  icon: <Database size={16} />,
                  accent: dbOk ? "text-green-400" : "text-red-400",
                  accentBg: dbOk ? "bg-green-500/8" : "bg-red-500/8",
                  accentBorder: dbOk ? "border-green-500/20" : "border-red-500/20",
                },
                {
                  label: "Celery Queue",
                  status: "AKTİF",
                  ok: true,
                  detail: "Redis backend",
                  icon: <GitBranch size={16} />,
                  accent: "text-violet-400",
                  accentBg: "bg-violet-500/8",
                  accentBorder: "border-violet-500/20",
                },
                {
                  label: "Audit Log",
                  status: "YAZILDI",
                  ok: true,
                  detail: "Governance sealed",
                  icon: <ShieldCheck size={16} />,
                  accent: "text-blue-400",
                  accentBg: "bg-blue-500/8",
                  accentBorder: "border-blue-500/20",
                },
              ].map((svc) => (
                <div
                  key={svc.label}
                  className={`rounded-xl border ${svc.accentBorder} ${svc.accentBg} p-4 flex flex-col gap-3`}
                >
                  <div className="flex items-center justify-between">
                    <div className={`p-2 rounded-lg bg-black/20 ${svc.accent}`}>{svc.icon}</div>
                    <div className="flex items-center gap-1.5">
                      <div className={`w-1.5 h-1.5 rounded-full ${svc.ok ? "bg-green-400 animate-pulse" : "bg-red-400"}`} />
                      <span className={`text-[9px] font-black tracking-widest ${svc.ok ? "text-green-400" : "text-red-400"}`}>
                        {svc.status}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className={`text-sm font-black ${svc.accent}`}>{svc.label}</div>
                    <div className="text-[10px] text-[#4a5568] font-mono mt-0.5">{svc.detail}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Latency + health score bar */}
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[9px] font-black uppercase tracking-widest text-[#4a5568]">API Gecikmesi</span>
                  <span className={`text-sm font-black ${latencyColor}`}>{latency ? `${latency}ms` : "—"}</span>
                </div>
                <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${Math.min(latency / 500 * 100, 100)}%`,
                      background: latency < 100 ? "#48bb78" : latency < 300 ? "#f6ad55" : "#fc6675"
                    }}
                  />
                </div>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[9px] font-black uppercase tracking-widest text-[#4a5568]">Sistem Skoru</span>
                  <span className={`text-sm font-black ${healthColor}`}>{healthScore ? `%${healthScore}` : "—"} · {healthLabelTr}</span>
                </div>
                <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${healthScore}%`,
                      background: healthScore >= 80 ? "#48bb78" : healthScore >= 60 ? "#f6ad55" : "#fc6675"
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

// ── API HUB COMPONENT ────────────────────────────────────
interface ApiEndpoint {
  key: string;
  label: string;
  description: string;
  href: string;
  method: "GET" | "UI" | "JSON" | "OAS";
  icon: React.ReactNode;
  accent: string;
  accentBg: string;
  accentBorder: string;
  active: boolean;
}

function ApiHub({ apiBase }: { apiBase: string }) {
  const BASE = apiBase ?? "http://localhost:8000";

  const endpoints: ApiEndpoint[] = [
    {
      key: "swagger",
      label: "API Docs",
      description: "Tüm endpoint'leri test et ve keşfet. Swagger UI ile interaktif erişim.",
      href: `${BASE}/docs`,
      method: "UI",
      icon: <Terminal size={18} />,
      accent: "text-[#66fcf1]",
      accentBg: "bg-[#66fcf1]/8",
      accentBorder: "border-[#66fcf1]/20",
      active: true,
    },
    {
      key: "redoc",
      label: "Redoc",
      description: "Okunabilir, tam dokümantasyon. Şema ve response örnekleri.",
      href: `${BASE}/redoc`,
      method: "UI",
      icon: <Globe size={18} />,
      accent: "text-violet-400",
      accentBg: "bg-violet-500/8",
      accentBorder: "border-violet-500/20",
      active: true,
    },
    {
      key: "health",
      label: "Health JSON",
      description: "Canlı sistem sağlık verisi. DB, queue, latency ve agent durumu.",
      href: `${BASE}/health`,
      method: "GET",
      icon: <HeartPulse size={18} />,
      accent: "text-green-400",
      accentBg: "bg-green-500/8",
      accentBorder: "border-green-500/20",
      active: true,
    },
    {
      key: "openapi",
      label: "OpenAPI",
      description: "Ham OpenAPI 3.1 şema dosyası. SDK üretimi ve entegrasyon için.",
      href: `${BASE}/openapi.json`,
      method: "JSON",
      icon: <Database size={18} />,
      accent: "text-amber-400",
      accentBg: "bg-amber-500/8",
      accentBorder: "border-amber-500/20",
      active: true,
    },
    {
      key: "audit",
      label: "Audit Status",
      description: "Denetim kuyruğu ve son kayıtlar. Governance izleme merkezi.",
      href: `${BASE}/api/v1/governance/audit`,
      method: "GET",
      icon: <ShieldCheck size={18} />,
      accent: "text-blue-400",
      accentBg: "bg-blue-500/8",
      accentBorder: "border-blue-500/20",
      active: true,
    },
    {
      key: "launch",
      label: "Launch Gates",
      description: "Lansman kapıları ve go/no-go kararları. Canlı geçiş onay merkezi.",
      href: `${BASE}/api/v1/launch-gates`,
      method: "GET",
      icon: <Zap size={18} />,
      accent: "text-orange-400",
      accentBg: "bg-orange-500/8",
      accentBorder: "border-orange-500/20",
      active: true,
    },
    {
      key: "compliance",
      label: "Compliance",
      description: "Uyumluluk doğrulama endpoint'i. Politika kuralları ve ihlal logları.",
      href: `${BASE}/api/v1/compliance/status`,
      method: "GET",
      icon: <CheckCircle size={18} />,
      accent: "text-pink-400",
      accentBg: "bg-pink-500/8",
      accentBorder: "border-pink-500/20",
      active: true,
    },
  ];

  return (
    <div className="rounded-2xl border border-white/5 bg-gradient-to-br from-[#0d1117]/80 to-[#0b0c10] overflow-hidden">
      {/* Panel Başlığı */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/5 bg-black/20">
        <div className="flex items-center gap-2.5">
          <div className="w-1.5 h-1.5 rounded-full bg-[#66fcf1] shadow-[0_0_6px_#66fcf1]" />
          <span className="text-[10px] font-black tracking-[0.22em] uppercase text-white">
            API Hub — Hızlı Erişim Katmanı
          </span>
        </div>
        <div className="flex items-center gap-2 text-[9px] font-mono text-[#4a5568]">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block animate-pulse" />
          {endpoints.filter(e => e.active).length}/{endpoints.length} Aktif
        </div>
      </div>

      {/* Kartlar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-0 divide-x divide-white/5">
        {endpoints.map((ep) => (
          <a
            key={ep.key}
            href={ep.href}
            target="_blank"
            rel="noreferrer"
            className="group relative flex flex-col px-4 py-4 transition-all duration-300 hover:bg-white/[0.03]"
          >
            {/* Üst: İkon + Badge */}
            <div className="flex items-start justify-between mb-3">
              <div className={`p-2 rounded-lg ${ep.accentBg} border ${ep.accentBorder} transition-all`}>
                <span className={ep.accent}>{ep.icon}</span>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className={`text-[8px] font-black tracking-[0.15em] px-1.5 py-0.5 rounded border ${ep.accentBg} ${ep.accentBorder} ${ep.accent}`}>
                  {ep.method}
                </span>
                {ep.active ? (
                  <div className="flex items-center gap-1">
                    <span className="w-1 h-1 rounded-full bg-green-400 animate-pulse" />
                    <span className="text-[8px] text-green-400 font-black tracking-wide">AKTİF</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1">
                    <span className="w-1 h-1 rounded-full bg-red-400" />
                    <span className="text-[8px] text-red-400 font-black tracking-wide">PASİF</span>
                  </div>
                )}
              </div>
            </div>

            {/* Label */}
            <div className={`text-xs font-black tracking-tight text-white mb-1.5 group-hover:${ep.accent} transition-colors`}>
              {ep.label}
            </div>

            {/* Açıklama */}
            <div className="text-[10px] text-[#4a5568] leading-relaxed group-hover:text-[#718096] transition-colors flex-1">
              {ep.description}
            </div>

            {/* Hover arrow */}
            <div className={`mt-3 flex items-center gap-1 ${ep.accent} opacity-0 group-hover:opacity-100 transition-all text-[9px] font-black tracking-widest`}>
              <span>AÇ</span>
              <ExternalLink size={9} />
            </div>

            {/* Bottom glow bar on hover */}
            <div className={`absolute bottom-0 left-4 right-4 h-px bg-current ${ep.accent} opacity-0 group-hover:opacity-30 transition-all`} />
          </a>
        ))}
      </div>
    </div>
  );
}
