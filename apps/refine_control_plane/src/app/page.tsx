"use client";

import React, { useState, useEffect } from "react";
import { useList, useCustom, useApiUrl } from "@refinedev/core";
import {
  Activity,
  ShieldCheck,
  Cpu,
  HeartPulse,
  DollarSign,
  FlaskConical,
  Gauge,
  Database,
  ArrowRight,
  Zap,
  Globe,
  Binary,
  RotateCcw,
  LayoutDashboard,
  ZapOff,
  Terminal,
  Server,
  Fingerprint,
  Layers,
  GitBranch,
  AlertOctagon
} from "lucide-react";

// MODÜLER BİLEŞENLER
import { MetricCard } from "@/components/dashboard/MetricCard";
import { LiveEventStream } from "@/components/dashboard/LiveEventStream";
import { ApiHub } from "@/components/dashboard/ApiHub";
import { DashboardCommandPanel } from "@/components/dashboard/DashboardCommandPanel";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { LaunchEvidencePanel } from "../components/dashboard/LaunchEvidencePanel";
import { EvolutionTimeline } from "../components/dashboard/EvolutionTimeline";

interface DashboardData {
  health_score?: number;
  health_label?: string;
  active_agents?: number;
  api_latency_ms?: number;
  db_status?: string;
  status?: string;
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
  };
  canary?: {
    success_rate?: number;
    promoted?: number;
    total_patches_7d?: number;
  };
  governance?: {
    rollout_ready?: boolean;
    constitutional_locks?: boolean;
    quorum_status?: string;
    pending_approvals?: number;
  };
}

export default function ControlPlaneDashboard() {
  const [isClient, setIsClient] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "workflows" | "events" | "health" | "economy">("overview");
  const apiUrl = useApiUrl();

  useEffect(() => { setIsClient(true); }, []);

  // API Veri Çekme (Health Dashboard)
  const { query: { data: dashRaw, isLoading: dashLoading } } = useCustom({
    url: `${apiUrl}/health/dashboard`,
    method: "get",
    queryOptions: {
      enabled: isClient,
      refetchInterval: 8000,
      keepPreviousData: true,
    },
  });

  // Evolution Data
  const { query: { data: evoRaw } } = useCustom({
    url: `${apiUrl}/health/evolution`,
    method: "get",
    queryOptions: {
      enabled: isClient,
      refetchInterval: 15000,
      keepPreviousData: true,
    },
  });

  // İş Akışları
  const { query: { data: wfData } } = useList({
    resource: "workflows",
    pagination: { pageSize: 6 },
    queryOptions: { enabled: isClient },
  });

  const dash = (dashRaw?.data as DashboardData) || {};
  const evolutionEvents = (evoRaw?.data as any[]) || [];
  const workflows = wfData?.data || [];
  const wfStats = dash.workflows || {};
  
  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  const healthScore = dash.health_score ?? 0;
  const healthColor = healthScore >= 80 ? "text-green-400" : healthScore >= 60 ? "text-amber-400" : "text-red-400";
  const healthBg = healthScore >= 80 ? 'from-green-500/[0.05]' : healthScore >= 60 ? 'from-amber-500/[0.05]' : 'from-red-500/[0.05]';
  const latency = dash.api_latency_ms ?? 0;
  const budgetPct = dash.cost?.budget_used_pct ?? 0;

  return (
    <div className="min-h-screen bg-[#060a12] p-8 space-y-12 animate-in fade-in duration-1000 overflow-x-hidden pb-40">
      
      {/* ── BÖLÜM 1: ELITE MISSION STATUS HERO ──────────────────── */}
      <section className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        <div className="xl:col-span-8 flex flex-col justify-center space-y-8 relative">
           {/* Decor */}
           <div className="absolute -top-10 -left-10 w-40 h-40 bg-[var(--primary)]/5 blur-[100px] pointer-events-none" />
           
           <div className="flex items-center gap-6 relative z-10">
              <div className="px-5 py-2 rounded-2xl bg-black/40 border border-white/5 flex items-center gap-3">
                 <div className="w-2 h-2 rounded-full bg-[var(--primary)] shadow-[0_0_10px_var(--primary)] animate-pulse" />
                 <span className="text-[10px] font-black text-white uppercase tracking-[0.3em] font-mono italic">Egemen Motoru v14.02</span>
              </div>
              <div className="flex items-center gap-3 py-2 px-5 rounded-2xl bg-white/[0.02] border border-white/5">
                 <Globe size={14} className="text-gray-600" />
                 <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">
                    Şebeke Durumu: {dash.status === 'online' ? 'SENKRONİZE' : 'BAĞLANTI_KESİLDİ'}
                 </span>
              </div>
           </div>

           <div className="space-y-4">
              <h1 className="text-7xl xl:text-8xl font-black text-white tracking-tighter leading-[0.85] italic">
                MİSYON <span className="bg-gradient-to-r from-[var(--primary)] to-blue-500 bg-clip-text text-transparent decoration-[var(--primary)] underline-offset-8">KONTROL</span>
              </h1>
              <p className="text-gray-500 max-w-2xl text-base font-medium leading-relaxed uppercase tracking-tighter opacity-80 decoration-1 underline underline-offset-4 decoration-white/5">
                Egemen YAZ AGI İskeleti için Merkezi Otonom Yönetişim Üssü. 
                Her şey gözlemlenebilir. Her şey yönetişim altında.
              </p>
           </div>

           <div className="flex items-center gap-8 pt-4">
              <div className="flex items-center gap-4 py-3 px-6 bg-white/[0.015] border border-white/[0.03] rounded-3xl group cursor-pointer hover:border-[var(--primary)]/20 transition-all">
                 <div className="flex -space-x-3">
                    {[1,2,3,4].map(i => (
                       <div key={i} className="w-10 h-10 rounded-full border-4 border-[#060a12] bg-black shadow-xl flex items-center justify-center overflow-hidden">
                          <img src={`https://api.dicebear.com/7.x/bottts/svg?seed=${i}&backgroundColor=060a12`} alt="Operator" className="w-full h-full p-1" />
                       </div>
                    ))}
                 </div>
                 <div className="flex flex-col">
                    <span className="text-[10px] font-black text-white uppercase tracking-widest">Aktif Quorum</span>
                    <span className="text-[9px] font-bold text-gray-600 uppercase tracking-widest mt-1 italic">4 ONAYLI DÜĞÜM</span>
                 </div>
              </div>
              
              <div className="flex items-center gap-4 py-3 px-6 bg-[var(--primary)]/10 border border-[var(--primary)]/20 rounded-3xl">
                 <Fingerprint size={20} className="text-[var(--primary)]" />
                 <div className="flex flex-col">
                    <span className="text-[10px] font-black text-[var(--primary)] uppercase tracking-widest italic">Sistem Bütünlüğü</span>
                    <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mt-1">MÜHÜRLÜ / DOĞRULANDI</span>
                 </div>
              </div>
           </div>
        </div>

        {/* Neural Vitality Card */}
        <div className="xl:col-span-4 h-full">
            <div className={`glass-panel p-10 rounded-[3rem] border-white/[0.04] bg-gradient-to-br ${healthBg} to-transparent relative overflow-hidden group shadow-2xl h-full flex flex-col justify-between`}>
                <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity duration-1000">
                   <HeartPulse size={200} className={healthColor} />
                </div>

                <div className="relative z-10 flex flex-col h-full justify-between">
                    <div className="flex items-center justify-between">
                        <div className="flex flex-col gap-1">
                           <span className="text-[11px] font-black text-white uppercase tracking-[0.3em] font-mono italic">Nöral Çekirdek Durumu</span>
                           <span className="text-[8px] font-black text-gray-600 uppercase tracking-[0.5em]">{dash.health_label || "STABİL"} EŞİK ÜSTÜ</span>
                        </div>
                        <div className={`p-4 bg-black/40 rounded-2xl border border-white/5 shadow-inner ${healthColor}`}>
                           <HeartPulse size={24} className="animate-pulse" />
                        </div>
                    </div>

                    <div className="mt-10">
                        <div className={`text-9xl font-black tracking-tighter ${healthColor} italic drop-shadow-[0_0_30px_rgba(255,255,255,0.05)]`}>
                            {healthScore}<span className="text-4xl ml-2">%</span>
                        </div>
                        <div className="w-full h-2 bg-black/40 rounded-full mt-6 overflow-hidden border border-white/[0.03]">
                           <div className={`h-full transition-all duration-1000 ${healthColor.replace('text', 'bg')}`} style={{ width: `${healthScore}%` }} />
                        </div>
                    </div>

                    <div className="mt-10 pt-10 border-t border-white/[0.03] flex items-center justify-between">
                        <div className="flex flex-col gap-1">
                            <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Ağ Gecikmesi</span>
                            <span className="text-lg font-black text-white font-mono tracking-tighter italic">{latency} MS</span>
                        </div>
                        <div className="flex flex-col items-end gap-1 text-right">
                            <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Global Çalışma Süresi</span>
                            <span className="text-lg font-black text-[var(--primary)] font-mono tracking-tighter italic">99.98% NOMİNAL</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
      </section>

      {/* ── BÖLÜM 2: ANA KPI BANDI ───────────────────────── */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-8">
        <EliteMetricItem
          label="Aktif Izgara Birimleri"
          value={dash.active_agents ?? "—"}
          subLabel="Otonom Ajanlar Çevrimiçi"
          color="text-[var(--primary)]"
          icon={<Cpu size={20} />}
          loading={dashLoading}
          accent="bg-[var(--primary)]/10"
        />
        <EliteMetricItem
          label="İş Akışı Güvenilirliği"
          value={`%${wfStats.success_rate_pct ?? 0}`}
          subLabel={`${wfStats.completed ?? 0} Tamamlandı`}
          color="text-green-500"
          icon={<ShieldCheck size={20} />}
          loading={dashLoading}
          accent="bg-green-500/10"
        />
        <EliteMetricItem
          label="Ekonomik Yük"
          value={`$${dash.cost?.total_usd?.toFixed(0) ?? 0}`}
          subLabel={`%${budgetPct} Limit Kullanıldı`}
          color={budgetPct > 80 ? "text-amber-500" : "text-gray-300"}
          icon={<DollarSign size={20} />}
          loading={dashLoading}
          accent="bg-amber-500/10"
          bar={budgetPct}
        />
        <EliteMetricItem
          label="Bilimsel Güven"
          value={`%${dash.canary?.success_rate ?? 0}`}
          subLabel={`${dash.canary?.promoted ?? 0} Yamalı Evrim`}
          color="text-violet-500"
          icon={<FlaskConical size={20} />}
          loading={dashLoading}
          accent="bg-violet-500/10"
        />
      </section>

      {/* ── BÖLÜM 3: COMMAND & STREAM HUB ────────────────────── */}
      <section className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        <div className="xl:col-span-4 h-full">
            <DashboardCommandPanel apiBase={apiUrl} />
        </div>
        <div className="xl:col-span-8 h-full">
            <LiveEventStream apiUrl={apiUrl} />
        </div>
      </section>

      {/* ── BÖLÜM 4: MISSION OPERATIONS COMMANDER ────────────── */}
      <section className="glass-panel rounded-[3.5rem] overflow-hidden flex flex-col min-h-[600px] border-white/[0.04] bg-[#0b0c10]/40 shadow-[0_32px_128px_rgba(0,0,0,0.4)]">
          
          {/* Tab Navigation Elite */}
          <div className="flex items-center gap-0 border-b border-white/[0.03] bg-black/40 px-10 pt-4 custom-scrollbar overflow-x-auto">
              {[
                { id: "overview",  label: "ÇEKİRDEK DURUMU", icon: <LayoutDashboard size={16} /> },
                { id: "workflows", label: "ORKESTRASYON", icon: <Binary size={16} />, badge: wfStats.running || 0 },
                { id: "events",    label: "TELEMETRİ", icon: <Zap size={16} /> },
                { id: "health",    label: "DİRENÇ", icon: <ShieldCheck size={16} /> },
                { id: "economy",   label: "FİNANS", icon: <DollarSign size={16} /> },
              ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`relative flex items-center gap-3 px-10 py-6 text-[11px] font-black uppercase tracking-[0.3em] transition-all duration-500 border-r border-white/[0.02] last:border-0 ${
                        activeTab === tab.id 
                        ? "text-[var(--primary)] bg-[var(--primary)]/[0.03] italic"
                        : "text-gray-600 hover:text-gray-300 hover:bg-white/[0.01]"
                    }`}
                  >
                      <span className={activeTab === tab.id ? "text-[var(--primary)] scale-110" : "text-gray-700 opacity-60"}>{tab.icon}</span>
                      {tab.label}
                      {tab.badge !== undefined && tab.badge > 0 && (
                          <span className="ml-3 px-2 py-0.5 rounded bg-[var(--primary)]/10 text-[var(--primary)] text-[9px] border border-[var(--primary)]/20 font-mono italic">
                              {tab.badge}
                          </span>
                      )}
                      {activeTab === tab.id && (
                          <div className="absolute bottom-0 left-0 w-full h-1 bg-[var(--primary)] shadow-[0_-5px_20px_var(--primary)]" />
                      )}
                  </button>
              ))}
          </div>

          <div className="flex-1 p-12">
              {activeTab === "overview" && (
                <div className="space-y-12">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
                      
                      {/* Left: Quick Access Hub */}
                      <div className="space-y-8">
                          <h3 className="text-[11px] font-black uppercase tracking-[0.4em] text-gray-600 px-2 italic border-l-2 border-[var(--primary)]">Geçit Erişimi</h3>
                          <div className="grid grid-cols-1 gap-4">
                              {[
                                  { label: "Refine Komuta Merkezi", sub: "localhost:3100", href: "http://localhost:3100", icon: <ArrowRight size={14}/> },
                                  { label: "Egemen API Dokümanları", sub: "FastAPI Prodüksiyon v1", href: `${apiUrl}/docs`, icon: <Terminal size={14}/> },
                                  { label: "Telemetri Kayıtları", sub: "S-SEVİYE JSON Akışı", href: `${apiUrl}/health`, icon: <Activity size={14}/> },
                              ].map(link => (
                                  <a key={link.label} href={link.href} target="_blank" className="flex items-center justify-between p-6 rounded-[2rem] border border-white/5 bg-white/[0.01] hover:bg-[var(--primary)]/[0.03] hover:border-[var(--primary)]/30 transition-all group shadow-lg">
                                      <div className="flex items-center gap-5">
                                          <div className="p-3 bg-black/40 rounded-xl border border-white/5 text-gray-700 group-hover:text-[var(--primary)] transition-colors">
                                             {link.icon}
                                          </div>
                                          <div>
                                              <div className="text-[12px] font-black text-white uppercase tracking-tight italic">{link.label}</div>
                                              <div className="text-[9px] text-gray-600 mt-1 font-mono uppercase opacity-50">{link.sub}</div>
                                          </div>
                                      </div>
                                      <div className="text-gray-700 group-hover:text-[var(--primary)] transition-all group-hover:translate-x-1"><ArrowRight size={16}/></div>
                                  </a>
                              ))}
                          </div>
                      </div>

                      {/* Middle: Governance Quorum & Decisions */}
                      <div className="space-y-8">
                          <h3 className="text-[11px] font-black uppercase tracking-[0.4em] text-gray-600 px-2 italic border-l-2 border-amber-500">Otonom Yönetişim</h3>
                          <div className="space-y-4">
                              {[
                                  { label: "Anayasal Güvenlik Kilitleri", val: dash.governance?.constitutional_locks ? "DEVREDE" : "ÇEVRİMDIŞI", ok: dash.governance?.constitutional_locks },
                                  { label: "Bütçesel Devre Kesici", val: budgetPct > 90 ? "LİMİT-ÜSTÜ" : "KİLİTLİ", ok: budgetPct <= 90 },
                                  { label: "Stratejik Karar Şeceresi", val: "MÜHÜRLÜ_V3", ok: true },
                              ].map(item => (
                                  <div key={item.label} className="p-6 rounded-[2rem] border border-white/5 bg-white/[0.012] flex items-center justify-between group hover:bg-white/[0.025] transition-all">
                                      <span className="text-[11px] font-black text-gray-500 uppercase tracking-tight italic underline decoration-white/5 underline-offset-4">{item.label}</span>
                                      <span className={`text-[10px] font-black px-4 py-1.5 rounded-xl bg-black/60 shadow-inner ${item.ok ? 'text-[var(--primary)] border border-[var(--primary)]/20' : 'text-amber-500 border border-amber-500/20'}`}>
                                          {item.val}
                                      </span>
                                  </div>
                              ))}
                              
                              {dash.governance?.pending_approvals && dash.governance.pending_approvals > 0 ? (
                                  <div className="p-8 rounded-[2.5rem] bg-amber-500/[0.03] border border-amber-500/20 flex flex-col gap-4 animate-pulse shadow-2xl">
                                      <div className="flex items-center gap-3">
                                         <AlertOctagon size={18} className="text-amber-500" />
                                         <span className="text-[10px] font-black text-amber-500 uppercase tracking-[0.3em] font-mono italic">Doğrulama Bekleniyor</span>
                                      </div>
                                      <p className="text-[11px] text-gray-500 leading-relaxed font-bold italic">
                                          Sistem geneli {dash.governance.pending_approvals} adet kritik operasyon onay bekliyor.
                                      </p>
                                      <button className="w-full py-3 bg-amber-500/10 border border-amber-500/30 text-amber-500 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-amber-500/20 transition-all">
                                         Onayları İncele
                                      </button>
                                  </div>
                              ) : (
                                  <div className="p-8 rounded-[2.5rem] bg-green-500/[0.03] border border-green-500/20 flex flex-col gap-4 shadow-xl">
                                      <div className="flex items-center gap-3 text-green-500">
                                         <ShieldCheck size={18} />
                                         <span className="text-[10px] font-black uppercase tracking-[0.3em] font-mono italic">Politika Senkronize</span>
                                      </div>
                                      <p className="text-[11px] text-gray-500 leading-relaxed font-bold italic">
                                          Tüm yüksek riskli operasyonlar geçerli quorum konsensüsüne ulaştı. Şebeke stabil.
                                      </p>
                                  </div>
                              )}
                          </div>
                      </div>

                      {/* Right: Infrastructure & Identity */}
                      <div className="space-y-8">
                          <h3 className="text-[11px] font-black uppercase tracking-[0.4em] text-gray-600 px-2 italic border-l-2 border-violet-500">Kimlik & Altyapı</h3>
                          <div className="glass-panel p-10 rounded-[2.5rem] border-white/5 bg-white/[0.015] flex flex-col gap-10 shadow-2xl relative overflow-hidden">
                              <div className="absolute -bottom-10 -right-10 opacity-[0.02] text-violet-500 group-hover:opacity-[0.05] transition-opacity">
                                <Cpu size={180} />
                              </div>
                              {[
                                  { label: "Çekirdek Kernel", val: "Egemen Yaz Framework v14.02", icon: <Layers size={14}/> },
                                  { label: "Ortam Modu", val: "CANLI MİSYON OPS", icon: <Globe size={14}/> },
                                  { label: "VCS Branch Takibi", val: "Federation/p2p-sync", icon: <GitBranch size={14}/> },
                                  { label: "Audit Ledger Index", val: "sha256:7f3aa9e11b...a1c", icon: <Database size={14}/> },
                              ].map(info => (
                                  <div key={info.label} className="flex flex-col gap-2 relative z-10">
                                      <div className="flex items-center gap-3 text-gray-700">
                                         {info.icon}
                                         <span className="text-[9px] font-black text-gray-700 uppercase tracking-[0.2em]">{info.label}</span>
                                      </div>
                                      <span className="text-sm font-black text-white truncate italic tracking-tighter decoration-[var(--primary)] underline-offset-4 decoration-1">{info.val}</span>
                                  </div>
                              ))}
                          </div>
                      </div>
                  </div>

                  {/* Launch Evidence & Evolution Timeline Elite Row */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 animate-in fade-in slide-in-from-bottom-10 duration-1000 delay-500">
                      <div className="lg:col-span-8">
                          <LaunchEvidencePanel governance={dash.governance} />
                      </div>
                      <div className="lg:col-span-4">
                          <EvolutionTimeline events={evolutionEvents} />
                      </div>
                  </div>
                </div>
              )}

              {activeTab === "workflows" && (
                <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-700 px-4">
                    <div className="flex items-center justify-between mb-10 pb-6 border-b border-white/[0.03]">
                        <div className="flex items-center gap-4">
                           <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 text-[var(--primary)]">
                              <Binary size={20} />
                           </div>
                           <div>
                              <h3 className="text-2xl font-black text-white uppercase italic tracking-tighter">Orkestrasyon Akışı</h3>
                              <p className="text-[10px] text-gray-600 font-black uppercase tracking-widest mt-1 opacity-60">Gerçek Zamanlı Otonom İş Akışı Durumu</p>
                           </div>
                        </div>
                        <div className="flex items-center gap-10">
                            <div className="flex flex-col items-center">
                               <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest block mb-1">Tamamlanan</span>
                               <span className="text-lg font-black text-green-500 italic font-mono">{wfStats.completed}</span>
                            </div>
                            <div className="flex flex-col items-center">
                               <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest block mb-1">Yürütülüyor</span>
                               <span className="text-lg font-black text-[var(--primary)] italic font-mono">{wfStats.running}</span>
                            </div>
                        </div>
                    </div>
                    {workflows.map((wf: any) => (
                        <EliteWorkflowRow key={wf.id} wf={wf} />
                    ))}
                    {workflows.length === 0 && (
                        <div className="py-40 text-center opacity-20">
                            <div className="p-10 bg-white/5 rounded-full border border-white/5 inline-flex mb-8">
                               <Binary size={48} className="animate-pulse" />
                            </div>
                            <p className="font-black text-gray-400 uppercase text-[12px] tracking-[0.6em]">Veri Akışı Bekleniyor...</p>
                        </div>
                    )}
                </div>
              )}

              {activeTab === "events" && (
                  <div className="h-full flex flex-col gap-10 animate-in zoom-in-95 duration-700">
                      <div className="flex items-center justify-between px-2">
                        <div className="flex flex-col gap-1">
                          <h3 className="text-xl font-black text-white uppercase italic tracking-tighter">Küresel Telemetri Merkezi</h3>
                          <p className="text-[10px] font-black text-gray-600 uppercase tracking-widest mt-1">Bölgeler Arası Olay Akışı v8.2</p>
                        </div>
                        <div className="flex items-center gap-4 bg-black/40 px-6 py-3 rounded-2xl border border-white/5">
                           <div className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] animate-ping" />
                           <span className="text-[10px] font-mono text-[var(--primary)] font-black italic tracking-widest uppercase">CANLI_TOHUM: {Math.random().toString(36).substring(7).toUpperCase()}</span>
                        </div>
                      </div>
                      <div className="flex-1 rounded-[3rem] border border-white/[0.05] bg-black/40 overflow-hidden relative shadow-2xl">
                           <LiveEventStream apiUrl={apiUrl} height="500px" />
                      </div>
                  </div>
              )}

              {activeTab === "health" && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 animate-in fade-in zoom-in-95 duration-1000">
                    {[
                        { label: "API Gateway Cluster", val: "99.99%", status: "UP", metric: `${latency}ms RT`, icon: <Globe size={18}/> },
                        { label: "PostgreSQL P2P Pool", val: "98.5%", status: "UP", metric: "24 ACTIVE", icon: <Database size={18}/> },
                        { label: "Redis Mesh Cache", val: "100%", status: "UP", metric: "3.2GB MEM", icon: <Zap size={18}/> },
                        { label: "Vector Index Nodes", val: "ACTIVE", status: "UP", metric: "OPTIMIZED", icon: <Binary size={18}/> },
                        { label: "Cortex Evolution", val: "READY", status: "IDLE", metric: "v14.02", icon: <HeartPulse size={18}/> },
                        { label: "Audit Ledger Store", val: "14.2TB", status: "OK", metric: "92% FREE", icon: <ShieldCheck size={18}/> },
                        { label: "Celery Workers Grid", val: "8/8", status: "UP", metric: "0 PENDING", icon: <Cpu size={18}/> },
                        { label: "Security Mesh Net", val: "SYNCED", status: "UP", metric: "GLOBAL", icon: <Fingerprint size={18}/> },
                    ].map(node => (
                        <div key={node.label} className="group p-10 rounded-[2.5rem] border border-white/5 bg-white/[0.012] hover:bg-white/[0.03] hover:border-[var(--primary)]/30 transition-all flex flex-col justify-between h-48 shadow-xl relative overflow-hidden">
                            <div className="absolute -top-5 -right-5 opacity-[0.01] group-hover:opacity-[0.05] transition-opacity duration-1000 text-[var(--primary)]">
                               {node.icon}
                            </div>
                            <div className="flex items-center justify-between relative z-10">
                                <div className="flex items-center gap-3">
                                   <div className="p-2 bg-black/40 rounded-lg text-gray-600 group-hover:text-white transition-colors">
                                      {node.icon}
                                   </div>
                                   <span className="text-[11px] font-black text-gray-500 uppercase tracking-tighter group-hover:text-white transition-colors">{node.label}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                   <span className="text-[8px] font-black text-green-500 tracking-widest">{node.status}</span>
                                   <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_12px_rgba(34,197,94,0.6)] group-hover:animate-ping" />
                                </div>
                            </div>
                            <div className="flex items-end justify-between relative z-10 pt-10 border-t border-white/[0.03]">
                                <div className="text-4xl font-black text-[var(--primary)] tracking-tighter italic group-hover:scale-110 transition-transform origin-left">{node.val}</div>
                                <div className="text-[9px] font-mono font-black text-gray-700 group-hover:text-gray-500 transition-colors">{node.metric}</div>
                            </div>
                        </div>
                    ))}
                </div>
              )}

              {activeTab === "economy" && (
                  <div className="animate-in fade-in slide-in-from-bottom-10 duration-1000 space-y-12">
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                          <div className="lg:col-span-2 glass-panel p-12 rounded-[3.5rem] border-white/5 bg-white/[0.012] shadow-2xl relative overflow-hidden group">
                               <div className="absolute top-0 right-0 p-12 opacity-[0.02] text-amber-500 group-hover:opacity-[0.05] transition-opacity">
                                  <DollarSign size={200} />
                                </div>
                               <h3 className="text-[11px] font-black text-gray-600 uppercase tracking-[0.4em] mb-12 italic border-l-2 border-amber-500 px-4">Model Economic Allocation</h3>
                               <div className="space-y-10 relative z-10">
                                   {[
                                       { model: "Claude 3.5 Sonnet", cost: 24.12, calls: 4902, color: "bg-violet-500" },
                                       { model: "DeepSeek Coder v2", cost: 8.45, calls: 12091, color: "bg-blue-500" },
                                       { model: "GPT-4o Omnis", cost: 12.30, calls: 1842, color: "bg-green-500" },
                                       { model: "Sovereign SLM 8B", cost: 0.00, calls: 45210, color: "bg-gray-500" },
                                   ].map(m => (
                                       <div key={m.model} className="space-y-4 group/item">
                                           <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className={`w-2 h-2 rounded-full ${m.color} shadow-[0_0_10px_currentColor]`} />
                                                    <span className="text-[13px] font-black text-white uppercase tracking-tight italic group-hover/item:text-[var(--primary)] transition-colors">{m.model}</span>
                                                </div>
                                                <span className="text-[14px] font-black font-mono text-gray-400 italic">${m.cost.toFixed(2)}</span>
                                           </div>
                                           <div className="w-full h-2 bg-black/40 rounded-full overflow-hidden border border-white/[0.03]">
                                               <div className={`h-full ${m.color} opacity-80 shadow-[0_0_15px_currentColor] transition-all duration-1000`} style={{ width: `${(m.cost / 40) * 100}%` }} />
                                           </div>
                                           <div className="flex justify-between text-[9px] font-black text-gray-700 uppercase tracking-widest italic pt-1">
                                               <span>VOLUME: {m.calls.toLocaleString()} REQ</span>
                                               <span>EFFICIENCY: ${(m.cost / (m.calls || 1)).toFixed(5)} / OP</span>
                                           </div>
                                       </div>
                                   ))}
                               </div>
                          </div>
                          <div className="space-y-10">
                               <div className="glass-panel p-10 rounded-[3rem] border border-[var(--primary)]/20 bg-[var(--primary)]/[0.03] shadow-2xl">
                                    <h4 className="text-[11px] font-black text-[var(--primary)] uppercase tracking-[0.3em] mb-6 italic">Fiscal Velocity</h4>
                                    <div className="text-6xl font-black text-white italic tracking-tighter">$4.92<span className="text-2xl ml-2 opacity-40">/24H</span></div>
                                    <p className="text-[12px] text-gray-500 mt-6 leading-relaxed font-bold italic">
                                       <Activity size={14} className="inline mr-2 text-[var(--primary)]" />
                                       Detected 12% drift decrease vs baseline. Autonomous model rotation active.
                                    </p>
                               </div>
                               <div className="glass-panel p-10 rounded-[3rem] border border-amber-500/20 bg-amber-500/[0.03] shadow-xl">
                                    <div className="flex items-center gap-4 mb-6">
                                       <AlertOctagon size={20} className="text-amber-500" />
                                       <h4 className="text-[11px] font-black text-amber-500 uppercase tracking-[0.3em] italic">Governance Threshold</h4>
                                    </div>
                                    <div className="text-[11px] text-gray-600 leading-relaxed font-bold uppercase tracking-tight">
                                        Budget utilization passed 90% threshold. "Economic Circuit Breaker" is currently restricting non-critical evolutionary tasks.
                                    </div>
                                    <button className="mt-8 w-full py-4 bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 text-[10px] font-black uppercase tracking-widest rounded-2xl border border-amber-500/30 transition-all">
                                       Modify Quotas
                                    </button>
                               </div>
                          </div>
                      </div>
                  </div>
              )}
          </div>
      </section>

      {/* API HUB ELITE */}
      <ApiHub apiBase={apiUrl} />

    </div>
  );
}

function EliteMetricItem({ label, value, subLabel, color, icon, loading, accent, bar }: any) {
  return (
    <div className="glass-panel p-10 rounded-[3rem] border-white/[0.04] bg-white/[0.012] hover:bg-white/[0.025] hover:border-[var(--primary)]/20 transition-all group relative overflow-hidden shadow-2xl flex flex-col justify-between min-h-[220px]">
       {loading ? (
         <div className="space-y-6">
            <Skeleton className="h-4 w-40 rounded" />
            <Skeleton className="h-12 w-24 rounded" />
            <Skeleton className="h-4 w-32 rounded" />
         </div>
       ) : (
         <>
            <div className="flex justify-between items-start">
               <div className="flex flex-col gap-2">
                  <span className="text-[11px] font-black text-gray-600 uppercase tracking-[0.3em] italic group-hover:text-white transition-colors">
                    {label}
                  </span>
                  <div className="w-12 h-0.5 bg-white/5 group-hover:bg-[var(--primary)]/40 transition-colors" />
               </div>
               <div className={`p-4 ${accent} rounded-[1.5rem] ${color} shadow-xl group-hover:scale-125 transition-transform duration-500`}>
                  {icon}
               </div>
            </div>
            
            <div className="mt-8">
               <div className={`text-6xl font-black tracking-tighter ${color} italic`}>{value}</div>
               <div className="flex items-center gap-3 mt-4">
                  <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">{subLabel}</span>
                  {bar !== undefined && (
                    <div className="flex-1 h-1 bg-black/40 rounded-full overflow-hidden border border-white/[0.03]">
                       <div className={`h-full ${color.replace('text', 'bg')} opacity-60`} style={{ width: `${bar}%` }} />
                    </div>
                  )}
               </div>
            </div>
         </>
       )}
       <div className="absolute top-0 right-0 w-24 h-24 bg-white/[0.01] rounded-full blur-2xl -mr-12 -mt-12 pointer-events-none group-hover:bg-[var(--primary)]/[0.05] transition-all" />
    </div>
  );
}

function EliteWorkflowRow({ wf }: { wf: any }) {
  const isComp = wf.status === 'completed';
  const color = isComp ? 'text-green-500' : 'text-[var(--primary)]';

  return (
    <div className="group flex items-center justify-between p-10 rounded-[2.5rem] border border-white/5 bg-white/[0.012] hover:bg-white/[0.03] hover:border-[var(--primary)]/20 transition-all duration-500 shadow-xl cursor-help relative overflow-hidden">
        <div className="flex items-center gap-8 relative z-10 w-1/3">
            <div className={`p-5 rounded-2xl bg-black/40 border transition-all duration-500 flex items-center justify-center ${isComp ? 'border-green-500/20 text-green-500' : 'border-[var(--primary)]/20 text-[var(--primary)] shadow-[0_0_20px_rgba(102,252,241,0.1)]'}`}>
                 {isComp ? <ShieldCheck size={24} /> : <Zap size={24} className="animate-pulse" />}
            </div>
            <div className="truncate">
                <div className="text-xl font-black text-white hover:text-[var(--primary)] transition-colors uppercase tracking-tight italic">
                   {wf.title || wf.workflow_type}
                </div>
                <div className="flex items-center gap-3 mt-1">
                   <span className="text-[9px] font-mono text-gray-700 uppercase tracking-widest">ID: {wf.id.substring(0,16)}</span>
                   <div className="w-1 h-1 rounded-full bg-white/10" />
                   <span className="text-[8px] font-black text-gray-800 uppercase tracking-widest">TRACE_V2_READY</span>
                </div>
            </div>
        </div>
        
        <div className="hidden xl:flex flex-col items-center w-64 relative z-10">
             <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/[0.03]">
                 <div className={`h-full shadow-[0_0_10px_currentColor] transition-all duration-1000 ${isComp ? 'bg-green-500 shadow-green-500/20' : 'bg-[var(--primary)] shadow-[var(--primary)]/20'}`} 
                      style={{ width: `${wf.progress_pct || (isComp ? 100 : 40)}%` }} />
             </div>
             <div className="flex justify-between w-full mt-3 px-1">
                <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Evrimsel İlerleme</span>
                <span className="text-[10px] font-mono font-black text-gray-500 italic">%{wf.progress_pct || (isComp ? 100 : 40)}</span>
             </div>
        </div>

        <div className="flex items-center gap-10 relative z-10">
            <div className={`px-8 py-2 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] border shadow-lg transition-all italic scale-90 group-hover:scale-100
                ${isComp ? 'text-green-500 border-green-500/20 bg-green-500/[0.03]' : 
                  wf.status === 'running' ? 'text-[var(--primary)] border-[var(--primary)]/20 bg-[var(--primary)]/[0.03]' : 
                  'text-amber-500 border-amber-500/20 bg-amber-500/[0.03]'}
            `}>
                {wf.status}
            </div>
            <ArrowRight size={20} className="text-gray-800 group-hover:text-[var(--primary)] group-hover:translate-x-2 transition-all" />
        </div>
        
        {/* Background Gradient */}
        <div className={`absolute inset-0 bg-gradient-to-r ${isComp ? 'from-green-500/[0.01]' : 'from-[var(--primary)]/[0.01]'} to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none`} />
    </div>
  );
}
