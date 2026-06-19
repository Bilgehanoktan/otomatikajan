"use client";

import React from "react";
import { ArrowRight, Globe, Zap, Database, GitBranch } from "lucide-react";
import { useTranslations } from "next-intl";

interface QuickLinkProps {
  href: string;
  label: string;
  sub: string;
  external?: boolean;
}

export function QuickLink({ href, label, sub, external }: QuickLinkProps) {
  return (
    <a
      href={href}
      target={external ? "_blank" : undefined}
      rel={external ? "noreferrer" : undefined}
      className="flex items-center justify-between p-4 rounded-xl border border-white/[0.05] bg-white/[0.02] hover:bg-white/[0.05] hover:border-[var(--primary)]/30 hover:shadow-[0_4px_20px_rgba(102,252,241,0.05)] transition-all group"
    >
      <div className="flex items-center gap-4">
        <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center group-hover:bg-[var(--primary)]/10 transition-colors">
            <Globe size={14} className="text-gray-500 group-hover:text-[var(--primary)] transition-colors" />
        </div>
        <div>
          <div className="text-xs font-black text-white uppercase tracking-wider">{label}</div>
          <div className="text-[10px] text-gray-500 font-mono mt-1 group-hover:text-gray-400 transition-colors">{sub}</div>
        </div>
      </div>
      <ArrowRight
        size={14}
        className="text-gray-600 group-hover:text-[var(--primary)] group-hover:translate-x-1 transition-all flex-shrink-0 ml-4"
      />
    </a>
  );
}

export function ApiHub({ apiBase }: { apiBase: string }) {
  const t = useTranslations("dashboard");
  const adminLinks = [
    { label: t("quickAccess.refine"), sub: t("quickAccess.apiSub"), icon: <Zap size={20} />, href: "/docs", color: "text-[var(--primary)]", bg: "bg-[var(--primary)]/10" },
    { label: t("quickAccess.docs"), sub: t("quickAccess.redocSub"), icon: <GitBranch size={20} />, href: "/redoc", color: "text-violet-400", bg: "bg-violet-400/10" },
    { label: t("quickAccess.telemetry"), sub: t("quickAccess.jsonSub"), icon: <Globe size={20} />, href: `${apiBase}/health`, color: "text-blue-400", bg: "bg-blue-400/10" },
    { label: t("quickAccess.auditLedger"), sub: t("quickAccess.auditLedgerSub"), icon: <Database size={20} />, href: `${apiBase}/health/dashboard`, color: "text-amber-400", bg: "bg-amber-400/10" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        {adminLinks.map((link) => (
            <a 
              key={link.label} 
              href={link.href} 
              target="_blank" 
              rel="noreferrer"
              className="glass-panel p-6 rounded-[2rem] border-white/[0.04] bg-white/[0.012] hover:bg-white/[0.03] hover:border-[var(--primary)]/30 transition-all duration-500 group relative overflow-hidden"
            >
                <div className="flex items-center gap-5 relative z-10">
                   <div className={`p-4 ${link.bg} ${link.color} rounded-2xl border border-white/5 group-hover:scale-110 transition-transform`}>
                      {link.icon}
                   </div>
                   <div>
                      <h4 className="text-[12px] font-black text-white uppercase tracking-tight italic group-hover:text-[var(--primary)] transition-colors">{link.label}</h4>
                      <p className="text-[9px] text-gray-600 font-black uppercase tracking-widest mt-1 opacity-60 group-hover:opacity-100 transition-opacity">{link.sub}</p>
                   </div>
                </div>
                <div className="absolute top-0 right-0 p-6 opacity-[0.02] group-hover:opacity-[0.08] transition-opacity">
                   {link.icon}
                </div>
            </a>
        ))}
    </div>
  );
}
