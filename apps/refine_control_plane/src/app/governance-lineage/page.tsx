"use client";

import React, { useState, useEffect } from "react";
import { 
    GitBranch, 
    Clock, 
    Activity, 
    Shield, 
    ChevronRight,
    Search,
    Filter,
    ChevronDown,
    BrainCircuit
} from "lucide-react";

export default function GovernanceLineagePage() {
    const [lineage, setLineage] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");

    const fetchLineage = async () => {
        try {
            const response = await fetch('/api/v1/governance/lineage?limit=50');
            const data = await response.json();
            setLineage(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error("Lineage verileri alınamadı", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLineage();
    }, []);

    const filteredLineage = lineage.filter(item => 
        item.decision_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.rationale?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.component_name?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return (
        <div className="p-8 text-teal-400 font-mono animate-pulse bg-[#050510] min-h-screen">
            Yönetişim Soyağacı Yükleniyor... [LINEAGE_SERVICE]
        </div>
    );

    return (
        <div className="p-8 space-y-8 min-h-screen bg-[#050510] text-gray-200">
            <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/5 pb-8">
                <div>
                    <h1 className="text-4xl font-black bg-gradient-to-r from-[#66fcf1] to-[#45a29e] bg-clip-text text-transparent uppercase tracking-tight">
                        KARAR SOYAĞACI
                    </h1>
                    <p className="text-gray-500 mt-2 font-mono uppercase tracking-[0.2em] text-[10px]">
                        Otonom Karar İzlenebilirliği ve Etki Analizi | Autonomous Decision Family Tree
                    </p>
                </div>
                
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                        <input 
                            type="text" 
                            placeholder="Karar veya Bileşen Ara..." 
                            className="bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-teal-500/50 transition-all w-64"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <button className="p-2 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors">
                        <Filter size={18} className="text-gray-400" />
                    </button>
                    <button onClick={fetchLineage} className="p-2 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors">
                        <Clock size={18} className="text-gray-400" />
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-1 gap-4">
                {filteredLineage.map((item, idx) => (
                    <div 
                        key={item.id} 
                        className="group bg-gray-900/40 backdrop-blur-md rounded-2xl border border-white/5 hover:border-teal-500/30 transition-all duration-300 overflow-hidden shadow-lg"
                    >
                        <div className="p-6 flex flex-col md:flex-row gap-6 items-start">
                            {/* CAUSALITY INDICATOR */}
                            <div className="flex flex-col items-center gap-2">
                                <div className={`p-3 rounded-2xl ${
                                    item.decision_type === 'REPAIR' ? 'bg-orange-500/10 text-orange-400' :
                                    item.decision_type === 'POLICY_CHANGE' ? 'bg-purple-500/10 text-purple-400' :
                                    'bg-teal-500/10 text-teal-400'
                                } border border-white/5 shadow-inner`}>
                                    {item.decision_type === 'REPAIR' ? <Activity size={24} /> : 
                                     item.decision_type === 'POLICY_CHANGE' ? <Shield size={24} /> : 
                                     <GitBranch size={24} />}
                                </div>
                                {idx < filteredLineage.length - 1 && (
                                    <div className="w-px h-12 bg-gradient-to-b from-teal-500/50 to-transparent" />
                                )}
                            </div>

                            <div className="flex-1 space-y-3">
                                <div className="flex flex-wrap items-center gap-2">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-teal-500/80">#{item.id.slice(0,8)}</span>
                                    <span className="text-white/20">•</span>
                                    <span className="px-2 py-0.5 rounded-md bg-white/5 text-[10px] font-bold text-gray-400 border border-white/5 uppercase">
                                        {item.component_name}
                                    </span>
                                    {item.parent_id && (
                                        <>
                                            <ChevronRight size={14} className="text-gray-600" />
                                            <span className="px-2 py-0.5 rounded-md bg-teal-500/10 text-[10px] font-bold text-teal-400 border border-teal-500/20">
                                                PARENT: {item.parent_id.slice(0,8)}
                                            </span>
                                        </>
                                    )}
                                </div>

                                <h3 className="text-xl font-bold text-white group-hover:text-teal-400 transition-colors uppercase italic tracking-tighter">
                                    {item.decision_type.replace('_', ' ')}
                                </h3>

                                <p className="text-gray-400 text-sm font-medium leading-relaxed max-w-4xl">
                                    {item.rationale || "Gerekçe belirtilmedi."}
                                </p>

                                <div className="pt-4 flex flex-wrap items-center gap-6">
                                    <div className="flex items-center gap-2">
                                        <div className="text-[10px] text-gray-600 uppercase font-black tracking-widest">Confidence</div>
                                        <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                            <div 
                                                className="h-full bg-teal-500 shadow-[0_0_10px_#66fcf1]" 
                                                style={{ width: `${(item.confidence_score || 1) * 100}%` }}
                                            />
                                        </div>
                                        <span className="text-xs font-mono font-bold text-teal-400">{(item.confidence_score*100).toFixed(0)}%</span>
                                    </div>
                                    
                                    <div className="flex items-center gap-2">
                                        <div className="text-[10px] text-gray-600 uppercase font-black tracking-widest">TS</div>
                                        <span className="text-xs font-mono text-gray-400">{new Date(item.created_at).toLocaleString('tr-TR')}</span>
                                    </div>

                                    {item.integrity_hash && (
                                        <div className="flex items-center gap-2 py-1 px-3 rounded-full bg-teal-500/5 border border-teal-500/20">
                                            <Shield size={12} className="text-teal-400" />
                                            <span className="text-[10px] font-mono text-teal-400 font-bold tracking-tighter">MÜHÜR: {item.integrity_hash.substring(0, 16)}...</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="flex flex-col gap-2 min-w-[120px]">
                                <button className="w-full py-2 bg-white/5 hover:bg-white/10 border border-white/5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all">
                                    KANITLARI GÖR
                                </button>
                                <button className="w-full py-2 border border-teal-500/20 text-teal-500/70 hover:text-teal-400 hover:bg-teal-500/5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all">
                                    ROOT CAUSE
                                </button>
                            </div>
                        </div>
                        
                        {/* TRIGGER EVENT MINI VIEW */}
                        {item.trigger_event && (
                            <div className="px-6 pb-6 pt-2">
                                <details className="group/event">
                                    <summary className="list-none cursor-pointer flex items-center gap-2 text-[10px] font-bold text-gray-600 uppercase hover:text-gray-400 transition-colors">
                                        <ChevronDown size={12} className="group-open/event:rotate-180 transition-transform" />
                                        Tetikleyici Veri (Payload)
                                    </summary>
                                    <pre className="mt-4 p-4 bg-black/40 rounded-xl border border-white/5 text-[10px] font-mono text-teal-400/80 overflow-x-auto">
                                        {JSON.stringify(item.trigger_event, null, 2)}
                                    </pre>
                                </details>
                            </div>
                        )}
                    </div>
                ))}

                {filteredLineage.length === 0 && (
                    <div className="h-96 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-3xl bg-white/[0.01]">
                        <BrainCircuit size={48} className="text-gray-700 mb-4 animate-pulse" />
                        <p className="text-gray-500 font-mono text-sm uppercase tracking-widest">Kayıtlı Karar Bulunmuyor</p>
                    </div>
                )}
            </div>
        </div>
    );
}
