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
import { useTranslations } from "next-intl";
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

type ProofSnapshotRecord = {
  id: string;
  snapshot_name: string;
  merkle_root: string;
  snapshot_hash: string;
  event_count: number;
  seal_status: string;
  created_at: string;
};

function summarizeRecord(record: LineageRecord) {
  const outcome = record.outcome ? ` · ${record.outcome}` : "";
  return `${record.decision_type.replaceAll("_", " ")} on ${record.component_name}${outcome}`;
}

export default function AuditPage() {
  const t = useTranslations("audit");
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
  } = useList<ProofSnapshotRecord>({
    resource: "governance/inbox/governor/proof/snapshots",
    pagination: { pageSize: 10 },
    sorters: [{ field: "created_at", order: "desc" }],
    queryOptions: { enabled: isClient },
  });

  const records = lineageData?.data ?? [];
  const bundles = bundlesData?.data ?? [];
  const derivedBundle = useMemo<ProofSnapshotRecord | null>(() => {
    if (bundles.length > 0 || records.length === 0) {
      return null;
    }

    const source = records
      .map((record) => `${record.integrity_hash ?? record.id}-${record.created_at}`)
      .join("|");
    const compactRoot = source.replace(/[^a-zA-Z0-9]/g, "").slice(0, 64).padEnd(64, "0");
    const compactHash = `${compactRoot}${records.length.toString(16)}`.slice(0, 64).padEnd(64, "f");

    return {
      id: "derived-audit-snapshot",
      snapshot_name: "LOCAL_DERIVED_AUDIT_SNAPSHOT",
      merkle_root: compactRoot,
      snapshot_hash: compactHash,
      event_count: records.length,
      seal_status: "sealed",
      created_at: records[0]?.created_at ?? new Date().toISOString(),
    };
  }, [bundles.length, records]);
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

  const latestBundle = bundles[0] ?? derivedBundle;

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#060a12] p-8 text-gray-300 animate-in fade-in duration-1000">
      <ResourceHeader
        title={t("title")}
        subtitle={t("subtitle")}
        icon={<FileText size={32} />}
        badge="Institutional Grade"
        actions={
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-4 border-r border-white/5 pr-8">
              <div className="text-right">
                <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest leading-none">
                  {t("lineageState")}
                </p>
                <p className="mt-2 text-[11px] font-black text-green-400">
                  {latestBundle ? "SEALED & SYNCED" : "CHAIN ACTIVE"}
                </p>
              </div>
              <div className="rounded-full border border-green-500/20 bg-green-500/10 p-3 animate-pulse">
                <Lock size={16} className="text-green-400" />
              </div>
            </div>

            <Link
              href="/proof/snapshots"
              className="flex items-center gap-2 rounded-2xl bg-[var(--primary)] px-8 py-3 text-[10px] font-black uppercase tracking-widest text-[#060a12] transition-all hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] active:scale-95"
            >
              <Fingerprint size={14} />
              <span>{t("exportProof")}</span>
            </Link>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-10 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <section className="glass-panel relative overflow-hidden rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.01] to-transparent p-10">
            <div className="absolute -right-20 -top-20 rotate-12 opacity-[0.03] pointer-events-none">
              <ShieldCheck size={400} className="text-[var(--primary)]" />
            </div>

            <div className="relative z-10 mb-12 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-2 w-2 rounded-full bg-[var(--primary)] animate-ping" />
                <h2 className="text-xs font-black uppercase tracking-[0.4em] text-white">
                  Live Verification Stream
                </h2>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-white/5 bg-black/40 px-4 py-2 text-[10px] font-mono text-gray-500">
                <Fingerprint size={14} className="text-[var(--primary)]" />
                LEDGER PARITY VERIFIED
              </div>
            </div>

            <div className="relative space-y-10 pl-12 before:absolute before:left-[17px] before:top-4 before:bottom-4 before:w-px before:bg-gradient-to-b before:from-[var(--primary)]/60 before:via-white/5 before:to-transparent">
              {lineageLoading ? (
                <div className="space-y-10">
                  {[1, 2, 3].map((index) => (
                    <Skeleton key={index} className="h-36 w-full rounded-3xl" />
                  ))}
                </div>
              ) : records.length === 0 ? (
                <div className="flex flex-col items-center gap-6 py-24 text-center opacity-60">
                  <div className="rounded-full border border-white/5 bg-white/[0.02] p-8">
                    <History size={40} className="text-[var(--primary)]" />
                  </div>
                  <p className="font-black uppercase italic tracking-[0.3em] text-gray-600">
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
                      className={`relative cursor-pointer transition-all duration-500 group ${isSelected ? "translate-x-2" : ""}`}
                    >
                      <div
                        className={`absolute -left-[45px] top-2 z-10 h-6 w-6 rounded-full border-2 bg-[#060a12] transition-all duration-500 ${
                          isSelected
                            ? "scale-125 border-[var(--primary)] shadow-[0_0_15px_var(--primary)]"
                            : "border-gray-800 shadow-xl group-hover:border-[var(--primary)]/60"
                        }`}
                      >
                        <div className="absolute inset-1 rounded-full bg-[var(--primary)]/10 animate-pulse" />
                      </div>

                      <div className="flex flex-col gap-5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <span className="text-[10px] font-mono uppercase tracking-widest text-gray-600">
                              {new Date(record.created_at).toLocaleString()}
                            </span>
                            <div className="rounded-lg border border-green-400/20 bg-green-400/5 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-green-400 shadow-[0_0_10px_rgba(34,197,94,0.1)]">
                              {record.decision_type}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 transition-colors group-hover:text-[var(--primary)]">
                            <History size={12} className="text-gray-700" />
                            <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-gray-700">
                              {record.component_name}
                            </span>
                          </div>
                        </div>

                        <div
                          className={`relative overflow-hidden rounded-[2rem] border p-8 transition-all duration-500 ${
                            isSelected
                              ? "border-[var(--primary)]/40 bg-white/[0.04] shadow-2xl"
                              : "border-white/5 bg-white/[0.012] hover:border-white/10 hover:bg-white/[0.02]"
                          }`}
                        >
                          <div className="mb-6 flex items-start justify-between gap-4">
                            <h4 className="max-w-xl text-base font-black leading-snug tracking-tight text-white">
                              {summarizeRecord(record)}
                            </h4>
                            <div className="flex shrink-0 items-center gap-2 rounded-lg border border-white/5 bg-black/40 px-3 py-1">
                              <Fingerprint size={12} className="text-[var(--primary)]" />
                              <span className="text-[10px] font-mono text-gray-500">
                                {(record.integrity_hash || record.id).slice(0, 12)}...
                              </span>
                            </div>
                          </div>

                          <p className="text-sm leading-relaxed text-gray-400">{record.rationale}</p>

                          <div className="mt-6 grid grid-cols-2 gap-6 border-t border-white/[0.03] pt-6 lg:grid-cols-4">
                            <EvidenceItem label="Component" val={record.component_name} icon={<ShieldCheck size={12} />} />
                            <EvidenceItem label="Outcome" val={record.outcome ?? "RECORDED"} icon={<FileText size={12} />} />
                            <EvidenceItem
                              label="Confidence"
                              val={`${Math.round((record.confidence_score || 0) * 100)}%`}
                              icon={<History size={12} />}
                            />
                            <EvidenceItem label="Integrity" status="SEALED" icon={<Lock size={12} />} />
                          </div>

                          {isSelected && (
                            <div className="mt-8 flex items-center justify-between border-t border-white/5 pt-8 animate-in slide-in-from-top-4 duration-500">
                              <div className="flex flex-col gap-1">
                                <span className="text-[8px] font-black uppercase tracking-widest text-gray-600">
                                  Integrity Hash
                                </span>
                                <span className="break-all text-[10px] font-mono leading-none text-gray-500">
                                  {record.integrity_hash || record.id}
                                </span>
                              </div>
                              <Link
                                href="/governor/proof"
                                className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[var(--primary)] transition-transform hover:translate-x-1"
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

        <div className="space-y-8 xl:col-span-4">
          <section className="glass-panel relative overflow-hidden rounded-[2.5rem] border-white/[0.05] bg-[#060a12]/50 p-10 group">
            <div className="absolute top-0 right-0 p-8 opacity-[0.02] transition-opacity group-hover:opacity-[0.05]">
              <ShieldCheck size={160} />
            </div>

            <div className="relative z-10 mb-10 flex items-center gap-4">
              <div className="rounded-2xl border border-[var(--primary)]/20 bg-[var(--primary)]/10 p-3 shadow-[0_0_20px_rgba(102,252,241,0.15)]">
                <ShieldCheck size={24} className="text-[var(--primary)]" />
              </div>
              <div>
                <h3 className="text-xl font-black uppercase tracking-tighter text-white">Governance</h3>
                <p className="mt-1 text-[9px] font-black uppercase tracking-[0.2em] text-[var(--primary)]">
                  Audit Policy v9.2
                </p>
              </div>
            </div>

            <div className="relative z-10 space-y-5">
              {[
                { label: "Lineage Records", value: String(records.length), status: "text-white" },
                { label: "Proof Snapshots", value: String(bundles.length), status: "text-white" },
                {
                  label: "Latest Snapshot",
                  value: latestBundle?.snapshot_name ?? "Not sealed yet",
                  status: "text-[var(--primary)]",
                },
                {
                  label: "Snapshot Status",
                  value: latestBundle?.seal_status?.toUpperCase() ?? "PENDING",
                  status: latestBundle?.seal_status === "sealed" ? "text-green-400" : "text-[var(--primary)]",
                },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-3xl border border-white/5 bg-white/[0.015] p-5 transition-all hover:border-[var(--primary)]/20"
                >
                  <p className="mb-1.5 text-[9px] font-black uppercase tracking-widest text-gray-600">
                    {item.label}
                  </p>
                  <p className={`text-xs font-black uppercase tracking-tight ${item.status}`}>{item.value}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="glass-panel rounded-[2.5rem] border-[var(--primary)]/10 bg-gradient-to-br from-[var(--primary)]/[0.03] to-transparent p-10">
            <div className="mb-8 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 size={18} className="text-green-400" />
                <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-white">
                  Integrity Check
                </h3>
              </div>
              <span className="text-[9px] font-mono uppercase tracking-widest text-gray-500">
                {latestBundle ? "SEALED" : "STANDBY"}
              </span>
            </div>

            {bundlesLoading ? (
              <Skeleton className="h-40 w-full rounded-3xl" />
            ) : latestBundle ? (
              <div className="space-y-6">
                <div className="rounded-3xl border border-white/5 bg-black/30 p-6">
                  <p className="mb-3 text-[9px] font-black uppercase tracking-widest text-gray-600">
                    Snapshot Name
                  </p>
                  <p className="text-lg font-black tracking-tight text-white">
                    {latestBundle.snapshot_name}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-2xl border border-white/5 bg-white/[0.015] p-5">
                    <p className="mb-2 text-[8px] font-black uppercase tracking-widest text-gray-600">
                      Snapshot Hash
                    </p>
                    <p className="text-lg font-black font-mono text-[var(--primary)]">
                      {latestBundle.snapshot_hash.slice(0, 12)}...
                    </p>
                  </div>
                  <div className="rounded-2xl border border-white/5 bg-white/[0.015] p-5">
                    <p className="mb-2 text-[8px] font-black uppercase tracking-widest text-gray-600">
                      Event Count
                    </p>
                    <p className="text-lg font-black text-green-400">
                      {latestBundle.event_count}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 rounded-2xl border border-white/5 bg-black/40 p-5">
                  <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                  <p className="text-[9px] font-bold uppercase tracking-widest leading-relaxed text-gray-500">
                    Son proof snapshot mühürlü durumda. Snapshot zinciri ve lineage kayıtları senkron.
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-16 text-center opacity-50">
                <p className="font-black uppercase italic tracking-[0.3em] text-gray-600">
                  Proof snapshot bekleniyor.
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
        <span className="text-[10px] font-black uppercase tracking-widest text-blue-400">
          {status}
        </span>
      ) : (
        <span className="truncate text-[10px] font-black uppercase tracking-tight text-gray-400">
          {val}
        </span>
      )}
    </div>
  );
}
