"use client";

import React from "react";
import { Skeleton } from "./Skeleton";

interface MetricCardProps {
  label: string;
  value: string | number;
  subLabel?: string;
  color: string;
  barPct?: number;
  barColor?: string;
  icon: React.ReactNode;
  hero?: boolean;
  loading?: boolean;
}

export function MetricCard({
  label,
  value,
  subLabel,
  color,
  barPct,
  barColor,
  icon,
  hero,
  loading,
}: MetricCardProps) {
  const resolveBarColor = () => {
    if (barColor) return barColor;
    if (color.includes("teal") || color.includes("cyan") || color.includes("[var(--primary)]")) return "#66fcf1";
    if (color.includes("green")) return "#48bb78";
    if (color.includes("red")) return "#f56565";
    if (color.includes("amber") || color.includes("yellow")) return "#ed8936";
    return "#45a29e";
  };

  if (loading) {
    return (
      <div className={`rounded-2xl border border-white/[0.05] backdrop-blur-md ${
        hero ? "p-6 bg-[#0e1320]/75 shadow-none" : "p-5 bg-[#0e1320]/75 shadow-none"
      }`}>
        <div className="flex items-start justify-between mb-4">
          <Skeleton className="h-2 w-20" />
          <div className="p-1.5 rounded-lg bg-white/5 border border-white/5">
               <Skeleton className="h-4 w-4 rounded-md" />
          </div>
        </div>
        <Skeleton className={`${hero ? "h-12 w-32" : "h-10 w-20"} mb-3`} />
        <Skeleton className="h-2 w-24 opacity-50" />
        {barPct !== undefined && <Skeleton className="h-[2px] w-full mt-4" />}
      </div>
    );
  }

  return (
    <div className={`group relative overflow-hidden rounded-2xl border backdrop-blur-md transition-all duration-500 ${
      hero
        ? "border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.04] to-[#0e1320]/90 p-6 shadow-[0_8px_32px_-4px_rgba(0,0,0,0.5)] hover:border-[var(--primary)]/30 hover:shadow-[0_8px_32px_-4px_rgba(0,0,0,0.6),0_0_20px_var(--primary-glow)]"
        : "border-white/[0.05] bg-[#0e1320]/80 p-5 hover:border-white/[0.15] hover:shadow-[0_8px_24px_-4px_rgba(0,0,0,0.4)]"
    }`}>
      <div className="flex items-start justify-between mb-4">
        <span className="text-[9px] font-black tracking-[0.25em] uppercase text-gray-500 font-mono group-hover:text-gray-400 transition-colors">{label}</span>
        <div className={`p-2 rounded-xl transition-all duration-500 ${hero ? "bg-[var(--primary)]/10 border border-[var(--primary)]/20" : "bg-white/5 border border-white/5 group-hover:bg-white/10 group-hover:border-white/10"}`}>
            {icon}
        </div>
      </div>
      
      <div className={`font-black leading-none transition-all duration-700 ${hero ? "text-[46px] tracking-tight group-hover:tracking-tighter" : "text-[32px]"} ${color}`}>
        {value}
      </div>
      
      {subLabel && (
        <div className="text-[10px] text-gray-500 mt-2.5 font-mono tracking-wider transition-colors duration-500 group-hover:text-gray-400">
            {subLabel}
        </div>
      )}
      
      {barPct !== undefined && (
        <div className={`${hero ? "mt-5 h-[3px]" : "mt-4 h-[2px]"} bg-white/[0.04] rounded-full overflow-hidden`}>
          <div
            className="h-full rounded-full transition-all duration-[1500ms] ease-out shadow-[0_0_8px_currentColor]"
            style={{ width: `${Math.min(barPct, 100)}%`, background: resolveBarColor(), color: resolveBarColor() }}
          />
        </div>
      )}
      
      {/* Premium subtle glow on hover */}
      {hero && (
        <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--primary)]/5 blur-[60px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
      )}
    </div>
  );
}
