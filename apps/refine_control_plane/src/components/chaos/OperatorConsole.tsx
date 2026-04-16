"use client";

import React, { useState } from "react";
import { Zap, Snowflake, ShieldX, Terminal, Loader2, AlertTriangle, Fingerprint } from "lucide-react";

interface ActionProps {
  onAction: (action: string, reason: string) => Promise<void>;
  isLocked?: boolean;
}

export default function OperatorConsole({ onAction, isLocked = false }: ActionProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const [showReasonInput, setShowReasonInput] = useState<string | null>(null);
  const [reason, setReason] = useState("");

  const handleTrigger = async (action: string) => {
    if (!reason) {
       setShowReasonInput(action);
       return;
    }
    setLoading(action);
    await onAction(action, reason);
    setLoading(null);
    setShowReasonInput(null);
    setReason("");
  };

  return (
    <div className="p-6 rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-2xl relative overflow-hidden h-full">
      {/* HEADER */}
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
          <Terminal className="text-amber-500 w-5 h-5 font-bold" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">Operator Action Console</h2>
          <p className="text-[#45a29e] text-[10px] uppercase tracking-widest font-mono">High-Privilege Command Center</p>
        </div>
      </div>

      {/* RBAC NOTICE */}
      <div className="mb-8 p-3 rounded-lg bg-[#45a29e]/5 border border-[#45a29e]/10 flex items-center gap-3">
        <Fingerprint size={16} className="text-[#45a29e]" />
        <span className="text-[10px] text-[#c5c6c7] font-medium leading-tight">
          Session authorized for <span className="text-white font-bold">SOVEREIGN-ADMIN</span>. All mutations are globally audited and signed via mesh co-repo GitOps.
        </span>
      </div>

      {/* ACTIONS GRID */}
      <div className="grid grid-cols-1 gap-4">
        <ActionButton 
          icon={<RefreshIcon loading={loading === 'recalibrate'} />}
          label="Mesh Recalibrate"
          sub="Force global latency/health pulse."
          onClick={() => handleTrigger('recalibrate')}
          variant="primary"
          disabled={!!loading || isLocked}
        />
        <ActionButton 
          icon={<Snowflake size={18} className={loading === 'freeze' ? 'animate-spin' : ''}/>}
          label="Global Emergency Freeze"
          sub="Force absolute Advisory Mode mesh-wide."
          onClick={() => handleTrigger('freeze')}
          variant="warning"
          disabled={!!loading || isLocked}
        />
        <ActionButton 
          icon={<ShieldX size={18} />}
          label="Regional Quarantine"
          sub="Isolate suspected compromised nodes."
          onClick={() => handleTrigger('quarantine')}
          variant="danger"
          disabled={!!loading || isLocked}
        />
      </div>

      {/* REASON MODAL (SIMULATED INLINE) */}
      {showReasonInput && (
        <div className="absolute inset-0 z-50 bg-[#0b0c10]/95 backdrop-blur-xl p-8 flex flex-col justify-center animate-in fade-in zoom-in duration-200">
          <div className="flex items-center gap-2 mb-4 text-amber-500">
             <AlertTriangle size={20} />
             <h4 className="font-bold uppercase tracking-tight">Confirm Action: {showReasonInput}</h4>
          </div>
          <p className="text-xs text-[#c5c6c7] mb-6 leading-relaxed">
            Provide a mandatory operational justification for this mutation. This record will be persisted in global audit logs and GitOps history.
          </p>
          <textarea 
            className="w-full bg-[#1f2833]/50 border border-[#1f2833] rounded-xl p-4 text-sm text-white focus:outline-none focus:border-[#66fcf1] transition-colors h-24 mb-6 placeholder:text-white/20"
            placeholder="Operational justification required..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <div className="flex gap-4">
            <button 
              className="flex-1 py-3 rounded-xl bg-[#1f2833] text-white text-sm font-bold hover:bg-[#1f2833]/80 transition-all"
              onClick={() => { setShowReasonInput(null); setReason(""); }}
            >
              Cancel
            </button>
            <button 
              className="flex-1 py-3 rounded-xl bg-amber-600 text-[#0b0c10] text-sm font-black uppercase tracking-widest hover:brightness-110 transition-all disabled:opacity-50"
              onClick={() => handleTrigger(showReasonInput)}
              disabled={!reason}
            >
              Execute
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ActionButton({ icon, label, sub, onClick, variant = "primary", disabled }: any) {
  const styles: any = {
    primary: "border-[#1f2833] hover:border-[#66fcf1]/30 hover:bg-[#66fcf1]/5 group-hover:first:text-[#66fcf1]",
    warning: "border-amber-500/20 hover:border-amber-500/50 hover:bg-amber-500/5",
    danger: "border-red-500/20 hover:border-red-500/50 hover:bg-red-500/5"
  };

  const iconColors: any = {
     primary: "text-[#45a29e] group-hover:text-[#66fcf1]",
     warning: "text-amber-500",
     danger: "text-red-500"
  };

  return (
    <button 
      className={`group flex items-center gap-5 p-4 rounded-2xl border bg-[#1f2833]/20 transition-all duration-300 text-left disabled:opacity-30 disabled:cursor-not-allowed ${styles[variant]}`}
      onClick={onClick}
      disabled={disabled}
    >
      <div className={`p-3 rounded-xl bg-[#0b0c10]/40 transition-colors ${iconColors[variant]}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm font-bold text-white tracking-tight">{label}</p>
        <p className="text-[10px] text-[#45a29e] font-mono leading-tight mt-0.5">{sub}</p>
      </div>
    </button>
  );
}

function RefreshIcon({ loading }: { loading: boolean }) {
  return loading ? <Loader2 size={18} className="animate-spin" /> : <Zap size={18} />;
}
