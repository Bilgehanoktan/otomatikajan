"use client";

import React, { useState, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { Search, Command, X, ArrowRight, Zap, Target, ShieldCheck, Bug } from "lucide-react";

interface CommandItem {
    id: string;
    label: string;
    description: string;
    icon: React.ReactNode;
    category: "Operations" | "Governance" | "Navigation";
}

export const CommandPalette = () => {
    const t = useTranslations("dashboard.commandPalette");
    const [isOpen, setIsOpen] = useState(false);
    const [search, setSearch] = useState("");
    const modalRef = useRef<HTMLDivElement>(null);

    const COMMANDS: CommandItem[] = [
        { id: "run-workflow", label: t("commands.runWorkflow.label"), description: t("commands.runWorkflow.desc"), icon: <Zap size={16}/>, category: "Operations" },
        { id: "seal-audit", label: t("commands.sealAudit.label"), description: t("commands.sealAudit.desc"), icon: <ShieldCheck size={16}/>, category: "Governance" },
        { id: "health-check", label: t("commands.healthCheck.label"), description: t("commands.healthCheck.desc"), icon: <Bug size={16}/>, category: "Operations" },
        { id: "view-proposals", label: t("commands.viewProposals.label"), description: t("commands.viewProposals.desc"), icon: <Target size={16}/>, category: "Governance" },
        { id: "go-dashboard", label: t("commands.goDashboard.label"), description: t("commands.goDashboard.desc"), icon: <ArrowRight size={16}/>, category: "Navigation" },
    ];

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "k") {
                e.preventDefault();
                setIsOpen(prev => !prev);
            }
            if (e.key === "Escape") {
                setIsOpen(false);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, []);

    const filtered = COMMANDS.filter(c => 
        c.label.toLowerCase().includes(search.toLowerCase()) || 
        c.category.toLowerCase().includes(search.toLowerCase())
    );

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[1000] flex items-start justify-center pt-[15vh] px-4 animate-in fade-in duration-200">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/80 backdrop-blur-xl" onClick={() => setIsOpen(false)} />
            
            {/* Modal */}
            <div 
                ref={modalRef} 
                className="relative w-full max-w-2xl bg-[#0b0c10] border border-white/10 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5),0_0_20px_rgba(102,252,241,0.1)] overflow-hidden animate-in zoom-in-95 slide-in-from-top-4 duration-300"
            >
                {/* Search Bar */}
                <div className="flex items-center gap-4 px-6 py-5 border-b border-white/5 bg-white/[0.02]">
                    <Search className="text-[var(--primary)]" size={20} />
                    <input 
                        autoFocus
                        type="text" 
                        value={search}
                        placeholder={t("searchPlaceholder")}
                        onChange={(e) => setSearch(e.target.value)}
                        className="flex-1 bg-transparent border-none outline-none text-lg text-white font-medium placeholder:text-gray-600"
                    />
                    <div className="flex items-center gap-1 px-2 py-1 rounded bg-white/5 border border-white/10 text-[10px] text-gray-500 font-black">
                        <Command size={10} />
                        <span>K</span>
                    </div>
                </div>

                {/* Results */}
                <div className="max-h-[400px] overflow-y-auto custom-scrollbar pt-2 pb-4">
                    {filtered.length > 0 ? (
                        <div className="space-y-4 px-2">
                            {["Operations", "Governance", "Navigation"].map(cat => {
                                const catItems = filtered.filter(f => f.category === cat);
                                if (catItems.length === 0) return null;
                                return (
                                    <div key={cat} className="space-y-1">
                                        <h3 className="px-4 py-2 text-[9px] font-black text-gray-600 uppercase tracking-[0.3em]">{cat}</h3>
                                        {catItems.map(item => (
                                            <div 
                                                key={item.id} 
                                                className="flex items-center gap-4 px-4 py-3 mx-2 rounded-xl border border-transparent hover:bg-white/[0.04] hover:border-white/5 transition-all group cursor-pointer"
                                            >
                                                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-gray-500 group-hover:text-[var(--primary)] group-hover:bg-[var(--primary)]/10 transition-all">
                                                    {item.icon}
                                                </div>
                                                <div className="flex-1">
                                                    <div className="text-[13px] font-bold text-white uppercase tracking-tight group-hover:text-[var(--primary)] transition-colors">{item.label}</div>
                                                    <div className="text-[10px] text-gray-500 mt-0.5">{item.description}</div>
                                                </div>
                                                <ArrowRight size={14} className="text-gray-700 group-hover:text-[var(--primary)] -translate-x-2 opacity-0 group-hover:translate-x-0 group-hover:opacity-100 transition-all" />
                                            </div>
                                        ))}
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="py-20 text-center space-y-4">
                            <div className="text-gray-700 text-[10px] font-black uppercase tracking-[0.5em]">{t("noResults")}</div>
                            <p className="text-[11px] text-gray-500">{t("noResultsDesc", { search })}</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-3 border-t border-white/5 bg-black/40 flex items-center justify-between">
                    <div className="flex items-center gap-4 text-[9px] font-bold text-gray-600 uppercase tracking-widest">
                        <span className="flex items-center gap-1"><span className="px-1.5 py-0.5 rounded bg-white/5">↑↓</span> {t("footer.navigate")}</span>
                        <span className="flex items-center gap-1"><span className="px-1.5 py-0.5 rounded bg-white/5">Enter</span> {t("footer.select")}</span>
                        <span className="flex items-center gap-1"><span className="px-1.5 py-0.5 rounded bg-white/5">Esc</span> {t("footer.close")}</span>
                    </div>
                    <div className="text-[9px] font-black text-[var(--primary)]/50 uppercase tracking-[0.2em]">Sovereign Operator Shell</div>
                </div>
            </div>
        </div>
    );
};
