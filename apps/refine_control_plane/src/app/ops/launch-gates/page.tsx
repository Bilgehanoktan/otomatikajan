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
    ArrowRight
} from "lucide-react";

export default function LaunchGatesPage() {
    const [isClient, setIsClient] = useState(false);
    useEffect(() => setIsClient(true), []);

    if (!isClient) return <div className="min-h-screen bg-[#0b0c10]" />;
    // Mock data based on the latest gatekeeper run
    const gates = [
        {
            id: "budget",
            title: "Bütçe Bütünlüğü",
            icon: <Wallet className="text-[#66fcf1]" size={24} />,
            status: "PASS",
            metric: "$0.00 consumed",
            threshold: "Max $90.00 (90%)",
            detail: "Ekonomik drift tespit edilmedi. Cari tüketim limitler dahilinde."
        },
        {
            id: "governance",
            title: "Yönetişim Kilidi",
            icon: <ShieldAlert className="text-[#66fcf1]" size={24} />,
            status: "PASS",
            metric: "Constitutional Guards Active",
            threshold: "Strict Lockdown",
            detail: "Kritik oturum sürücüleri (DB/Session) otonom değişime karşı kilitli."
        },
        {
            id: "quorum",
            title: "Mutabakat (Quorum)",
            icon: <Users className="text-[#66fcf1]" size={24} />,
            status: "PASS",
            metric: "0 Pending Sign-offs",
            threshold: "Tier-1 Requirements",
            detail: "Bu katman için gerekli tüm operatör onayları tamamlanmış durumda."
        },
        {
            id: "accuracy",
            title: "Doğruluk Skorları",
            icon: <Activity className="text-[#66fcf1]" size={24} />,
            status: "PASS",
            metric: "0.94 Confidence",
            threshold: "Min 0.90",
            detail: "Sistem kararlılığı ve verifikasyon ağ skoru beklentilerin üzerinde."
        }
    ];

    return (
        <div className="p-8 space-y-8 animate-in fade-in zoom-in-95 duration-700">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2 border-b border-white/5">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Zap className="text-[#66fcf1] animate-pulse" size={14} />
                        <span className="text-[10px] uppercase tracking-[0.3em] font-bold text-[#45a29e]">Production Readiness</span>
                    </div>
                    <h1 className="text-4xl font-black text-white tracking-tight italic">LANSMAN KAPILARI</h1>
                    <p className="text-gray-400 mt-2 max-w-xl">Canlıya geçiş (Live Rollout) öncesi sistemin geçmek zorunda olduğu 4 temel güvenlik ayağı.</p>
                </div>
                
                <div className="flex items-center gap-4 bg-white/5 p-4 rounded-2xl border border-white/5">
                    <div className="text-right">
                        <p className="text-[10px] uppercase tracking-widest text-[#45a29e] font-bold">Genel Durum</p>
                        <p className="text-lg font-bold text-white uppercase italic">Müsait (Ready)</p>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-[#66fcf1]/20 flex items-center justify-center border border-[#66fcf1]/30">
                        <CheckCircle2 size={24} className="text-[#66fcf1]" />
                    </div>
                </div>
            </div>

            {/* Gates Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {gates.map((gate) => (
                    <div key={gate.id} className="glass-card p-6 flex flex-col h-full group hover:bg-white/[0.02] transition-colors relative overflow-hidden">
                        <div className="mb-6 flex items-start justify-between">
                            <div className="p-3 bg-white/5 rounded-2xl border border-white/5 group-hover:scale-110 transition-transform duration-500">
                                {gate.icon}
                            </div>
                            <div className={`px-3 py-1 rounded-full text-[10px] font-black tracking-widest border ${
                                gate.status === "PASS" 
                                    ? "bg-[#66fcf1]/10 text-[#66fcf1] border-[#66fcf1]/20" 
                                    : "bg-red-500/10 text-red-500 border-red-500/20"
                            }`}>
                                {gate.status}
                            </div>
                        </div>

                        <h3 className="text-lg font-bold text-white mb-2">{gate.title}</h3>
                        <p className="text-sm text-gray-400 mb-6 flex-1 italic">"{gate.detail}"</p>

                        <div className="space-y-4 pt-4 border-t border-white/5">
                            <div className="flex justify-between items-center">
                                <span className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Güncel</span>
                                <span className="text-xs font-mono text-[#66fcf1]">{gate.metric}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Eşik</span>
                                <span className="text-xs font-mono text-white/60">{gate.threshold}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Security Notice */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 glass-card p-8 border-l-4 border-[#66fcf1] flex gap-6 items-start">
                    <div className="p-4 bg-[#66fcf1]/10 rounded-2xl text-[#66fcf1]">
                        <Info size={32} />
                    </div>
                    <div>
                        <h4 className="text-xl font-bold text-white mb-2 italic">Otonom Blokaj Protokolü</h4>
                        <p className="text-gray-400 text-sm leading-relaxed mb-4">
                            Lansman kapılarından herhangi biri 'FAIL' durumuna düştüğü anda, sistem otonom olarak `Emergency Policy Core` protokolünü devreye sokar. Bu durum bekleyen tüm rollout'ları iptal eder ve `Constitutional Guard` tüm dosya yazma yetkilerini geri çeker.
                        </p>
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-2">
                                <CheckCircle2 size={16} className="text-[#66fcf1]" />
                                <span className="text-[10px] font-bold text-gray-300">Self-Healing Active</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle2 size={16} className="text-[#66fcf1]" />
                                <span className="text-[10px] font-bold text-gray-300">Quorum Lock Engaged</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="glass-card p-8 bg-gradient-to-br from-[#66fcf1]/5 to-transparent flex flex-col justify-center items-center text-center space-y-4">
                    <p className="text-[10px] uppercase tracking-[0.3em] font-bold text-[#45a29e]">Action Required</p>
                    <h3 className="text-xl font-black text-white italic tracking-tight uppercase">MANUEL ROLLOUT TETİKLE</h3>
                    <p className="text-xs text-gray-500">Tüm kapılar yeşil ise yeni bir pilot rollout başlatabilirsiniz.</p>
                    <button className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-[#66fcf1] text-black font-black text-sm uppercase tracking-widest hover:scale-[1.02] transition-all rounded-xl shadow-[0_0_30px_rgba(102,252,241,0.2)]">
                        Handover Başlat
                        <ArrowRight size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
}
