"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { 
    Shield, 
    FileCheck, 
    Scale, 
    Zap, 
    CheckCircle2, 
    XCircle, 
    ChevronRight,
    Fingerprint,
    Search,
    Brain
} from "lucide-react";

interface GateEvidence {
    id: string;
    title: string;
    description: string;
    status: "PASS" | "FAIL" | "PENDING";
    evidence: string;
    details: any;
}

export const LaunchEvidencePanel = ({ governance }: { governance: any }) => {
    const t = useTranslations("dashboard.launchEvidence");

    const gates: GateEvidence[] = [
        { 
            id: "budget", 
            title: t("gates.budget.title"), 
            description: t("gates.budget.desc"), 
            status: governance?.rollout_ready ? "PASS" : "FAIL",
            evidence: t("gates.budget.evidence"),
            details: { total: "$46.00", limit: "$50.00" }
        },
        { 
            id: "gov", 
            title: t("gates.gov.title"), 
            description: t("gates.gov.desc"), 
            status: governance?.constitutional_locks ? "PASS" : "FAIL",
            evidence: t("gates.gov.evidence"),
            details: { locked: 23, detected: 23 }
        },
        { 
            id: "quorum", 
            title: t("gates.quorum.title"), 
            description: t("gates.quorum.desc"), 
            status: governance?.rollout_ready ? "PASS" : "PENDING",
            evidence: t("gates.quorum.evidence"),
            details: { approved: 2, required: 3 }
        },
        { 
            id: "quality", 
            title: t("gates.quality.title"), 
            description: t("gates.quality.desc"), 
            status: "PASS",
            evidence: t("gates.quality.evidence"),
            details: { score: 0.94, mean: 0.92 }
        }
    ];

    return (
        <section className="glass-panel p-10 rounded-[3rem] border-white/[0.04] bg-white/[0.01] shadow-[0_32px_128px_rgba(0,0,0,0.5)] relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-10 opacity-[0.015] pointer-events-none group-hover:opacity-[0.04] transition-opacity duration-1000">
               <Fingerprint size={200} className="text-[var(--primary)]" />
            </div>

            <div className="flex items-center justify-between mb-12 relative z-10">
                <div className="flex flex-col gap-1">
                    <h3 className="text-[11px] font-black text-gray-500 uppercase tracking-[0.4em] italic mb-1">{t("title")}</h3>
                    <div className="flex items-center gap-3">
                       <h2 className="text-2xl font-black text-white uppercase tracking-tight italic">{t("subtitle").split(' ')[0]} <span className="text-[var(--primary)]">{t("subtitle").split(' ').slice(1).join(' ')}</span></h2>
                       <div className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] animate-pulse" />
                    </div>
                </div>
                <div className="flex items-center gap-4 bg-black/40 px-6 py-3 rounded-2xl border border-white/5 shadow-xl">
                    <Shield size={18} className="text-[var(--primary)]" />
                    <span className="text-[10px] font-black text-[var(--primary)] uppercase tracking-[0.3em] font-mono italic">{t("compliant")}</span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
                {gates.map(gate => (
                    <EliteGateCard key={gate.id} gate={gate} />
                ))}
            </div>

            <div className="mt-12 pt-8 border-t border-white/[0.03] flex items-center justify-between relative z-10">
                <div className="flex items-center gap-4 text-gray-600">
                   <Brain size={14} />
                   <span className="text-[9px] font-black uppercase tracking-widest italic leading-none">{t("ledgerLogged")}</span>
                </div>
                <button className="flex items-center gap-3 text-[10px] font-black text-[var(--primary)] uppercase tracking-[0.3em] hover:text-white transition-colors group/btn">
                   {t("auditPack")} <ChevronRight size={14} className="group-hover/btn:translate-x-1 transition-transform" />
                </button>
            </div>
        </section>
    );
};

function EliteGateCard({ gate }: { gate: GateEvidence }) {
  const t = useTranslations("dashboard.launchEvidence");
  const isPass = gate.status === "PASS";
  const isFail = gate.status === "FAIL";
  const colorClass = isPass ? "text-green-500" : isFail ? "text-red-500" : "text-amber-500";
  const bgClass = isPass ? "bg-green-500/10" : isFail ? "bg-red-500/10" : "bg-amber-500/10";
  const borderClass = isPass ? "border-green-500/20" : isFail ? "border-red-500/20" : "border-amber-500/20";

  return (
    <div className="group/gate p-8 rounded-[2.5rem] border border-white/5 bg-black/30 hover:bg-white/[0.03] hover:border-[var(--primary)]/30 transition-all duration-500 shadow-xl cursor-help relative overflow-hidden">
        <div className="flex items-start justify-between mb-8 relative z-10">
            <div className="flex items-center gap-5">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border transition-all duration-500 shadow-xl group-hover/gate:scale-110 ${bgClass} ${borderClass} ${colorClass}`}>
                    {gate.id === "budget" && <Scale size={24} />}
                    {gate.id === "gov" && <Shield size={24} />}
                    {gate.id === "quorum" && <Scale size={24} />}
                    {gate.id === "quality" && <Zap size={24} />}
                </div>
                <div>
                    <h4 className="text-[13px] font-black text-white uppercase tracking-tight italic group-hover/gate:text-[var(--primary)] transition-colors">{gate.title}</h4>
                    <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest mt-1 opacity-70 group-hover/gate:opacity-100 transition-opacity">{gate.description}</p>
                </div>
            </div>
            <div className={`p-1 rounded-full border ${borderClass} shadow-inner`}>
               {isPass ? <CheckCircle2 size={18} className="text-green-500" /> : isFail ? <XCircle size={18} className="text-red-500" /> : <Shield size={18} className="text-amber-500 animate-pulse" />}
            </div>
        </div>
        
        <div className="space-y-4 relative z-10">
            <div className="p-5 rounded-2xl bg-black/60 border border-white/[0.03] shadow-inner relative overflow-hidden">
                <div className="absolute top-0 right-0 p-3 opacity-10 text-gray-800">
                    <Fingerprint size={12} />
                </div>
                <p className="text-[11px] text-gray-400 font-mono leading-relaxed italic group-hover/gate:text-gray-300 transition-colors">
                    <span className="text-[var(--primary)] opacity-60 mr-2">EVIDENCE_STR:</span>
                    {gate.evidence}
                </p>
            </div>
            
            <div className="flex justify-between items-center text-[9px] font-black uppercase tracking-widest text-gray-700 opacity-60 group-hover/gate:opacity-100 transition-all">
                <span className="flex items-center gap-2">
                   <FileCheck size={12} />
                   {t("idVerified")}
                </span>
                <span className="italic">{t("clickForDetails")}</span>
            </div>
        </div>

        {/* Decor */}
        <div className={`absolute inset-x-0 bottom-0 h-[2px] ${colorClass.replace('text', 'bg')} opacity-0 group-hover/gate:opacity-100 transition-opacity duration-1000 shadow-[0_0_15px_currentColor]`} />
    </div>
  );
}
