"use client";

import React from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Eye,
  FileText,
  GitPullRequestDraft,
  KeyRound,
  ListChecks,
  Lock,
  Play,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  ShieldCheck,
  ShieldOff,
  Terminal,
  Trash2,
} from "lucide-react";
import {
  AIPatchSuggestionRecord,
  ApiKeyCreateResponse,
  ApiKeyRecord,
  EvidenceRecord,
  OpsSnapshot,
  PatchRevisionRecord,
  PrDraftRecord,
  PrVerificationRecord,
  ProposalRecord,
  QuotaUsage,
  ResearchRecord,
  ReviewLedgerEntryRecord,
  ReviewLedgerExportRecord,
  ReviewLedgerVerifyRecord,
  ReviewerFeedbackRecord,
  AgentPromotionRecord,
  AgentPolicySimulationResponse,
  acceptAiPatchSuggestionForReview,
  approveProposal,
  createBilgeApiKey,
  createAiPatchSuggestion,
  createDraftPr,
  createPatchRevision,
  createProposal,
  createResearchRequest,
  createReviewerFeedback,
  exportReviewLedgerChain,
  getAiPatchSuggestion,
  getReviewLedgerChain,
  getProposalAuditReport,
  listPatchRevisions,
  listAiPatchSuggestions,
  listResearchEvidences,
  listReviewerFeedback,
  loadBilgeApiOpsSnapshot,
  redactPlaintextKey,
  revokeBilgeApiKey,
  runProposalGate,
  runReleaseReadiness,
  updateApiKeyQuota,
  rejectAiPatchSuggestion,
  verifyDraftPr,
  verifyAiPatchSuggestion,
  verifyPatchRevision,
  verifyReviewLedgerChain,
  enableRemediationRunbook,
  disableRemediationRunbook,
  triggerRemediation,
  runEmergencyRecovery,
  setManagementGate,
  acknowledgeFinding,
  dismissFinding,
  runWatchdogScan,
  getAgentPromotion,
  isBilgeApiAuthError,
  approveAgentPromotion,
  rejectAgentPromotion,
  executeAgentPromotion,
  simulateAgentPromotion,
  retryAgentRun,
  enableAgent,
  disableAgent,
} from "@/lib/bilgeapiOpsClient";
import { useTranslations } from "next-intl";
import { useGetIdentity } from "@refinedev/core";



type OpsTab = "dashboard" | "keys" | "research" | "prs" | "revisions" | "ai" | "governor" | "remediation" | "ledger" | "audit" | "agents";

type ActionLog = {
  id: string;
  label: string;
  status: "OK" | "ERR";
  detail: string;
};

const AUTH_RECOVERY_MARKER = "bilgeapi_ops_auth_recovery_attempted";

const roles = ["ADMIN", "OPERATOR", "AUDIT_OBSERVER", "SOVEREIGN_PRIME"];
const tabs: Array<{ id: OpsTab; label: string; icon: LucideIcon }> = [
  { id: "dashboard", label: "Dashboard", icon: Activity },
  { id: "keys", label: "API Keys", icon: KeyRound },
  { id: "research", label: "Research", icon: Search },
  { id: "prs", label: "Draft PRs", icon: GitPullRequestDraft },
  { id: "revisions", label: "Revisions", icon: RotateCcw },
  { id: "ai", label: "AI Suggestions", icon: Terminal },
  { id: "governor", label: "Governor", icon: AlertTriangle },
  { id: "remediation", label: "Self-Healing", icon: ShieldCheck },
  { id: "ledger", label: "Ledger", icon: ClipboardCheck },
  { id: "audit", label: "Audit", icon: ClipboardCheck },
  { id: "agents", label: "Agents", icon: Terminal },
];

function asNumberOrNull(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function pct(used: number, limit?: number | null): number | null {
  if (!limit || limit <= 0) return null;
  return Math.min(999, Math.round((used / limit) * 100));
}

function compactDate(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function statusTone(status?: string): string {
  const clean = (status || "").toUpperCase();
  if (["PASSED", "GO", "COMPLETED", "APPROVED", "REVIEW_READY", "VERIFIED", "ACTIVE", "OK"].includes(clean)) {
    return "border-emerald-400/20 bg-emerald-400/10 text-emerald-200";
  }
  if (["WARNING", "NEEDS_HUMAN_CAUTION", "PENDING", "RUNNING", "MEDIUM"].includes(clean)) {
    return "border-amber-400/20 bg-amber-400/10 text-amber-200";
  }
  if (["FAILED", "BLOCKED", "REJECTED", "REVOKED", "LOW", "HIGH"].includes(clean)) {
    return "border-rose-400/20 bg-rose-400/10 text-rose-200";
  }
  return "border-white/10 bg-white/5 text-gray-300";
}

export default function BilgeAPIOpsConsole() {
  const t = useTranslations("opsConsole");
  const { data: identity } = useGetIdentity<any>();
  
  const isMutateAllowed = React.useMemo(() => {
    if (!identity) return false;
    const rolesList = identity.roles || (identity.role ? [identity.role] : []);
    const upperRoles = rolesList.map((r: string) => String(r).toUpperCase());
    return upperRoles.includes("ADMIN") || upperRoles.includes("SOVEREIGN_PRIME") || upperRoles.includes("OPERATOR") || upperRoles.includes("OPS_COMMANDER");
  }, [identity]);

  const [activeTab, setActiveTab] = React.useState<OpsTab>("dashboard");
  const [apiKey, setApiKey] = React.useState("");
  const [snapshot, setSnapshot] = React.useState<OpsSnapshot | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [actionLog, setActionLog] = React.useState<ActionLog[]>([]);
  const [createdKey, setCreatedKey] = React.useState<ApiKeyCreateResponse | null>(null);
  const [research, setResearch] = React.useState<ResearchRecord | null>(null);
  const [evidences, setEvidences] = React.useState<EvidenceRecord[]>([]);
  const [selectedProposalId, setSelectedProposalId] = React.useState("");
  const [auditReport, setAuditReport] = React.useState("");
  const [selectedDraftId, setSelectedDraftId] = React.useState("");
  const [feedback, setFeedback] = React.useState<ReviewerFeedbackRecord[]>([]);
  const [revisions, setRevisions] = React.useState<PatchRevisionRecord[]>([]);
  const [aiSuggestions, setAiSuggestions] = React.useState<AIPatchSuggestionRecord[]>([]);
  const [selectedAiSuggestionId, setSelectedAiSuggestionId] = React.useState("");
  const [selectedAiSuggestion, setSelectedAiSuggestion] = React.useState<AIPatchSuggestionRecord | null>(null);
  const [lastVerification, setLastVerification] = React.useState<PrVerificationRecord | null>(null);
  const [ledgerChainId, setLedgerChainId] = React.useState("");
  const [ledgerEntries, setLedgerEntries] = React.useState<ReviewLedgerEntryRecord[]>([]);
  const [ledgerVerification, setLedgerVerification] = React.useState<ReviewLedgerVerifyRecord | null>(null);
  const [ledgerExport, setLedgerExport] = React.useState<ReviewLedgerExportRecord | null>(null);
  const [selectedAgentPromoId, setSelectedAgentPromoId] = React.useState("");
  const [selectedAgentPromo, setSelectedAgentPromo] = React.useState<AgentPromotionRecord | null>(null);
  const [promoSimulationResult, setPromoSimulationResult] = React.useState<AgentPolicySimulationResponse | null>(null);
  const [simulatingPromo, setSimulatingPromo] = React.useState(false);

  const [keyForm, setKeyForm] = React.useState({
    role: "OPERATOR",
    description: "ops console key",
    tenant_id: "tenant-alpha",
    quota_daily: "",
    quota_monthly: "",
  });
  const [quotaForm, setQuotaForm] = React.useState({ key_id: "", quota_daily: "", quota_monthly: "" });
  const [researchForm, setResearchForm] = React.useState({
    incident_id: "incident-ops-console",
    query: "BilgeAPI release gate hardening follow-up",
  });
  const [feedbackForm, setFeedbackForm] = React.useState({ reviewer_id: "operator", comment: "" });
  const [revisionForm, setRevisionForm] = React.useState({
    feedback_id: "",
    revised_patch_code:
      "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n--- a/apps/bilgeapi/main.py\n+++ b/apps/bilgeapi/main.py\n@@\n+# revised patch placeholder\n",
  });
  const [aiForm, setAiForm] = React.useState({
    feedback_id: "",
    revision_id: "",
    instruction: "Reduce reviewer risk, keep patch scoped, and add tests.",
    reject_reason: "",
  });
  const [remediationForm, setRemediationForm] = React.useState({
    finding_id: "",
    runbook_id: "",
  });
  const [emergencyForm, setEmergencyForm] = React.useState({
    finding_id: "",
    action_type: "restart_stateless_service",
  });

  React.useEffect(() => {
    const saved = sessionStorage.getItem("bilgeapi_ops_api_key");
    if (saved) {
      setApiKey(saved);
    } else if (identity) {
      const roles = identity.roles || (identity.role ? [identity.role] : []);
      const upperRoles = roles.map((r: string) => r.toUpperCase());
      const isUserAdmin = upperRoles.includes("ADMIN") || upperRoles.includes("SOVEREIGN_PRIME");
      if (isUserAdmin) {
        setApiKey("dev-test-key-001");
      }
    }
  }, [identity]);

  const record = React.useCallback((label: string, status: "OK" | "ERR", detail: string) => {
    setActionLog((current) => [{ id: `${Date.now()}-${label}`, label, status, detail }, ...current].slice(0, 8));
  }, []);

  const refresh = React.useCallback(async () => {
    if (!apiKey.trim()) {
      record("auth", "ERR", "X-API-Key required");
      return;
    }
    setLoading(true);
    try {
      sessionStorage.setItem("bilgeapi_ops_api_key", apiKey.trim());
      const next = await loadBilgeApiOpsSnapshot(apiKey);
      sessionStorage.removeItem(AUTH_RECOVERY_MARKER);
      setSnapshot(next);
      if (!selectedProposalId && next.proposals[0]) setSelectedProposalId(next.proposals[0].id);
      if (!selectedDraftId && next.drafts[0]) setSelectedDraftId(next.drafts[0].id);
      record("snapshot", "OK", `${next.apiKeys.length} keys, ${next.proposals.length} proposals`);
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      record("snapshot", "ERR", msg);

      if (isBilgeApiAuthError(error)) {
        sessionStorage.removeItem("bilgeapi_ops_api_key");
        setApiKey("");
        setSnapshot(null);

        if (sessionStorage.getItem(AUTH_RECOVERY_MARKER) !== "1") {
          sessionStorage.setItem(AUTH_RECOVERY_MARKER, "1");
          window.location.reload();
          return;
        }

        console.warn("[Auth] BilgeAPI rejected the stored credential. Cleared the stale session key.");
      }
    } finally {
      setLoading(false);
    }
  }, [apiKey, record, selectedDraftId, selectedProposalId]);

  React.useEffect(() => {
    if (apiKey.trim() && !snapshot) {
      void refresh();
    }
  }, [apiKey, refresh, snapshot]);

  const apiKeys = snapshot?.apiKeys ?? [];
  const quotas = snapshot?.quotaUsage ?? [];
  const proposals = snapshot?.proposals ?? [];
  const drafts = snapshot?.drafts ?? [];
  const verifications = snapshot?.verifications ?? [];
  const snapshotAiSuggestions = snapshot?.aiSuggestions ?? [];
  const auditEvents = snapshot?.auditEvents ?? [];
  const ledgerRecent = snapshot?.ledgerRecent ?? [];
  const releaseLatest = snapshot?.releaseLatest ?? null;
  const remediationRunbooks = snapshot?.remediationRunbooks ?? [];
  const remediationAttempts = snapshot?.remediationAttempts ?? [];
  const systemFindings = snapshot?.systemFindings ?? [];
  const watchdogStatus = snapshot?.watchdogStatus ?? null;
  const managementGate = snapshot?.managementGate ?? null;
  const managementUnlocked = Boolean(managementGate?.unlocked);
  // listAgentPromotions are retrieved via snapshot load
  const agentPromotions = snapshot?.agentPromotions ?? [];
  const agentRuns = snapshot?.agentRuns ?? [];
  const agentCapabilities = snapshot?.agentCapabilities ?? [];
  const agentAuthRequired = (snapshot?.errors ?? []).some((error) =>
    error.startsWith("agent_") && error.toLowerCase().includes("platform login"),
  );
  const agentDataNotice = "Agent data requires platform session. BilgeAPI panels remain available.";


  const quotaRows = apiKeys.map((key) => ({
    key,
    usage: quotas.find((item) => item.key_id === key.id),
  }));

  const activeKeyCount = apiKeys.filter((key) => key.is_active).length;
  const revokedKeyCount = apiKeys.filter((key) => !key.is_active).length;
  const exceededCount = quotaRows.filter(({ usage }) => {
    if (!usage) return false;
    return usage.daily_remaining === 0 || usage.monthly_remaining === 0;
  }).length;
  const cautionCount = verifications.filter((item) => item.review_decision === "NEEDS_HUMAN_CAUTION").length;
  const pendingDraftCount = drafts.filter((item) => ["PENDING", "COMPLETED"].includes(item.status)).length;
  const managementGateTone = managementUnlocked
    ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100"
    : "border-amber-300/20 bg-amber-300/10 text-amber-100";

  async function runAction<T>(label: string, task: Promise<T>, after?: (value: T) => void | Promise<void>) {
    try {
      const result = await task;
      await after?.(result);
      record(label, "OK", "completed");
      await refresh();
      return result;
    } catch (error) {
      record(label, "ERR", error instanceof Error ? error.message : String(error));
      return null;
    }
  }

  async function loadDraftContext(draftId: string) {
    setSelectedDraftId(draftId);
    setLedgerChainId(`chain_${draftId}`);
    const [nextFeedback, nextRevisions, nextAiSuggestions] = await Promise.all([
      listReviewerFeedback(apiKey, draftId).catch(() => []),
      listPatchRevisions(apiKey, draftId).catch(() => []),
      listAiPatchSuggestions(apiKey, draftId).catch(() => []),
    ]);
    setFeedback(nextFeedback);
    setRevisions(nextRevisions);
    setAiSuggestions(nextAiSuggestions);
  }

  async function loadPromotionContext(promoId: string) {
    setSelectedAgentPromoId(promoId);
    setPromoSimulationResult(null);
    setSimulatingPromo(true);
    try {
      const promo = await getAgentPromotion(apiKey, promoId);
      setSelectedAgentPromo(promo);
      
      const sim = await simulateAgentPromotion(apiKey, promoId);
      setPromoSimulationResult(sim);
    } catch (error) {
      record("load_promotion", "ERR", error instanceof Error ? error.message : String(error));
    } finally {
      setSimulatingPromo(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#060a12] p-6 text-gray-200">
      <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-cyan-100">
            <ShieldCheck size={14} />
            {t("phase27")}
          </div>
          <h1 className="text-3xl font-black text-white">{t("title")}</h1>
          <p className="mt-2 max-w-3xl text-sm text-gray-400">
            {t("subtitle")}
          </p>
        </div>
        <div className="flex flex-col gap-3 rounded-lg border border-white/10 bg-black/30 p-3 md:flex-row md:items-center">
          <div className="relative min-w-72">
            <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              type="password"
              placeholder={t("apiKeyPlaceholder")}
              className="w-full rounded-lg border border-white/10 bg-black/40 py-2 pl-9 pr-3 text-sm text-white outline-none focus:border-cyan-300/30"
            />
          </div>
          <button
            onClick={() => void refresh()}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-xs font-black uppercase tracking-widest text-cyan-100 hover:bg-cyan-300/15"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            {t("refresh")}
          </button>
          <button
            onClick={() => {
              sessionStorage.removeItem("bilgeapi_ops_api_key");
              setApiKey("");
              setSnapshot(null);
            }}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-black uppercase tracking-widest text-gray-300 hover:bg-white/10"
          >
            <ShieldOff size={15} />
            {t("clear")}
          </button>
        </div>
      </div>

      <nav className="mb-6 flex flex-wrap gap-2">
        {tabs.map(({ id, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-black uppercase tracking-widest ${
              activeTab === id
                ? "border-cyan-300/30 bg-cyan-300/15 text-cyan-100"
                : "border-white/10 bg-white/5 text-gray-400 hover:text-white"
            }`}
          >
            <Icon size={15} />
            {t(`tabs.${id}`)}
          </button>
        ))}
      </nav>

      {!apiKey.trim() ? (
        <section className="rounded-lg border border-amber-300/20 bg-amber-300/10 p-6 text-amber-100">
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} />
            <span className="text-sm font-bold">{t("apiKeyRequired")}</span>
          </div>
        </section>
      ) : null}

      {snapshot?.errors.length ? (
        <section className="mb-6 rounded-lg border border-amber-300/20 bg-amber-300/10 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-amber-100">
            <AlertTriangle size={15} />
            {t("partialData")}
          </div>
          <div className="grid gap-2 text-xs text-amber-50 md:grid-cols-2">
            {snapshot.errors.slice(0, 6).map((error) => (
              <span key={error} className="rounded border border-amber-300/10 bg-black/20 px-2 py-1">
                {error}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {activeTab === "dashboard" ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Metric label={t("metrics.totalApiKeys")} value={apiKeys.length} icon={<KeyRound size={16} />} tone="cyan" />
            <Metric label={t("metrics.activeRevoked")} value={`${activeKeyCount} / ${revokedKeyCount}`} icon={<ShieldCheck size={16} />} tone="green" />
            <Metric label={t("metrics.quotaExceeded")} value={exceededCount} icon={<AlertTriangle size={16} />} tone={exceededCount ? "rose" : "gray"} />
            <Metric label={t("metrics.releaseGate")} value={releaseLatest ? `${releaseLatest.score.toFixed(0)} ${releaseLatest.status}` : "-"} icon={<ListChecks size={16} />} tone="cyan" />
            <Metric label={t("metrics.pendingResearch")} value={research?.status === "PENDING" ? 1 : 0} icon={<Search size={16} />} tone="amber" />
            <Metric label={t("metrics.prDraftReview")} value={pendingDraftCount} icon={<GitPullRequestDraft size={16} />} tone="violet" />
            <Metric label={t("metrics.needsCaution")} value={cautionCount} icon={<AlertTriangle size={16} />} tone={cautionCount ? "amber" : "gray"} />
            <Metric label={t("metrics.auditEvents")} value={auditEvents.length} icon={<ClipboardCheck size={16} />} tone="green" />
            <Metric label={t("metrics.ledgerEntries")} value={ledgerRecent.length} icon={<ClipboardCheck size={16} />} tone="violet" />
            <Metric label={t("metrics.agentCapabilities")} value={agentCapabilities.length} icon={<Terminal size={16} />} tone="cyan" />
            <Metric label={t("metrics.agentSandboxRuns")} value={agentRuns.length} icon={<Activity size={16} />} tone="green" />
            <Metric label={t("metrics.agentPromotions")} value={agentPromotions.length} icon={<ClipboardCheck size={16} />} tone="violet" />
          </div>

          <Panel title={t("panels.managementGate")} icon={managementUnlocked ? <ShieldCheck size={16} /> : <Lock size={16} />}>
            <div className="grid gap-4 xl:grid-cols-[1fr_auto] xl:items-center">
              <div className="space-y-2">
                <div className={`inline-flex rounded-lg border px-3 py-1 text-[10px] font-black uppercase tracking-widest ${managementGateTone}`}>
                  {managementUnlocked ? t("labels.unlocked") : t("labels.locked")}
                </div>
                <p className="text-sm text-gray-300">
                  BilgeAPI remediation, emergency recovery, and runbook mutation stay blocked until an admin unlocks this gate.
                </p>
                <p className="text-xs text-gray-500">
                  Forbidden actions remain blocked by backend policy even when this gate is unlocked.
                </p>
              </div>
              <button
                onClick={() =>
                  void runAction(
                    managementUnlocked ? "lock_management_gate" : "unlock_management_gate",
                    setManagementGate(
                      apiKey,
                      !managementUnlocked,
                      managementUnlocked ? "operator_dashboard_lock" : "operator_dashboard_unlock",
                    ),
                  )
                }
                disabled={!isMutateAllowed || loading}
                className={`inline-flex items-center justify-center gap-2 rounded-lg border px-4 py-2 text-xs font-black uppercase tracking-widest disabled:opacity-40 disabled:cursor-not-allowed ${
                  managementUnlocked
                    ? "border-amber-300/20 bg-amber-300/10 text-amber-100 hover:bg-amber-300/15"
                    : "border-emerald-300/20 bg-emerald-300/10 text-emerald-100 hover:bg-emerald-300/15"
                }`}
              >
                {managementUnlocked ? <Lock size={15} /> : <ShieldCheck size={15} />}
                {managementUnlocked ? t("labels.lockManagement") : t("labels.unlockManagement")}
              </button>
            </div>
          </Panel>

          <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
            <Panel title={t("panels.recentAuditTrail")} icon={<ClipboardCheck size={16} />}>
              <CompactTable
                headers={["Event", "Entity", "Actor", "Created"]}
                rows={auditEvents.slice(0, 10).map((event) => [
                  event.event_type,
                  `${event.entity_type}:${event.entity_id}`,
                  event.actor_id,
                  compactDate(event.created_at),
                ])}
                empty={t("labels.emptyAudit")}
              />
            </Panel>
            <Panel title={t("panels.releaseGateStatus")} icon={<ListChecks size={16} />}>
              <div className="space-y-4">
                <div className={`rounded-lg border p-4 ${statusTone(releaseLatest?.status)}`}>
                  <div className="text-xs font-black uppercase tracking-widest">{t("latest")}</div>
                  <div className="mt-2 text-3xl font-black">{releaseLatest ? releaseLatest.score.toFixed(2) : "-"}</div>
                  <div className="mt-1 text-xs">{releaseLatest ? `${releaseLatest.status} / ${releaseLatest.id}` : t("noReleaseCheck")}</div>
                </div>
                <button
                  onClick={() => void runAction("release_gate", runReleaseReadiness(apiKey))}
                  disabled={!isMutateAllowed || loading}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-xs font-black uppercase tracking-widest text-cyan-100 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Play size={15} />
                  {t("runGate")}
                </button>
              </div>
            </Panel>
          </section>
        </div>
      ) : null}

      {activeTab === "keys" ? (
        <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
          <Panel title={t("panels.createApiKey")} icon={<KeyRound size={16} />}>
            <FormGrid>
              <select value={keyForm.role} onChange={(event) => setKeyForm({ ...keyForm, role: event.target.value })} className={inputClass}>
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
              <input className={inputClass} value={keyForm.tenant_id} onChange={(event) => setKeyForm({ ...keyForm, tenant_id: event.target.value })} placeholder={t("labels.tenantId")} />
              <input className={inputClass} value={keyForm.description} onChange={(event) => setKeyForm({ ...keyForm, description: event.target.value })} placeholder={t("labels.description")} />
              <input className={inputClass} value={keyForm.quota_daily} onChange={(event) => setKeyForm({ ...keyForm, quota_daily: event.target.value })} placeholder={t("labels.dailyQuota")} />
              <input className={inputClass} value={keyForm.quota_monthly} onChange={(event) => setKeyForm({ ...keyForm, quota_monthly: event.target.value })} placeholder={t("labels.monthlyQuota")} />
              <button
                onClick={() =>
                  void runAction(
                    "create_key",
                    createBilgeApiKey(apiKey, {
                      role: keyForm.role,
                      description: keyForm.description || null,
                      tenant_id: keyForm.tenant_id || null,
                      quota_daily: asNumberOrNull(keyForm.quota_daily),
                      quota_monthly: asNumberOrNull(keyForm.quota_monthly),
                    }),
                    (value) => {
                      setCreatedKey(value);
                      record("create_key_redacted", "OK", JSON.stringify(redactPlaintextKey(value)));
                    },
                  )
                }
                className={primaryButtonClass}
              >
                <Save size={15} />
                {t("buttons.create")}
              </button>
            </FormGrid>
            {createdKey ? (
              <div className="mt-4 rounded-lg border border-emerald-300/20 bg-emerald-300/10 p-4">
                <div className="mb-2 text-xs font-black uppercase tracking-widest text-emerald-100">{t("labels.plaintextShownOnce")}</div>
                <code className="block break-all rounded bg-black/40 p-3 text-xs text-white">{createdKey.plaintext_key}</code>
              </div>
            ) : null}
          </Panel>

          <Panel title={t("panels.apiKeysAndQuotas")} icon={<Terminal size={16} />}>
            <div className="mb-4 grid gap-2 md:grid-cols-[1fr_0.7fr_0.7fr_auto]">
              <input className={inputClass} value={quotaForm.key_id} onChange={(event) => setQuotaForm({ ...quotaForm, key_id: event.target.value })} placeholder={t("labels.keyId")} />
              <input className={inputClass} value={quotaForm.quota_daily} onChange={(event) => setQuotaForm({ ...quotaForm, quota_daily: event.target.value })} placeholder={t("labels.dailyQuota")} />
              <input className={inputClass} value={quotaForm.quota_monthly} onChange={(event) => setQuotaForm({ ...quotaForm, quota_monthly: event.target.value })} placeholder={t("labels.monthlyQuota")} />
              <button
                onClick={() =>
                  void runAction(
                    "quota_update",
                    updateApiKeyQuota(apiKey, quotaForm.key_id, asNumberOrNull(quotaForm.quota_daily), asNumberOrNull(quotaForm.quota_monthly)),
                  )
                }
                className={secondaryButtonClass}
              >
                <Save size={15} />
                {t("buttons.set")}
              </button>
            </div>
            <div className="space-y-3">
              {quotaRows.map(({ key, usage }) => (
                <KeyRow
                  key={key.id}
                  apiKeyRecord={key}
                  usage={usage}
                  onPick={() => setQuotaForm({ key_id: key.id, quota_daily: key.quota_daily?.toString() ?? "", quota_monthly: key.quota_monthly?.toString() ?? "" })}
                  onRevoke={() => void runAction("revoke_key", revokeBilgeApiKey(apiKey, key.id, "revoked from ops console"))}
                />
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "research" ? (
        <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
          <Panel title={t("panels.researchActions")} icon={<Search size={16} />}>
            <FormGrid>
              <input className={inputClass} value={researchForm.incident_id} onChange={(event) => setResearchForm({ ...researchForm, incident_id: event.target.value })} placeholder="incident_id" />
              <input className={inputClass} value={researchForm.query} onChange={(event) => setResearchForm({ ...researchForm, query: event.target.value })} placeholder="research query" />
              <button
                className={primaryButtonClass}
                onClick={() =>
                  void runAction("research", createResearchRequest(apiKey, researchForm.incident_id, researchForm.query), async (value) => {
                    setResearch(value);
                    setEvidences(await listResearchEvidences(apiKey, value.id).catch(() => []));
                  })
                }
              >
                <Search size={15} />
                {t("buttons.start")}
              </button>
              <button
                className={secondaryButtonClass}
                disabled={!research}
                onClick={() => research && void runAction("proposal", createProposal(apiKey, research.id))}
              >
                <FileText size={15} />
                {t("buttons.proposal")}
              </button>
            </FormGrid>
            <div className="mt-4 rounded-lg border border-white/10 bg-black/20 p-4 text-xs text-gray-300">
              <div className="font-black uppercase tracking-widest text-white">{t("labels.latestResearch")}</div>
              <div className="mt-2">{research ? `${research.id} / ${research.status}` : t("labels.noSessionResearch")}</div>
            </div>
            <CompactTable
              headers={["Domain", "Trust", "Title"]}
              rows={evidences.map((evidence) => [evidence.source_domain, evidence.trust_score.toFixed(0), evidence.title || evidence.source_url])}
              empty={t("labels.emptyEvidence")}
            />
          </Panel>
          <Panel title={t("panels.proposals")} icon={<FileText size={16} />}>
            <div className="mb-3 flex flex-wrap gap-2">
              <input className={inputClass} value={selectedProposalId} onChange={(event) => setSelectedProposalId(event.target.value)} placeholder="proposal_id" />
              <button className={secondaryButtonClass} onClick={() => selectedProposalId && void runAction("approve_proposal", approveProposal(apiKey, selectedProposalId))}>
                <CheckCircle2 size={15} />
                {t("buttons.approve")}
              </button>
              <button className={secondaryButtonClass} onClick={() => selectedProposalId && void runAction("run_gate", runProposalGate(apiKey, selectedProposalId))}>
                <Play size={15} />
                {t("buttons.gate")}
              </button>
              <button className={secondaryButtonClass} onClick={() => selectedProposalId && void runAction("draft_pr", createDraftPr(apiKey, selectedProposalId))}>
                <GitPullRequestDraft size={15} />
                {t("buttons.draft")}
              </button>
              <button
                className={secondaryButtonClass}
                onClick={() =>
                  selectedProposalId &&
                  void runAction("audit_report", getProposalAuditReport(apiKey, selectedProposalId), (text) => setAuditReport(text))
                }
              >
                <Eye size={15} />
                {t("buttons.view")}
              </button>
            </div>
            <ProposalList proposals={proposals} onSelect={setSelectedProposalId} />
            {auditReport ? <pre className="mt-4 max-h-80 overflow-auto rounded-lg border border-white/10 bg-black/40 p-4 text-xs text-gray-300">{auditReport}</pre> : null}
          </Panel>
        </div>
      ) : null}

      {activeTab === "prs" ? (
        <Panel title="Draft PRs & Sandbox Verifications" icon={<GitPullRequestDraft size={16} />}>
          <DraftList
            drafts={drafts}
            verifications={verifications}
            onSelect={(id) => void loadDraftContext(id)}
            onVerify={(id) => void runAction("verify_draft", verifyDraftPr(apiKey, id), (value) => setLastVerification(value))}
          />
          {lastVerification ? <VerificationSummary verification={lastVerification} /> : null}
        </Panel>
      ) : null}

      {activeTab === "revisions" ? (
        <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
          <Panel title="Reviewer Feedback" icon={<ClipboardCheck size={16} />}>
            <FormGrid>
              <input className={inputClass} value={selectedDraftId} onChange={(event) => setSelectedDraftId(event.target.value)} placeholder="pr_draft_id" />
              <input className={inputClass} value={feedbackForm.reviewer_id} onChange={(event) => setFeedbackForm({ ...feedbackForm, reviewer_id: event.target.value })} placeholder="reviewer_id" />
              <textarea className={`${inputClass} min-h-24 md:col-span-2`} value={feedbackForm.comment} onChange={(event) => setFeedbackForm({ ...feedbackForm, comment: event.target.value })} placeholder="reviewer comment" />
              <button
                className={primaryButtonClass}
                onClick={() =>
                  selectedDraftId &&
                  void runAction(
                    "feedback",
                    createReviewerFeedback(apiKey, selectedDraftId, feedbackForm.reviewer_id, feedbackForm.comment),
                    async () => setFeedback(await listReviewerFeedback(apiKey, selectedDraftId).catch(() => [])),
                  )
                }
              >
                <Save size={15} />
                Add
              </button>
              <button className={secondaryButtonClass} onClick={() => selectedDraftId && void loadDraftContext(selectedDraftId)}>
                <RefreshCw size={15} />
                Load
              </button>
            </FormGrid>
            <CompactTable
              headers={["ID", "Reviewer", "Status", "Comment"]}
              rows={feedback.map((item) => [item.id, item.reviewer_id, item.status, item.comment])}
              empty="No feedback loaded"
            />
          </Panel>
          <Panel title="Patch Revisions" icon={<RotateCcw size={16} />}>
            <FormGrid>
              <input className={inputClass} value={revisionForm.feedback_id} onChange={(event) => setRevisionForm({ ...revisionForm, feedback_id: event.target.value })} placeholder="feedback_id optional" />
              <textarea className={`${inputClass} min-h-36 md:col-span-2`} value={revisionForm.revised_patch_code} onChange={(event) => setRevisionForm({ ...revisionForm, revised_patch_code: event.target.value })} placeholder="revised patch diff" />
              <button
                className={primaryButtonClass}
                onClick={() =>
                  selectedDraftId &&
                  void runAction(
                    "create_revision",
                    createPatchRevision(apiKey, selectedDraftId, revisionForm.revised_patch_code, revisionForm.feedback_id || null),
                    async () => setRevisions(await listPatchRevisions(apiKey, selectedDraftId).catch(() => [])),
                  )
                }
              >
                <Save size={15} />
                Create
              </button>
            </FormGrid>
            <RevisionList
              revisions={revisions}
              onVerify={(id) => void runAction("verify_revision", verifyPatchRevision(apiKey, id), (value) => setLastVerification(value))}
            />
          </Panel>
        </div>
      ) : null}

      {activeTab === "ai" ? (
        <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
          <Panel title="AI Patch Suggestions" icon={<Terminal size={16} />}>
            <FormGrid>
              <input className={inputClass} value={selectedDraftId} onChange={(event) => setSelectedDraftId(event.target.value)} placeholder="pr_draft_id" />
              <input className={inputClass} value={aiForm.feedback_id} onChange={(event) => setAiForm({ ...aiForm, feedback_id: event.target.value })} placeholder="feedback_id optional" />
              <input className={inputClass} value={aiForm.revision_id} onChange={(event) => setAiForm({ ...aiForm, revision_id: event.target.value })} placeholder="revision_id optional" />
              <textarea className={`${inputClass} min-h-24 md:col-span-2`} value={aiForm.instruction} onChange={(event) => setAiForm({ ...aiForm, instruction: event.target.value })} placeholder="human reviewer instruction" />
              <button
                className={primaryButtonClass}
                onClick={() =>
                  selectedDraftId &&
                  void runAction(
                    "create_ai_suggestion",
                    createAiPatchSuggestion(apiKey, selectedDraftId, aiForm.instruction, aiForm.feedback_id || null, aiForm.revision_id || null),
                    async (value) => {
                      setSelectedAiSuggestionId(value.id);
                      setSelectedAiSuggestion(value);
                      setAiSuggestions(await listAiPatchSuggestions(apiKey, selectedDraftId).catch(() => []));
                    },
                  )
                }
              >
                <Save size={15} />
                Generate
              </button>
              <button
                className={secondaryButtonClass}
                onClick={() => selectedDraftId && void runAction("load_ai_suggestions", listAiPatchSuggestions(apiKey, selectedDraftId), (value) => setAiSuggestions(value))}
              >
                <RefreshCw size={15} />
                Load
              </button>
            </FormGrid>
            <CompactTable
              headers={["ID", "Status", "Risk", "Provider", "Hash"]}
              rows={(aiSuggestions.length ? aiSuggestions : snapshotAiSuggestions).map((item) => [
                item.id,
                item.status,
                item.risk_level,
                item.provider,
                item.prompt_hash.slice(0, 12),
              ])}
              empty="No AI suggestion loaded"
            />
          </Panel>
          <Panel title="AI Suggestion Review Gate" icon={<ShieldCheck size={16} />}>
            <FormGrid>
              <input className={inputClass} value={selectedAiSuggestionId} onChange={(event) => setSelectedAiSuggestionId(event.target.value)} placeholder="ai_suggestion_id" />
              <button
                className={secondaryButtonClass}
                onClick={() =>
                  selectedAiSuggestionId &&
                  void runAction("get_ai_suggestion", getAiPatchSuggestion(apiKey, selectedAiSuggestionId), (value) => setSelectedAiSuggestion(value))
                }
              >
                <Eye size={15} />
                Load
              </button>
              <button
                className={primaryButtonClass}
                onClick={() =>
                  selectedAiSuggestionId &&
                  void runAction("verify_ai_suggestion", verifyAiPatchSuggestion(apiKey, selectedAiSuggestionId), (value) => setLastVerification(value))
                }
              >
                <Play size={15} />
                Verify
              </button>
              <button
                className={secondaryButtonClass}
                onClick={() =>
                  selectedAiSuggestionId &&
                  void runAction("accept_ai_suggestion", acceptAiPatchSuggestionForReview(apiKey, selectedAiSuggestionId), async () => {
                    if (selectedDraftId) setAiSuggestions(await listAiPatchSuggestions(apiKey, selectedDraftId).catch(() => []));
                  })
                }
              >
                <CheckCircle2 size={15} />
                Accept
              </button>
              <input className={inputClass} value={aiForm.reject_reason} onChange={(event) => setAiForm({ ...aiForm, reject_reason: event.target.value })} placeholder="reject reason optional" />
              <button
                className={secondaryButtonClass}
                onClick={() =>
                  selectedAiSuggestionId &&
                  void runAction("reject_ai_suggestion", rejectAiPatchSuggestion(apiKey, selectedAiSuggestionId, aiForm.reject_reason || null), async () => {
                    if (selectedDraftId) setAiSuggestions(await listAiPatchSuggestions(apiKey, selectedDraftId).catch(() => []));
                  })
                }
              >
                <ShieldOff size={15} />
                Reject
              </button>
            </FormGrid>
            {selectedAiSuggestion ? (
              <div className="mt-4 space-y-3">
                <div className="flex flex-wrap gap-2">
                  <span className={`rounded-full border px-2 py-1 text-[10px] font-black uppercase tracking-widest ${statusTone(selectedAiSuggestion.status)}`}>{selectedAiSuggestion.status}</span>
                  <span className={`rounded-full border px-2 py-1 text-[10px] font-black uppercase tracking-widest ${statusTone(selectedAiSuggestion.risk_level)}`}>{selectedAiSuggestion.risk_level}</span>
                </div>
                <pre className="max-h-[420px] overflow-auto rounded-lg border border-white/10 bg-black/40 p-4 text-xs text-gray-300">
                  {selectedAiSuggestion.suggested_patch_code}
                </pre>
              </div>
            ) : (
              <EmptyState text="Load or generate an AI suggestion" />
            )}
          </Panel>
        </div>
      ) : null}

      {activeTab === "ledger" ? (
        <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
          <Panel title="Immutable Review Ledger" icon={<ClipboardCheck size={16} />}>
            <FormGrid>
              <input
                className={inputClass}
                value={ledgerChainId}
                onChange={(event) => setLedgerChainId(event.target.value)}
                placeholder="chain_id, e.g. chain_prd_123"
              />
              <button
                className={secondaryButtonClass}
                onClick={() =>
                  ledgerChainId &&
                  void runAction("ledger_chain", getReviewLedgerChain(apiKey, ledgerChainId), (value) => {
                    setLedgerEntries(value.entries);
                    setLedgerVerification(null);
                    setLedgerExport(null);
                  })
                }
              >
                <Eye size={15} />
                Load
              </button>
              <button
                className={primaryButtonClass}
                onClick={() =>
                  ledgerChainId &&
                  void runAction("ledger_verify", verifyReviewLedgerChain(apiKey, ledgerChainId), (value) => setLedgerVerification(value))
                }
              >
                <Play size={15} />
                Verify
              </button>
              <button
                className={secondaryButtonClass}
                onClick={() =>
                  ledgerChainId &&
                  void runAction("ledger_export", exportReviewLedgerChain(apiKey, ledgerChainId), (value) => setLedgerExport(value))
                }
              >
                <FileText size={15} />
                Export
              </button>
            </FormGrid>
            {ledgerVerification ? (
              <div className={`mt-4 rounded-lg border p-4 ${ledgerVerification.valid ? "border-emerald-300/20 bg-emerald-300/10" : "border-rose-300/20 bg-rose-300/10"}`}>
                <div className="text-xs font-black uppercase tracking-widest text-white">
                  {ledgerVerification.valid ? t("labels.chainVerified") : t("labels.chainBroken")}
                </div>
                <div className="mt-2 text-xs text-gray-300">
                  {ledgerVerification.entry_count} entries / head {ledgerVerification.head_hash || "-"}
                </div>
              </div>
            ) : null}
            <LedgerEntryList entries={ledgerEntries.length ? ledgerEntries : ledgerRecent} />
          </Panel>
          <Panel title="Ledger Export Preview" icon={<FileText size={16} />}>
            {ledgerExport ? (
              <pre className="max-h-[560px] overflow-auto rounded-lg border border-white/10 bg-black/40 p-4 text-xs text-gray-300">
                {ledgerExport.content}
              </pre>
            ) : (
              <CompactTable
                headers={["Chain", "Seq", "Event", "Hash"]}
                rows={ledgerRecent.map((entry) => [
                  entry.chain_id,
                  entry.sequence_no,
                  entry.event_type,
                  entry.event_hash.slice(0, 12),
                ])}
                empty="No ledger entry loaded"
              />
            )}
          </Panel>
        </div>
      ) : null}

      {activeTab === "governor" ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <Metric
              label={t("labels.watchdogStatusLabel")}
              value={watchdogStatus?.enabled ? `${t("labels.enabled")} / ACTIVE` : t("labels.disabled")}
              icon={<ShieldCheck size={20} />}
              tone={watchdogStatus?.enabled ? "green" : "rose"}
            />
            <Metric
              label="Open Findings"
              value={watchdogStatus?.open_findings ?? 0}
              icon={<AlertTriangle size={20} />}
              tone={(watchdogStatus?.open_findings ?? 0) > 0 ? "amber" : "gray"}
            />
            <Metric
              label="High / Critical Findings"
              value={watchdogStatus?.high_or_critical_findings ?? 0}
              icon={<AlertTriangle size={20} />}
              tone={(watchdogStatus?.high_or_critical_findings ?? 0) > 0 ? "rose" : "gray"}
            />
          </div>

          <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
            <Panel title="Governor Findings" icon={<AlertTriangle size={16} />}>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs text-gray-400">
                  Active threats, vulnerability findings, and anomalies detected by Acting Governor.
                </p>
                <button
                  onClick={() => void runAction("run_watchdog_scan", runWatchdogScan(apiKey))}
                  disabled={!isMutateAllowed || loading}
                  className={primaryButtonClass}
                >
                  <Play size={14} />
                  {t("labels.runScanNow")}
                </button>
              </div>

              <div className="mt-4 overflow-x-auto rounded-lg border border-white/10">
                <table className="w-full min-w-[640px] border-collapse text-left text-xs">
                  <thead className="bg-white/5 text-[10px] uppercase tracking-widest text-gray-500">
                    <tr>
                      <th className="px-3 py-2 font-black">{t("table.findingId")}</th>
                      <th className="px-3 py-2 font-black">{t("table.source")}</th>
                      <th className="px-3 py-2 font-black">{t("table.title")}</th>
                      <th className="px-3 py-2 font-black">{t("table.severity")}</th>
                      <th className="px-3 py-2 font-black">{t("table.riskScore")}</th>
                      <th className="px-3 py-2 font-black">{t("table.status")}</th>
                      <th className="px-3 py-2 font-black">{t("table.actions")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {systemFindings.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-3 py-4 text-center text-gray-500 font-bold uppercase tracking-widest">
                          {t("labels.noFindings")}
                        </td>
                      </tr>
                    ) : (
                      systemFindings.map((finding) => (
                        <tr key={finding.id} className="border-t border-white/5">
                          <td className="px-3 py-2 font-mono text-cyan-200">{finding.id}</td>
                          <td className="px-3 py-2">
                            <span className="text-gray-400">{finding.source_type}</span>
                            <span className="ml-1 text-[10px] font-mono text-gray-500">({finding.source_id.slice(0, 12)})</span>
                          </td>
                          <td className="px-3 py-2">
                            <div className="font-bold text-gray-200">{finding.title}</div>
                            <div className="text-[10px] text-gray-500 truncate max-w-xs">{finding.description}</div>
                          </td>
                          <td className="px-3 py-2">
                            <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(finding.severity)}`}>
                              {finding.severity}
                            </span>
                          </td>
                          <td className="px-3 py-2 font-mono text-white">{finding.risk_score}</td>
                          <td className="px-3 py-2">
                            <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(finding.status)}`}>
                              {finding.status}
                            </span>
                          </td>
                          <td className="px-3 py-2">
                            <div className="flex gap-2">
                              {finding.status === "OPEN" && (
                                <>
                                  <button
                                    onClick={() => void runAction(`ack_finding_${finding.id}`, acknowledgeFinding(apiKey, finding.id))}
                                    className="rounded border border-emerald-300/20 bg-emerald-300/10 px-2 py-1 text-[10px] font-black uppercase tracking-widest text-emerald-100"
                                  >
                                    {t("buttons.acknowledge")}
                                  </button>
                                  <button
                                    onClick={() => void runAction(`dismiss_finding_${finding.id}`, dismissFinding(apiKey, finding.id))}
                                    className="rounded border border-rose-300/20 bg-rose-300/10 px-2 py-1 text-[10px] font-black uppercase tracking-widest text-rose-100"
                                  >
                                    {t("buttons.dismiss")}
                                  </button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Panel>

            <div className="space-y-6">
              {/* Test Assertion Check: Forbidden Governor Actions */}
              <Panel title={t("panels.forbiddenActions")} icon={<Lock size={16} />}>
                <p className="mb-4 text-xs text-gray-400">
                  {t("labels.forbiddenDesc")}
                </p>
                <div className="space-y-2 text-xs">
                  {[
                    { action: "auto_merge" },
                    { action: "auto_deploy" },
                    { action: "auto_revoke_key" },
                    { action: "production_migration_apply" },
                    { action: "branch_push" },
                    { action: "production_config_change" },
                  ].map(({ action }) => (
                    <div key={action} className="flex items-center justify-between rounded border border-rose-400/10 bg-rose-400/5 p-2.5">
                      <div>
                        <span className="font-mono font-bold text-rose-300">{action}</span>
                        <p className="mt-0.5 text-[10px] text-gray-500">{t(`labels.forbiddenActionsList.${action}`)}</p>
                      </div>
                      <span className="rounded border border-rose-300/20 bg-rose-300/10 px-2 py-0.5 text-[9px] font-black uppercase tracking-widest text-rose-100">
                        {t("labels.forbidden")}
                      </span>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title={t("panels.governanceAudit")} icon={<ShieldCheck size={16} />}>
                <div className="space-y-4 text-xs text-gray-400">
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span>{t("labels.watchdogEnabled")}</span>
                    <span className="font-bold text-emerald-400">{watchdogStatus?.enabled ? t("labels.yes") : t("labels.no")}</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span>{t("labels.riskThreshold")}</span>
                    <span className="font-mono font-bold text-white">{watchdogStatus?.risk_threshold ?? 70}</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span>{t("labels.autoFindingCreation")}</span>
                    <span className="font-bold text-emerald-400">{watchdogStatus?.auto_finding ? t("labels.enabled") : t("labels.disabled")}</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span>{t("labels.humanGateRequired")}</span>
                    <span className="font-bold text-amber-400">{watchdogStatus?.human_gate_required ? t("labels.yes") : t("labels.no")}</span>
                  </div>
                  <p className="text-[10px] text-gray-500">
                    {t("labels.watchdogFooter")}
                  </p>
                </div>
              </Panel>
            </div>
          </div>
        </div>
      ) : null}

      {activeTab === "remediation" ? (
        <div className="space-y-6">
          {!managementUnlocked ? (
            <section className="rounded-lg border border-amber-300/20 bg-amber-300/10 p-4 text-amber-100">
              <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest">
                <Lock size={15} />
                {t("labels.managementActionsLocked")}
              </div>
              <p className="mt-2 text-xs text-amber-50">
                {t("labels.managementGateWarning")}
              </p>
            </section>
          ) : null}

          <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
            <Panel title="Trigger Remediation" icon={<ShieldCheck size={16} />}>
              <FormGrid>
                <input
                  className={inputClass}
                  value={remediationForm.finding_id}
                  onChange={(event) => setRemediationForm({ ...remediationForm, finding_id: event.target.value })}
                  placeholder="finding_id (e.g. fnd_a1b2c3d4)"
                />
                <select
                  className={inputClass}
                  value={remediationForm.runbook_id}
                  onChange={(event) => setRemediationForm({ ...remediationForm, runbook_id: event.target.value })}
                >
                  <option value="">Select Runbook</option>
                  {remediationRunbooks.map((rb) => (
                    <option key={rb.id} value={rb.id}>
                      {rb.name} ({rb.action_type})
                    </option>
                  ))}
                </select>
                <button
                  disabled={!managementUnlocked}
                  className={`${primaryButtonClass} disabled:cursor-not-allowed disabled:opacity-40`}
                  onClick={() =>
                    managementUnlocked &&
                    remediationForm.finding_id &&
                    remediationForm.runbook_id &&
                    void runAction(
                      "trigger_remediation",
                      triggerRemediation(apiKey, remediationForm.finding_id, remediationForm.runbook_id)
                    )
                  }
                >
                  <Play size={15} />
                  Execute Remediation
                </button>
              </FormGrid>
            </Panel>

            <Panel title="Emergency Recovery (Liveness Only)" icon={<AlertTriangle size={16} />}>
              <FormGrid>
                <input
                  className={inputClass}
                  value={emergencyForm.finding_id}
                  onChange={(event) => setEmergencyForm({ ...emergencyForm, finding_id: event.target.value })}
                  placeholder="finding_id (CRITICAL only)"
                />
                <select
                  className={inputClass}
                  value={emergencyForm.action_type}
                  onChange={(event) => setEmergencyForm({ ...emergencyForm, action_type: event.target.value })}
                >
                  <option value="restart_stateless_service">Restart Stateless API Service</option>
                  <option value="restart_worker">Restart Worker Service</option>
                </select>
                <button
                  disabled={!managementUnlocked || !isMutateAllowed || loading}
                  className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-300/20 bg-rose-300/10 px-4 py-2 text-xs font-black uppercase tracking-widest text-rose-100 hover:bg-rose-300/15 disabled:cursor-not-allowed disabled:opacity-40"
                  onClick={() =>
                    managementUnlocked &&
                    isMutateAllowed &&
                    emergencyForm.finding_id &&
                    void runAction(
                      "emergency_recovery",
                      runEmergencyRecovery(apiKey, emergencyForm.finding_id, emergencyForm.action_type)
                    )
                  }
                >
                  <Play size={15} />
                  Run Emergency Recovery
                </button>
              </FormGrid>
            </Panel>
          </div>

          <Panel title="Remediation Runbooks" icon={<ListChecks size={16} />}>
            <div className="mt-4 overflow-x-auto rounded-lg border border-white/10">
              <table className="w-full min-w-[640px] border-collapse text-left text-xs">
                <thead className="bg-white/5 text-[10px] uppercase tracking-widest text-gray-500">
                  <tr>
                    <th className="px-3 py-2 font-black">Name</th>
                    <th className="px-3 py-2 font-black">Action Type</th>
                    <th className="px-3 py-2 font-black">Severity</th>
                    <th className="px-3 py-2 font-black">Mode</th>
                    <th className="px-3 py-2 font-black">Human Gate</th>
                    <th className="px-3 py-2 font-black">Status</th>
                    <th className="px-3 py-2 font-black">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {remediationRunbooks.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-3 py-4 text-center text-gray-500 font-bold uppercase tracking-widest">
                        No runbook loaded
                      </td>
                    </tr>
                  ) : (
                    remediationRunbooks.map((rb) => (
                      <tr key={rb.id} className="border-t border-white/5">
                        <td className="px-3 py-2 text-gray-200 font-bold">{rb.name}</td>
                        <td className="px-3 py-2 font-mono text-cyan-200">{rb.action_type}</td>
                        <td className="px-3 py-2">{rb.severity_allowed}</td>
                        <td className="px-3 py-2 text-gray-400">{rb.execution_mode}</td>
                        <td className="px-3 py-2">
                          <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${rb.requires_human_gate ? "border-amber-300/20 bg-amber-300/10 text-amber-100" : "border-emerald-300/20 bg-emerald-300/10 text-emerald-100"}`}>
                            {rb.requires_human_gate ? "REQUIRED" : "NO"}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${rb.enabled ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100" : "border-rose-300/20 bg-rose-300/10 text-rose-100"}`}>
                            {rb.enabled ? "enabled" : "disabled"}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          {rb.enabled ? (
                            <button
                              disabled={!managementUnlocked}
                              onClick={() => managementUnlocked && void runAction(`disable_runbook_${rb.id}`, disableRemediationRunbook(apiKey, rb.id))}
                              className="rounded border border-rose-300/20 bg-rose-300/10 px-2 py-1 text-[10px] font-black uppercase tracking-widest text-rose-100 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                              Disable
                            </button>
                          ) : (
                            <button
                              disabled={!managementUnlocked}
                              onClick={() => managementUnlocked && void runAction(`enable_runbook_${rb.id}`, enableRemediationRunbook(apiKey, rb.id))}
                              className="rounded border border-emerald-300/20 bg-emerald-300/10 px-2 py-1 text-[10px] font-black uppercase tracking-widest text-emerald-100 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                              Enable
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel title="Remediation Attempts History" icon={<ClipboardCheck size={16} />}>
            <div className="mt-4 overflow-x-auto rounded-lg border border-white/10">
              <table className="w-full min-w-[640px] border-collapse text-left text-xs">
                <thead className="bg-white/5 text-[10px] uppercase tracking-widest text-gray-500">
                  <tr>
                    <th className="px-3 py-2 font-black">Attempt ID</th>
                    <th className="px-3 py-2 font-black">Finding ID</th>
                    <th className="px-3 py-2 font-black">Action</th>
                    <th className="px-3 py-2 font-black">Status</th>
                    <th className="px-3 py-2 font-black">No</th>
                    <th className="px-3 py-2 font-black">Output / Error</th>
                    <th className="px-3 py-2 font-black">Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {remediationAttempts.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-3 py-4 text-center text-gray-500 font-bold uppercase tracking-widest">
                        No attempt registered
                      </td>
                    </tr>
                  ) : (
                    remediationAttempts.map((att) => (
                      <tr key={att.id} className="border-t border-white/5">
                        <td className="px-3 py-2 font-mono text-cyan-200">{att.id}</td>
                        <td className="px-3 py-2 font-mono">{att.finding_id}</td>
                        <td className="px-3 py-2 text-gray-300">{att.action_type}</td>
                        <td className="px-3 py-2">
                          <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(att.status)}`}>
                            {att.status}
                          </span>
                        </td>
                        <td className="px-3 py-2">{att.attempt_no}</td>
                        <td className="px-3 py-2 max-w-xs truncate text-gray-400" title={att.error_message || att.output_summary || ""}>
                          {att.error_message || att.output_summary || "-"}
                        </td>
                        <td className="px-3 py-2 text-gray-500">{compactDate(att.completed_at || att.created_at)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "audit" ? (
        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <Panel title="Audit Trail" icon={<ClipboardCheck size={16} />}>
            <CompactTable
              headers={["Event", "Actor", "Entity", "Created"]}
              rows={auditEvents.map((event) => [event.event_type, event.actor_id, `${event.entity_type}:${event.entity_id}`, compactDate(event.created_at)])}
              empty="No audit event loaded"
            />
          </Panel>
          <Panel title="Operator Action Log" icon={<Terminal size={16} />}>
            <div className="space-y-2">
              {actionLog.length === 0 ? <EmptyState text="No local action yet" /> : null}
              {actionLog.map((item) => (
                <div key={item.id} className="flex flex-col gap-1 border-b border-white/5 pb-2 last:border-0 last:pb-0">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white text-xs">{item.label}</span>
                    <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium border ${
                      item.status === "OK" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300" : "border-rose-500/20 bg-rose-500/10 text-rose-300"
                    }`}>
                      {item.status}
                    </span>
                  </div>
                  {item.detail && <p className="text-[11px] text-gray-400 break-all">{item.detail}</p>}
                </div>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === "agents" ? (
        <div className="space-y-6">
          {agentAuthRequired ? (
            <section className="rounded-lg border border-amber-300/20 bg-amber-300/10 p-4">
              <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-amber-100">
                <AlertTriangle size={15} />
                <span>{agentDataNotice}</span>
              </div>
            </section>
          ) : null}
          <div className="grid gap-4 xl:grid-cols-[1fr_1.4fr]">
            
            {/* Left side: Capabilities list and Runs list */}
            <div className="space-y-6">
              
              <Panel title="Agent Capabilities" icon={<Terminal size={16} />}>
                <div className="space-y-3">
                  {agentCapabilities.length === 0 ? (
                    <EmptyState text={agentAuthRequired ? agentDataNotice : "No agent capability loaded"} />
                  ) : (
                    agentCapabilities.map((cap) => (
                      <div key={cap.agent_key} className="rounded-lg border border-white/10 bg-black/20 p-4">
                        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-mono text-sm font-black text-cyan-200">{cap.agent_key}</span>
                              <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${cap.enabled ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100" : "border-rose-300/20 bg-rose-300/10 text-rose-100"}`}>
                                {cap.enabled ? "enabled" : "disabled"}
                              </span>
                              <span className="rounded border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-black uppercase tracking-widest text-gray-300">
                                {cap.sandbox_mode}
                              </span>
                            </div>
                            <div className="mt-2 text-xs font-bold text-gray-200">{cap.agent_name}</div>
                            <div className="mt-1 text-[10px] text-gray-500">{cap.description}</div>
                          </div>
                          <div className="flex gap-2">
                            {cap.enabled ? (
                              <button
                                onClick={() => void runAction(`disable_agent_${cap.agent_key}`, disableAgent(apiKey, cap.agent_key))}
                                className="rounded border border-rose-300/20 bg-rose-300/10 px-3 py-2 text-xs font-black uppercase tracking-widest text-rose-100 hover:bg-rose-300/15"
                              >
                                Disable
                              </button>
                            ) : (
                              <button
                                onClick={() => void runAction(`enable_agent_${cap.agent_key}`, enableAgent(apiKey, cap.agent_key))}
                                className="rounded border border-emerald-300/20 bg-emerald-300/10 px-3 py-2 text-xs font-black uppercase tracking-widest text-emerald-100 hover:bg-emerald-300/15"
                              >
                                Enable
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </Panel>

              <Panel title="Recent Sandbox Runs" icon={<Activity size={16} />}>
                <div className="space-y-3">
                  {agentRuns.length === 0 ? (
                    <EmptyState text={agentAuthRequired ? agentDataNotice : "No agent run loaded"} />
                  ) : (
                    agentRuns.slice(0, 15).map((run) => (
                      <div key={run.run_id} className="rounded-lg border border-white/10 bg-black/20 p-4 text-xs">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-mono font-black text-white">{run.run_id}</span>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(run.status)}`}>
                              {run.status}
                            </span>
                            {["FAILED", "BLOCKED"].includes(String(run.status).toUpperCase()) ? (
                              <button
                                onClick={() => void runAction(`retry_agent_run_${run.run_id}`, retryAgentRun(apiKey, run.run_id))}
                                className="inline-flex items-center gap-1 rounded border border-amber-300/20 bg-amber-300/10 px-2 py-1 text-[10px] font-black uppercase tracking-widest text-amber-100 hover:bg-amber-300/15"
                              >
                                <RefreshCw size={12} />
                                Retry Failed
                              </button>
                            ) : null}
                          </div>
                        </div>
                        <div className="mt-2 grid grid-cols-2 gap-2 text-gray-400">
                          <div>Agent: <span className="text-gray-200">{run.agent_key}</span></div>
                          <div>Cost: <span className="text-gray-200">${run.cost.toFixed(4)}</span></div>
                          <div>Mode: <span className="text-gray-200">{run.sandbox_mode}</span></div>
                          <div>Net: <span className="text-gray-200">{run.network_policy}</span></div>
                        </div>
                        {run.ledger_chain_id && (
                          <div className="mt-2 text-[10px] text-gray-500 font-mono">Ledger Chain: {run.ledger_chain_id}</div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </Panel>

            </div>

            {/* Right side: Promotion Requests & Detail Panel */}
            <div className="space-y-6">
              
              <Panel title="Promotion Requests" icon={<ClipboardCheck size={16} />}>
                <div className="space-y-3">
                  {agentPromotions.length === 0 ? (
                    <EmptyState text={agentAuthRequired ? agentDataNotice : "No promotion request registered"} />
                  ) : (
                    agentPromotions.map((promo) => (
                      <button
                        key={promo.promotion_id}
                        onClick={() => void loadPromotionContext(promo.promotion_id)}
                        className={`w-full rounded-lg border p-4 text-left hover:border-cyan-300/20 ${selectedAgentPromoId === promo.promotion_id ? "border-cyan-300/30 bg-cyan-300/5" : "border-white/10 bg-black/20"}`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-mono text-sm font-black text-white">{promo.promotion_id}</span>
                          <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(promo.status)}`}>
                            {promo.status}
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-gray-400">Target Path: <span className="font-mono text-gray-200">{promo.target_repo_path}</span></div>
                        <div className="mt-1 text-xs text-gray-400">Run: <span className="font-mono text-gray-300">{promo.run_id}</span></div>
                      </button>
                    ))
                  )}
                </div>
              </Panel>

              {selectedAgentPromo && (
                <Panel title="Promotion Detail & Review Gate" icon={<ShieldCheck size={16} />}>
                  <div className="space-y-4 text-xs">
                    
                    <div className="grid grid-cols-2 gap-4 rounded-lg border border-white/5 bg-black/30 p-3">
                      <div>
                        <div className="text-[10px] font-black uppercase tracking-widest text-gray-500">Status</div>
                        <span className={`inline-block mt-1 rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(selectedAgentPromo.status)}`}>
                          {selectedAgentPromo.status}
                        </span>
                      </div>
                      <div>
                        <div className="text-[10px] font-black uppercase tracking-widest text-gray-500">Verification Score</div>
                        <span className={`inline-block mt-1 font-mono font-bold ${selectedAgentPromo.verification_score >= 1.0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {selectedAgentPromo.verification_score >= 1.0 ? "1.0 (PASSED)" : `${selectedAgentPromo.verification_score} (FAILED)`}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2 rounded border border-white/5 bg-black/10 p-3 font-mono">
                      <div><span className="text-gray-500">Target Path : </span><span className="text-cyan-200">{selectedAgentPromo.target_repo_path}</span></div>
                      <div><span className="text-gray-500">Artifact Type: </span><span className="text-white">{selectedAgentPromo.artifact_type}</span></div>
                      <div><span className="text-gray-500">Artifact Hash: </span><span className="text-gray-400">{selectedAgentPromo.artifact_hash.slice(0, 16)}...</span></div>
                      <div><span className="text-gray-500">Manifest Hash : </span><span className="text-gray-400">{selectedAgentPromo.manifest_hash ? `${selectedAgentPromo.manifest_hash.slice(0, 16)}...` : "-"}</span></div>
                      <div><span className="text-gray-500">Verified Hash : </span><span className="text-gray-400">{selectedAgentPromo.verified_artifact_hash ? `${selectedAgentPromo.verified_artifact_hash.slice(0, 16)}...` : "-"}</span></div>
                      <div><span className="text-gray-500">Approved Hash : </span><span className="text-gray-400">{selectedAgentPromo.approved_artifact_hash ? `${selectedAgentPromo.approved_artifact_hash.slice(0, 16)}...` : "-"}</span></div>
                      <div><span className="text-gray-500">Promoted Hash : </span><span className="text-gray-400">{selectedAgentPromo.promoted_artifact_hash ? `${selectedAgentPromo.promoted_artifact_hash.slice(0, 16)}...` : "-"}</span></div>
                      <div><span className="text-gray-500">Ledger Hash   : </span><span className="text-gray-400">{selectedAgentPromo.ledger_event_hash ? `${selectedAgentPromo.ledger_event_hash.slice(0, 16)}...` : "-"}</span></div>
                    </div>

                    {/* Policy Simulation / Governance Preview (32E) */}
                    <div>
                      <div className="mb-2 text-[10px] font-black uppercase tracking-widest text-gray-400">Governance dry-run simulation & risk preview</div>
                      {simulatingPromo ? (
                        <div className="rounded border border-white/5 bg-black/20 p-4 text-center text-gray-500">Simulating policy rules...</div>
                      ) : promoSimulationResult ? (
                        <div className={`rounded-lg border p-4 space-y-3 ${
                          promoSimulationResult.decision === "BLOCK"
                            ? "border-rose-400/20 bg-rose-400/10"
                            : promoSimulationResult.decision === "HUMAN_GATE_REQUIRED"
                            ? "border-amber-400/20 bg-amber-400/10"
                            : "border-emerald-400/20 bg-emerald-400/10"
                        }`}>
                          <div className="flex items-center justify-between">
                            <span className="font-bold uppercase tracking-wider">Decision: {promoSimulationResult.decision}</span>
                            <span className={`rounded border px-2 py-0.5 text-[9px] font-black uppercase tracking-widest ${
                              promoSimulationResult.risk_level === "CRITICAL"
                                ? "border-rose-400/20 bg-rose-400/10 text-rose-200"
                                : promoSimulationResult.risk_level === "HIGH"
                                ? "border-amber-400/20 bg-amber-400/10 text-amber-200"
                                : "border-emerald-400/20 bg-emerald-400/10 text-emerald-200"
                            }`}>
                              Risk: {promoSimulationResult.risk_level} ({promoSimulationResult.risk_score.toFixed(1)})
                            </span>
                          </div>
                          {promoSimulationResult.reasons.length > 0 && (
                            <div className="space-y-1">
                              <div className="text-[10px] font-black uppercase tracking-widest opacity-75">Analysis / Reasons:</div>
                              <ul className="list-disc list-inside space-y-1 text-gray-300">
                                {promoSimulationResult.reasons.map((r, i) => <li key={i}>{r}</li>)}
                              </ul>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="rounded border border-white/5 bg-black/20 p-4 text-center text-gray-500">No simulation preview loaded</div>
                      )}
                    </div>

                    {/* Verification details */}
                    {selectedAgentPromo.verification_details && Object.keys(selectedAgentPromo.verification_details).length > 0 && (
                      <div className="space-y-1">
                        <div className="text-[10px] font-black uppercase tracking-widest text-gray-400">Verifier Reports:</div>
                        <pre className="max-h-40 overflow-auto rounded border border-white/5 bg-black/40 p-3 font-mono text-xs text-rose-300">
                          {JSON.stringify(selectedAgentPromo.verification_details, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* UI Actions (Approve, Reject, Execute) */}
                    <div className="mt-4 flex flex-wrap gap-2 pt-2 border-t border-white/5">
                      
                      {selectedAgentPromo.status === "PENDING_APPROVAL" && (
                        <>
                          <button
                            onClick={() => void runAction(
                              "approve_promotion",
                              approveAgentPromotion(apiKey, selectedAgentPromo.promotion_id),
                              () => loadPromotionContext(selectedAgentPromo.promotion_id)
                            )}
                            className="inline-flex items-center gap-2 rounded-lg border border-emerald-300/20 bg-emerald-300/10 px-3 py-2 text-xs font-black uppercase tracking-widest text-emerald-100 hover:bg-emerald-300/15"
                          >
                            <CheckCircle2 size={14} />
                            Approve
                          </button>
                          
                          <button
                            onClick={() => void runAction(
                              "reject_promotion",
                              rejectAgentPromotion(apiKey, selectedAgentPromo.promotion_id),
                              () => loadPromotionContext(selectedAgentPromo.promotion_id)
                            )}
                            className="inline-flex items-center gap-2 rounded-lg border border-rose-300/20 bg-rose-300/10 px-3 py-2 text-xs font-black uppercase tracking-widest text-rose-100 hover:bg-rose-300/15"
                          >
                            <ShieldOff size={14} />
                            Reject
                          </button>
                        </>
                      )}

                      {/* Execute promotion button with all critical safety checks */}
                      {(() => {
                        const isApproved = selectedAgentPromo.status === "APPROVED";
                        const isSimulationDone = promoSimulationResult !== null;
                        const isSimAllowed = promoSimulationResult?.decision === "ALLOW" || promoSimulationResult?.decision === "HUMAN_GATE_REQUIRED";
                        const isHashValid = selectedAgentPromo.artifact_hash === selectedAgentPromo.verified_artifact_hash &&
                                            selectedAgentPromo.artifact_hash === selectedAgentPromo.approved_artifact_hash;
                        const isVerifierPassed = selectedAgentPromo.verification_score >= 1.0;
                        const isLedgerValid = !!selectedAgentPromo.ledger_event_hash;

                        const executeDisabled = !isApproved || !isSimulationDone || !isSimAllowed || !isHashValid || !isVerifierPassed || !isLedgerValid;

                        return (
                          <div className="w-full space-y-2">
                            <button
                              disabled={executeDisabled}
                              onClick={() => void runAction(
                                "execute_promotion",
                                executeAgentPromotion(apiKey, selectedAgentPromo.promotion_id),
                                () => loadPromotionContext(selectedAgentPromo.promotion_id)
                              )}
                              className="w-full inline-flex items-center justify-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-4 py-2.5 text-xs font-black uppercase tracking-widest text-cyan-100 hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                              <Play size={14} />
                              Execute Integration
                            </button>
                            
                            {/* Execution blocker warnings */}
                            {executeDisabled && (
                              <div className="rounded border border-rose-400/10 bg-rose-400/5 p-2 text-[10px] text-rose-300 space-y-1">
                                <span className="font-bold uppercase tracking-wider block">Safety Gate Restrictions (Execute Blocked):</span>
                                {!isApproved && <div>• Request status must be APPROVED (Current: {selectedAgentPromo.status})</div>}
                                {!isSimulationDone && <div>• Governance policy dry-run simulation is required</div>}
                                {isSimulationDone && !isSimAllowed && <div>• Policy simulator decision is BLOCK</div>}
                                {!isHashValid && <div>• Integrity check failed: lifecycle hashes mismatch</div>}
                                {!isVerifierPassed && <div>• Static verifier score must be 1.0 (Current: {selectedAgentPromo.verification_score})</div>}
                                {!isLedgerValid && <div>• Ledger event audit proof must be verified and logged</div>}
                              </div>
                            )}
                          </div>
                        );
                      })()}

                    </div>

                  </div>
                </Panel>
              )}

            </div>

          </div>
        </div>
      ) : null}
    </div>
  );
}

const inputClass =
  "rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white outline-none placeholder:text-gray-600 focus:border-cyan-300/30";

const primaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-xs font-black uppercase tracking-widest text-cyan-100 hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-40";

const secondaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-black uppercase tracking-widest text-gray-200 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40";

function FormGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid gap-3 md:grid-cols-2">{children}</div>;
}

function Panel({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="glass-panel rounded-lg border-white/10 bg-[#0b0f19]/90 p-5">
      <div className="mb-4 flex items-center gap-2 border-b border-white/5 pb-3">
        <span className="text-cyan-200">{icon}</span>
        <h2 className="text-sm font-black uppercase tracking-widest text-white">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value, icon, tone }: { label: string; value: string | number; icon: React.ReactNode; tone: "cyan" | "green" | "amber" | "rose" | "violet" | "gray" }) {
  const tones = {
    cyan: "border-cyan-300/20 bg-cyan-300/10 text-cyan-100",
    green: "border-emerald-300/20 bg-emerald-300/10 text-emerald-100",
    amber: "border-amber-300/20 bg-amber-300/10 text-amber-100",
    rose: "border-rose-300/20 bg-rose-300/10 text-rose-100",
    violet: "border-violet-300/20 bg-violet-300/10 text-violet-100",
    gray: "border-white/10 bg-white/5 text-gray-200",
  };
  return (
    <div className={`rounded-lg border p-4 ${tones[tone]}`}>
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[10px] font-black uppercase tracking-widest opacity-75">{label}</span>
        {icon}
      </div>
      <div className="text-2xl font-black text-white">{value}</div>
    </div>
  );
}

function CompactTable({ headers, rows, empty }: { headers: string[]; rows: Array<Array<string | number>>; empty: string }) {
  if (rows.length === 0) return <EmptyState text={empty} />;
  return (
    <div className="mt-4 overflow-x-auto rounded-lg border border-white/10">
      <table className="w-full min-w-[640px] border-collapse text-left text-xs">
        <thead className="bg-white/5 text-[10px] uppercase tracking-widest text-gray-500">
          <tr>
            {headers.map((header) => (
              <th key={header} className="px-3 py-2 font-black">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`${rowIndex}-${row[0]}`} className="border-t border-white/5">
              {row.map((cell, cellIndex) => (
                <td key={`${rowIndex}-${cellIndex}`} className="max-w-80 truncate px-3 py-2 text-gray-300">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-6 text-center text-xs font-bold uppercase tracking-widest text-gray-500">
      {text}
    </div>
  );
}

function LedgerEntryList({ entries }: { entries: ReviewLedgerEntryRecord[] }) {
  if (entries.length === 0) return <EmptyState text="No immutable ledger entry loaded" />;
  return (
    <div className="mt-4 space-y-3">
      {entries.map((entry) => (
        <div key={entry.id} className="rounded-lg border border-white/10 bg-black/20 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs font-black text-white">{entry.chain_id}</span>
            <span className="rounded border border-cyan-300/20 bg-cyan-300/10 px-2 py-0.5 text-[10px] font-black uppercase tracking-widest text-cyan-100">
              #{entry.sequence_no}
            </span>
            <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(entry.event_type)}`}>
              {entry.event_type}
            </span>
          </div>
          <div className="mt-2 grid gap-2 text-xs text-gray-500 md:grid-cols-2">
            <span>{entry.entity_type}:{entry.entity_id}</span>
            <span className="font-mono">hash {entry.event_hash.slice(0, 16)}</span>
          </div>
          <pre className="mt-3 max-h-40 overflow-auto rounded-lg border border-white/10 bg-black/40 p-3 text-xs text-gray-300">
            {JSON.stringify(entry.payload_summary || {}, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  );
}

function KeyRow({
  apiKeyRecord,
  usage,
  onPick,
  onRevoke,
}: {
  apiKeyRecord: ApiKeyRecord;
  usage?: QuotaUsage;
  onPick: () => void;
  onRevoke: () => void;
}) {
  const dailyPct = pct(usage?.daily_used ?? 0, apiKeyRecord.quota_daily);
  const monthlyPct = pct(usage?.monthly_used ?? 0, apiKeyRecord.quota_monthly);
  return (
    <div className="rounded-lg border border-white/10 bg-black/20 p-4">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-sm font-black text-white">{apiKeyRecord.id}</span>
            <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${apiKeyRecord.is_active ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100" : "border-rose-300/20 bg-rose-300/10 text-rose-100"}`}>
              {apiKeyRecord.is_active ? "active" : "revoked"}
            </span>
            <span className="rounded border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-black uppercase tracking-widest text-gray-300">
              {apiKeyRecord.role}
            </span>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            {apiKeyRecord.tenant_id || "tenant:none"} / {apiKeyRecord.key_fingerprint} / last used {compactDate(apiKeyRecord.last_used_at)}
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={onPick} className={secondaryButtonClass}>
            <Eye size={14} />
            Pick
          </button>
          <button onClick={onRevoke} disabled={!apiKeyRecord.is_active} className="inline-flex items-center gap-2 rounded-lg border border-rose-300/20 bg-rose-300/10 px-3 py-2 text-xs font-black uppercase tracking-widest text-rose-100 disabled:opacity-40">
            <Trash2 size={14} />
            Revoke
          </button>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <QuotaBar label="Daily" used={usage?.daily_used ?? 0} limit={apiKeyRecord.quota_daily} percent={dailyPct} />
        <QuotaBar label="Monthly" used={usage?.monthly_used ?? 0} limit={apiKeyRecord.quota_monthly} percent={monthlyPct} />
      </div>
    </div>
  );
}

function QuotaBar({ label, used, limit, percent }: { label: string; used: number; limit?: number | null; percent: number | null }) {
  const blocked = limit === 0;
  const width = percent === null ? 0 : Math.min(100, percent);
  return (
    <div>
      <div className="mb-1 flex justify-between text-[10px] font-black uppercase tracking-widest text-gray-500">
        <span>{label}</span>
        <span>{limit == null ? "unlimited" : `${used}/${limit}`}</span>
      </div>
      <div className="h-2 rounded bg-white/10">
        <div className={`h-2 rounded ${blocked || (percent ?? 0) >= 100 ? "bg-rose-400" : (percent ?? 0) >= 80 ? "bg-amber-400" : "bg-cyan-300"}`} style={{ width: `${blocked ? 100 : width}%` }} />
      </div>
    </div>
  );
}

function ProposalList({ proposals, onSelect }: { proposals: ProposalRecord[]; onSelect: (id: string) => void }) {
  if (proposals.length === 0) return <EmptyState text="No proposal loaded" />;
  return (
    <div className="space-y-2">
      {proposals.map((proposal) => (
        <button key={proposal.id} onClick={() => onSelect(proposal.id)} className="w-full rounded-lg border border-white/10 bg-black/20 p-3 text-left hover:border-cyan-300/20">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs font-black text-white">{proposal.id}</span>
            <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(proposal.approval_status)}`}>
              {proposal.approval_status}
            </span>
            <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(proposal.gate_status)}`}>
              {proposal.gate_status}
            </span>
          </div>
          <div className="mt-2 truncate text-xs text-gray-400">{proposal.title}</div>
        </button>
      ))}
    </div>
  );
}

function DraftList({
  drafts,
  verifications,
  onSelect,
  onVerify,
}: {
  drafts: PrDraftRecord[];
  verifications: PrVerificationRecord[];
  onSelect: (id: string) => void;
  onVerify: (id: string) => void;
}) {
  if (drafts.length === 0) return <EmptyState text="No draft PR loaded" />;
  return (
    <div className="space-y-3">
      {drafts.map((draft) => {
        const verification = verifications.find((item) => item.pr_draft_id === draft.id);
        return (
          <div key={draft.id} className="rounded-lg border border-white/10 bg-black/20 p-4">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-sm font-black text-white">{draft.id}</span>
                  <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(draft.risk_level)}`}>
                    {draft.risk_level}
                  </span>
                  <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(verification?.review_decision)}`}>
                    {verification?.review_decision || "unverified"}
                  </span>
                </div>
                <div className="mt-2 text-xs text-gray-400">{draft.title}</div>
                <pre className="mt-3 max-h-48 overflow-auto rounded-lg border border-white/10 bg-black/40 p-3 text-xs text-gray-300">{draft.body}</pre>
              </div>
              <div className="flex gap-2">
                <button onClick={() => onSelect(draft.id)} className={secondaryButtonClass}>
                  <Eye size={14} />
                  Context
                </button>
                <button onClick={() => onVerify(draft.id)} className={primaryButtonClass}>
                  <Play size={14} />
                  Verify
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function VerificationSummary({ verification }: { verification: PrVerificationRecord }) {
  return (
    <div className="mt-4 rounded-lg border border-cyan-300/20 bg-cyan-300/10 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-sm font-black text-white">{verification.id}</span>
        <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(verification.review_decision)}`}>
          {verification.review_decision}
        </span>
        <span className="text-xs text-cyan-100">Score {verification.review_score}</span>
      </div>
      <pre className="mt-3 max-h-64 overflow-auto rounded-lg border border-white/10 bg-black/40 p-3 text-xs text-gray-300">
        {verification.verification_report || JSON.stringify(verification, null, 2)}
      </pre>
    </div>
  );
}

function RevisionList({ revisions, onVerify }: { revisions: PatchRevisionRecord[]; onVerify: (id: string) => void }) {
  if (revisions.length === 0) return <EmptyState text="No revision loaded" />;
  return (
    <div className="mt-4 space-y-2">
      {revisions.map((revision) => (
        <div key={revision.id} className="rounded-lg border border-white/10 bg-black/20 p-3">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs font-black text-white">{revision.id}</span>
                <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(revision.risk_level)}`}>
                  {revision.risk_level}
                </span>
                <span className={`rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest ${statusTone(revision.verification_status)}`}>
                  {revision.verification_status}
                </span>
              </div>
              <div className="mt-1 text-xs text-gray-500">revision #{revision.revision_number}</div>
            </div>
            <button onClick={() => onVerify(revision.id)} className={primaryButtonClass}>
              <Play size={14} />
              Verify
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
