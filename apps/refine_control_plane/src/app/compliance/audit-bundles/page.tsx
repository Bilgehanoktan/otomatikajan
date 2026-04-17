"use client";

import React, { useState, useEffect } from "react";
import { 
    FileArchive, 
    Download, 
    Search, 
    Calendar, 
    ShieldCheck, 
    CheckCircle2,
    Lock
} from "lucide-react";

export default function AuditBundlesPage() {
    const [isClient, setIsClient] = useState(false);
    useEffect(() => setIsClient(true), []);

    if (!isClient) return <div className="min-h-screen bg-[#0b0c10]" />;
    // Mock data based on the pilot rollout
    const bundles = [
        {
            id: "LAUNCH_f462f604",
            name: "LAUNCH_f462f604_61319b0a.zip",
            purpose: "FINAL_PRODUCTION_HANDOVER",
            project: "Resilience Pilot v1",
            createdAt: "2026-04-17 19:23:29",
            operator: "CLI_OPERATOR",
            seal: "SHA256:61319b0a...",
            size: "1.2 MB",
            status: "sealed"
        },
        {
            id: "TEST_f4cd34e9",
            name: "TEST_BUNDLE_f4cd34e9.zip",
            purpose: "Compliance_DryRun",
            project: "System Global",
            createdAt: "2026-04-17 19:06:05",
            operator: "CLI_OPERATOR",
            seal: "SHA256:f4cd34e9...",
            size: "0.8 MB",
            status: "sealed"
        }
    ];

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-700">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 rounded-full bg-[#66fcf1] animate-pulse" />
                        <span className="text-[10px] uppercase tracking-[0.3em] font-bold text-[#45a29e]">Compliance Fabric</span>
                    </div>
                    <h1 className="text-4xl font-black text-white tracking-tight">DENETİM PAKETLERİ</h1>
                    <p className="text-gray-400 mt-2 max-w-xl">Kriptografik mühürlü, değişmez kanıt paketleri. Her paket, otonom kararların ve politika evrimlerinin tam soyağacını içerir.</p>
                </div>
                
                <div className="flex items-center gap-3">
                    <div className="relative group">
                        <div className="absolute -inset-1 bg-gradient-to-r from-[#66fcf1] to-[#45a29e] rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
                        <div className="relative flex items-center gap-3 glass-card px-4 py-2 text-[#45a29e]">
                            <Search size={18} />
                            <input 
                                type="text" 
                                placeholder="Paketlerde ara..." 
                                className="bg-transparent border-none outline-none text-sm w-48 placeholder-[#45a29e]/50"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Bundles Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {bundles.map((bundle) => (
                    <div key={bundle.id} className="glass-card p-6 group hover:border-[#66fcf1]/30 transition-all duration-500 relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-[#66fcf1]/5 blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-[#66fcf1]/10 transition-colors" />
                        
                        <div className="flex items-start justify-between mb-6 relative z-10">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center text-[#66fcf1] group-hover:scale-110 transition-transform duration-500 border border-white/5">
                                    <FileArchive size={24} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-white group-hover:text-[#66fcf1] transition-colors">{bundle.name}</h3>
                                    <p className="text-xs text-gray-500 font-mono mt-1">{bundle.id}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 px-3 py-1 bg-[#66fcf1]/10 rounded-full border border-[#66fcf1]/20">
                                <Lock size={12} className="text-[#66fcf1]" />
                                <span className="text-[10px] font-bold text-[#66fcf1] uppercase tracking-wider">{bundle.status}</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-6 relative z-10">
                            <div className="space-y-1">
                                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Amaç</p>
                                <p className="text-xs text-gray-300">{bundle.purpose}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Proje</p>
                                <p className="text-xs text-gray-300">{bundle.project}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Tarih</p>
                                <div className="flex items-center gap-2 text-xs text-gray-300">
                                    <Calendar size={12} className="text-[#45a29e]" />
                                    {bundle.createdAt}
                                </div>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Boyut</p>
                                <p className="text-xs text-gray-300">{bundle.size}</p>
                            </div>
                        </div>

                        <div className="flex items-center justify-between pt-4 border-t border-white/5 relative z-10">
                            <div className="flex items-center gap-2 text-[10px] font-mono text-gray-500">
                                <ShieldCheck size={14} className="text-[#45a29e]" />
                                SEAL: {bundle.seal}
                            </div>
                            <button className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-[#66fcf1]/10 text-white rounded-lg transition-all text-xs border border-white/5 hover:border-[#66fcf1]/30">
                                <Download size={14} />
                                İndir
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Verification HUD */}
            <div className="premium-gradient-bg p-8 rounded-3xl border border-[#66fcf1]/20 text-black relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:rotate-12 transition-transform duration-700">
                    <ShieldCheck size={120} />
                </div>
                <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                    <div className="space-y-4">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-black/10 rounded-full border border-black/10">
                            <CheckCircle2 size={14} />
                            <span className="text-[10px] font-black uppercase tracking-widest">Global Integrity Status</span>
                        </div>
                        <h2 className="text-3xl font-black leading-tight">MÜHÜR CANLI DOĞRULANIYOR</h2>
                        <p className="text-sm font-medium opacity-80 max-w-md italic">Sistemdeki tüm denetim paketleri periyodik olarak SHA-256 zinciri üzerinden doğrulanmaktadır. Manipülasyon tespiti durumunda tüm otonom işlemler dondurulur.</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="glass-card bg-white/20 border-black/10 text-center px-8 py-4">
                            <span className="block text-4xl font-black mb-1">2/2</span>
                            <span className="text-[10px] font-bold uppercase tracking-widest">Valid Packs</span>
                        </div>
                        <div className="glass-card bg-white/20 border-black/10 text-center px-8 py-4">
                            <span className="block text-4xl font-black mb-1">100%</span>
                            <span className="text-[10px] font-bold uppercase tracking-widest">Integrity</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
