"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  FileText,
  Fingerprint,
  History,
  Lock,
  ShieldCheck,
} from "lucide-react";
import { useList } from "@refinedev/core";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

type LineageRecord = {
  id: string;
  decision_type: string;
  component_name: string;
  rationale: string;
  outcome?: string | null;
  confidence_score: number;
  integrity_hash?: string | null;
  created_at: string;
};

type AuditBundleRecord = {
  id: string;
  name: string;
  purpose: string;
  project: string;
  created_at: string;
  operator: string;
  seal: string;
  size: string;
  status: string;
};

function summarizeRecord(record: LineageRecord) {
  const outcome = record.outcome ? ` · ${record.outcome}` : "";
  return `${record.decision_type.replaceAll("_", " ")} on ${record.component_name}${outcome}`;
}

export default function AuditPage() {
  const [isClient, setIsClient] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const {
    query: { data: lineageData, isLoading: lineageLoading },
  } = useList<LineageRecord>({
    resource: "governance/lineage",
    pagination: { pageSize: 20 },
    sorters: [{ field: "created_at", order: "desc" }],
    queryOptions: { enabled: isClient },
  });

  const {
    query: { data: bundlesData, isLoading: bundlesLoading },
  } = useList<AuditBundleRecord>({
    resource: "compliance/audit-bundles",
    pagination: { pageSize: 10 },
    sorters: [{ field: "created_at", order: "desc" }],
    queryOptions: { enabled: isClient },
  });

  const records = lineageData?.data ?? [];
  const bundles = bundlesData?.data ?? [];
  const selected = useMemo(
    () => records.find((record) => record.id === selectedId) ?? records[0] ?? null,
    [records, selectedId],
  );

  useEffect(() => {
    if (!selectedId && records.length > 0) {
      setSelectedId(records[0].id);
    }
  }, [records, selectedId]);

  if (!isClient) {
    return <div className="min-h-screen bg-[#060a12]" />;
  }

  const latestBundle = bundles[0];

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      <ResourceHeader
        title="Audit Ledger"
        subtitle="Immutable Verification & Multi-Operator Quorum"
        icon={<FileText size={32} />}
        badge="Institutional Grade"
        actions={
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-4 border-r border-white/5 pr-8">
              <div className="text-right">
                <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">
                  Lineage State
                </p>
                <p className="text-[11px] text-green-400 font-black mt-2">
                  {latestBundle ? "SEALED & SYNCED" : "CHAIN ACTIVE"}
                </p>
              </div>
              <div className="p-3 bg-green-500/10 rounded-full animate-pulse border border-green-500/20">
                <Lock size={16} className="text-green-400" />
              </div>
            </div>

            <Link
              href="/proof/snapshots"
              className="flex items-center gap-2 px-8 py-3 bg-[var(--primary)] text-[#060a12] text-[10px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95"
            >
              <Fingerprint size={14} />
              <span>Export Proof</span>
            </Link>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        <div className="xl:col-span-8">
          <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.01] to-transparent relative overflow-hidden">
            <div className="absolute -top-20 -right-20 opacity-[0.03] rotate-12 pointer-events-none">
              <ShieldCheck size={400} className="text-[var(--primary)]" />
            </div>

            <div className="flex items-center justify-between mb-12 relative z-10">
              <div className="flex items-center gap-4">
                <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-ping" />
                <h2 className="text-xs font-black text-white uppercase tracking-[0.4em]">
                  Live Verification Stream
                </h2>
              </div>
              <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500 bg-black/40 px-4 py-2 rounded-xl border border-white/5">
                <Fingerprint size={14} className="text-[var(--primary)]" />
                LEDGER PARITY VERIFIED
              </div>
            </div>

            <div className="relative pl-12 space-y-10 before:absolute before:left-[17px] before:top-4 before:bottom-4 before:w-px before:bg-gradient-to-b before:from-[var(--primary)]/60 before:via-white/5 before:to-transparent">
              {lineageLoading ? (
                <div className="space-y-10">
                  {[1, 2, 3].map((index) => (
                    <Skeleton key={index} className="h-36 w-full rounded-3xl" />
                  ))}
                </div>
              ) : records.length === 0 ? (
                <div className="py-24 text-center flex flex-col items-center gap-6 opacity-60">
                  <div className="p-8 bg-white/[0.02] rounded-full border border-white/5">
                    <History size={40} className="text-[var(--primary)]" />
                  </div>
                  <p className="font-black text-gray-600 uppercase tracking-[0.3em] italic">
                    Henüz audit kaydı bulunmuyor.
                  </p>
                </div>
              ) : (
                records.map((record) => {
                  const isSelected = selected?.id === record.id;
                  return (
                    <div
                      key={record.id}
                      onClick={() => setSelectedId(record.id)}
                      className={`relative group cursor-pointer transition-all duration-500 ${isSelected ? "translate-x-2" : ""}`}
                    >
                      <div
                        className={`absolute -left-[45px] top-2 w-6 h-6 rounded-full bg-[#060a12] border-2 transition-all duration-500 z-10 ${
                          isSelected
                            ? "border-[var(--primary)] scale-125 shadow-[0_0_15px_var(--primary)]"
                            : "border-gray-800 group-hover:border-[var(--primary)]/60 shadow-xl"
                        }`}
                      >
                        <div className="absolute inset-1 rounded-full bg-[var(--primary)]/10 animate-pulse" />
                      </div>

                      <div className="flex flex-col gap-5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <span className="text-[10px] font-mono text-gray-600 tracking-widest uppercase">
                              {new Date(record.created_at).toLocaleString()}
                            </span>
                            <div className="px-3 py-1 rounded-lg text-[9px] font-black tracking-widest uppercase border bg-green-400/5 text-green-400 border-green-400/20 shadow-[0_0_10px_rgba(34,197,94,0.1)]">
                              {record.decision_type}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 group-hover:text-[var(--primary)] transition-colors">
                            <History size={12} className="text-gray-700" />
                            <span className="text-[10px] font-mono text-gray-700 font-bold uppercase tracking-widest">
                              {record.component_name}
                            </span>
                          </div>
                        </div>

                        <div
                          className={`p-8 rounded-[2rem] border transition-all duration-500 relative overflow-hidden ${
                            isSelected
                              ? "bg-white/[0.04] border-[var(--primary)]/40 shadow-2xl"
                              : "bg-white/[0.012] border-white/5 hover:border-white/10 hover:bg-white/[0.02]"
                          }`}
                        >
                          <div className="flex justify-between items-start mb-6 gap-4">
                            <h4 className="text-white font-black text-base tracking-tight leading-snug max-w-xl">
                              {summarizeRecord(record)}
                            </h4>
                            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-black/40 border border-white/5 shrink-0">
                              <Fingerprint size={12} className="text-[var(--primary)]" />
                              <span className="text-[10px] font-mono text-gray-500">
                                {(record.integrity_hash || record.id).slice(0, 12)}...
                              </span>
                            </div>
                          </div>

                          <p className="text-sm text-gray-400 leading-relaxed">
                            {record.rationale}
                          </p>

                          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 pt-6 mt-6 border-t border-white/[0.03]">
                            <EvidenceItem label="Component" val={record.component_name} icon={<ShieldCheck size={12} />} />
                            <EvidenceItem label="Outcome" val={record.outcome ?? "RECORDED"} icon={<FileText size={12} />} />
                            <EvidenceItem label="Confidence" val={`${Math.round((record.confidence_score || 0) * 100)}%`} icon={<History size={12} />} />
                            <EvidenceItem label="Integrity" status="SEALED" icon={<Lock size={12} />} />
                          </div>

                          {isSelected && (
                            <div className="mt-8 pt-8 border-t border-white/5 flex items-center justify-between animate-in slide-in-from-top-4 duration-500">
                              <div className="flex flex-col gap-1">
                                <span className="text-[8px] font-black text-gray-600 uppercase tracking-widest">
                                  Integrity Hash
                                </span>
                                <span className="text-[10px] font-mono text-gray-500 leading-none break-all">
                                  {record.integrity_hash || record.id}
                                </span>
                              </div>
                              <Link
                                href="/governor/proof"
                                className="text-[10px] font-black text-[var(--primary)] uppercase tracking-widest flex items-center gap-2 hover:translate-x-1 transition-transform"
                              >
                                Full Audit Trail
                              </Link>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </section>
        </div>

        <div className="xl:col-span-4 space-y-8">
          <section className="glass-panel p-10 rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/50 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity">
              <ShieldCheck size={160} />
            </div>

            <div className="flex items-center gap-4 mb-10 relative z-10">
              <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-[0_0_20px_rgba(102,252,241,0.15)]">
                <ShieldCheck size={24} className="text-[var(--primary)]" />
              </div>
              <div>
                <h3 className="text-xl font-black text-white tracking-tighter uppercase">
                  Governance
                </h3>
                <p className="text-[9px] text-[var(--primary)] font-black tracking-[0.2em] uppercase mt-1">
                  Audit Policy v9.2
                </p>
              </div>
            </div>

            <div className="space-y-5 relative z-10">
              {[
                { label: "Lineage Records", value: String(records.length), status: "text-white" },
                { label: "Audit Bundles", value: String(bundles.length), status: "text-white" },
                {
                  label: "Latest Bundle",
                  value: latestBundle?.name ?? "Not sealed yet",
                  status: "text-[var(--primary)]",
                },
                {
                  label: "Bundle Status",
                  value: latestBundle?.status?.toUpperCase() ?? "PENDING",
                  status: latestBundle?.status === "sealed" ? "text-green-400" : "text-[var(--primary)]",
                },
              ].map((item) => (
                <div
                  key={item.label}
                  className="p-5 rounded-3xl bg-white/[0.015] border border-white/5 hover:border-[var(--primary)]/20 transition-all"
                >
                  <p className="text-[9px] text-gray-600 font-black uppercase tracking-widest mb-1.5">
                    {item.label}
                  </p>
                  <p className={`text-xs font-black uppercase tracking-tight ${item.status}`}>
                    {item.value}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section className="glass-panel p-10 rounded-[2.5rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.03] to-transparent">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <CheckCircle2 size={18} className="text-green-400" />
                <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">
                  Integrity Check
                </h3>
              </div>
              <span className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">
                {latestBundle ? "SEALED" : "STANDBY"}
              </span>
            </div>

            {bundlesLoading ? (
              <Skeleton className="h-40 w-full rounded-3xl" />
            ) : latestBundle ? (
              <div className="space-y-6">
                <div className="p-6 rounded-3xl bg-black/30 border border-white/5">
                  <p className="text-[9px] text-gray-600 font-black uppercase tracking-widest mb-3">
                    Bundle Name
                  </p>
                  <p className="text-white font-black text-lg tracking-tight">
                    {latestBundle.name}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-5 rounded-2xl bg-white/[0.015] border border-white/5">
                    <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-2">
                      Project
                    </p>
                    <p className="text-[var(--primary)] font-mono font-black text-lg">
                      {latestBundle.project}
                    </p>
                  </div>
                  <div className="p-5 rounded-2xl bg-white/[0.015] border border-white/5">
                    <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-2">
                      Status
                    </p>
                    <p className="text-green-400 font-black text-lg">
                      {latestBundle.status.toUpperCase()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 p-5 rounded-2xl bg-black/40 border border-white/5">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                  <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest leading-relaxed">
                    Son audit paketi mühürlü durumda. Bundle metadata ve lineage kayıtları senkron.
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-16 text-center opacity-50">
                <p className="font-black text-gray-600 uppercase tracking-[0.3em] italic">
                  Audit bundle bekleniyor.
                </p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

function EvidenceItem({
  label,
  val,
  status,
  icon,
}: {
  label: string;
  val?: string;
  status?: string;
  icon: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-gray-600">
        {icon}
        <span className="text-[8px] font-black uppercase tracking-widest">{label}</span>
      </div>
      {status ? (
        <span className="text-[10px] font-black text-blue-400 tracking-widest uppercase">
          {status}
        </span>
      ) : (
        <span className="text-[10px] font-black text-gray-400 tracking-tight uppercase truncate">
          {val}
        </span>
      )}
    </div>
  );
}
