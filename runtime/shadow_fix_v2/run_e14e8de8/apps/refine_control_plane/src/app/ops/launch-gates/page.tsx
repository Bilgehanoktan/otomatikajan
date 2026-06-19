"use client";

import React, { useEffect, useState } from "react";
import {
    Activity,
    Wallet,
    Zap,
    CheckCircle2,
    Info,
    ArrowRight,
    Lock,
    Rocket,
    ShieldCheck,
    AlertOctagon,
    Target,
    Users
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/runtime";

type LaunchGateStatus = "PASS" | "FAIL" | "WAIT";

type LaunchGateApiResponse = {
    passed: boolean;
    gates: {
        budget?: {
            status?: string;
            global_consumption?: number;
            rollout_threshold?: number;
        };
        governance?: {
            status?: string;
            internal_guards_active?: boolean;
            root_detected?: string;
        };
        quorum?: {
            status?: string;
            pending_critical_signoffs?: number;
            message?: string;
        };
        accuracy?: {
            status?: string;
            score?: number;
            threshold?: number;
            last_validation_id?: string;
        };
    };
    timestamp?: string;
};

type LaunchGateCard = {
    id: string;
    title: string;
    icon: React.ReactNode;
    status: LaunchGateStatus;
    metric: string;
    threshold: string;
    detail: string;
};

function normalizeGateStatus(status?: string): LaunchGateStatus {
    return status === "PASS" || status === "SUCCESS" ? "PASS" : "FAIL";
}

function formatPercent(value?: number) {
    if (typeof value !== "number") return "N/A";
    return `${Math.round(value * 100)}%`;
}

function formatUsagePercent(value?: number) {
    if (typeof value !== "number") return "N/A";
    const normalized = value <= 1 ? value * 100 : value;
    return `${normalized.toFixed(2)}%`;
}

function buildGateCards(response: LaunchGateApiResponse | null): LaunchGateCard[] {
    if (!response?.gates) {
        return [
            {
                id: "no-data",
                title: "Veri Bekleniyor",
                icon: <Info size={24} />,
                status: "WAIT",
                metric: "0 items",
                threshold: "N/A",
                detail: "Henüz canlı launch gate kaydı alınamadı."
            }
        ];
    }

    const budget = response.gates.budget;
    const governance = response.gates.governance;
    const quorum = response.gates.quorum;
    const accuracy = response.gates.accuracy;

    return [
        {
            id: "budget",
            title: "BUDGET-GUARD",
            icon: <Wallet size={24} />,
            status: normalizeGateStatus(budget?.status),
            metric: formatUsagePercent(budget?.global_consumption),
            threshold: typeof budget?.rollout_threshold === "number" ? `<= ${budget.rollout_threshold.toFixed(0)}%` : "N/A",
            detail: "Global maliyet tüketimi rollout eşiğinin altında kalmalı."
        },
        {
            id: "governance",
            title: "GOVERNANCE-GUARD",
            icon: <ShieldCheck size={24} />,
            status: normalizeGateStatus(governance?.status),
            metric: governance?.internal_guards_active ? "active" : "inactive",
            threshold: "internal guards",
            detail: governance?.root_detected ? `Runtime root: ${governance.root_detected}` : "Yönetişim korumaları aktif olmalı."
        },
        {
            id: "quorum",
            title: "QUORUM-GATE",
            icon: <Users size={24} />,
            status: normalizeGateStatus(quorum?.status),
            metric: `${quorum?.pending_critical_signoffs ?? 0} pending`,
            threshold: quorum?.message || "Quorum reached",
            detail: "Kritik onay kuyruğunda bekleyen imza kalmamalı."
        },
        {
            id: "accuracy",
            title: "ACCURACY-GATE",
            icon: <Target size={24} />,
            status: normalizeGateStatus(accuracy?.status),
            metric: formatPercent(accuracy?.score),
            threshold: typeof accuracy?.threshold === "number" ? `>= ${formatPercent(accuracy.threshold)}` : "N/A",
            detail: accuracy?.last_validation_id ? `Last validation: ${accuracy.last_validation_id}` : "Son doğrulama skoru eşik üstünde olmalı."
        }
    ];
}

export default function LaunchGatesPage() {
    const [isClient, setIsClient] = useState(false);
    const [launchGates, setLaunchGates] = useState<LaunchGateApiResponse | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;

        async function loadLaunchGates() {
            try {
                setIsLoading(true);
                const data = await safeFetchJson<LaunchGateApiResponse>(
                    `${getApiBaseUrl()}/governance/ops/launch-gates`,
                    { useOfflineFallback: false }
                );
                if (!cancelled) {
                    setLaunchGates(data);
                    setLoadError(null);
                }
            } catch (error) {
                if (!cancelled) {
                    setLoadError(error instanceof Error ? error.message : "Launch gate verisi alınamadı.");
                    setLaunchGates(null);
                }
            } finally {
                if (!cancelled) setIsLoading(false);
            }
        }

        setIsClient(true);
        loadLaunchGates();

        return () => {
            cancelled = true;
        };
    }, []);

    if (!isClient || isLoading) return <div className="min-h-screen bg-[#060a12]"><Skeleton /></div>;

    const finalGates = buildGateCards(launchGates);
    const passCount = finalGates.filter((gate) => gate.status === "PASS").length;
    const actionableGateCount = finalGates.filter((gate) => gate.status !== "WAIT").length;
    const readiness = actionableGateCount > 0 ? Math.round((passCount / actionableGateCount) * 100) : 0;
    const allGatesPassed = actionableGateCount > 0 && passCount === actionableGateCount && launchGates?.passed === true;

    return (
        <div className="p-8 min-h-screen bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
            <ResourceHeader
                title="Launch Gates"
                subtitle="Production Readiness Checkpoint & Rollout Protocols"
                icon={<Rocket size={32} />}
                badge="Pre-Flight Tier"
                actions={
                    <div className="flex items-center gap-6">
                        <div className={`glass-card !p-3 flex flex-col items-end ${allGatesPassed ? "border-green-500/20" : "border-red-500/20"}`}>
                            <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest">Global Ready</span>
                            <span className={`text-sm font-black ${allGatesPassed ? "text-green-400" : "text-red-400"}`}>
                                {allGatesPassed ? "NOMINAL" : "BLOCKED"}
                            </span>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className="text-[9px] text-gray-700 font-black uppercase tracking-widest italic">Protocol v2.1</span>
                        </div>
                    </div>
                }
            />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 mb-10">
                <div className="lg:col-span-8">
                    <section className="glass-panel p-1 py-10 rounded-[3rem] border-white/[0.03] bg-gradient-to-br from-white/[0.02] to-transparent relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                            <Target size={300} />
                        </div>

                        <div className="flex flex-col items-center justify-center relative z-10 px-10 text-center">
                            <div className="flex items-center gap-4 mb-4">
                                <Zap size={20} className="text-[var(--primary)] animate-pulse" />
                                <h3 className="text-xs font-black text-white uppercase tracking-[0.4em]">Integrated Mission Readiness</h3>
                            </div>
                            <div className="relative mb-8">
                                <div className="text-[8rem] font-black text-white leading-none tracking-tighter opacity-10 blur-sm absolute inset-0 select-none">{readiness}%</div>
                                <div className="text-[8rem] font-black text-white leading-none tracking-tighter relative select-none">{readiness}<span className="text-[2rem] text-[var(--primary)]">%</span></div>
                            </div>
                            <p className="max-w-md text-gray-500 text-[11px] font-black uppercase tracking-widest leading-relaxed">
                                {allGatesPassed ? (
                                    <>
                                        Tüm alt-sistemler operasyonel nominal eşik değerlerini karşıladı. <br />
                                        Sistem bir sonraki mühürleme ve devir işlemi için onaylanmıştır.
                                    </>
                                ) : (
                                    <>
                                        Launch gate kaynaklarından en az biri henüz nominal değil. <br />
                                        Devir işlemi için gate sonuçları tekrar incelenmelidir.
                                    </>
                                )}
                            </p>
                            {loadError && (
                                <p className="mt-5 text-[10px] text-red-400 font-black uppercase tracking-widest">
                                    API Hatası: {loadError}
                                </p>
                            )}
                        </div>

                        <div className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-[var(--primary)]/20 to-transparent animate-scan" style={{ top: "40%" }} />
                    </section>
                </div>

                <div className="lg:col-span-4 h-full">
                    <div className="glass-panel p-10 rounded-[3rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.05] to-transparent h-full flex flex-col items-center justify-center text-center group">
                        <div className="p-5 bg-[var(--primary)]/10 rounded-[2rem] border border-[var(--primary)]/20 shadow-[0_0_30px_rgba(102,252,241,0.1)] mb-8 group-hover:scale-110 transition-transform duration-700">
                            {allGatesPassed ? (
                                <CheckCircle2 size={42} className="text-[var(--primary)]" />
                            ) : (
                                <AlertOctagon size={42} className="text-red-400" />
                            )}
                        </div>
                        <h3 className="text-xl font-black text-white uppercase tracking-tighter mb-4">Final Protocol Handover</h3>
                        <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest mb-10 max-w-[200px] mx-auto leading-loose">
                            {allGatesPassed
                                ? "Tüm kapılar yeşil. Yeni bir mühürleme ve rollout tetiklenebilir."
                                : "En az bir canlı launch gate nominal değil. Handover kilitli kalmalıdır."}
                        </p>
                        <button
                            disabled={!allGatesPassed}
                            className="w-full flex items-center justify-center gap-3 px-8 py-5 bg-[var(--primary)] text-[#060a12] font-black text-xs uppercase tracking-[0.2em] hover:shadow-[0_8px_48px_rgba(102,252,241,0.4)] transition-all rounded-2xl active:scale-95 group/btn disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            Handover Tetikle
                            <ArrowRight size={18} className="group-hover/btn:translate-x-2 transition-transform" />
                        </button>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
                {finalGates.map((gate) => (
                    <div key={gate.id} className="glass-panel p-8 rounded-[2.5rem] border-white/[0.03] bg-white/[0.015] hover:bg-white/[0.04] hover:border-[var(--primary)]/20 transition-all group/gate relative overflow-hidden">
                        <div className="mb-8 flex items-start justify-between">
                            <div className="p-4 bg-black/40 rounded-2xl border border-white/5 text-gray-500 group-hover/gate:text-[var(--primary)] group-hover/gate:border-[var(--primary)]/20 transition-all duration-500">
                                {gate.icon}
                            </div>
                            <div className={`px-3 py-1 rounded-lg text-[9px] font-black tracking-widest border transition-all ${
                                gate.status === "PASS"
                                    ? "bg-green-500/10 text-green-500 border-green-500/20 shadow-[0_0_15px_rgba(34,197,94,0.1)]"
                                    : gate.status === "WAIT"
                                        ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                                        : "bg-red-500/10 text-red-500 border-red-500/20"
                            }`}>
                                {gate.status}
                            </div>
                        </div>

                        <h3 className="text-base font-black text-white uppercase tracking-tight mb-3 transition-colors group-hover/gate:text-[var(--primary)]">{gate.title}</h3>
                        <p className="text-[10px] text-gray-600 mb-8 flex-1 italic font-bold tracking-tight leading-relaxed">"{gate.detail}"</p>

                        <div className="space-y-4 pt-6 border-t border-white/[0.03]">
                            <div className="flex justify-between items-center">
                                <span className="text-[9px] uppercase tracking-widest text-gray-700 font-black">Güncel</span>
                                <span className="text-xs font-mono font-black text-[var(--primary)]">{gate.metric}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-[9px] uppercase tracking-widest text-gray-700 font-black">Eşik</span>
                                <span className="text-xs font-mono font-bold text-gray-400">{gate.threshold}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <section className="glass-panel p-10 rounded-[3rem] border-white/[0.03] bg-[#060a12]/50 relative overflow-hidden group/notice shadow-2xl">
                <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover/notice:opacity-[0.08] transition-opacity pointer-events-none">
                    <AlertOctagon size={180} className="text-red-500" />
                </div>

                <div className="flex flex-col lg:flex-row gap-10 items-start">
                    <div className="p-6 bg-red-500/10 rounded-3xl border border-red-500/20 text-red-500 shadow-[0_0_30px_rgba(239,68,68,0.1)]">
                        <AlertOctagon size={40} className="animate-pulse" />
                    </div>
                    <div className="flex-1">
                        <h4 className="text-2xl font-black text-white tracking-tighter uppercase mb-3">Otonom Blokaj Protokolü</h4>
                        <p className="text-gray-500 text-xs font-bold leading-loose mb-8 max-w-2xl uppercase tracking-wider">
                            Lansman kapılarından herhangi biri 'FAIL' durumuna düştüğü anda, sistem otonom olarak `Emergency Policy Core` protokolünü devreye sokar. Bu durum bekleyen tüm rollout'ları iptal eder ve `Constitutional Guard` tüm dosya yazma yetkilerini geri çeker.
                        </p>
                        <div className="flex flex-wrap items-center gap-8">
                            <div className="flex items-center gap-3">
                                <ShieldCheck size={18} className="text-green-500" />
                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Self-Healing Active</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <Lock size={18} className="text-[var(--primary)]" />
                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Quorum Lock Engaged</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <Activity size={18} className="text-blue-400" />
                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Baseline Monitoring</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
