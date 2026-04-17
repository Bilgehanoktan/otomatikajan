"use client";

import React from "react";
import { 
    Rocket, 
    CheckCircle2, 
    Clock, 
    ArrowUpRight,
    BarChart,
    ExternalLink,
    ShieldCheck,
    Cpu
} from "lucide-react";

export default function HandoverStatusPage() {
    // Mock data based on the Phase 31 Pilot Rollout
    const rollouts = [
        {
            id: "f462f604",
            name: "Resilience Pilot v1",
            status: "LIVE",
            tier: "Tier-2",
            progress: 100,
            launchedAt: "2026-04-17 19:23:29",
            auditBundle: "LAUNCH_f462f604_61319b0a.zip",
            observability: "Healthy",
            autonomy: "Advisory Mode"
        }
    ];

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-700">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/5 pb-8">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#66fcf1]" />
                        <span className="text-[10px] uppercase tracking-[0.3em] font-bold text-[#45a29e]">Operational Deployment</span>
                    </div>
                    <h1 className="text-4xl font-black text-white tracking-tight">ROLLOUT MERKEZİ</h1>
                    <p className="text-gray-400 mt-2 max-w-xl">Canlıya aktarımı tamamlanan veya devam eden pilot projelerin operasyonel takibi.</p>
                </div>
                
                <div className="flex gap-4">
                    <div className="glass-card px-6 py-4 flex items-center gap-4">
                        <div className="text-right">
                            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Aktif Pilotlar</p>
                            <p className="text-2xl font-black text-white tracking-tighter">01</p>
                        </div>
                        <div className="w-px h-8 bg-white/10" />
                        <div className="text-right">
                            <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Success Rate</p>
                            <p className="text-2xl font-black text-[#66fcf1] tracking-tighter">100%</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Active Rollouts */}
            <div className="space-y-6">
                <h3 className="text-[10px] uppercase tracking-[0.3em] text-[#45a29e] font-black">CANLI PİLOTLAR</h3>
                
                <div className="grid grid-cols-1 gap-6">
                    {rollouts.map((rollout) => (
                        <div key={rollout.id} className="glass-card overflow-hidden group hover:border-[#66fcf1]/20 transition-all duration-500">
                            <div className="flex flex-col xl:flex-row divide-y xl:divide-y-0 xl:divide-x divide-white/5">
                                {/* Left Section: Identity */}
                                <div className="p-8 xl:w-1/3 bg-gradient-to-br from-white/[0.02] to-transparent">
                                    <div className="flex items-start justify-between mb-8">
                                        <div className="p-4 bg-white/5 rounded-2xl border border-white/5 group-hover:scale-110 transition-transform duration-500">
                                            <Rocket className="text-[#66fcf1]" size={32} />
                                        </div>
                                        <div className="flex items-center gap-2 bg-[#66fcf1]/10 px-3 py-1 rounded-full border border-[#66fcf1]/20">
                                            <div className="w-1.5 h-1.5 rounded-full bg-[#66fcf1] animate-pulse" />
                                            <span className="text-[10px] font-black tracking-widest text-[#66fcf1] italic uppercase">{rollout.status}</span>
                                        </div>
                                    </div>
                                    
                                    <h2 className="text-2xl font-black text-white mb-2 italic uppercase tracking-tighter">{rollout.name}</h2>
                                    <p className="text-xs text-gray-500 font-mono mb-6 uppercase tracking-widest">PROJECT_ID: {rollout.id}</p>
                                    
                                    <div className="space-y-3">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-gray-500 font-bold uppercase tracking-widest text-[9px]">Lansman Zamanı</span>
                                            <span className="text-gray-300 font-mono italic">{rollout.launchedAt}</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-gray-500 font-bold uppercase tracking-widest text-[9px]">İzolasyon Katmanı</span>
                                            <span className="text-gray-300">{rollout.tier}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Middle Section: Metrics */}
                                <div className="p-8 flex-1 grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                                    <div className="text-center space-y-2">
                                        <div className="inline-flex p-3 bg-white/5 rounded-xl border border-white/5 mb-2">
                                            <ShieldCheck size={20} className="text-[#45a29e]" />
                                        </div>
                                        <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Audit Bundle</p>
                                        <p className="text-xs text-white font-mono truncate px-4">{rollout.auditBundle}</p>
                                    </div>
                                    <div className="text-center space-y-2">
                                        <div className="inline-flex p-3 bg-white/5 rounded-xl border border-white/5 mb-2">
                                            <BarChart size={20} className="text-[#45a29e]" />
                                        </div>
                                        <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Observability</p>
                                        <p className="text-xs text-[#66fcf1] font-bold uppercase tracking-tighter italic">{rollout.observability}</p>
                                    </div>
                                    <div className="text-center space-y-2">
                                        <div className="inline-flex p-3 bg-white/5 rounded-xl border border-white/5 mb-2">
                                            <Cpu size={20} className="text-[#45a29e]" />
                                        </div>
                                        <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Autonomy Level</p>
                                        <p className="text-xs text-yellow-500 font-bold uppercase tracking-tighter italic">{rollout.autonomy}</p>
                                    </div>
                                </div>

                                {/* Right Section: Actions */}
                                <div className="p-8 xl:w-72 flex flex-col justify-center gap-3 bg-white/[0.01]">
                                    <button className="w-full flex items-center justify-between px-5 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-all border border-white/5 text-xs font-bold uppercase tracking-widest">
                                        Logları İzle
                                        <ArrowUpRight size={14} />
                                    </button>
                                    <button className="w-full flex items-center justify-between px-5 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-all border border-white/5 text-xs font-bold uppercase tracking-widest">
                                        Audit Paketi
                                        <ExternalLink size={14} />
                                    </button>
                                    <button className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-xl transition-all border border-red-500/10 text-xs font-black uppercase tracking-[0.2em]">
                                        Freeze
                                    </button>
                                </div>
                            </div>
                            
                            {/* Handover Progress Bar */}
                            <div className="h-1 w-full bg-white/5">
                                <div className="h-full bg-gradient-to-r from-[#45a29e] to-[#66fcf1] shadow-[0_0_10px_rgba(102,252,241,0.5)]" style={{ width: '100%' }} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Empty States / Future Capacity */}
            <div className="glass-card p-12 border-dashed border-2 flex flex-col items-center text-center space-y-4 opacity-40">
                <div className="p-6 bg-white/5 rounded-full">
                    <Clock size={48} className="text-gray-500" />
                </div>
                <h3 className="text-lg font-bold text-gray-400 italic">SIRADAKİ PİLOT BEKLENİYOR</h3>
                <p className="text-sm text-gray-500 max-w-sm">Tüm lansman kriterleri karşılandığında Tier-1 projeleri burada listedenecektir.</p>
            </div>
        </div>
    );
}
