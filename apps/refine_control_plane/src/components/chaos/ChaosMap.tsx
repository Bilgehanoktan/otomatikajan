"use client";

import React, { useMemo } from "react";
import { Globe, ShieldAlert, Cpu, Activity, Zap, Server, Wifi } from "lucide-react";

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
  // Define node positions based on regions
  // In a real app, these could be geo-mapped or force-directed
  const nodes = useMemo(() => {
    const layout = [
      { x: "20%", y: "45%" }, // US
      { x: "50%", y: "40%" }, // EU
      { x: "80%", y: "55%" }, // ASIA
      { x: "45%", y: "75%" }, // AU/SA Placeholder
    ];
    return regions.map((r, i) => ({
      ...r,
      ...layout[i % layout.length]
    }));
  }, [regions]);

  return (
    <div className="relative w-full h-[550px] bg-[#0b0c10]/40 rounded-3xl border border-[#1f2833] overflow-hidden backdrop-blur-md group shadow-[inset_0_0_50px_rgba(31,40,51,0.5)]">
      {/* SCANLINE EFFECT */}
      <div className="absolute inset-0 pointer-events-none z-20 opacity-[0.03] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(102,252,241,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%]"></div>
      
      {/* BACKGROUND GRID */}
      <div className="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] pointer-events-none"></div>
      
      {/* HEADER OVERLAY */}
      <div className="absolute top-8 left-8 z-30">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-[#66fcf1]/10 rounded-xl border border-[#66fcf1]/30 shadow-[0_0_20px_rgba(102,252,241,0.1)]">
            <Globe className="w-6 h-6 text-[#66fcf1] animate-spin-slow" />
          </div>
          <div>
            <h3 className="text-white text-lg font-black tracking-tight flex items-center gap-2 uppercase">
              Omni-Mesh Core
              <span className="text-[10px] bg-green-500/20 text-green-400 px-2 py-0.5 rounded border border-green-500/30 font-black">ENCRYPTED</span>
            </h3>
            <p className="text-[#45a29e] text-[10px] uppercase tracking-[0.2em] font-black mt-0.5 opacity-70">Sovereign Layer-0 Topology</p>
          </div>
        </div>
      </div>

      {/* SVG LAYER FOR LINKS & ANIMATIONS */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        
        {/* Connection Lines */}
        {nodes.map((n, i) => {
          if (i === nodes.length - 1) return null;
          const next = nodes[i + 1];
          return (
            <LinkLine 
              key={`${n.id}-${next.id}`} 
              x1={n.x} y1={n.y} x2={next.x} y2={next.y} 
              status={n.health === 'critical' || next.health === 'critical' ? 'down' : 'active'} 
              latency={Math.max(n.latency, next.latency)} 
            />
          );
        })}
        
        {/* Cross-Link (Simulated) */}
        {nodes.length > 2 && (
           <LinkLine x1={nodes[0].x} y1={nodes[0].y} x2={nodes[nodes.length-1].x} y2={nodes[nodes.length-1].y} status="active" latency={142} />
        )}
      </svg>

      {/* REGION NODES */}
      <div className="absolute inset-0 z-20">
        {nodes.map((region) => (
          <div 
            key={region.id} 
            className="absolute -translate-x-1/2 -translate-y-1/2 transition-all duration-700"
            style={{ left: region.x, top: region.y }}
          >
            <RegionNode region={region} />
          </div>
        ))}
      </div>

      {/* FOOTER STATS */}
      <div className="absolute bottom-10 right-10 flex gap-6 z-30">
        <StatBadge icon={<Activity size={14}/>} label="Federation Quorum" value="LOCKED" color="text-green-400" />
        <StatBadge icon={<Zap size={14}/>} label="Global Consensus" value="1.4ms" color="text-[#66fcf1]" />
        <StatBadge icon={<Wifi size={14}/>} label="Mesh Drift" value="0.002%" color="text-blue-400" />
      </div>
    </div>
  );
}

function RegionNode({ region }: { region: RegionStatus }) {
  const isHealthy = region.health === "healthy";
  const isCritical = region.health === "critical";

  return (
    <div className="group/node cursor-crosshair">
      <div className="flex flex-col items-center gap-4 transition-all duration-500 hover:scale-110">
        <div className={`relative p-6 rounded-3xl border-2 backdrop-blur-2xl shadow-2xl transition-all duration-500 ${
          isHealthy 
            ? 'border-[#66fcf1]/50 bg-[#1f2833]/80 shadow-[#66fcf1]/20' 
            : isCritical 
              ? 'border-red-500 bg-red-900/40 shadow-red-500/30 animate-pulse' 
              : 'border-yellow-500/50 bg-yellow-900/30 shadow-yellow-500/20'
        }`}>
          {/* PULSE RINGS */}
          {isHealthy && (
            <>
              <div className="absolute inset-0 rounded-3xl bg-[#66fcf1]/10 animate-ping opacity-10"></div>
              <div className="absolute -inset-2 rounded-[2rem] border border-[#66fcf1]/20 scale-110 opacity-40 group-hover/node:scale-125 transition-transform duration-1000"></div>
            </>
          )}
          
          <div className="relative z-10 flex flex-col items-center justify-center">
            {isHealthy ? (
              <Cpu className="w-10 h-10 text-[#66fcf1] group-hover/node:rotate-90 transition-transform duration-500" />
            ) : isCritical ? (
              <ShieldAlert className="w-10 h-10 text-red-500" />
            ) : (
              <Server className="w-10 h-10 text-yellow-500" />
            )}
            
            <div className="mt-3 flex gap-1">
               <div className={`w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500'} shadow-[0_0_5px_currentColor]`}></div>
               <div className="w-1.5 h-1.5 rounded-full bg-white/10"></div>
               <div className="w-1.5 h-1.5 rounded-full bg-white/10"></div>
            </div>
          </div>
        </div>
        
        <div className="text-center bg-[#0b0c10]/80 px-4 py-2 rounded-xl border border-[#1f2833] backdrop-blur-md opacity-90 group-hover/node:opacity-100 transition-opacity">
          <h4 className="text-white text-xs font-black tracking-widest uppercase mb-0.5">{region.name}</h4>
          <div className="flex items-center gap-2 justify-center">
            <span className={`text-[9px] font-black font-mono tracking-tighter px-1.5 py-0.5 rounded uppercase border ${
              isHealthy ? 'text-[#66fcf1] border-[#66fcf1]/20 bg-[#66fcf1]/5' : 'text-red-400 border-red-500/20 bg-red-500/5'
            }`}>
              {region.role}
            </span>
            <span className="text-[10px] text-white/40 font-mono">{region.latency}ms</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkLine({ x1, y1, x2, y2, status, latency }: any) {
  const isDown = status === "down";
  const isHighLatency = latency > 150;
  
  const strokeColor = isDown ? "#ef4444" : isHighLatency ? "#f59e0b" : "#66fcf1";
  const speed = Math.max(0.5, latency / 50);

  return (
    <>
      {/* GLOWING BACKGROUND LINE */}
      <line 
        x1={x1} y1={y1} x2={x2} y2={y2} 
        stroke={strokeColor} 
        strokeWidth="4" 
        strokeLinecap="round"
        className="opacity-[0.05]"
        filter="url(#glow)"
      />
      
      {/* CORE CONNECTION LINE */}
      <line 
        x1={x1} y1={y1} x2={x2} y2={y2} 
        stroke={strokeColor} 
        strokeWidth="1.5" 
        strokeDasharray={isDown ? "6 6" : isHighLatency ? "20 10" : "0"}
        opacity={isDown ? "0.2" : "0.6"}
        className={isHighLatency && !isDown ? "animate-pulse" : ""}
      />

      {/* DATA PACKETS */}
      {!isDown && (
        <>
          <circle r="2.5" fill={strokeColor} className="shadow-[0_0_10px_currentColor]">
            <animateMotion 
              dur={`${speed}s`} 
              repeatCount="indefinite" 
              path={`M ${x1} ${y1} L ${x2} ${y2}`} 
            />
          </circle>
          <circle r="1.5" fill={strokeColor} opacity="0.6">
            <animateMotion 
              dur={`${speed}s`} 
              begin={`${speed / 2}s`}
              repeatCount="indefinite" 
              path={`M ${x1} ${y1} L ${x2} ${y2}`} 
            />
          </circle>
        </>
      )}
    </>
  );
}

function StatBadge({ icon, label, value, color }: any) {
  return (
    <div className="px-5 py-3 rounded-2xl bg-[#0b0c10]/60 border border-[#1f2833] flex items-center gap-4 backdrop-blur-xl group hover:border-[#66fcf1]/30 transition-all shadow-xl hover:translate-y-[-2px]">
      <div className="p-2 bg-[#1f2833] rounded-lg text-[#66fcf1] group-hover:bg-[#66fcf1] group-hover:text-[#0b0c10] transition-colors">{icon}</div>
      <div className="flex flex-col">
        <span className="text-[10px] font-black text-[#45a29e] uppercase tracking-widest leading-none mb-1">{label}</span>
        <span className={`text-[13px] font-black font-mono tracking-tighter ${color} leading-none`}>{value}</span>
      </div>
    </div>
  );
}
