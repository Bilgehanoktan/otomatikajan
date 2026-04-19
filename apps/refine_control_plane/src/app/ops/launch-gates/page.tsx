"use client";

import React, { useState, useEffect } from "react";
import { 
    Activity, 
    Wallet, 
    ShieldAlert, 
    Users, 
    Zap,
    CheckCircle2,
    XCircle,
    Info,
    ArrowRight,
    Lock,
    Unlock,
    Rocket,
    ShieldCheck,
    AlertOctagon,
    Target
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function LaunchGatesPage() {
    const [isClient, setIsClient] = useState(false);
    useEffect(() => setIsClient(true), []);

    if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

    // Mock data based on the latest gatekeeper run
    const gates = [
        {
            id: "budget",
            title: "Bütçe Bütünlüğü",
            icon: <Wallet size={24} />,
            status: "PASS",
            metric: "$0.00 consumed",
            threshold: "Max $90.00 (90%)",
            detail: "Ekonomik drift tespit edilmedi. Cari tüketim limitler dahilinde."
        },
        {
            id: "governance",
            title: "Yönetişim Kilidi",
            icon: <ShieldAlert size={24} />,
            status: "PASS",
            metric: "Constitutional Guards Active",
            threshold: "Strict Lockdown",
            detail: "Kritik oturum sürücüleri (DB/Session) otonom değişime karşı kilitli."
        },
        {
            id: "quorum",
            title: "Mutabakat (Quorum)",
            icon: <Users size={24} />,
            status: "PASS",
            metric: "0 Pending Sign-offs",
            threshold: "Tier-1 Requirements",
            detail: "Bu katman için gerekli tüm operatör onayları tamamlanmış durumda."
        },
        {
            id: "accuracy",
            title: "Doğruluk Skorları",
            icon: <Target size={24} />,
            status: "PASS",
            metric: "0.94 Confidence",
            threshold: "Min 0.90",
            detail: "Sistem kararlılığı ve verifikasyon ağ skoru beklentilerin üzerinde."
        }
    ];

    return (
        <div className="p-8 min-h-screen bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
            
            <ResourceHeader 
                title="Launch Gates" 
                subtitle="Production Readiness Checkpoint & Rollout Protocols" 
                icon={<Rocket size={32} />}
                badge="Pre-Flight Tier"
                actions={
                  <div className="flex items-center gap-6">
                     <div className="glass-card !p-3 flex flex-col items-end border-green-500/20">
                        <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest">Global Ready</span>
                        <span className="text-sm font-black text-green-400">NOMINAL</span>
                     </div>
                     <div className="flex flex-col items-end">
                        <span className="text-[9px] text-gray-700 font-black uppercase tracking-widest italic">Protocol v2.1</span>
                     </div>
                  </div>
                }
            />

            {/* MAIN HUD SECTION */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 mb-10">
                {/* Readiness Gauge */}
                <div className="lg:col-span-8">
                   <section className="glass-panel p-1 py-10 rounded-[3rem] border-white/[0.03] bg-gradient-to-br from-white/[0.02] to-transparent relative overflow-hidden group">
                      <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                         <Target size={300} />
                      </div>
                      
                      <div className="flex flex-col items-center justify-center relative z-10 px-10 text-center">
                         <div className="flex items-center gap-4 mb-4">
                            <Zap size={20} className="text-[var(--primary)] animate-pulse" />
                            <h3 className="text-xs font-black text-white uppercase tracking-[0.4em]">Integrated Mission Readiness</h3>
                         </div>
                         <div className="relative mb-8">
                             <div className="text-[8rem] font-black text-white leading-none tracking-tighter opacity-10 blur-sm absolute inset-0 select-none">100%</div>
                             <div className="text-[8rem] font-black text-white leading-none tracking-tighter relative select-none">100<span className="text-[2rem] text-[var(--primary)]">%</span></div>
                         </div>
                         <p className="max-w-md text-gray-500 text-[11px] font-black uppercase tracking-widest leading-relaxed">
                            Tüm alt-sistemler operasyonel nominal eşik değerlerini karşıladı. <br />
                            Sistem bir sonraki mühürleme ve devir işlemi için onaylanmıştır.
                         </p>
                      </div>

                      {/* Animated scan line */}
                      <div className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-[var(--primary)]/20 to-transparent animate-scan" style={{top: '40%'}} />
                   </section>
                </div>

                {/* Handover Action */}
                <div className="lg:col-span-4 h-full">
                   <div className="glass-panel p-10 rounded-[3rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.05] to-transparent h-full flex flex-col items-center justify-center text-center group">
                      <div className="p-5 bg-[var(--primary)]/10 rounded-[2rem] border border-[var(--primary)]/20 shadow-[0_0_30px_rgba(102,252,241,0.1)] mb-8 group-hover:scale-110 transition-transform duration-700">
                         <CheckCircle2 size={42} className="text-[var(--primary)]" />
                      </div>
                      <h3 className="text-xl font-black text-white uppercase tracking-tighter mb-4">Final Protocol Handover</h3>
                      <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest mb-10 max-w-[200px] mx-auto leading-loose">
                         Tüm kapılar yeşil. Yeni bir mühürleme ve rollout tetiklenebilir.
                      </p>
                      <button className="w-full flex items-center justify-center gap-3 px-8 py-5 bg-[var(--primary)] text-[#060a12] font-black text-xs uppercase tracking-[0.2em] hover:shadow-[0_8px_48px_rgba(102,252,241,0.4)] transition-all rounded-2xl active:scale-95 group/btn">
                          Handover Tetikle
                          <ArrowRight size={18} className="group-hover/btn:translate-x-2 transition-transform" />
                      </button>
                   </div>
                </div>
            </div>

            {/* Gates Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
                {gates.map((gate) => (
                    <div key={gate.id} className="glass-panel p-8 rounded-[2.5rem] border-white/[0.03] bg-white/[0.015] hover:bg-white/[0.04] hover:border-[var(--primary)]/20 transition-all group/gate relative overflow-hidden">
                        <div className="mb-8 flex items-start justify-between">
                            <div className="p-4 bg-black/40 rounded-2xl border border-white/5 text-gray-500 group-hover/gate:text-[var(--primary)] group-hover/gate:border-[var(--primary)]/20 transition-all duration-500">
                                {gate.icon}
                            </div>
                            <div className={`px-3 py-1 rounded-lg text-[9px] font-black tracking-widest border transition-all ${
                                gate.status === "PASS" 
                                    ? "bg-green-500/10 text-green-500 border-green-500/20 shadow-[0_0_15px_rgba(34,197,94,0.1)]" 
                                    : "bg-red-500/10 text-red-500 border-red-500/20"
                            }`}>
                                {gate.status}
                            </div>
                        </div>

                        <h3 className="text-base font-black text-white uppercase tracking-tight mb-3 transition-colors group-hover/gate:text-[var(--primary)]">{gate.title}</h3>
                        <p className="text-[10px] text-gray-600 mb-8 flex-1 italic font-bold tracking-tight leading-relaxed">"{gate.detail}"</p>

                        <div className="space-y-4 pt-6 border-t border-white/[0.03]">
                            <div className="flex justify-between items-center">
                                <span className="text-[9px] uppercase tracking-widest text-gray-700 font-black">Güncel</span>
                                <span className="text-xs font-mono font-black text-[var(--primary)]">{gate.metric}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-[9px] uppercase tracking-widest text-gray-700 font-black">Eşik</span>
                                <span className="text-xs font-mono font-bold text-gray-400">{gate.threshold}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Autonomy Blocking Protocol Notice */}
            <section className="glass-panel p-10 rounded-[3rem] border-white/[0.03] bg-[#060a12]/50 relative overflow-hidden group/notice shadow-2xl">
                <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover/notice:opacity-[0.08] transition-opacity pointer-events-none">
                    <AlertOctagon size={180} className="text-red-500" />
                </div>
                
                <div className="flex flex-col lg:flex-row gap-10 items-start">
                    <div className="p-6 bg-red-500/10 rounded-3xl border border-red-500/20 text-red-500 shadow-[0_0_30px_rgba(239,68,68,0.1)]">
                        <AlertOctagon size={40} className="animate-pulse" />
                    </div>
                    <div className="flex-1">
                        <h4 className="text-2xl font-black text-white tracking-tighter uppercase mb-3">Otonom Blokaj Protokolü</h4>
                        <p className="text-gray-500 text-xs font-bold leading-loose mb-8 max-w-2xl uppercase tracking-wider">
                           Lansman kapılarından herhangi biri 'FAIL' durumuna düştüğü anda, sistem otonom olarak `Emergency Policy Core` protokolünü devreye sokar. Bu durum bekleyen tüm rollout'ları iptal eder ve `Constitutional Guard` tüm dosya yazma yetkilerini geri çeker.
                        </p>
                        <div className="flex flex-wrap items-center gap-8">
                            <div className="flex items-center gap-3">
                                <ShieldCheck size={18} className="text-green-500" />
                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Self-Healing Active</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <Lock size={18} className="text-[var(--primary)]" />
                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Quorum Lock Engaged</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <Activity size={18} className="text-blue-400" />
                                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Baseline Monitoring</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
