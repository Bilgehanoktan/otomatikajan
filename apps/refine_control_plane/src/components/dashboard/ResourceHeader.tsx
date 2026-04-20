"use client";

import React from "react";
import { ArrowLeft } from "lucide-react";

interface ResourceHeaderProps {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  badge?: string;
  onBack?: () => void;
  actions?: React.ReactNode;
  staleMeta?: {
    is_stale: boolean;
    age_seconds: number;
    source: string;
  };
}

export function ResourceHeader({ title, subtitle, icon, badge, onBack, actions, staleMeta }: ResourceHeaderProps) {
  return (
    <header className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-6">
      <div className="flex items-center gap-6">
        <div className="relative group">
           <div className="p-4 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-[0_0_30px_rgba(102,252,241,0.05)] group-hover:border-[var(--primary)]/40 transition-all duration-500">
             <div className="text-[var(--primary)] group-hover:scale-110 transition-transform duration-500">
               {icon}
             </div>
           </div>
           {/* Glow effect */}
           <div className="absolute -inset-1 bg-[var(--primary)]/10 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
        </div>
        
        <div>
          <div className="flex items-center gap-3">
            {onBack && (
              <button 
                onClick={onBack}
                className="p-1 hover:bg-white/5 rounded-full text-gray-500 hover:text-white transition-all mr-1"
              >
                <ArrowLeft size={16} />
              </button>
            )}
            <h1 className="text-4xl font-black text-white tracking-tighter leading-none">
              {title}
            </h1>
            {badge && (
               <span className="px-2 py-0.5 rounded bg-[var(--primary)]/20 border border-[var(--primary)]/30 text-[9px] text-[var(--primary)] font-black uppercase tracking-widest h-fit">
                  {badge}
               </span>
            )}
            {staleMeta?.is_stale && (
               <span className="px-2 py-0.5 rounded bg-orange-500/10 border border-orange-500/20 text-[9px] text-orange-400 font-black uppercase tracking-widest h-fit flex items-center gap-1 animate-pulse">
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.6)]" />
                  Degraded (T-{staleMeta.age_seconds}s)
               </span>
            )}
          </div>
          <p className="text-gray-500 tracking-[0.25em] text-[10px] font-black uppercase mt-3 opacity-80 flex items-center gap-2">
            <span className="w-1 h-1 rounded-full bg-[var(--primary)]/60 animate-pulse" />
            {subtitle}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {actions}
      </div>
    </header>
  );
}
