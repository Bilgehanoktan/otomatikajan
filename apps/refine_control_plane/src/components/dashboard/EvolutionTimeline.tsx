"use client";

import React from "react";
import { 
    Zap, 
    FlaskConical, 
    Search,
    ChevronRight,
    History,
    Activity
} from "lucide-react";

interface EvolutionEvent {
    title: string;
    desc: string;
    time: string;
    type: "diagnosis" | "tournament" | "promotion";
    evidence?: string;
    info?: string;
    status?: string;
}

export const EvolutionTimeline = ({ events }: { events: EvolutionEvent[] }) => {
    return (
        <section className="glass-panel p-10 rounded-[3rem] border-white/[0.04] bg-white/[0.015] shadow-2xl relative overflow-hidden group">
            <div className="flex items-center justify-between mb-10 pb-6 border-b border-white/[0.03]">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-violet-500/10 rounded-2xl border border-violet-500/20 text-violet-500">
                        <History size={20} />
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-white uppercase italic tracking-tighter">Evrimsel Şecere</h3>
                        <p className="text-[10px] text-gray-600 font-black uppercase tracking-widest mt-1">Otonom Tamir & Gelişim Günlüğü</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-black/40 border border-white/5 text-[9px] font-black text-gray-500 uppercase tracking-widest italic">
                    <Activity size={12} className="text-[var(--primary)] animate-pulse" />
                    CANLI_AKIS_STREAMS
                </div>
            </div>

            <div className="space-y-6 relative ml-4 border-l border-white/[0.05] pl-10 py-2">
                {events.map((event, idx) => (
                    <div key={idx} className="relative group/ev transition-all">
                        {/* Timeline Dot */}
                        <div className={`absolute -left-[51px] top-1 w-5 h-5 rounded-full border-4 border-[#060a12] z-10 
                            ${event.type === 'promotion' ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.4)]' : 
                              event.type === 'tournament' ? 'bg-violet-500 shadow-[0_0_10px_rgba(139,92,246,0.4)]' : 
                              'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.4)]'}`} 
                        />
                        
                        <div className="flex flex-col gap-2">
                            <div className="flex items-center justify-between">
                                <span className={`text-[10px] font-black uppercase tracking-widest border px-2 py-0.5 rounded
                                    ${event.type === 'promotion' ? 'text-green-500 border-green-500/20 bg-green-500/5' : 
                                      event.type === 'tournament' ? 'text-violet-500 border-violet-500/20 bg-violet-500/5' : 
                                      'text-amber-500 border-amber-500/20 bg-amber-500/5'}`}>
                                    {event.type === 'diagnosis' ? 'TEŞHİS' : event.type === 'tournament' ? 'TURNUVA' : 'TERFİ'}
                                </span>
                                <span className="text-[9px] font-mono text-gray-700 font-black italic">{new Date(event.time).toLocaleTimeString()}</span>
                            </div>
                            
                            <h4 className="text-sm font-black text-white uppercase italic tracking-tight group-hover/ev:text-[var(--primary)] transition-colors">{event.title}</h4>
                            <p className="text-[11px] text-gray-500 leading-relaxed font-bold">{event.desc}</p>
                            
                            {(event.evidence || event.info || event.status) && (
                                <div className="mt-2 p-3 rounded-xl bg-black/40 border border-white/[0.03] flex items-center justify-between group-hover/ev:border-[var(--primary)]/20 transition-all">
                                    <div className="flex items-center gap-3">
                                        {event.type === 'diagnosis' && <Search size={12} className="text-gray-600" />}
                                        {event.type === 'tournament' && <FlaskConical size={12} className="text-gray-600" />}
                                        {event.type === 'promotion' && <Zap size={12} className="text-gray-600" />}
                                        <span className="text-[9px] font-mono text-gray-600 uppercase tracking-widest">
                                            {event.evidence || event.info || event.status}
                                        </span>
                                    </div>
                                    <ChevronRight size={12} className="text-gray-800 opacity-0 group-hover/ev:opacity-100 group-hover/ev:translate-x-1 transition-all" />
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {events.length === 0 && (
                    <div className="py-20 text-center opacity-20 italic font-black text-gray-600 uppercase text-[10px] tracking-[0.4em]">
                        Evrimsel Veri Bulunamadı
                    </div>
                )}
            </div>
        </section>
    );
};
