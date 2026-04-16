"use client";

import React from "react";
import { useShow, useOne, useCustomMutation } from "@refinedev/core";
import { 
    ChevronLeft, 
    RefreshCcw, 
    Play, 
    XOctagon, 
    CheckCircle, 
    ExternalLink, 
    Database, 
    History,
    Network,
    Terminal,
    AlertTriangle,
    ShieldCheck,
    Stethoscope
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

export default function WorkflowShowPage() {
    const { id } = useParams();
    const router = useRouter();
    const { query: { data, isLoading } } = useShow({
        resource: "workflows",
        id: id as string,
    });
    const workflow = data?.data as any;

    const { mutate: retry } = useCustomMutation();
    const { mutate: cancel } = useCustomMutation();
    const { mutate: approve } = useCustomMutation();
    const { mutate: replay } = useCustomMutation();

    const [isReplayModalOpen, setIsReplayModalOpen] = React.useState(false);
    const [selectedStepForReplay, setSelectedStepForReplay] = React.useState<string | null>(null);
    const [replayMode, setReplayMode] = React.useState<"same_input" | "from_step" | "with_override">("same_input");
    const [overrideJson, setOverrideJson] = React.useState("{}");
    const [diagnosis, setDiagnosis] = React.useState<any>(null);
    const [isDiagnosing, setIsDiagnosing] = React.useState(false);

    const handleRetry = () => {
        retry({
            url: `workflows/${id}/retry`,
            method: "post",
            values: {},
        });
    };

    const handleCancel = () => {
        cancel({
            url: `workflows/${id}/cancel`,
            method: "post",
            values: {},
        });
    };

    const handleApprove = () => {
        approve({
            url: `workflows/${id}/approve`,
            method: "post",
            values: { 
                operator_id: "admin_human",
                notes: "Authorized via Faz 13.04 Control Plane" 
            },
        });
    };

    const handleReplay = () => {
        let overrides = null;
        if (replayMode === "with_override") {
            try {
                overrides = JSON.parse(overrideJson);
            } catch (e) {
                alert("Invalid JSON in overrides");
                return;
            }
        }

        replay({
            url: `workflows/${id}/replay`,
            method: "post",
            values: { 
                from_step: selectedStepForReplay || (workflow?.steps?.[0]?.id),
                mode: replayMode,
                overrides: overrides,
                operator_id: "admin_human", // Linked to RBAC
                reason: `Manual ${replayMode} initiated via Control Plane`
            },
        }, {
            onSuccess: () => {
                setIsReplayModalOpen(false);
                setSelectedStepForReplay(null);
            },
            onError: (error: any) => {
                const detail = error?.response?.data?.detail || "Replay failed";
                alert(`SECURITY ALERT: ${detail}`);
            }
        });
    };

    const handleDiagnose = async (stepId: string) => {
        setIsDiagnosing(true);
        try {
            const res = await fetch(`http://localhost:8000/workflows/${id}/steps/${stepId}/diagnose`);
            const data = await res.json();
            setDiagnosis(data);
        } catch (e) {
            alert("Failed to connect to Diagnosis Engine");
        } finally {
            setIsDiagnosing(false);
        }
    };

    const getSelectedStepSchema = () => {
        if (!selectedStepForReplay) return null;
        return workflow?.steps?.find((s: any) => s.id === selectedStepForReplay)?.input_schema;
    };

    const getSelectedStepInputData = () => {
        if (!selectedStepForReplay) return {};
        return workflow?.steps?.find((s: any) => s.id === selectedStepForReplay)?.input_data || {};
    };

    React.useEffect(() => {
        if (replayMode === "with_override" && selectedStepForReplay) {
            setOverrideJson(JSON.stringify({ input: getSelectedStepInputData() }, null, 2));
        }
    }, [replayMode, selectedStepForReplay]);

    if (isLoading) return <div className="p-10 text-[#66fcf1] animate-pulse">Synchronizing neural link...</div>;

    const SIGNOZ_URL = `http://localhost:3301/trace/${id}`; // Simplified for demo

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <Link 
                href="/workflows" 
                className="inline-flex items-center gap-2 text-gray-500 hover:text-[#66fcf1] mb-8 transition-colors group"
            >
                <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
                Back to Cluster
            </Link>

            <div className="flex flex-col md:flex-row justify-between items-start gap-6 mb-10">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <h2 className="text-4xl font-bold text-white tracking-tight">{workflow?.title || "Workflow Detail"}</h2>
                        <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border ${
                            workflow?.status === "running" ? "text-[#66fcf1] border-[#66fcf1]/30 bg-[#66fcf1]/5" : "text-gray-400 border-white/10 bg-white/5"
                        }`}>
                            {workflow?.status}
                        </span>
                    </div>
                    <p className="text-gray-500 font-mono text-sm">{id}</p>
                </div>

                <div className="flex gap-4">
                    {workflow?.status === "running" && (
                        <button 
                            onClick={handleCancel}
                            className="flex items-center gap-2 px-5 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 rounded-xl text-sm font-bold transition-all"
                        >
                            <XOctagon size={18} />
                            Abort Sequence
                        </button>
                    )}
                    {(workflow?.status === "pending_approval" || workflow?.status === "waiting_approval") && (
                        <button 
                            onClick={handleApprove}
                            className="flex items-center gap-2 px-6 py-2.5 premium-gradient text-black rounded-xl text-sm font-bold shadow-[0_0_20px_rgba(102,252,241,0.3)] transition-all hover:scale-105"
                        >
                            <CheckCircle size={18} />
                            Authorize Execution [admin_operator_01]
                        </button>
                    )}
                    {["failed", "error", "completed", "cancelled"].includes(workflow?.status || "") && (
                        <button 
                            onClick={() => {
                                setSelectedStepForReplay(null);
                                setIsReplayModalOpen(true);
                            }}
                            className="flex items-center gap-2 px-6 py-2.5 premium-gradient text-black shadow-[0_0_15px_rgba(102,252,241,0.2)] rounded-xl text-sm font-bold hover:scale-105 transition-all"
                        >
                            <RefreshCcw size={18} />
                            Durable Replay
                        </button>
                    )}
                    <a 
                        href={SIGNOZ_URL} 
                        target="_blank" 
                        className="flex items-center gap-2 px-6 py-2.5 glass text-[#66fcf1] border-[#66fcf1]/20 rounded-xl text-sm font-bold hover:bg-[#66fcf1]/10 transition-all"
                    >
                        <ExternalLink size={18} />
                        View Traces
                    </a>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Timeline & Progress */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Progress Bar View */}
                    <div className="glass-card p-0 overflow-hidden">
                        <div className="p-6 border-b border-white/5 flex items-center justify-between">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <Network size={18} className="text-[#66fcf1]" />
                                Execution Pipeline
                            </h3>
                            <span className="text-[10px] text-gray-500 font-mono tracking-widest uppercase">
                                {workflow?.steps?.filter((s:any) => s.status === "completed").length} / {workflow?.steps?.length} Steps OK
                            </span>
                        </div>
                        <div className="p-8">
                            <div className="relative space-y-12">
                                {/* Vertical line */}
                                <div className="absolute left-[15px] top-2 bottom-2 w-0.5 bg-white/5" />
                                
                                {workflow?.steps?.map((step: any, idx: number) => (
                                    <div key={step.id} className="relative flex items-start gap-6 group">
                                        <div className={`relative z-10 w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all duration-500 ${
                                            step.status === "completed" ? "bg-green-500 border-green-500 shadow-[0_0_15px_rgba(34,197,94,0.4)]" :
                                            step.status === "running" ? "bg-[#0b0c10] border-[#66fcf1] shadow-[0_0_15px_rgba(102,252,241,0.4)]" :
                                            "bg-[#0b0c10] border-white/10"
                                        }`}>
                                            {step.status === "completed" ? <CheckCircle size={14} className="text-black" /> : 
                                             step.status === "running" ? <div className="w-2 h-2 bg-[#66fcf1] rounded-full animate-ping" /> : 
                                             <div className="w-2 h-2 bg-white/10 rounded-full" />}
                                        </div>
                                        
                                        <div className="flex-1">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h4 className={`text-base font-bold transition-colors ${
                                                        step.status === "completed" ? "text-white" : 
                                                        step.status === "running" ? "text-[#66fcf1]" : "text-gray-500"
                                                    }`}>
                                                        {step.name}
                                                    </h4>
                                                    <p className="text-[10px] text-gray-500 font-mono mt-1 uppercase tracking-tight">{step.action}</p>
                                                </div>
                                                <div className="text-right">
                                                    <span className={`text-[10px] font-bold uppercase tracking-wider ${
                                                        step.status === "completed" ? "text-green-500" :
                                                        step.status === "running" ? "text-[#66fcf1]" : "text-gray-600"
                                                    }`}>
                                                        {step.status}
                                                    </span>
                                                    {step.completed_at && (
                                                        <p className="text-[9px] text-gray-600 font-mono mt-1">
                                                            {new Date(step.completed_at).toLocaleTimeString()}
                                                        </p>
                                                    )}
                                                    {step.status === "failed" && (
                                                        <button 
                                                            onClick={() => handleDiagnose(step.id)}
                                                            className="mt-2 p-1.5 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500 border border-yellow-500/20 rounded-lg text-[10px] font-bold flex items-center gap-1 transition-all"
                                                        >
                                                            <Stethoscope size={12} />
                                                            AI Diagnosis
                                                        </button>
                                                    )}
                                                    {step.is_compensated && (
                                                        <div className="mt-2 inline-flex items-center gap-1 px-2 py-0.5 bg-purple-500/10 border border-purple-500/20 rounded-md text-[9px] font-bold text-purple-400 uppercase tracking-widest">
                                                            <ShieldCheck size={10} />
                                                            Compensated
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                            {step.output_summary && (
                                                <div className="mt-4 p-4 rounded-xl bg-white/[0.03] border border-white/5 text-xs text-gray-400 font-mono leading-relaxed">
                                                    {step.output_summary}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Report / Summary Section */}
                    {workflow?.final_report && (
                        <div className="glass-card">
                            <h3 className="text-sm font-bold text-white mb-6 flex items-center gap-2">
                                <Terminal size={18} className="text-[#66fcf1]" />
                                Final Synthesis Report
                            </h3>
                            <div className="prose prose-invert max-w-none prose-sm leading-relaxed p-6 rounded-2xl bg-white/[0.02] border border-white/5 text-gray-300">
                                {workflow.final_report}
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Column: Context & History */}
                <div className="space-y-8">
                    {/* History / Durable Events */}
                    <div className="glass-card">
                        <h3 className="text-sm font-bold text-white mb-6 flex items-center gap-2">
                            <History size={18} className="text-[#45a29e]" />
                            Event Log
                        </h3>
                        <div className="space-y-4">
                            {workflow?.history?.length > 0 ? (
                                workflow.history.slice(-8).reverse().map((event: any, i: number) => (
                                    <div key={i} className="flex gap-3 items-start p-3 rounded-lg hover:bg-white/[0.02] transition-colors border-l-2 border-[#45a29e]/20">
                                        <div className="text-[10px] text-gray-600 font-mono pt-1">
                                            {new Date(event.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}
                                        </div>
                                        <div>
                                            <p className="text-[11px] font-bold text-gray-300 capitalize">{event.event_type.replace('_', ' ')}</p>
                                            <p className="text-[9px] text-gray-500 font-mono mt-0.5">{event.step_id || "global"}</p>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="text-xs text-gray-600 text-center py-4 italic">No history recorded yet.</p>
                            )}
                        </div>
                    </div>

                    {/* Context Keys */}
                    <div className="glass-card">
                        <h3 className="text-sm font-bold text-white mb-6 flex items-center gap-2">
                            <Database size={18} className="text-[#66fcf1]" />
                            Active Context Keys
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            {workflow?.context_keys?.map((key: string) => (
                                <span key={key} className="px-2 py-1 bg-white/5 rounded-md text-[10px] font-mono text-gray-400 border border-white/5">
                                    {key}
                                </span>
                            ))}
                            {(!workflow?.context_keys || workflow.context_keys.length === 0) && (
                                <p className="text-xs text-gray-600 italic">Empty context object.</p>
                            )}
                        </div>
                    </div>

                    {/* Metadata / RBAC Policy */}
                    <div className="p-4 rounded-xl bg-[#66fcf1]/5 border border-[#66fcf1]/10 flex items-center gap-3">
                        <ShieldCheck size={20} className="text-[#66fcf1]" />
                        <div>
                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Active Security Policy</p>
                            <p className="text-xs text-white font-mono">RBAC: Enforced (Phase 13.04.C)</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Diagnosis Overlay */}
            {diagnosis && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-md p-4">
                    <div className="glass-card w-full max-w-lg border-yellow-500/30">
                        <h3 className="text-xl font-bold text-yellow-500 flex items-center gap-2 mb-6">
                            <Stethoscope size={24} />
                            Metacognitive Analysis
                        </h3>
                        <div className="space-y-6">
                            <div className="p-4 rounded-xl bg-black/40 border border-white/5 text-sm text-gray-300 leading-relaxed font-mono">
                                {diagnosis.reasoning}
                            </div>
                            {diagnosis.recommended_override && (
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Recommended Fix Overlay</label>
                                    <pre className="p-4 rounded-xl bg-black/60 border border-[#66fcf1]/20 text-[#66fcf1] text-[10px] overflow-auto max-h-40">
                                        {JSON.stringify(diagnosis.recommended_override, null, 2)}
                                    </pre>
                                </div>
                            )}
                            <div className="flex gap-4 pt-4">
                                <button 
                                    onClick={() => {
                                        setReplayMode("with_override");
                                        setOverrideJson(JSON.stringify(diagnosis.recommended_override, null, 2));
                                        setSelectedStepForReplay(workflow?.steps?.find((s:any) => s.status === "failed")?.id);
                                        setDiagnosis(null);
                                        setIsReplayModalOpen(true);
                                    }}
                                    className="flex-1 py-3 bg-yellow-500 hover:bg-yellow-600 text-black font-bold rounded-xl transition-all"
                                >
                                    Apply & Replay
                                </button>
                                <button 
                                    onClick={() => setDiagnosis(null)}
                                    className="px-8 py-3 glass text-white font-bold rounded-xl transition-all"
                                >
                                    Dismiss
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Replay Modal */}
            {isReplayModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="glass-card w-full max-w-xl border-[#66fcf1]/20 shadow-[0_0_50px_rgba(0,0,0,0.5)]">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <RefreshCcw className="text-[#66fcf1]" />
                                Configure Durable Replay
                            </h3>
                            <button onClick={() => setIsReplayModalOpen(false)} className="text-gray-500 hover:text-white">
                                <XOctagon size={24} />
                            </button>
                        </div>

                        <div className="space-y-6">
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Replay Start Point</label>
                                <div className="p-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white font-mono">
                                    {selectedStepForReplay ? `Step: ${selectedStepForReplay}` : "Entire Workflow (Default)"}
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Replay Mode</label>
                                <div className="grid grid-cols-3 gap-3">
                                    {(["same_input", "from_step", "with_override"] as const).map(mode => (
                                        <button 
                                            key={mode}
                                            onClick={() => setReplayMode(mode)}
                                            className={`p-3 rounded-xl border text-[10px] font-bold uppercase transition-all ${
                                                replayMode === mode ? "border-[#66fcf1] text-[#66fcf1] bg-[#66fcf1]/5" : "border-white/10 text-gray-500 hover:border-white/20"
                                            }`}
                                        >
                                            {mode.replace('_', ' ')}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {replayMode === "with_override" && (
                                <div className="space-y-4">
                                    {getSelectedStepSchema() && (
                                        <div>
                                            <label className="block text-[10px] font-bold text-[#45a29e] uppercase tracking-widest mb-2">Required Schema Definition</label>
                                            <div className="p-3 bg-white/[0.02] border border-white/5 rounded-xl text-[10px] text-gray-400 font-mono">
                                                <pre>{JSON.stringify(getSelectedStepSchema(), null, 2)}</pre>
                                            </div>
                                        </div>
                                    )}
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Manual Override (JSON)</label>
                                        <textarea 
                                            className="w-full h-40 bg-black/50 border border-white/10 rounded-xl p-4 text-xs font-mono text-[#66fcf1] focus:border-[#66fcf1] outline-none shadow-inner"
                                            value={overrideJson}
                                            onChange={(e) => setOverrideJson(e.target.value)}
                                            placeholder='{"input": {"key": "value"}, "context": {"flag": true}}'
                                        />
                                    </div>
                                </div>
                            )}

                            <button 
                                onClick={handleReplay}
                                className="w-full py-4 premium-gradient text-black font-bold rounded-xl shadow-[0_0_30px_rgba(102,252,241,0.2)] hover:scale-[1.02] transition-all"
                            >
                                Initiate Replay Sequence
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
