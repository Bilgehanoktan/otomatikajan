"use client";

import React, { useState, useEffect } from "react";
import { useList, useUpdate } from "@refinedev/core";
import { 
  AlertTriangle, 
  CheckCircle2, 
  Info, 
  Flame, 
  Clock, 
  Filter, 
  Plus, 
  Activity, 
  ShieldAlert, 
  Radio, 
  ChevronRight,
  Zap,
  Target,
  Terminal,
  Search
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";
import { Incident } from "@/types/mission-control";

export default function IncidentsPage() {
  const [isClient, setIsClient] = useState(false);
  useEffect(() => setIsClient(true), []);

  const { query: { data, isLoading, isError, refetch } } = useList({
    resource: "incidents",
    sorters: [{ field: "created_at", order: "desc" }],
    queryOptions: { enabled: isClient }
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

  const incidentsRaw = data?.data;
  const incidents = Array.isArray(incidentsRaw) ? (incidentsRaw as unknown as Incident[]) : [];
  const staleMeta = (data as any)?.__sqv_meta || (incidents as any).__sqv_meta;

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Incident Control" 
        subtitle="Real-time Chaos Monitoring & Autonomous Mitigation" 
        icon={<AlertTriangle size={32} />}
        badge="Critical Ops"
        staleMeta={staleMeta}
        actions={
          <div className="flex items-center gap-8">
             <div className="flex items-center gap-4 border-r border-white/5 pr-8">
                <div className="text-right">
                   <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">Global Pulse</p>
                   <p className="text-sm font-black text-blue-400 mt-2">NOMINAL</p>
                </div>
                <div className="p-3 bg-blue-500/10 rounded-full border border-blue-500/20">
                   <Radio size={16} className="text-blue-400 animate-pulse" />
                </div>
             </div>
             
             <button className="flex items-center gap-2 px-8 py-3 bg-red-500/10 text-red-500 border border-red-500/20 text-[10px] font-black uppercase tracking-widest rounded-2xl hover:bg-red-500/20 transition-all active:scale-95 shadow-xl">
                <Zap size={14} />
                <span>Chaos Protocol</span>
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* INCIDENT FEED - Main Column */}
        <div className="xl:col-span-8">
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
                 <Terminal size={300} />
              </div>

              <div className="flex items-center justify-between mb-12 relative z-10 px-2">
                 <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-ping shadow-[0_0_12px_rgba(239,68,68,0.6)]" />
                    <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">Integrated Chaos Stream</h2>
                 </div>
                 <div className="flex items-center gap-6">
                    <div className="relative">
                       <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                       <input 
                         type="text" 
                         placeholder="OLAY ARA..."
                         className="bg-black/40 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-[10px] font-black text-white focus:outline-none focus:border-[var(--primary)]/20 transition-all w-48"
                       />
                    </div>
                    <button className="p-2.5 bg-white/5 border border-white/5 rounded-xl text-gray-500 hover:text-white transition-all">
                       <Filter size={18} />
                    </button>
                 </div>
              </div>

              <div className="space-y-6 relative z-10 max-h-[800px] overflow-y-auto pr-3 custom-scrollbar">
                 {isLoading ? (
                    <div className="space-y-6">
                       {[1,2,3].map(i => <Skeleton key={i} className="h-40 rounded-3xl" />)}
                    </div>
                 ) : isError ? (
                    <div className="py-20 text-center flex flex-col items-center gap-6">
                       <div className="p-6 bg-red-500/10 rounded-full border border-red-500/20 text-red-500">
                          <AlertTriangle size={32} />
                       </div>
                       <p className="font-mono text-[10px] uppercase text-gray-500 tracking-[0.2em]">Telemetry Connection Severed</p>
                       <button onClick={() => refetch()} className="text-[10px] font-black text-[var(--primary)] uppercase tracking-widest hover:underline">Re-establish Sync</button>
                    </div>
                 ) : incidents.length === 0 ? (
                    <div className="py-32 text-center text-gray-600 font-black uppercase tracking-[0.3em] italic opacity-40">
                       Aktif olay tespit edilmedi. Sistem otonom dengede.
                    </div>
                 ) : (
                    incidents.map((inc: any) => (
                       <EliteIncidentItem 
                         key={inc.id} 
                         incident={inc} 
                         onResolve={() => handleResolve(inc.id)} 
                       />
                    ))
                 )}
              </div>
           </section>
        </div>

        {/* SIDEBAR - Operational Context */}
        <div className="xl:col-span-4 space-y-8">
           {/* Severity Radar */}
           <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/50 relative overflow-hidden group shadow-xl">
              <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
                 <ShieldAlert size={140} className="text-red-500" />
              </div>
              
              <div className="flex items-center gap-4 mb-10 relative z-10 text-red-500">
                 <div className="p-3 bg-red-500/10 rounded-2xl border border-red-500/20 shadow-xl">
                    <ShieldAlert size={24} />
                 </div>
                 <div>
                    <h3 className="text-xl font-black text-white tracking-tighter uppercase">Severity Monitor</h3>
                    <p className="text-[9px] text-red-400 font-black tracking-[0.2em] uppercase mt-1">Hazard Phase 3</p>
                 </div>
              </div>

              <div className="space-y-6 relative z-10">
                 <SeverityGauge label="Critical / P0" value={incidents.filter((i:any) => i.severity === 'critical').length} color="bg-red-500" total={incidents.length} />
                 <SeverityGauge label="High / P1" value={incidents.filter((i:any) => i.severity === 'high').length} color="bg-orange-500" total={incidents.length} />
                 <SeverityGauge label="Medium / P2" value={incidents.filter((i:any) => i.severity === 'medium').length} color="bg-blue-500" total={incidents.length} />
              </div>
           </section>

           {/* Mitigation HUD */}
           <section className="glass-panel p-10 rounded-[3rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.05] to-transparent relative overflow-hidden group shadow-2xl">
              <div className="absolute -bottom-10 -right-10 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-1000">
                 <Activity size={200} className="text-[var(--primary)]" />
              </div>
              <h3 className="text-xs font-black text-white mb-8 flex items-center gap-3 uppercase tracking-[0.3em] relative z-10 italic">
                 <Activity size={20} className="text-[var(--primary)]" />
                 Mitigation HUD
              </h3>
              
              <div className="space-y-6 relative z-10">
                 <div className="p-6 rounded-2xl bg-black/40 border border-white/5 group-hover:border-[var(--primary)]/20 transition-all">
                    <p className="text-[10px] text-gray-500 font-bold leading-relaxed uppercase tracking-widest mb-4">
                       Otonom tamir motoru son 1 saatte 12 adet düşük öncelikli olayda self-healing başarısı sağladı.
                    </p>
                    <div className="flex items-center justify-between">
                       <span className="text-[11px] font-black text-green-400">92% SUCCESS</span>
                       <button className="text-[9px] font-black text-gray-700 uppercase hover:text-white transition-colors">Details</button>
                    </div>
                 </div>
                 
                 <button className="w-full flex items-center justify-center gap-3 py-5 bg-[var(--primary)] text-[#060a12] font-black text-[10px] uppercase tracking-[0.2em] rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95 group/btn">
                    Tümünü Temizle
                    <ChevronRight size={14} className="group-hover/btn:translate-x-2 transition-transform" />
                 </button>
              </div>
           </section>
        </div>
      </div>
    </div>
  );
}

function EliteIncidentItem({ incident, onResolve }: { incident: any, onResolve: () => void }) {
  const isCritical = incident.severity === 'critical';
  const isResolved = incident.status === 'resolved';

  return (
    <div className={`p-8 rounded-[2rem] border transition-all duration-500 group/item relative overflow-hidden
      ${isCritical ? 'bg-red-500/[0.02] border-red-500/20 hover:border-red-500/40' : 'bg-white/[0.015] border-white/5 hover:border-white/10 hover:bg-white/[0.025]'}
    `}>
       <div className="flex justify-between items-start gap-8 relative z-10">
          <div className="flex items-start gap-6">
             <div className={`p-5 rounded-2xl border transition-all duration-500 shadow-xl
               ${isCritical ? 'bg-red-500/10 border-red-500/20 text-red-500 group-hover/item:scale-110' : 'bg-black/40 border-white/5 text-gray-600 group-hover/item:text-blue-400'}
             `}>
                {isCritical ? <Flame size={24} className="animate-pulse" /> : <ShieldAlert size={24} />}
             </div>
             
             <div>
                <div className="flex flex-wrap items-center gap-4 mb-2">
                   <h3 className="text-lg font-black text-white uppercase tracking-tight group-hover/item:text-[var(--primary)] transition-colors">
                     {incident.incident_type.replace('_', ' ')}
                   </h3>
                   <span className={`px-2.5 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border transition-all
                     ${isResolved ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/20 shadow-[0_0_10px_rgba(102,252,241,0.1)]'}
                   `}>
                     {incident.status}
                   </span>
                </div>
                <p className={`text-xs font-bold leading-relaxed tracking-tight max-w-xl mb-6
                  ${isCritical ? 'text-red-200 opacity-80' : 'text-gray-500'}
                `}>{incident.message}</p>
                
                <div className="flex items-center gap-6 pt-6 border-t border-white/[0.03]">
                   <div className="flex items-center gap-2">
                      <Clock size={12} className="text-gray-700" />
                      <span className="text-[9px] font-mono font-black text-gray-700 uppercase tracking-widest">{new Date(incident.created_at).toLocaleTimeString()}</span>
                   </div>
                   {incident.project_id && (
                     <div className="flex items-center gap-2">
                        <Target size={12} className="text-gray-700" />
                        <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">NODE_ID: {String(incident.project_id).substring(0,8)}</span>
                     </div>
                   )}
                </div>
             </div>
          </div>

          <div className="flex flex-col items-end gap-3 min-w-[120px]">
             {!isResolved ? (
               <button 
                 onClick={onResolve}
                 className="px-6 py-2.5 bg-white/5 border border-white/10 rounded-xl text-[10px] font-black uppercase text-white hover:bg-[var(--primary)] hover:text-[#060a12] hover:border-[var(--primary)] transition-all active:scale-95"
               >
                 Aksiyon Al
               </button>
             ) : (
               <div className="flex items-center gap-2 text-green-500 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-xl">
                  <CheckCircle2 size={16} />
                  <span className="text-[9px] font-black uppercase tracking-widest">Çözüldü</span>
               </div>
             )}
          </div>
       </div>
       
       {isCritical && (
         <div className="absolute inset-0 bg-red-500/5 pointer-events-none group-hover:bg-red-500/10 transition-all duration-1000" />
       )}
    </div>
  );
}

function SeverityGauge({ label, value, color, total }: any) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="group cursor-help">
       <div className="flex justify-between items-end mb-3 px-1">
          <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest group-hover:text-white transition-colors">{label}</span>
          <span className={`text-[11px] font-black font-mono tracking-tighter ${color.replace('bg-', 'text-')}`}>{value}</span>
       </div>
       <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden border border-white/[0.03] group-hover:border-white/10 transition-all relative">
          <div className={`h-full opacity-60 transition-all duration-1000 ${color} shadow-[0_0_15px_currentColor]`} style={{ width: `${pct}%` }}></div>
       </div>
    </div>
  );
}
