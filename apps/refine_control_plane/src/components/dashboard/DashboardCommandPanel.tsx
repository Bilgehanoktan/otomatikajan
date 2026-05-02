"use client";

import React, { useState } from "react";
import { Rocket, ShieldAlert, FileSearch, ShieldCheck, Play, ArrowRight, Loader2 } from "lucide-react";
import { safeFetchJson } from "@/lib/api";
import { App } from "antd";

interface CommandButtonProps {
  label: string;
  sub: string;
  icon: React.ReactNode;
  color: string;
  onClick: () => void;
  loading?: boolean;
}

function CommandButton({ label, sub, icon, color, onClick, loading }: CommandButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`group relative flex items-center justify-between p-4 rounded-2xl border border-white/[0.05] bg-white/[0.02] hover:bg-white/[0.05] hover:border-[var(--primary)]/30 hover:shadow-[0_8px_32px_rgba(0,0,0,0.4)] transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none text-left w-full`}
    >
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-xl bg-black/40 border border-white/5 transition-colors group-hover:border-[var(--primary)]/20 ${color}`}>
          {loading ? <Loader2 size={18} className="animate-spin" /> : icon}
        </div>
        <div>
          <div className="text-[11px] font-black text-white uppercase tracking-wider">{label}</div>
          <div className="text-[9px] text-gray-500 font-mono mt-1 group-hover:text-gray-400">{sub}</div>
        </div>
      </div>
      <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-[var(--primary)]/10 group-hover:text-[var(--primary)] transition-all">
          <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
      </div>
    </button>
  );
}

export function DashboardCommandPanel({ apiBase }: { apiBase: string }) {
  const { notification } = App.useApp();
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const handleAction = async (action: string, endpoint: string, method: string = "POST", body: any = null) => {
    setLoadingAction(action);
    try {
      // Phase 32: Use safeFetchJson for resilience and auth-cookie inclusion
      const data = await safeFetchJson(`/api/v1${endpoint}`, {
        method,
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      
      notification.success({
        message: "Komut İletildi",
        description: data.message || "İşlem başarıyla tetiklendi.",
        placement: "bottomRight"
      });
    } catch (err: any) {
      notification.error({
        message: "Bağlantı Hatası",
        description: `Backend servisine ulaşılamadı veya geçersiz yanıt alındı. Hata: ${err.message}`,
        placement: "bottomRight"
      });
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] animate-pulse shadow-[0_0_8px_var(--primary)]" />
          <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.25em]">Hızlı Aksiyonlar</h3>
        </div>
        <span className="text-[8px] font-mono text-gray-600 uppercase">Operator Auth: Active</span>
      </div>

      <div className="grid grid-cols-1 gap-3 flex-1 overflow-y-auto pr-1">
        <CommandButton
          label="Operasyonel Tatbikat (Drill)"
          sub="Governance Drill Trigger · /governance/drills/trigger"
          icon={<ShieldAlert size={18} />}
          color="text-amber-400"
          loading={loadingAction === "drill"}
          onClick={() => handleAction("drill", "/governance/drills/trigger?scenario=RESILIENCE_DRILL_01")}
        />

        <CommandButton
          label="Üretim Devir Teslim (Handover)"
          sub="Production Handover · /governance/ops/handover"
          icon={<Rocket size={18} />}
          color="text-[#66fcf1]"
          loading={loadingAction === "handover"}
          onClick={() => handleAction("handover", "/governance/ops/handover?project_id=SOV-PILOT-01&dry_run=true")}
        />

        <CommandButton
          label="Denetim Paketi Oluştur"
          sub="Generate Audit Bundle · /compliance/audit-bundles"
          icon={<FileSearch size={18} />}
          color="text-gray-400"
          loading={loadingAction === "audit"}
          onClick={() => handleAction("audit", "/compliance/audit-bundles", "POST", { name: `Audit_${new Date().toISOString().split('T')[0]}` })}
        />

        <CommandButton
          label="Onay Bekleyenler"
          sub="Pending Approvals · /approvals?status=pending"
          icon={<ShieldCheck size={18} />}
          color="text-green-400"
          loading={loadingAction === "approvals"}
          onClick={() => window.open(`/approvals?status=pending`, "_blank")}
        />
      </div>

      <div className="mt-8 pt-6 border-t border-white/5">
         <div className="flex items-center gap-4 justify-between bg-black/30 p-4 rounded-xl border border-white/[0.03]">
            <div className="flex flex-col">
               <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest leading-none">Safe Mode</span>
               <span className="text-[10px] font-bold text-gray-400 mt-1 uppercase">Aktif</span>
            </div>
            <div className="w-12 h-6 bg-white/5 rounded-full relative p-1 cursor-pointer hover:bg-white/10 transition-colors">
               <div className="w-4 h-4 bg-green-400 rounded-full shadow-[0_0_8px_rgba(72,187,120,0.5)]" />
            </div>
         </div>
      </div>
    </div>
  );
}
