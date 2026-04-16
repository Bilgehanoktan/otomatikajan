"use client";

import React from "react";
import { useShow, useNavigation, useUpdate } from "@refinedev/core";
import { ArrowLeft, Play, Pause, Square, AlertCircle, CheckCircle2, Clock, Code, Terminal } from "lucide-react";

export default function WorkflowDetail() {
    const { query } = useShow({
        resource: "workflows"
    });
    const { list } = useNavigation();
    const { mutate: updateStatus } = useUpdate();

    const { data, isLoading, isError } = query;
    const workflow = data?.data;

    if (isLoading) return <div className="p-20 text-center text-[#66fcf1]">Loading Neural Context...</div>;
    if (isError) return <div className="p-20 text-center text-red-500">Flux Capacitance Failure: Could not load workflow.</div>;

    const steps = workflow?.steps || [];

    const getStatusColor = (status: string) => {
        switch (status?.toUpperCase()) {
            case "COMPLETED": return "text-green-400";
            case "RUNNING": return "text-[#66fcf1]";
            case "FAILED": return "text-red-400";
            case "PENDING": return "text-gray-500";
            default: return "text-gray-400";
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            {/* HEADER */}
            <div className="flex justify-between items-start mb-10">
                <div className="flex items-center gap-6">
                    <button 
                        onClick={() => list("workflows")}
                        className="p-3 rounded-xl bg-[#1f2833] border border-white/5 hover:bg-[#45a29e]/20 transition-all text-[#66fcf1]"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <h1 className="text-3xl font-bold text-white tracking-tight">Run: {workflow?.workflow_type}</h1>
                            <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border ${getStatusColor(workflow?.status).replace('text', 'bg').replace('400', '500/10')} ${getStatusColor(workflow?.status).replace('text', 'border')}`}>
                                {workflow?.status}
                            </span>
                        </div>
                        <p className="text-[#45a29e] text-sm font-mono">UUID: {workflow?.id}</p>
                    </div>
                </div>
                
                <div className="flex gap-3">
                    <button className="flex items-center gap-2 px-5 py-2.5 bg-[#1f2833] border border-white/5 rounded-xl text-gray-400 hover:text-white transition-all">
                        <Pause size={18} />
                        <span className="text-sm font-bold">Pause</span>
                    </button>
                    <button className="flex items-center gap-2 px-5 py-2.5 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 hover:bg-red-500/20 transition-all">
                        <Square size={18} />
                        <span className="text-sm font-bold">Abort</span>
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* EXECUTION GRAPH / STEPS */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-[#0b0c10]/40 flex flex-col">
                        <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                             <Code size={20} className="text-[#66fcf1]" />
                             Execution Sequence
                        </h2>
                        
                        <div className="space-y-4 relative">
                            {/* Connector Line */}
                            <div className="absolute left-[27px] top-8 bottom-8 w-[2px] bg-gradient-to-b from-[#66fcf1]/50 via-[#45a29e]/20 to-transparent" />
                            
                            {steps.map((step: any, index: number) => (
                                <div key={step.id} className="relative z-10 flex items-start gap-6 group">
                                    <div className={`w-14 h-14 rounded-full flex items-center justify-center border-2 bg-[#0b0c10] transition-shadow duration-500 ${
                                        step.status === 'COMPLETED' ? 'border-green-400 shadow-[0_0_15px_rgba(74,222,128,0.2)]' :
                                        step.status === 'RUNNING' ? 'border-[#66fcf1] shadow-[0_0_20px_#66fcf1/30] animate-pulse' :
                                        step.status === 'FAILED' ? 'border-red-400' : 'border-[#1f2833]'
                                    }`}>
                                        {step.status === 'COMPLETED' ? <CheckCircle2 className="text-green-400" size={24} /> :
                                         step.status === 'FAILED' ? <AlertCircle className="text-red-400" size={24} /> :
                                         <span className="text-[#45a29e] font-bold">{index + 1}</span>}
                                    </div>
                                    
                                    <div className={`flex-1 p-5 rounded-2xl border transition-all ${
                                        step.status === 'RUNNING' ? 'bg-[#1f2833]/30 border-[#66fcf1]/30' : 'bg-white/5 border-white/5 group-hover:bg-white/[0.08]'
                                    }`}>
                                        <div className="flex justify-between items-start mb-2">
                                            <h3 className="font-bold text-white tracking-tight">{step.name || step.action}</h3>
                                            <span className="text-[10px] font-mono text-gray-500 uppercase">{String(step.id).substring(0,6)}</span>
                                        </div>
                                        <p className="text-xs text-[#c5c6c7] leading-relaxed mb-4">{step.description || 'No description available for this neural operation.'}</p>
                                        
                                        {step.error && (
                                            <div className="p-3 rounded-lg bg-red-400/5 border border-red-400/20 text-red-400 text-[10px] font-mono mb-4 italic">
                                                ERROR: {step.error}
                                            </div>
                                        )}

                                        <div className="flex items-center gap-4 text-[10px] text-[#45a29e] font-semibold">
                                            <span className="flex items-center gap-1.5"><Clock size={12} /> {step.started_at ? new Date(step.started_at).toLocaleTimeString() : 'WAITING'}</span>
                                            {step.retries > 0 && <span className="text-orange-400">RETRIES: {step.retries}</span>}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* SIDEBAR METADATA */}
                <div className="space-y-6">
                    <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-[#0b0c10]/40">
                         <h2 className="text-sm font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                             <Terminal size={16} className="text-[#66fcf1]" />
                             Context Metrics
                         </h2>
                         <div className="space-y-4">
                            <MetricRow label="Priority" value={workflow?.priority || "Normal"} />
                            <MetricRow label="Triggered By" value={workflow?.source || "Sovereign Executive"} />
                            <MetricRow label="Sub-Agents" value={workflow?.agent_ids?.length || 0} />
                            <MetricRow label="Cognitive Load" value="1.2 TFLOPS" />
                         </div>
                    </div>

                    <div className="p-6 rounded-2xl bg-gradient-to-br from-[#66fcf1]/5 to-transparent border border-[#66fcf1]/10">
                        <p className="text-[10px] text-[#66fcf1] font-bold uppercase tracking-widest mb-2">Otonom Durum</p>
                        <p className="text-xs text-[#c5c6c7] leading-relaxed">
                            Sovereign AGI bu iÅŸ akÄ±ÅŸÄ±nÄ± %85 gÃ¼ven oranÄ± ile yÃ¶netiyor. Sonraki adÄ±mda manuel onay gerekebilir.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

function MetricRow({ label, value }: { label: string, value: any }) {
    return (
        <div className="flex justify-between items-center py-2 border-b border-white/[0.03]">
            <span className="text-xs text-gray-500">{label}</span>
            <span className="text-xs text-[#c5c6c7] font-medium">{value}</span>
        </div>
    );
}
