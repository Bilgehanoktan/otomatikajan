"use client";

import React from "react";
import { Globe, ShieldAlert, Cpu, Activity, Zap } from "lucide-react";

interface RegionStatus {
  id: string;
  name: string;
  role: string;
  health: "healthy" | "degraded" | "critical";
  latency: number;
}

interface ChaosMapProps {
  regions: RegionStatus[];
  links: { from: string; to: string; latency: number; status: "active" | "down" }[];
}

export default function ChaosMap({ regions, links }: ChaosMapProps) {
  return (
    <div className="relative w-full h-[500px] bg-[#0b0c10]/40 rounded-3xl border border-[#1f2833] overflow-hidden backdrop-blur-sm group">
      {/* BACKGROUND GRID EFFECT */}
      <div className="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] pointer-events-none"></div>
      
      {/* HEADER OVERLAY */}
      <div className="absolute top-6 left-6 z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#66fcf1]/10 rounded-lg border border-[#66fcf1]/30">
            <Globe className="w-5 h-5 text-[#66fcf1] animate-spin-slow" />
          </div>
          <div>
            <h3 className="text-white font-bold tracking-tight">Geo-Spatial Mesh Core</h3>
            <p className="text-[#45a29e] text-[10px] uppercase tracking-widest font-mono">Real-time Federation Topology</p>
          </div>
        </div>
      </div>

      {/* SVG LAYER FOR LINKS */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          <linearGradient id="latencyGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#66fcf1" stopOpacity="0" />
            <stop offset="50%" stopColor="#66fcf1" stopOpacity="1" />
            <stop offset="100%" stopColor="#66fcf1" stopOpacity="0" />
          </linearGradient>
        </defs>
        
        {/* Connection Lines (Simulated between fixed positions for now) */}
        <LinkLine x1="20%" y1="40%" x2="50%" y2="50%" status="active" latency={85} />
        <LinkLine x1="50%" y1="50%" x2="80%" y2="40%" status="active" latency={160} />
        <LinkLine x1="20%" y1="40%" x2="80%" y2="40%" status="down" latency={200} />
      </svg>

      {/* REGION NODES */}
      <div className="absolute inset-0 flex justify-around items-center px-10">
        {regions.map((region) => (
          <RegionNode key={region.id} region={region} />
        ))}
      </div>

      {/* FOOTER STATS */}
      <div className="absolute bottom-6 right-6 flex gap-4">
        <StatBadge icon={<Activity size={12}/>} label="Quorum" value="SECURE" color="text-green-400" />
        <StatBadge icon={<Zap size={12}/>} label="Mesh Lag" value="42ms" color="text-[#66fcf1]" />
      </div>
    </div>
  );
}

function RegionNode({ region }: { region: RegionStatus }) {
  const isHealthy = region.health === "healthy";
  return (
    <div className="flex flex-col items-center gap-4 transition-transform hover:scale-105">
      <div className={`relative p-5 rounded-2xl border-2 backdrop-blur-xl shadow-2xl transition-all duration-500 ${
        isHealthy 
          ? 'border-[#66fcf1]/50 bg-[#1f2833]/80 shadow-[#66fcf1]/20' 
          : 'border-red-500/50 bg-red-900/30 shadow-red-500/20'
      }`}>
        {/* PULSE RING */}
        {isHealthy && (
          <div className="absolute inset-0 rounded-2xl bg-[#66fcf1]/20 animate-ping opacity-20"></div>
        )}
        
        <div className="relative z-10">
          {isHealthy ? <Cpu className="w-8 h-8 text-[#66fcf1]" /> : <ShieldAlert className="w-8 h-8 text-red-500" />}
        </div>
      </div>
      
      <div className="text-center">
        <h4 className="text-white text-sm font-bold tracking-tight uppercase">{region.name}</h4>
        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
          isHealthy ? 'text-[#66fcf1] border-[#66fcf1]/20' : 'text-red-400 border-red-500/20'
        }`}>
          {region.role}
        </span>
      </div>
    </div>
  );
}

function LinkLine({ x1, y1, x2, y2, status, latency }: any) {
  const isDown = status === "down";
  return (
    <>
      <line 
        x1={x1} y1={y1} x2={x2} y2={y2} 
        stroke={isDown ? "#ef4444" : "#66fcf1"} 
        strokeWidth="1" 
        strokeDasharray={isDown ? "4 4" : "0"}
        opacity={isDown ? "0.3" : "0.5"}
      />
      {!isDown && (
        <circle r="3" fill="#66fcf1" opacity="0.8">
          <animateMotion 
            dur={`${latency / 20}s`} 
            repeatCount="indefinite" 
            path={`M ${x1} ${y1} L ${x2} ${y2}`} 
          />
        </circle>
      )}
    </>
  );
}

function StatBadge({ icon, label, value, color }: any) {
  return (
    <div className="px-3 py-1.5 rounded-lg bg-[#1f2833]/60 border border-[#1f2833] flex items-center gap-2 backdrop-blur-md">
      <span className="text-[#45a29e]">{icon}</span>
      <span className="text-[10px] font-medium text-white/60 uppercase">{label}:</span>
      <span className={`text-[10px] font-bold font-mono ${color}`}>{value}</span>
    </div>
  );
}
