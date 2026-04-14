"use client";

import { useList, useUpdate } from "@refinedev/core";
import { AlertTriangle, CheckCircle, Info, Flame, Clock, Filter } from "lucide-react";

export default function IncidentsPage() {
  const { query: { data, isLoading, isError, refetch } } = useList({
    resource: "incidents",
    sorters: [{ field: "created_at", order: "desc" }],
  });

  const { mutate: updateIncident } = useUpdate();

  const handleResolve = (id: string) => {
    updateIncident({
       resource: "incidents",
       id,
       values: { status: "resolved" },
    }, {
       onSuccess: () => refetch(),
    });
  };

  const incidents = data?.data ?? [];

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-red-500/10 rounded-xl backdrop-blur-md border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#c5c6c7]">
              Operational Incidents
            </h1>
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">System Health / Proactive Monitoring</p>
          </div>
        </div>
      </header>

      {/* INCIDENTS FEED */}
      <section className="glass-panel rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-[#1f2833] flex justify-between items-center bg-gradient-to-b from-transparent to-[#0b0c10]/40">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-white">Live Incident Feed</h2>
            <span className="px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 text-[10px] font-bold uppercase tracking-tighter animate-pulse">Live</span>
          </div>
          <div className="flex gap-2">
            <button className="p-2 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-white transition-colors">
              <Filter size={18} />
            </button>
          </div>
        </div>
        
        <div className="p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-2 border-[#66fcf1] border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : isError ? (
            <div className="text-red-400 p-4 rounded-lg bg-red-400/10 border border-red-400/20 text-center">
              Failed to connect to Incident Tracker.
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {incidents.length === 0 ? (
                <div className="text-center py-20 text-[#45a29e] italic">No active incidents detected. Global systems stable.</div>
              ) : (
                incidents.map((inc: any) => (
                  <div key={inc.id} className="group p-5 rounded-xl border border-[#1f2833] bg-[#0b0c10] hover:bg-[#1f2833]/50 transition-all">
                    <div className="flex justify-between items-start gap-6">
                      <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-lg mt-1
                          ${inc.severity === 'critical' ? 'bg-red-500/20 text-red-500' : 
                            inc.severity === 'high' ? 'bg-orange-500/20 text-orange-400' : 
                            'bg-blue-500/20 text-blue-400'}`}>
                          {inc.severity === 'critical' ? <Flame size={20} /> : <AlertTriangle size={20} />}
                        </div>
                        <div>
                          <div className="flex items-center gap-3">
                            <h3 className="text-white font-medium text-lg capitalize">{inc.incident_type.replace('_', ' ')}</h3>
                            <span className={`px-3 py-0.5 rounded-full text-[10px] font-bold uppercase
                              ${inc.status === 'resolved' ? 'bg-green-500/10 text-green-400' : 'bg-[#66fcf1]/10 text-[#66fcf1]'}`}>
                              {inc.status}
                            </span>
                          </div>
                          <p className="text-gray-400 text-sm mt-1 leading-relaxed">{inc.message}</p>
                          
                          <div className="flex items-center gap-4 mt-4 text-[10px] font-mono">
                            <div className="flex items-center gap-1 text-[#45a29e]">
                              <Clock className="w-3 h-3" />
                              <span>{new Date(inc.created_at).toLocaleTimeString()}</span>
                            </div>
                            {inc.project_id && (
                              <div className="text-purple-400 uppercase tracking-tighter">PROJECT: {inc.project_id.substring(0,8)}</div>
                            )}
                          </div>
                        </div>
                      </div>

                      {inc.status === 'open' && (
                        <button 
                          onClick={() => handleResolve(inc.id)}
                          className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-xs font-bold hover:bg-[#66fcf1] hover:text-black transition-all"
                        >
                          Resolve
                        </button>
                      )}
                      
                      {inc.status === 'resolved' && (
                        <div className="text-green-500 p-2">
                           <CheckCircle size={20} />
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
