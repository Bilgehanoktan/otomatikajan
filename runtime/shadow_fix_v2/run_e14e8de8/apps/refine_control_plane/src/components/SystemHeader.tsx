"use client";

import React from "react";
import { useApiUrl, useCustom, useGetIdentity } from "@refinedev/core";
import {
    Activity,
    ShieldCheck,
    Cpu,
    Bell,
    Settings,
    Search,
    Plus,
    UserCircle
} from "lucide-react";
import { App } from "antd";
import LanguageSwitcher from "./LanguageSwitcher";
import { useTranslations } from "next-intl";

const SystemHeaderContent = () => {
    const t = useTranslations("dashboard");
    const { notification } = App.useApp();
    const apiUrl = useApiUrl();
    const { query: { data } } = useCustom({
        url: `${apiUrl}/workflows/stats/summary`,
        method: "get",
        queryOptions: {
            staleTime: 30000,
            refetchOnWindowFocus: false,
        }
    });

    const { data: identity } = useGetIdentity<any>();
    const stats = data?.data as any;
    const running = stats?.running || 0;
    const successRate = stats?.success_rate_pct || 100;
    const failed = stats?.failed || 0;
    const isCrisisMode = (stats?.health || 100) < 10;

    const [operatorEmail, setOperatorEmail] = React.useState<string | null>(null);

    React.useEffect(() => {
        if (typeof window !== "undefined") {
            setOperatorEmail(window.localStorage.getItem("sqv_operator_email"));
        }
    }, []);

    return (
        <header className="h-16 w-full max-w-full overflow-hidden border-b border-white/5 px-4 lg:px-6 flex items-center justify-between gap-4 glass-panel sticky top-0 z-50 backdrop-blur-xl">
            <div className="flex min-w-0 items-center gap-4">
                {!isCrisisMode && (
                    <div className="relative group hidden md:block min-w-0 animate-in fade-in duration-700">
                        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-[var(--primary)] transition-all duration-300" />
                        <input
                            type="text"
                            placeholder={t("searchPlaceholder")}
                            className="bg-white/5 border border-white/5 rounded-full pl-11 pr-5 py-2 text-[11px] font-medium text-gray-300 focus:outline-none focus:border-[var(--primary)]/30 focus:bg-white/[0.08] focus:ring-4 focus:ring-[var(--primary)]/5 transition-all w-48 xl:w-72 placeholder:text-gray-600"
                        />
                    </div>
                )}
                {isCrisisMode && (
                    <div className="flex items-center gap-3 px-4 py-1.5 rounded-full bg-red-500/10 border border-red-500/20 animate-pulse">
                        <span className="w-2 h-2 bg-red-400 rounded-full shadow-[0_0_8px_rgba(248,113,113,0.5)]" />
                        <span className="text-[10px] font-black text-red-400 uppercase tracking-[0.1em]">{t("criticalRisk")}</span>
                    </div>
                )}
            </div>

            <div className="flex min-w-0 shrink items-center justify-end gap-4 xl:gap-6">
                {/* Metabolic Health Indicator */}
                <div className="hidden 2xl:flex items-center gap-4 px-6 border-l border-white/5">
                    <div className="flex flex-col items-end">
                        <span className="text-[9px] text-gray-500 uppercase tracking-[0.2em] font-black mb-1">{t("metabolicPulse")}</span>
                        <div className="flex items-center gap-2">
                             <div className="h-1.5 w-32 bg-white/5 rounded-full overflow-hidden border border-white/5">
                                <div
                                    className="h-full transition-all duration-1000 shadow-[0_0_100px_rgba(102,252,241,0.5)]"
                                    style={{
                                        width: `${(data?.data as any)?.health_score * 100 || 0}%`,
                                        background: (data?.data as any)?.health_score > 0.8 ? '#66fcf1' : (data?.data as any)?.health_score > 0.4 ? '#f6ad55' : '#f56565'
                                    }}
                                />
                             </div>
                             <span className="text-[11px] font-black text-white w-8">%{Math.round((data?.data as any)?.health_score * 100) || 0}</span>
                        </div>
                    </div>
                    <div className={`p-2 rounded-xl ${(data?.data as any)?.health_score > 0.4 ? 'bg-[var(--primary)]/5 text-[var(--primary)]' : 'bg-red-500/10 text-red-400'} animate-pulse`}>
                        <Activity size={18} />
                    </div>
                </div>

                {/* System Metrics */}
                <div className="hidden xl:flex items-center gap-6 2xl:gap-10 border-r border-white/10 pr-4 2xl:pr-8">
                    <div className="flex items-center gap-3 group">
                        <div className={`p-2 rounded-lg ${isCrisisMode ? "bg-red-500/10" : "bg-[var(--primary)]/5"} border border-white/5`}>
                            <Activity size={14} className={isCrisisMode ? "text-red-400" : "text-[var(--primary)]"} />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[9px] text-gray-500 uppercase tracking-[0.2em] font-black">{t("active")}</span>
                            <div className="text-xs font-black text-white">{running}</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-green-500/5 border border-white/5">
                            <ShieldCheck size={14} className="text-green-400" />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[9px] text-gray-500 uppercase tracking-[0.2em] font-black">{t("success")}</span>
                            <div className="text-xs font-black text-green-400">%{successRate}</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${isCrisisMode ? "bg-red-500/10" : "bg-white/5"} border border-white/5`}>
                            <Cpu size={14} className={isCrisisMode ? "text-red-400" : "text-[#45a29e]"} />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[9px] text-gray-500 uppercase tracking-[0.2em] font-black">{t("error")}</span>
                            <div className="text-xs font-black text-red-400">{failed}</div>
                        </div>
                    </div>
                </div>

                {/* Actions & User */}
                <div className="flex min-w-0 items-center gap-3 2xl:gap-5">
                    <button
                        onClick={() => window.location.href = "/workflows"}
                        className="hidden lg:flex items-center gap-2.5 px-5 py-2 bg-[var(--primary)] text-[#0b0c10] text-[11px] font-black uppercase rounded-xl hover:shadow-[0_0_25px_var(--primary-glow)] hover:-translate-y-0.5 transition-all active:scale-95 group"
                    >
                        <Plus size={16} className="group-hover:rotate-90 transition-all duration-300" />
                        <span>{t("start")}</span>
                    </button>

                    <LanguageSwitcher />

                    <div className="flex items-center gap-1 bg-white/5 border border-white/5 p-1 rounded-2xl">
                        <button
                            onClick={() => notification.info({ message: t("notificationsTitle"), description: t("notificationsDesc") })}
                            className="p-2.5 text-gray-400 hover:text-[var(--primary)] hover:bg-white/5 rounded-xl transition-all relative group" title={t("notificationsTitle")}
                        >
                            <Bell size={18} />
                            <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red-400 rounded-full border-2 border-[#0b0c10]" />
                        </button>
                        <button
                            onClick={() => notification.info({ message: t("settingsTitle"), description: t("settingsLocked") })}
                            className="p-2.5 text-gray-500 hover:text-white hover:bg-white/5 rounded-xl transition-all" title={t("settingsTitle")}
                        >
                            <Settings size={18} />
                        </button>
                    </div>

                    <div className="hidden lg:flex min-w-0 items-center gap-3 pl-4 border-l border-white/10">
                        <div className="flex min-w-0 max-w-[9rem] 2xl:max-w-[13rem] flex-col items-end">
                            <span className="text-[11px] text-white font-black tracking-tight">{t("operator")}</span>
                            <span className="max-w-full truncate text-[8px] text-[var(--secondary)] font-black uppercase tracking-[0.18em] 2xl:tracking-[0.25em]">
                                {identity?.name || identity?.email || operatorEmail || "GUEST"}
                            </span>
                        </div>
                        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[var(--primary)]/20 to-transparent border border-[var(--primary)]/30 flex items-center justify-center group cursor-pointer hover:border-[var(--primary)]/60 transition-all overflow-hidden">
                            {identity?.avatar ? (
                                <img src={identity.avatar} alt="Avatar" className="w-full h-full object-cover group-hover:scale-110 transition-all" />
                            ) : (
                                <UserCircle size={26} className="text-[var(--primary)] group-hover:scale-110 transition-all" />
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
};

export const SystemHeader = () => {
    return <SystemHeaderContent />;
};

export default SystemHeader;
