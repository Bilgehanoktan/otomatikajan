"use client";

import React, { useState, useEffect } from "react";
import { 
    FileArchive, 
    Download, 
    Search, 
    Calendar, 
    ShieldCheck, 
    CheckCircle2,
    Lock
} from "lucide-react";
import { useTranslations } from "next-intl";

export default function AuditBundlesPage() {
    const t = useTranslations("bundles");
    const [isClient, setIsClient] = useState(false);
    useEffect(() => setIsClient(true), []);

    if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;
    
    // Mock data based on the pilot rollout
    const bundles = [
        {
            id: "LAUNCH_f462f604",
            name: "LAUNCH_f462f604_61319b0a.zip",
            purpose: "FINAL_PRODUCTION_HANDOVER",
            project: "Resilience Pilot v1",
            createdAt: "2026-04-17 19:23:29",
            operator: "CLI_OPERATOR",
            seal: "SHA256:61319b0a...",
            size: "1.2 MB",
            status: "sealed"
        },
        {
            id: "TEST_f4cd34e9",
            name: "TEST_BUNDLE_f4cd34e9.zip",
            purpose: "Compliance_DryRun",
            project: "System Global",
            createdAt: "2026-04-17 19:06:05",
            operator: "CLI_OPERATOR",
            seal: "SHA256:f4cd34e9...",
            size: "0.8 MB",
            status: "sealed"
        }
    ];

    return (
        <div className="p-8 space-y-12 animate-in fade-in duration-700 min-h-screen bg-[#060a12]">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-pulse shadow-[0_0_8px_var(--primary)]" />
                        <span className="text-[10px] uppercase tracking-[0.4em] font-black text-[var(--primary)] opacity-80">{t("subtitle")}</span>
                    </div>
                    <h1 className="text-5xl font-black text-white tracking-tighter uppercase italic">{t("title")}</h1>
                    <p className="text-gray-500 mt-4 max-w-2xl text-sm font-medium leading-relaxed italic">{t("description")}</p>
                </div>
                
                <div className="flex items-center gap-3">
                    <div className="relative group">
                        <div className="relative flex items-center gap-3 glass-panel border-white/5 bg-[#0b0f19]/40 px-5 py-3 text-gray-500 focus-within:border-[var(--primary)]/30 transition-all rounded-2xl">
                            <Search size={18} />
                            <input 
                                type="text" 
                                placeholder={t("searchPlaceholder")} 
                                className="bg-transparent border-none outline-none text-[10px] font-black uppercase tracking-widest w-48 placeholder:text-gray-700 text-white"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Bundles Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {bundles.map((bundle) => (
                    <div key={bundle.id} className="glass-panel p-8 group hover:border-[var(--primary)]/30 transition-all duration-500 relative overflow-hidden bg-[#0b0f19]/60 backdrop-blur-md rounded-[2.5rem] shadow-2xl border-white/10">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--primary)]/5 blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-[var(--primary)]/10 transition-colors" />
                        
                        <div className="flex items-start justify-between mb-8 relative z-10">
                            <div className="flex items-center gap-4">
                                <div className="w-14 h-14 rounded-2xl bg-black/40 flex items-center justify-center text-[var(--primary)] group-hover:scale-110 transition-transform duration-500 border border-white/5 shadow-inner">
                                    <FileArchive size={28} />
                                </div>
                                <div>
                                    <h3 className="font-black text-lg text-white group-hover:text-[var(--primary)] transition-colors uppercase tracking-tight italic">{bundle.name}</h3>
                                    <p className="text-[9px] text-gray-600 font-mono mt-1 tracking-[0.2em] font-black">{bundle.id}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 px-4 py-1.5 bg-[var(--primary)]/10 rounded-full border border-[var(--primary)]/20 shadow-[0_0_12px_rgba(102,252,241,0.05)]">
                                <Lock size={12} className="text-[var(--primary)]" />
                                <span className="text-[10px] font-black text-[var(--primary)] uppercase tracking-widest">{bundle.status}</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-8 mb-8 relative z-10">
                            <div className="space-y-2">
                                <p className="text-[9px] uppercase tracking-[0.2em] text-gray-600 font-black">{t("purpose")}</p>
                                <p className="text-xs text-white font-bold uppercase tracking-tight italic">{bundle.purpose}</p>
                            </div>
                            <div className="space-y-2">
                                <p className="text-[9px] uppercase tracking-[0.2em] text-gray-600 font-black">{t("project")}</p>
                                <p className="text-xs text-white font-bold uppercase tracking-tight italic">{bundle.project}</p>
                            </div>
                            <div className="space-y-2">
                                <p className="text-[9px] uppercase tracking-[0.2em] text-gray-600 font-black">{t("date")}</p>
                                <div className="flex items-center gap-2 text-xs text-gray-300 font-mono">
                                    <Calendar size={12} className="text-[var(--primary)] opacity-50" />
                                    {bundle.createdAt}
                                </div>
                            </div>
                            <div className="space-y-2">
                                <p className="text-[9px] uppercase tracking-[0.2em] text-gray-600 font-black">{t("size")}</p>
                                <p className="text-xs text-[var(--primary)] font-black font-mono">{bundle.size}</p>
                            </div>
                        </div>

                        <div className="flex items-center justify-between pt-6 border-t border-white/5 relative z-10">
                            <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500 font-bold group/seal">
                                <ShieldCheck size={14} className="text-[var(--primary)] group-hover/seal:scale-125 transition-transform" />
                                <span className="uppercase tracking-widest">{t("seal")}:</span> 
                                <span className="text-gray-400 group-hover/seal:text-white transition-colors">{bundle.seal}</span>
                            </div>
                            <button className="flex items-center gap-2 px-6 py-2.5 bg-[#0b0f19]/40 hover:bg-[var(--primary)]/10 text-white rounded-xl transition-all text-[10px] font-black uppercase tracking-widest border border-white/5 hover:border-[var(--primary)]/30 active:scale-95">
                                <Download size={14} />
                                {t("download")}
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Verification HUD */}
            <div className="glass-panel p-10 rounded-[3rem] border border-[var(--primary)]/20 bg-[#0b0f19]/90 backdrop-blur-xl relative overflow-hidden group shadow-[0_32px_64px_rgba(0,0,0,0.4)]">
                <div className="absolute top-0 right-0 p-8 opacity-[0.05] group-hover:rotate-12 transition-transform duration-1000">
                    <ShieldCheck size={180} />
                </div>
                <div className="flex flex-col md:flex-row items-center justify-between gap-12 relative z-10">
                    <div className="space-y-6">
                        <div className="inline-flex items-center gap-3 px-4 py-1.5 bg-[var(--primary)]/10 rounded-full border border-[var(--primary)]/20">
                            <CheckCircle2 size={16} className="text-[var(--primary)]" />
                            <span className="text-[10px] font-black uppercase tracking-widest text-[var(--primary)]">{t("verificationHud.integrityLabel")}</span>
                        </div>
                        <h2 className="text-4xl font-black leading-tight text-white uppercase italic">{t("verificationHud.status")}</h2>
                        <p className="text-sm font-medium text-gray-400 max-w-xl italic leading-relaxed">{t("verificationHud.description")}</p>
                    </div>
                    <div className="flex gap-6">
                        <div className="glass-panel bg-black/40 border-white/5 text-center px-10 py-6 rounded-[2rem] min-w-[160px]">
                            <span className="block text-5xl font-black mb-2 text-white italic">2/2</span>
                            <span className="text-[9px] font-black uppercase tracking-[0.3em] text-gray-500">{t("verificationHud.validPacks")}</span>
                        </div>
                        <div className="glass-panel bg-black/40 border-[var(--primary)]/20 text-center px-10 py-6 rounded-[2rem] min-w-[160px] shadow-[0_0_32px_rgba(102,252,241,0.05)]">
                            <span className="block text-5xl font-black mb-2 text-[var(--primary)] italic">100%</span>
                            <span className="text-[9px] font-black uppercase tracking-[0.3em] text-[var(--primary)]">{t("verificationHud.integrity")}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

