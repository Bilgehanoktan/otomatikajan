"use client";

import React, { useState, useEffect } from "react";
import { useCustom, useApiUrl } from "@refinedev/core";
import {
  Activity,
  ShieldAlert,
  Wrench,
  AlertCircle,
  ChevronUp,
  ChevronDown,
  X,
  ShieldCheck,
  Lock,
  ArrowRight,
  Zap,
  Loader2
} from "lucide-react";
import { App, Tooltip } from "antd";
import { safeFetchJson } from "@/lib/api";
import {
  RuntimeDiagnostic,
  RuntimeDiagnosticsResponse,
  compactRuntimeDiagnosticLabel
} from "@/lib/runtimeDiagnostics";

export function RuntimeDiagnosticsHUD() {
  const { message } = App.useApp();
  const apiUrl = useApiUrl();
  const [isOpen, setIsOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const [repairingId, setRepairingId] = useState<string | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const diagnosticsQuery = useCustom<RuntimeDiagnosticsResponse>({
    url: `${apiUrl}/health/runtime-diagnostics`,
    method: "get",
    queryOptions: {
      enabled: isMounted,
      refetchInterval: 15000,
    },
  });
  const { data: diagnosticsData, isLoading, refetch } = diagnosticsQuery.query;

  const diagnostics = diagnosticsData?.data?.diagnostics || [];
  const errorCount = diagnostics.filter(d => d.severity === "error").length;
  const warningCount = diagnostics.filter(d => d.severity === "warning").length;

  const runRepair = async (item: RuntimeDiagnostic) => {
    setRepairingId(item.id);
    try {
      const result = await safeFetchJson<{ status: string; actions?: string[]; recommended_action?: string }>(
        `/api/v1/health/runtime-diagnostics/${item.id}/repair`,
        {
          method: "POST",
          body: JSON.stringify({}),
        }
      );

      if (result.status === "repaired" || result.status === "noop") {
        message.success({
          content: `Onarım Başarılı: ${result.actions?.join(", ") || "Sistem stabilize edildi."}`,
          style: { marginTop: '10vh' }
        });
      } else {
        message.warning({
          content: result.recommended_action || "Operatör müdahalesi gerekiyor.",
          style: { marginTop: '10vh' }
        });
      }
      refetch();
    } catch (err: any) {
      message.error({
        content: `Onarım Hatası: ${err.message}`,
        style: { marginTop: '10vh' }
      });
    } finally {
      setRepairingId(null);
    }
  };

  if (!isMounted || (diagnostics.length === 0 && !isLoading)) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[1000] flex flex-col items-end gap-3 pointer-events-none">
      {/* Expanded HUD Panel */}
      {isOpen && (
        <div className="w-[380px] max-h-[500px] glass-panel border-white/10 bg-[#0b0c10]/95 shadow-[0_20px_60px_rgba(0,0,0,0.8)] rounded-[2rem] overflow-hidden flex flex-col animate-in slide-in-from-bottom-4 duration-300 pointer-events-auto">
          {/* Header */}
          <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[var(--primary)]/10 rounded-xl">
                <Activity size={16} className="text-[var(--primary)] animate-pulse" />
              </div>
              <div>
                <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em] italic leading-none">Runtime Diagnostics</h3>
                <p className="text-[9px] text-gray-500 font-bold uppercase mt-1 tracking-widest">{diagnostics.length} Active Signals</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 hover:bg-white/5 rounded-full text-gray-500 hover:text-white transition-colors"
            >
              <X size={16} />
            </button>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
            {diagnostics.map((item) => {
              const isError = item.severity === "error";
              const isWarning = item.severity === "warning";
              const label = compactRuntimeDiagnosticLabel(item);

              return (
                <div
                  key={item.id}
                  className={`p-4 rounded-2xl border transition-all duration-300 group ${
                    isError ? "bg-red-500/5 border-red-500/10 hover:border-red-500/30" :
                    isWarning ? "bg-amber-500/5 border-amber-500/10 hover:border-amber-500/30" :
                    "bg-cyan-500/5 border-cyan-500/10 hover:border-cyan-500/30"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${isError ? "bg-red-500 shadow-[0_0_8px_#ef4444]" : isWarning ? "bg-amber-500" : "bg-cyan-500"}`} />
                      <span className={`text-[10px] font-black uppercase tracking-wider ${isError ? "text-red-400" : isWarning ? "text-amber-400" : "text-cyan-400"}`}>
                        {label}
                      </span>
                    </div>
                    {item.id === "observer_write_denied" && (
                      <Tooltip title="Permission Locked">
                        <Lock size={12} className="text-red-500/50" />
                      </Tooltip>
                    )}
                  </div>

                  <p className="text-[11px] font-bold text-gray-300 leading-tight mb-2 italic">
                    {item.impact}
                  </p>

                  <div className="flex items-center justify-between gap-4 mt-4">
                    <span className="text-[9px] font-mono text-gray-600 uppercase tracking-widest truncate max-w-[180px]">
                      {item.recommended_action}
                    </span>

                    {item.auto_repairable ? (
                      <button
                        onClick={() => runRepair(item)}
                        disabled={repairingId === item.id}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--primary)]/10 border border-[var(--primary)]/20 text-[var(--primary)] text-[9px] font-black uppercase tracking-widest hover:bg-[var(--primary)]/20 transition-all disabled:opacity-50"
                      >
                        {repairingId === item.id ? <Loader2 size={10} className="animate-spin" /> : <Wrench size={10} />}
                        Repair
                      </button>
                    ) : item.requires_operator_action ? (
                      <div className="flex items-center gap-1 text-[9px] font-black text-amber-500/60 uppercase italic">
                        <ShieldAlert size={10} />
                        Manual
                      </div>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
            <span className="text-[8px] font-mono text-gray-600 uppercase">SIF-01 Guardrails Active</span>
            <button
              onClick={() => window.location.href = '/system-health'}
              className="flex items-center gap-2 text-[9px] font-black text-[var(--primary)] uppercase tracking-widest hover:translate-x-1 transition-all"
            >
              Full Intel <ArrowRight size={10} />
            </button>
          </div>
        </div>
      )}

      {/* Floating Badge (Trigger) */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`pointer-events-auto group relative p-4 rounded-full border shadow-[0_8px_32px_rgba(0,0,0,0.5)] transition-all duration-500 flex items-center gap-3 overflow-hidden ${
          isOpen ? "bg-white/5 border-white/10" :
          errorCount > 0 ? "bg-red-500/10 border-red-500/30 hover:bg-red-500/20" :
          warningCount > 0 ? "bg-amber-500/10 border-amber-500/30 hover:bg-amber-500/20" :
          "bg-[var(--primary)]/10 border-[var(--primary)]/30 hover:bg-[var(--primary)]/20"
        }`}
      >
        <div className="relative z-10">
          {errorCount > 0 ? (
            <ShieldAlert className="text-red-500 animate-pulse" size={20} />
          ) : warningCount > 0 ? (
            <AlertCircle className="text-amber-500" size={20} />
          ) : (
            <ShieldCheck className="text-[var(--primary)]" size={20} />
          )}
        </div>

        {!isOpen && (
          <div className="flex flex-col items-start pr-2 relative z-10">
            <span className="text-[8px] font-black text-gray-500 uppercase tracking-widest leading-none mb-1">Status</span>
            <span className={`text-[10px] font-black uppercase italic ${
              errorCount > 0 ? "text-red-400" : warningCount > 0 ? "text-amber-400" : "text-[var(--primary)]"
            }`}>
              {errorCount > 0 ? "Critical" : warningCount > 0 ? "Warning" : "Nominal"}
            </span>
          </div>
        )}

        {errorCount > 0 && !isOpen && (
          <div className="absolute inset-0 bg-red-500/5 animate-pulse pointer-events-none" />
        )}
      </button>
    </div>
  );
}
