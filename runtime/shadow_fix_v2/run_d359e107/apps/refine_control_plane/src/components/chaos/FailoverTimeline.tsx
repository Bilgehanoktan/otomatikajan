"use client";

import React from "react";
import { Clock, ArrowRight, ShieldAlert, CheckCircle2, RefreshCw } from "lucide-react";

interface TimelineEvent {
  event_id: string;
  region_id: string;
  action: string;
  timestamp: string;
  details: Record<string, any>;
}

interface TimelineProps {
  events: TimelineEvent[];
}

export default function FailoverTimeline({ events }: TimelineProps) {
  return (
    <div className="p-6 rounded-2xl border border-[#1f2833] bg-[#1f2833]/20 backdrop-blur-xl h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Clock className="text-[#66fcf1] w-5 h-5" />
          <h2 className="text-xl font-semibold text-white">Failover Timeline</h2>
        </div>
        <span className="text-[10px] text-[#45a29e] font-mono uppercase tracking-widest">Global Audit Stream</span>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
        {events.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center opacity-30 gap-3">
            <CheckCircle2 size={40} className="text-[#45a29e]" />
            <p className="text-sm font-medium">No recent chaos events detected.</p>
          </div>
        ) : (
          events.map((event, idx) => (
            <div key={event.event_id} className="relative pl-8 pb-4 group last:pb-0">
              {/* VERTICAL LINE */}
              {idx !== events.length - 1 && (
                <div className="absolute left-3 top-6 bottom-0 w-px bg-gradient-to-b from-[#66fcf1]/30 to-transparent"></div>
              )}
              
              {/* DOT */}
              <div className="absolute left-0 top-1 p-1 bg-[#0b0c10] border-2 border-[#66fcf1] rounded-full z-10 group-hover:scale-125 transition-transform duration-300 shadow-[0_0_10px_rgba(102,252,241,0.5)]">
                <div className="w-1.5 h-1.5 bg-[#66fcf1] rounded-full"></div>
              </div>

              {/* CONTENT CARD */}
              <div className="p-4 rounded-xl bg-[#0b0c10]/40 border border-[#1f2833] group-hover:border-[#66fcf1]/30 transition-all duration-300 hover:translate-x-1">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-black text-[#66fcf1] font-mono px-2 py-0.5 bg-[#66fcf1]/10 rounded border border-[#66fcf1]/20">
                      {event.region_id.toUpperCase()}
                    </span>
                    <ArrowRight className="w-3 h-3 text-[#45a29e]" />
                    <span className="text-[11px] font-bold text-white uppercase tracking-tight">{event.action}</span>
                  </div>
                  <span className="text-[9px] text-white/30 font-mono italic">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                
                <p className="text-[10px] text-[#c5c6c7] leading-relaxed">
                  {event.details.reason || `Automated federation transition logic triggered for ${event.region_id}.`}
                </p>
                
                {event.action.includes("FAILOVER") && (
                  <div className="mt-2 flex items-center gap-2 text-[9px] text-amber-500 font-bold">
                    <ShieldAlert size={10} /> CRITICAL TRANSITION
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* REFRESH STATUS */}
      <div className="mt-6 pt-4 border-t border-[#1f2833] flex justify-between items-center text-[9px] text-[#45a29e] font-mono">
        <div className="flex items-center gap-2">
          <RefreshCw size={10} className="animate-spin-slow" /> LIVE FEED ACTIVE
        </div>
        <span>MESH_ID: SOVEREIGN-01</span>
      </div>
    </div>
  );
}
