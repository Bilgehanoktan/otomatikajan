"use client";

import React from "react";
import { ShieldCheck, ShieldAlert, Users, Info } from "lucide-react";

interface QuorumProps {
  totalNodes: number;
  healthyNodes: number;
  isMaintained: boolean;
}

export default function QuorumHealthPanel({ totalNodes, healthyNodes, isMaintained }: QuorumProps) {
  const quorumRequired = Math.floor(totalNodes / 2) + 1;
  const healthPercentage = (healthyNodes / totalNodes) * 100;
  
  return (
    <div className="p-6 rounded-2xl border border-[#1f2833] bg-[#1f2833]/20 backdrop-blur-xl relative overflow-hidden group">
      {/* HEADER */}
      <div className="flex justify-between items-start mb-8">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isMaintained ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'} border`}>
            {isMaintained ? <ShieldCheck className="text-green-400 w-5 h-5" /> : <ShieldAlert className="text-red-500 w-5 h-5 animate-pulse" />}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">Quorum Integrity</h2>
            <p className="text-[#45a29e] text-[10px] uppercase tracking-widest font-mono">Split-Brain Protection Level</p>
          </div>
        </div>
        <div className="text-right">
          <span className={`text-2xl font-black font-mono tracking-tighter ${isMaintained ? 'text-white' : 'text-red-500'}`}>
            {healthyNodes} / {totalNodes}
          </span>
          <p className="text-[#45a29e] text-[10px] font-mono mt-1">ACTIVE REGIONS</p>
        </div>
      </div>

      {/* GAUGE / PROGRESS */}
      <div className="relative h-4 w-full bg-[#1f2833] rounded-full overflow-hidden mb-8 border border-white/5">
        <div 
          className={`h-full transition-all duration-1000 ease-out shadow-[0_0_15px_rgba(102,252,241,0.3)] ${
            isMaintained ? 'bg-gradient-to-r from-[#45a29e] to-[#66fcf1]' : 'bg-red-500 shadow-red-500/40'
          }`} 
          style={{ width: `${healthPercentage}%` }}
        ></div>
        {/* QUORUM THRESHOLD MARKER */}
        <div 
          className="absolute top-0 bottom-0 w-1 bg-white/40 shadow-[0_0_8px_white]" 
          style={{ left: `${(quorumRequired / totalNodes) * 100}%` }}
          title="Quorum Threshold"
        ></div>
      </div>

      {/* METRICS GRID */}
      <div className="grid grid-cols-2 gap-4">
        <MetricCard 
          icon={<Users size={14}/>} 
          label="Req. Major" 
          value={`${quorumRequired} Nodes`} 
          sub="Min. For Decision"
        />
        <MetricCard 
          icon={<Info size={14}/>} 
          label="Risk Factor" 
          value={healthyNodes <= quorumRequired ? "CRITICAL" : "LOW"} 
          sub="Separation Probability"
          danger={healthyNodes <= quorumRequired}
        />
      </div>

      {/* ADVISORY MODE STATUS */}
      {!isMaintained && (
        <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex gap-4 items-center">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-ping"></div>
          <p className="text-xs text-red-400 font-medium italic">
            Mesh partitioned. Advisory Mode (Read-Only) enforced globally to prevent state corruption.
          </p>
        </div>
      )}
    </div>
  );
}

function MetricCard({ icon, label, value, sub, danger = false }: any) {
  return (
    <div className="p-3 rounded-xl bg-[#0b0c10]/40 border border-[#1f2833] flex items-center gap-4 group-hover:border-[#66fcf1]/20 transition-colors">
      <div className={`p-2 rounded-lg ${danger ? 'bg-red-500/10 text-red-400' : 'bg-[#1f2833] text-[#45a29e]'}`}>
        {icon}
      </div>
      <div>
        <p className="text-[10px] text-[#45a29e] font-mono uppercase tracking-tighter">{label}</p>
        <p className={`text-sm font-bold ${danger ? 'text-red-500' : 'text-white'}`}>{value}</p>
        <p className="text-[9px] text-white/30">{sub}</p>
      </div>
    </div>
  );
}
