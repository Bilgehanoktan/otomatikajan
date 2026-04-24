"use client";

import React, { useState, useEffect } from "react";
import { 
    Rocket, 
    CheckCircle2, 
    Clock, 
    ArrowUpRight,
    BarChart,
    ExternalLink,
    ShieldCheck,
    Cpu,
    Lock,
    Zap,
    Globe,
    Terminal,
    AlertTriangle,
    ChevronRight,
    Fingerprint
} from "lucide-react";
import { useRouter } from "next/navigation";
import { AuditBundleModal } from "@/components/ops/AuditBundleModal";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function HandoverStatusPage() {
    const router = useRouter();
    const [isClient, setIsClient] = useState(false);
    const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);
    const [selectedRollout, setSelectedRollout] = useState<any>(null);
    const [frozenRollouts, setFrozenRollouts] = useState<Set<string>>(new Set());

    useEffect(() => { setIsClient(true); }, []);

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

    const handleLogIzle = (id: string) => {
        router.push(`/workflows/${id}`);
    };

    const handleAuditPaketi = (rollout: any) => {
        setSelectedRollout(rollout);
        setIsAuditModalOpen(true);
    };

    const handleFreeze = (id: string) => {
        if (window.confirm("CRITICAL: EMERGENCY FREEZE activation will suspend all autonomous activities for this rollout. Are you sure?")) {
            setFrozenRollouts(prev => new Set([...prev, id]));
        }
    };

    if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

    return (
        <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
            
            <ResourceHeader 
                title="Rollout Center" 
                subtitle="High-Fidelity Tracking of Live Deployment Pilots & Handover Integrity" 
                icon={<Rocket size={32} />}
                badge="Mission Success"
                actions={
                    <div className="flex items-center gap-8">
                         <div className="flex flex-col items-end border-r border-white/5 pr-8">
                            <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Global Success</span>
                            <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono tracking-tighter italic">100% NOMINAL</span>
                         </div>
                         <div className="flex flex-col items-end">
                            <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Active Pilots</span>
                            <span className="text-sm font-black text-white mt-2">01 ACTIVE</span>
                         </div>
                    </div>
                }
            />

            <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
                {/* ACTIVE PILOTS STREAM */}
                <div className="xl:col-span-12 space-y-10">
                    <div className="flex items-center justify-between px-4">
                        <div className="flex items-center gap-4">
                           <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-pulse shadow-[0_0_12px_rgba(102,252,241,0.6)]" />
                           <h3 className="text-xs font-black text-white uppercase tracking-[0.4em] italic">Live Deployment Nodes</h3>
                        </div>
                        <div className="flex items-center gap-6">
                           <span className="text-[10px] font-mono text-gray-700 uppercase tracking-widest">DRIVE_ID: SOV-RO-12</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 gap-10">
                        {rollouts.map((rollout) => {
                            const isFrozen = frozenRollouts.has(rollout.id);
                            return (
                                <EliteRolloutCard 
                                    key={rollout.id}
                                    rollout={rollout}
                                    isFrozen={isFrozen}
                                    onLogView={handleLogIzle}
                                    onAuditBundle={handleAuditPaketi}
                                    onFreeze={handleFreeze}
                                />
                            );
                        })}
                    </div>
                </div>

                {/* CAPACITY & FUTURE STATE */}
                <div className="xl:col-span-12 pt-10">
                    <section className="glass-panel p-16 rounded-[4rem] border-dashed border-2 border-white/5 bg-white/[0.01] flex flex-col items-center justify-center text-center group transition-all hover:border-[var(--primary)]/10">
                        <div className="p-8 bg-black/40 rounded-full border border-white/5 mb-8 group-hover:scale-110 transition-transform duration-700">
                            <Clock size={48} className="text-gray-600 group-hover:text-[var(--primary)] transition-colors" />
                        </div>
                        <h3 className="text-xl font-black text-gray-500 uppercase tracking-[0.4em] italic group-hover:text-white transition-colors">Awaiting Next Pilot</h3>
                        <p className="text-sm text-gray-600 font-bold max-w-sm mt-4 uppercase tracking-widest leading-loose opacity-60">
                            Tier-1 projects will be listed here once all launch criteria and verifier mesh benchmarks are satisfied.
                        </p>
                    </section>
                </div>
            </div>

            {/* Modals */}
            <AuditBundleModal 
                isOpen={isAuditModalOpen} 
                onClose={() => setIsAuditModalOpen(false)} 
                rollout={selectedRollout}
            />
        </div>
    );
}

function EliteRolloutCard({ rollout, isFrozen, onLogView, onAuditBundle, onFreeze }: any) {
    return (
        <div className={`glass-panel rounded-[3rem] border-white/[0.04] bg-[#060a12]/50 relative overflow-hidden group shadow-[0_32px_128px_rgba(0,0,0,0.5)] transition-all duration-1000 ${isFrozen ? 'border-red-500/20' : 'hover:border-[var(--primary)]/20'}`}>
            {/* Frozen UI Shield */}
            {isFrozen && (
                <div className="absolute inset-0 z-20 bg-red-950/30 backdrop-blur-sm flex items-center justify-center">
                    <div className="flex flex-col items-center gap-6 animate-in zoom-in duration-500">
                        <div className="p-8 bg-red-600 rounded-full shadow-[0_0_100px_rgba(220,38,38,0.5)] animate-pulse">
                            <Lock size={64} className="text-white" />
                        </div>
                        <div className="text-center">
                            <h2 className="text-3xl font-black text-white uppercase tracking-[0.5em] italic">Safety Freeze</h2>
                            <p className="text-red-400 text-[10px] font-black uppercase tracking-[0.3em] mt-3">All Autonomous Activities Suspended</p>
                        </div>
                    </div>
                </div>
            )}

            <div className={`flex flex-col xl:flex-row divide-y xl:divide-y-0 xl:divide-x divide-white/[0.03] ${isFrozen ? 'grayscale opacity-30 contrast-150' : ''}`}>
                {/* SECTION 1: Identity & Vitality */}
                <div className="p-10 xl:w-1/3 bg-gradient-to-br from-white/[0.02] to-transparent relative">
                    <div className="absolute top-0 right-0 p-8 opacity-[0.015] pointer-events-none group-hover:opacity-[0.05] transition-opacity">
                        <Fingerprint size={160} className="text-[var(--primary)]" />
                    </div>
                    
                    <div className="flex items-start justify-between mb-12 relative z-10">
                        <div className="p-5 bg-black/40 rounded-[2rem] border border-white/5 shadow-2xl group-hover:scale-110 transition-transform duration-700">
                            <Rocket size={32} className="text-[var(--primary)]" />
                        </div>
                        <div className="flex items-center gap-3 px-5 py-2 rounded-2xl bg-[var(--primary)]/10 border border-[var(--primary)]/20 text-[var(--primary)] shadow-[0_0_20px_rgba(102,252,241,0.1)]">
                            <div className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] animate-pulse" />
                            <span className="text-[10px] font-black tracking-[0.2em] uppercase italic">Node Live</span>
                        </div>
                    </div>

                    <h2 className="text-3xl font-black text-white italic uppercase tracking-tighter mb-2 relative z-10">{rollout.name}</h2>
                    <p className="text-[10px] text-gray-700 font-mono font-black uppercase tracking-[0.3em] mb-10 relative z-10">PID: {rollout.id.toUpperCase()}</p>
                    
                    <div className="space-y-4 relative z-10">
                        <div className="flex justify-between items-center px-2">
                           <span className="text-[9px] text-gray-600 font-black uppercase tracking-widest">Launched</span>
                           <span className="text-[11px] text-gray-300 font-mono font-black italic">{rollout.launchedAt}</span>
                        </div>
                        <div className="flex justify-between items-center px-2">
                           <span className="text-[9px] text-gray-600 font-black uppercase tracking-widest">Enclave Tier</span>
                           <span className="text-[11px] text-gray-300 font-black uppercase tracking-widest border-b border-[var(--primary)]/30 pb-1">{rollout.tier}</span>
                        </div>
                    </div>
                </div>

                {/* SECTION 2: Telemetry Matrix */}
                <div className="p-10 flex-1 grid grid-cols-1 md:grid-cols-3 gap-10 items-center bg-white/[0.005]">
                    <EliteMetricNode label="Audit Integrity" val={rollout.auditBundle} icon={<ShieldCheck size={24} />} isMono />
                    <EliteMetricNode label="Observability" val={rollout.observability} icon={<BarChart size={24} />} isHighlight />
                    <EliteMetricNode label="Autonomy Class" val={rollout.autonomy} icon={<Cpu size={24} />} isAlert />
                </div>

                {/* SECTION 3: Command Deck */}
                <div className="p-10 xl:w-80 flex flex-col justify-center gap-4 bg-black/20">
                    <EliteCommandButton label="Live Decision Logs" icon={<Terminal size={16} />} onClick={() => onLogView(rollout.id)} />
                    <EliteCommandButton label="Verify Audit Bundle" icon={<ExternalLink size={16} />} onClick={() => onAuditBundle(rollout)} />
                    <button 
                        disabled={isFrozen}
                        onClick={() => onFreeze(rollout.id)}
                        className={`w-full py-5 rounded-2xl border transition-all duration-500 text-[10px] font-black uppercase tracking-[0.3em] active:scale-95 flex items-center justify-center gap-3
                            ${isFrozen 
                                ? 'bg-red-500/50 text-white border-transparent cursor-not-allowed' 
                                : 'bg-red-500/10 hover:bg-red-600 text-red-500 hover:text-white border-red-500/20 hover:border-red-600 shadow-[0_0_20px_rgba(239,68,68,0.05)]'
                            }
                        `}
                    >
                        <AlertTriangle size={16} />
                        {isFrozen ? 'System Frozen' : 'Emergency Freeze'}
                    </button>
                </div>
            </div>

            {/* Holographic Progress Anchor */}
            <div className="h-1.5 w-full bg-white/5 relative overflow-hidden">
                <div 
                    className={`h-full shadow-[0_0_20px_currentColor] transition-all duration-1000 ${isFrozen ? 'bg-red-500 w-full text-red-500' : 'bg-gradient-to-r from-emerald-500 via-[var(--primary)] to-blue-500 w-full text-[var(--primary)]'}`} 
                />
            </div>
        </div>
    );
}

function EliteMetricNode({ label, val, icon, isMono, isHighlight, isAlert }: any) {
    return (
        <div className="flex flex-col items-center text-center gap-4 group/node">
            <div className={`p-5 rounded-[1.5rem] bg-black/40 border border-white/5 group-hover/node:border-[var(--primary)]/30 transition-all duration-500 shadow-xl group-hover/node:scale-110
                ${isHighlight ? 'text-[var(--primary)]' : isAlert ? 'text-yellow-500' : 'text-gray-600'}`}>
                {icon}
            </div>
            <div className="space-y-1">
                <p className="text-[9px] uppercase tracking-[0.2em] text-gray-600 font-black">{label}</p>
                <p className={`text-[11px] font-black uppercase tracking-tight max-w-[140px] truncate
                    ${isMono ? 'font-mono text-gray-400' : 'italic text-white'}`}>
                    {val}
                </p>
            </div>
        </div>
    );
}

function EliteCommandButton({ label, icon, onClick }: any) {
    return (
        <button 
            onClick={onClick}
            className="w-full flex items-center justify-between px-6 py-4 bg-white/[0.02] hover:bg-white/[0.08] border border-white/5 hover:border-[var(--primary)]/30 text-white rounded-2xl transition-all duration-500 group/btn active:scale-95 shadow-xl"
        >
            <span className="text-[10px] font-black uppercase tracking-widest">{label}</span>
            <div className="text-gray-600 group-hover/btn:text-[var(--primary)] transition-colors">
                {icon}
            </div>
        </button>
    );
}
