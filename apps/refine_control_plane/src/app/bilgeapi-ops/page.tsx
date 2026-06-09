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
} from "@/lib/bilgeapiOpsClient";

type OpsTab = "dashboard" | "keys" | "research" | "prs" | "revisions" | "ai" | "ledger" | "audit";

type ActionLog = {
  id: string;
  label: string;
  status: "OK" | "ERR";
  detail: string;
};

const roles = ["ADMIN", "OPERATOR", "AUDIT_OBSERVER", "SOVEREIGN_PRIME"];
const tabs: Array<{ id: OpsTab; label: string; icon: LucideIcon }> = [
  { id: "dashboard", label: "Dashboard", icon: Activity },
  { id: "keys", label: "API Keys", icon: KeyRound },
  { id: "research", label: "Research", icon: Search },
  { id: "prs", label: "Draft PRs", icon: GitPullRequestDraft },
  { id: "revisions", label: "Revisions", icon: RotateCcw },
  { id: "ai", label: "AI Suggestions", icon: Terminal },
  { id: "ledger", label: "Ledger", icon: ClipboardCheck },
  { id: "audit", label: "Audit", icon: ClipboardCheck },
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

  React.useEffect(() => {
    const saved = sessionStorage.getItem("bilgeapi_ops_api_key");
    if (saved) setApiKey(saved);
  }, []);

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
      setSnapshot(next);
      if (!selectedProposalId && next.proposals[0]) setSelectedProposalId(next.proposals[0].id);
      if (!selectedDraftId && next.drafts[0]) setSelectedDraftId(next.drafts[0].id);
      record("snapshot", "OK", `${next.apiKeys.length} keys, ${next.proposals.length} proposals`);
    } catch (error) {
      record("snapshot", "ERR", error instanceof Error ? error.message : String(error));
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

  return (
    <div className="min-h-screen bg-[#060a12] p-6 text-gray-200">
      <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-cyan-100">
            <ShieldCheck size={14} />
            Faz 27
          </div>
          <h1 className="text-3xl font-black text-white">BilgeAPI Ops Console</h1>
          <p className="mt-2 max-w-3xl text-sm text-gray-400">
            API keys, quotas, research, proposals, draft PRs, sandbox verifications, reviewer feedback,
            patch revisions, release gate and audit trail in one operator surface.
          </p>
        </div>
        <div className="flex flex-col gap-3 rounded-lg border border-white/10 bg-black/30 p-3 md:flex-row md:items-center">
          <div className="relative min-w-72">
            <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              type="password"
              placeholder="BilgeAPI admin/operator X-API-Key"
              className="w-full rounded-lg border border-white/10 bg-black/40 py-2 pl-9 pr-3 text-sm text-white outline-none focus:border-cyan-300/30"
            />
          </div>
          <button
            onClick={() => void refresh()}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-xs font-black uppercase tracking-widest text-cyan-100 hover:bg-cyan-300/15"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            Refresh
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
            Clear
          </button>
        </div>
      </div>

      <nav className="mb-6 flex flex-wrap gap-2">
        {tabs.map(({ id, label, icon: Icon }) => (
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
            {label}
          </button>
        ))}
      </nav>

      {!apiKey.trim() ? (
        <section className="rounded-lg border border-amber-300/20 bg-amber-300/10 p-6 text-amber-100">
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} />
            <span className="text-sm font-bold">BilgeAPI operator key is required before live data can load.</span>
          </div>
        </section>
      ) : null}

      {snapshot?.errors.length ? (
        <section className="mb-6 rounded-lg border border-amber-300/20 bg-amber-300/10 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-amber-100">
            <AlertTriangle size={15} />
            Partial data
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
            <Metric label="Total API Keys" value={apiKeys.length} icon={<KeyRound size={16} />} tone="cyan" />
            <Metric label="Active / Revoked" value={`${activeKeyCount} / ${revokedKeyCount}`} icon={<ShieldCheck size={16} />} tone="green" />
            <Metric label="Quota Exceeded" value={exceededCount} icon={<AlertTriangle size={16} />} tone={exceededCount ? "rose" : "gray"} />
            <Metric label="Release Gate" value={releaseLatest ? `${releaseLatest.score.toFixed(0)} ${releaseLatest.status}` : "-"} icon={<ListChecks size={16} />} tone="cyan" />
            <Metric label="Pending Research" value={research?.status === "PENDING" ? 1 : 0} icon={<Search size={16} />} tone="amber" />
            <Metric label="PR Draft Review" value={pendingDraftCount} icon={<GitPullRequestDraft size={16} />} tone="violet" />
            <Metric label="Needs Caution" value={cautionCount} icon={<AlertTriangle size={16} />} tone={cautionCount ? "amber" : "gray"} />
            <Metric label="Audit Events" value={auditEvents.length} icon={<ClipboardCheck size={16} />} tone="green" />
            <Metric label="Ledger Entries" value={ledgerRecent.length} icon={<ClipboardCheck size={16} />} tone="violet" />
          </div>

          <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
            <Panel title="Recent Audit Trail" icon={<ClipboardCheck size={16} />}>
              <CompactTable
                headers={["Event", "Entity", "Actor", "Created"]}
                rows={auditEvents.slice(0, 10).map((event) => [
                  event.event_type,
                  `${event.entity_type}:${event.entity_id}`,
                  event.actor_id,
                  compactDate(event.created_at),
                ])}
                empty="No audit event loaded"
              />
            </Panel>
            <Panel title="Release Gate Status" icon={<ListChecks size={16} />}>
              <div className="space-y-4">
                <div className={`rounded-lg border p-4 ${statusTone(releaseLatest?.status)}`}>
                  <div className="text-xs font-black uppercase tracking-widest">Latest</div>
                  <div className="mt-2 text-3xl font-black">{releaseLatest ? releaseLatest.score.toFixed(2) : "-"}</div>
                  <div className="mt-1 text-xs">{releaseLatest ? `${releaseLatest.status} / ${releaseLatest.id}` : "No release check loaded"}</div>
                </div>
                <button
                  onClick={() => void runAction("release_gate", runReleaseReadiness(apiKey))}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-xs font-black uppercase tracking-widest text-cyan-100"
                >
                  <Play size={15} />
                  Run Gate
                </button>
              </div>
            </Panel>
          </section>
        </div>
      ) : null}

      {activeTab === "keys" ? (
        <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
          <Panel title="Create API Key" icon={<KeyRound size={16} />}>
            <FormGrid>
              <select value={keyForm.role} onChange={(event) => setKeyForm({ ...keyForm, role: event.target.value })} className={inputClass}>
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
              <input className={inputClass} value={keyForm.tenant_id} onChange={(event) => setKeyForm({ ...keyForm, tenant_id: event.target.value })} placeholder="tenant_id" />
              <input className={inputClass} value={keyForm.description} onChange={(event) => setKeyForm({ ...keyForm, description: event.target.value })} placeholder="description" />
              <input className={inputClass} value={keyForm.quota_daily} onChange={(event) => setKeyForm({ ...keyForm, quota_daily: event.target.value })} placeholder="daily quota" />
              <input className={inputClass} value={keyForm.quota_monthly} onChange={(event) => setKeyForm({ ...keyForm, quota_monthly: event.target.value })} placeholder="monthly quota" />
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
                Create
              </button>
            </FormGrid>
            {createdKey ? (
              <div className="mt-4 rounded-lg border border-emerald-300/20 bg-emerald-300/10 p-4">
                <div className="mb-2 text-xs font-black uppercase tracking-widest text-emerald-100">Plaintext shown once</div>
                <code className="block break-all rounded bg-black/40 p-3 text-xs text-white">{createdKey.plaintext_key}</code>
              </div>
            ) : null}
          </Panel>

          <Panel title="API Keys & Quotas" icon={<Terminal size={16} />}>
            <div className="mb-4 grid gap-2 md:grid-cols-[1fr_0.7fr_0.7fr_auto]">
              <input className={inputClass} value={quotaForm.key_id} onChange={(event) => setQuotaForm({ ...quotaForm, key_id: event.target.value })} placeholder="key_id" />
              <input className={inputClass} value={quotaForm.quota_daily} onChange={(event) => setQuotaForm({ ...quotaForm, quota_daily: event.target.value })} placeholder="daily" />
              <input className={inputClass} value={quotaForm.quota_monthly} onChange={(event) => setQuotaForm({ ...quotaForm, quota_monthly: event.target.value })} placeholder="monthly" />
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
                Set
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
          <Panel title="Research & Proposal Actions" icon={<Search size={16} />}>
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
                Start
              </button>
              <button
                className={secondaryButtonClass}
                disabled={!research}
                onClick={() => research && void runAction("proposal", createProposal(apiKey, research.id))}
              >
                <FileText size={15} />
                Proposal
              </button>
            </FormGrid>
            <div className="mt-4 rounded-lg border border-white/10 bg-black/20 p-4 text-xs text-gray-300">
              <div className="font-black uppercase tracking-widest text-white">Latest Research</div>
              <div className="mt-2">{research ? `${research.id} / ${research.status}` : "No session research"}</div>
            </div>
            <CompactTable
              headers={["Domain", "Trust", "Title"]}
              rows={evidences.map((evidence) => [evidence.source_domain, evidence.trust_score.toFixed(0), evidence.title || evidence.source_url])}
              empty="No evidence loaded"
            />
          </Panel>
          <Panel title="Improvement Proposals" icon={<FileText size={16} />}>
            <div className="mb-3 flex flex-wrap gap-2">
              <input className={inputClass} value={selectedProposalId} onChange={(event) => setSelectedProposalId(event.target.value)} placeholder="proposal_id" />
              <button className={secondaryButtonClass} onClick={() => selectedProposalId && void runAction("approve_proposal", approveProposal(apiKey, selectedProposalId))}>
                <CheckCircle2 size={15} />
                Approve
              </button>
              <button className={secondaryButtonClass} onClick={() => selectedProposalId && void runAction("run_gate", runProposalGate(apiKey, selectedProposalId))}>
                <Play size={15} />
                Gate
              </button>
              <button className={secondaryButtonClass} onClick={() => selectedProposalId && void runAction("draft_pr", createDraftPr(apiKey, selectedProposalId))}>
                <GitPullRequestDraft size={15} />
                Draft
              </button>
              <button
                className={secondaryButtonClass}
                onClick={() =>
                  selectedProposalId &&
                  void runAction("audit_report", getProposalAuditReport(apiKey, selectedProposalId), (text) => setAuditReport(text))
                }
              >
                <Eye size={15} />
                Report
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
                  {ledgerVerification.valid ? "Chain verified" : "Chain broken"}
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
                <div key={item.id} className={`rounded-lg border p-3 text-xs ${item.status === "OK" ? "border-emerald-300/20 bg-emerald-300/10" : "border-rose-300/20 bg-rose-300/10"}`}>
                  <div className="font-black uppercase tracking-widest text-white">{item.label}</div>
                  <div className="mt-1 text-gray-300">{item.detail}</div>
                </div>
              ))}
            </div>
          </Panel>
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
