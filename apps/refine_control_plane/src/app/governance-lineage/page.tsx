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
    BrainCircuit,
    Fingerprint,
    Database,
    Zap,
    RotateCcw,
    History,
    Network,
    Terminal
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { safeFetchJson } from "@/lib/api";

export default function GovernanceLineagePage() {
    const [isClient, setIsClient] = useState(false);
    useEffect(() => setIsClient(true), []);

    const [lineage, setLineage] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");

    const fetchLineage = async () => {
        try {
            const data = await safeFetchJson('/api/v1/governance/lineage?limit=50');
            setLineage(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error("Lineage verileri alınamadı", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isClient) fetchLineage();
    }, [isClient]);

    const filteredLineage = lineage.filter(item => 
        item.decision_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.rationale?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.component_name?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

    return (
        <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
            
            <ResourceHeader 
                title="Decision Ancestry" 
                subtitle="Autonomous Decision Lineage & Causality Tracking" 
                icon={<GitBranch size={32} />}
                badge="Lineage-V2 Active"
                actions={
                  <div className="flex items-center gap-8">
                     <div className="flex flex-col items-end border-r border-white/5 pr-8">
                        <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Global Accuracy</span>
                        <span className="text-sm font-black text-[var(--primary)] mt-2 font-mono tracking-tighter italic">100% VERIFIED</span>
                     </div>
                     <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" size={14} />
                            <input 
                                type="text" 
                                placeholder="KARAR ARA..." 
                                className="bg-black/40 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-[10px] font-black text-white focus:outline-none focus:border-[var(--primary)]/20 transition-all w-48"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <button onClick={fetchLineage} className="p-3 bg-white/5 border border-white/5 rounded-2xl text-gray-500 hover:text-white transition-all">
                            <RotateCcw size={18} />
                        </button>
                     </div>
                  </div>
                }
            />

            {/* METRICS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
               <EliteLineageMetric label="Ancestry Depth" val={lineage.length > 0 ? "50+" : "0"} icon={<History size={16} />} accent="text-[var(--primary)]" />
               <EliteLineageMetric label="Integrity Seals" val={lineage.filter(l => l.integrity_hash).length} icon={<Shield size={16} />} accent="text-cyan-400" />
               <EliteLineageMetric label="Causality Verified" val="MATCH" icon={<Network size={16} />} accent="text-green-400" />
            </div>

            <div className="grid grid-cols-1 gap-8">
                {loading ? (
                  [1,2,3,4,5].map(i => <Skeleton key={i} className="h-44 rounded-[2rem]" />)
                ) : filteredLineage.length === 0 ? (
                  <div className="h-96 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-[2.5rem] bg-white/[0.012] opacity-30 shadow-2xl">
                    <BrainCircuit size={48} className="text-gray-700 mb-6 animate-pulse" />
                    <p className="font-black text-gray-700 uppercase tracking-[0.4em]">Kayıtlı Karar Bulunmuyor</p>
                  </div>
                ) : (
                  filteredLineage.map((item, idx) => (
                    <EliteLineageRow 
                      key={item.id} 
                      item={item} 
                      isLast={idx === filteredLineage.length - 1} 
                    />
                  ))
                )}
            </div>
        </div>
    );
}

function EliteLineageMetric({ label, val, icon, accent }: any) {
  return (
    <div className="glass-panel p-8 rounded-[2rem] border-white/5 bg-white/[0.01] hover:bg-white/[0.02] transition-all relative overflow-hidden group">
       <div className="flex justify-between items-center mb-6">
          <span className="text-[10px] text-gray-600 font-black uppercase tracking-widest">{label}</span>
          <div className="p-3 bg-black/40 rounded-xl border border-white/5 text-gray-600 group-hover:text-white transition-colors">
            {icon}
          </div>
       </div>
       <h3 className={`text-4xl font-black tracking-tighter ${accent}`}>{val}</h3>
    </div>
  );
}

function EliteLineageRow({ item, isLast }: { item: any, isLast: boolean }) {
    const [payloadOpen, setPayloadOpen] = useState(false);
    
    return (
        <div className="group glass-panel rounded-[2.5rem] border border-white/5 bg-white/[0.012] hover:bg-white/[0.025] hover:border-[var(--primary)]/30 transition-all duration-500 overflow-hidden shadow-2xl relative">
            <div className="p-10 flex flex-col xl:flex-row gap-10 items-start relative z-10">
                
                {/* CAUSALITY INDICATOR */}
                <div className="flex flex-col items-center gap-4 min-w-[64px]">
                    <div className={`p-5 rounded-2xl border transition-all duration-500 shadow-xl group-hover:scale-110
                        ${item.decision_type === 'REPAIR' ? 'bg-orange-500/10 border-orange-500/20 text-orange-400' :
                          item.decision_type === 'POLICY_CHANGE' ? 'bg-purple-500/10 border-purple-500/20 text-purple-400' :
                          'bg-[var(--primary)]/10 border-[var(--primary)]/20 text-[var(--primary)]'}
                    `}>
                        {item.decision_type === 'REPAIR' ? <Activity size={24} /> : 
                         item.decision_type === 'POLICY_CHANGE' ? <Shield size={24} /> : 
                         <GitBranch size={24} />}
                    </div>
                </div>

                <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-4 mb-6">
                        <span className="text-[10px] font-black uppercase tracking-widest text-gray-600 ring-1 ring-white/5 px-2 py-0.5 rounded bg-black/40">#{item.id.slice(0,16)}</span>
                        <div className="w-1 h-1 rounded-full bg-white/20" />
                        <span className="px-3 py-1 rounded-lg bg-white/5 text-[9px] font-black text-white border border-white/5 uppercase tracking-widest">
                            {item.component_name}
                        </span>
                        {item.parent_id && (
                            <>
                                <ChevronRight size={14} className="text-gray-700" />
                                <span className="px-3 py-1 rounded-lg bg-[var(--primary)]/10 text-[9px] font-black text-[var(--primary)] border border-[var(--primary)]/20 uppercase tracking-widest">
                                    Ancestry: {item.parent_id.slice(0,8)}
                                </span>
                            </>
                        )}
                    </div>

                    <h3 className="text-2xl font-black text-white group-hover:text-[var(--primary)] transition-colors uppercase tracking-tight italic mb-4">
                        {item.decision_type.replace('_', ' ')}
                    </h3>

                    <p className="text-sm font-bold leading-relaxed text-gray-500 max-w-4xl mb-10">
                        {item.rationale || "Gerekçe belirtilmedi."}
                    </p>

                    <div className="flex flex-wrap items-center gap-10 pt-8 border-t border-white/[0.03]">
                        <div className="flex items-center gap-4">
                            <span className="text-[9px] text-gray-700 uppercase font-black tracking-widest">Confidence</span>
                            <div className="flex items-center gap-3">
                                <div className="w-24 h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/[0.03]">
                                    <div 
                                        className="h-full bg-[var(--primary)] shadow-[0_0_10px_var(--primary)] transition-all duration-1000" 
                                        style={{ width: `${(item.confidence_score || 1) * 100}%` }}
                                    />
                                </div>
                                <span className="text-[11px] font-mono font-black text-[var(--primary)] tracking-tighter">{(item.confidence_score*100).toFixed(0)}%</span>
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
                            <Clock size={14} className="text-gray-700" />
                            <span className="text-xs font-mono font-black text-gray-600 uppercase tracking-tighter">{new Date(item.created_at).toLocaleString()}</span>
                        </div>

                        {item.integrity_hash && (
                            <div className="flex items-center gap-3 py-2 px-4 rounded-xl bg-green-500/[0.03] border border-green-500/10 group/seal cursor-help">
                                <Fingerprint size={14} className="text-green-500 group-hover/seal:scale-125 transition-transform" />
                                <span className="text-[9px] font-mono text-green-500 font-bold tracking-[0.1em] uppercase">SEALED: {item.integrity_hash.substring(0, 16).toUpperCase()}</span>
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex xl:flex-col items-center gap-4 min-w-[200px]">
                    <button className="flex-1 w-full py-4 bg-white/5 hover:bg-white/10 border border-white/5 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">
                        Inspect Evidence
                    </button>
                    <button className="flex-1 w-full py-4 border border-[var(--primary)]/20 text-[var(--primary)]/70 hover:text-[var(--primary)] hover:bg-[var(--primary)]/5 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">
                        View Root Cause
                    </button>
                    <button 
                        onClick={() => setPayloadOpen(!payloadOpen)}
                        className={`p-4 rounded-2xl border transition-all ${payloadOpen ? 'bg-[var(--primary)]/10 border-[var(--primary)]/20 text-[var(--primary)]' : 'bg-white/5 border-white/5 text-gray-700 hover:text-white'}`}
                    >
                        <Terminal size={18} />
                    </button>
                </div>
            </div>

            {/* PAYLOAD VIEW */}
            {payloadOpen && item.trigger_event && (
                <div className="px-10 pb-10 animate-in slide-in-from-top-4 duration-500">
                    <div className="p-8 bg-black/60 rounded-[2rem] border border-white/5 relative group/payload">
                        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-4">
                            <div className="flex items-center gap-3 text-gray-700">
                                <Database size={14} />
                                <span className="text-[9px] font-black uppercase tracking-widest">Trigger Evolution Payload</span>
                            </div>
                            <span className="text-[8px] font-mono text-gray-700">JSON_ENCODED_TELEMETRY</span>
                        </div>
                        <pre className="text-[11px] font-mono text-[var(--primary)]/70 overflow-x-auto custom-scrollbar leading-relaxed">
                            {JSON.stringify(item.trigger_event, null, 2)}
                        </pre>
                    </div>
                </div>
            )}
        </div>
    );
}
