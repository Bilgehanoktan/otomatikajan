import { getAuthHeaders } from "@/lib/auth";
import { safeFetchJson } from "@/lib/api";

export const BILGEAPI_PROXY_BASE = "/bilgeapi";
export const AGENT_API_BASE = "/api/v1/agents";

export type ApiKeyRecord = {
  id: string;
  key_prefix: string;
  key_fingerprint: string;
  role: string;
  description?: string | null;
  tenant_id?: string | null;
  is_active: boolean;
  created_by?: string | null;
  revoked_by?: string | null;
  revoke_reason?: string | null;
  created_at: string;
  expires_at?: string | null;
  revoked_at?: string | null;
  last_used_at?: string | null;
  quota_daily?: number | null;
  quota_monthly?: number | null;
};

export type ApiKeyCreateResponse = ApiKeyRecord & {
  plaintext_key: string;
};

export type QuotaUsage = {
  key_id: string;
  quota_daily?: number | null;
  quota_monthly?: number | null;
  daily_used: number;
  monthly_used: number;
  daily_remaining?: number | null;
  monthly_remaining?: number | null;
};

export type ResearchRecord = {
  id: string;
  incident_id: string;
  query: string;
  status: string;
  tenant_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type EvidenceRecord = {
  id: string;
  research_id: string;
  source_url: string;
  source_domain: string;
  title?: string | null;
  snippet?: string | null;
  raw_content_summary?: string | null;
  content_hash: string;
  trust_score: number;
  retrieved_at: string;
};

export type ProposalRecord = {
  id: string;
  research_id: string;
  title: string;
  rationale: string;
  patch_code: string;
  risk_analysis?: Record<string, unknown> | null;
  gate_status: string;
  gate_score?: number | null;
  approval_status: string;
  approved_by?: string | null;
  approved_at?: string | null;
  ready_for_human_apply: boolean;
  created_at: string;
  updated_at: string;
};

export type PrDraftRecord = {
  id: string;
  proposal_id: string;
  provider: string;
  status: string;
  github_pr_url?: string | null;
  branch_name?: string | null;
  title: string;
  body: string;
  evidence_hash?: string | null;
  risk_level: string;
  risk_flags?: string[] | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
};

export type PrVerificationRecord = {
  id: string;
  pr_draft_id: string;
  proposal_id: string;
  revision_id?: string | null;
  status: string;
  review_score: number;
  review_decision: string;
  risk_level: string;
  risk_flags?: string[] | null;
  affected_files?: string[] | null;
  mutation_detected: boolean;
  test_files_present: boolean;
  patch_size_lines: number;
  test_plan?: unknown;
  rollback_plan?: string | null;
  verification_report?: string | null;
  created_at: string;
  updated_at: string;
};

export type ReviewerFeedbackRecord = {
  id: string;
  pr_draft_id: string;
  reviewer_id: string;
  comment: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type PatchRevisionRecord = {
  id: string;
  pr_draft_id: string;
  feedback_id?: string | null;
  revision_number: number;
  revised_patch_code: string;
  risk_analysis?: Record<string, unknown> | null;
  risk_level: string;
  verification_status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type AIPatchSuggestionRecord = {
  id: string;
  pr_draft_id: string;
  feedback_id?: string | null;
  revision_id?: string | null;
  provider: string;
  model_name?: string | null;
  prompt_hash: string;
  context_summary?: Record<string, unknown> | null;
  suggested_patch_code: string;
  rationale?: string | null;
  risk_notes?: string | null;
  risk_level: string;
  verification_id?: string | null;
  status: string;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
};

export type ReleaseCheckRecord = {
  id: string;
  status: string;
  score: number;
  blockers: string[];
  warnings: string[];
  checked_modules: Record<string, string>;
  checked_endpoints: Record<string, string>;
  smoke_trace: Array<Record<string, unknown>>;
  app_version?: string | null;
  git_sha?: string | null;
  environment?: string | null;
  triggered_by?: string | null;
  created_at: string;
};

export type AuditEventRecord = {
  id: string;
  event_type: string;
  actor_id: string;
  actor_type: string;
  entity_type: string;
  entity_id: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ReviewLedgerEntryRecord = {
  id: string;
  chain_id: string;
  sequence_no: number;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor_id?: string | null;
  previous_hash?: string | null;
  payload_hash: string;
  event_hash: string;
  payload_summary?: Record<string, unknown> | null;
  created_at: string;
};

export type ReviewLedgerVerifyRecord = {
  chain_id: string;
  valid: boolean;
  entry_count: number;
  head_hash?: string | null;
  issues: Array<Record<string, unknown>>;
};

export type ReviewLedgerExportRecord = {
  chain_id: string;
  format: string;
  valid: boolean;
  entry_count: number;
  content: string;
};

export type RemediationRunbookRecord = {
  id: string;
  name: string;
  action_type: string;
  severity_allowed: string;
  requires_human_gate: boolean;
  enabled: boolean;
  execution_mode: string;
  max_attempts: number;
  cooldown_seconds: number;
  safety_notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type RemediationAttemptRecord = {
  id: string;
  finding_id: string;
  runbook_id?: string | null;
  action_type: string;
  status: string;
  attempt_no: number;
  before_health?: Record<string, unknown> | null;
  after_health?: Record<string, unknown> | null;
  output_summary?: string | null;
  error_message?: string | null;
  policy_decision?: Record<string, unknown> | null;
  forbidden_actions_checked?: string[] | null;
  ledger_chain_id?: string | null;
  created_by?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type SystemFindingRecord = {
  id: string;
  tenant_id?: string | null;
  source_type: string;
  source_id: string;
  source_hash: string;
  title: string;
  description: string;
  severity: string;
  risk_score: number;
  status: string;
  evidence_summary?: Record<string, unknown> | null;
  recommended_action?: string | null;
  human_gate_payload?: Record<string, unknown> | null;
  occurrence_count: number;
  first_seen_at: string;
  last_seen_at: string;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  dismissed_by?: string | null;
  dismissed_at?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  bilgeapi_research_id?: string | null;
  bilgeapi_proposal_id?: string | null;
  bilgeapi_pr_draft_id?: string | null;
  bilgeapi_verification_id?: string | null;
  bilgeapi_ledger_chain_id?: string | null;
  created_by?: string | null;
  correlation_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type WatchdogStatusRecord = {
  enabled: boolean;
  status: string;
  risk_threshold: number;
  auto_finding: boolean;
  human_gate_required: boolean;
  open_findings: number;
  high_or_critical_findings: number;
  last_scan_correlation_id?: string | null;
};

export type ManagementGateRecord = {
  unlocked: boolean;
  status: string;
  reason?: string | null;
  forbidden_actions: string[];
  human_gate_required: boolean;
  updated_by?: string | null;
};

export type OpsSnapshot = {
  apiKeys: ApiKeyRecord[];
  quotaUsage: QuotaUsage[];
  proposals: ProposalRecord[];
  drafts: PrDraftRecord[];
  verifications: PrVerificationRecord[];
  aiSuggestions: AIPatchSuggestionRecord[];
  releaseLatest: ReleaseCheckRecord | null;
  auditEvents: AuditEventRecord[];
  ledgerRecent: ReviewLedgerEntryRecord[];
  remediationRunbooks: RemediationRunbookRecord[];
  remediationAttempts: RemediationAttemptRecord[];
  systemFindings: SystemFindingRecord[];
  watchdogStatus: WatchdogStatusRecord | null;
  managementGate: ManagementGateRecord | null;
  agentPromotions: AgentPromotionRecord[];
  agentRuns: AgentRunRecord[];
  agentCapabilities: AgentCapabilityRecord[];
  errors: string[];
};


type JsonValue = Record<string, unknown> | Array<unknown>;

export class BilgeApiResponseError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "BilgeApiResponseError";
    this.status = status;
    this.detail = detail;
  }
}

export function isBilgeApiAuthError(error: unknown): error is BilgeApiResponseError {
  return error instanceof BilgeApiResponseError && (error.status === 401 || error.status === 403);
}

function buildHeaders(apiKey: string, hasBody = false): Headers {
  const headers = new Headers();
  if (apiKey.trim()) {
    headers.set("X-API-Key", apiKey.trim());
  }
  if (hasBody) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

async function readError(response: Response): Promise<string> {
  const raw = await response.text().catch(() => "");
  if (!raw) return `HTTP ${response.status}`;
  try {
    const parsed = JSON.parse(raw) as { detail?: unknown };
    return typeof parsed.detail === "string" ? parsed.detail : raw.slice(0, 240);
  } catch {
    return raw.slice(0, 240);
  }
}

export async function bilgeApiFetch<T>(
  apiKey: string,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const hasBody = Boolean(init.body);
  const response = await fetch(`${BILGEAPI_PROXY_BASE}${path}`, {
    ...init,
    headers: buildHeaders(apiKey, hasBody),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new BilgeApiResponseError(response.status, await readError(response));
  }

  return (await response.json()) as T;
}

export async function bilgeApiText(
  apiKey: string,
  path: string,
  init: RequestInit = {},
): Promise<string> {
  const hasBody = Boolean(init.body);
  const response = await fetch(`${BILGEAPI_PROXY_BASE}${path}`, {
    ...init,
    headers: buildHeaders(apiKey, hasBody),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new BilgeApiResponseError(response.status, await readError(response));
  }

  return response.text();
}

async function buildAgentHeaders(hasBody = false): Promise<Headers> {
  const headers = new Headers(await getAuthHeaders());
  headers.delete("X-API-Key");
  if (hasBody) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

export async function agentApiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  return safeFetchJson<T>(`${AGENT_API_BASE}${path}`, init);
}

export function redactPlaintextKey<T extends { plaintext_key?: string }>(payload: T): T {
  if (!payload.plaintext_key) return payload;
  return { ...payload, plaintext_key: `${payload.plaintext_key.slice(0, 12)}...[REDACTED]` };
}

async function settle<T>(label: string, task: Promise<T>, errors: string[]): Promise<T | null> {
  try {
    return await task;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    errors.push(`${label}: ${message}`);
    return null;
  }
}

async function verifyBilgeApiAccess(apiKey: string): Promise<JsonValue> {
  return bilgeApiFetch<JsonValue>(apiKey, "/v1/catalog");
}

export async function listBilgeApiKeys(apiKey: string): Promise<ApiKeyRecord[]> {
  return bilgeApiFetch<ApiKeyRecord[]>(apiKey, "/v1/admin/api-keys");
}

export async function createBilgeApiKey(
  apiKey: string,
  body: {
    role: string;
    description?: string | null;
    tenant_id?: string | null;
    expires_in_days?: number | null;
    quota_daily?: number | null;
    quota_monthly?: number | null;
  },
): Promise<ApiKeyCreateResponse> {
  return bilgeApiFetch<ApiKeyCreateResponse>(apiKey, "/v1/admin/api-keys", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function revokeBilgeApiKey(apiKey: string, keyId: string, reason: string): Promise<ApiKeyRecord> {
  return bilgeApiFetch<ApiKeyRecord>(apiKey, `/v1/admin/api-keys/${encodeURIComponent(keyId)}/revoke`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function updateApiKeyQuota(
  apiKey: string,
  keyId: string,
  quota_daily: number | null,
  quota_monthly: number | null,
): Promise<ApiKeyRecord> {
  return bilgeApiFetch<ApiKeyRecord>(apiKey, `/v1/admin/api-keys/${encodeURIComponent(keyId)}/quota`, {
    method: "PUT",
    body: JSON.stringify({ quota_daily, quota_monthly }),
  });
}

export async function getApiKeyQuotaUsage(apiKey: string, keyId: string): Promise<QuotaUsage> {
  return bilgeApiFetch<QuotaUsage>(apiKey, `/v1/admin/api-keys/${encodeURIComponent(keyId)}/quota-usage`);
}

export async function createResearchRequest(apiKey: string, incident_id: string, query: string): Promise<ResearchRecord> {
  return bilgeApiFetch<ResearchRecord>(apiKey, "/v1/improvements/research", {
    method: "POST",
    body: JSON.stringify({ incident_id, query }),
  });
}

export async function listResearchEvidences(apiKey: string, researchId: string): Promise<EvidenceRecord[]> {
  return bilgeApiFetch<EvidenceRecord[]>(apiKey, `/v1/improvements/research/${encodeURIComponent(researchId)}/evidences`);
}

export async function createProposal(apiKey: string, researchId: string): Promise<ProposalRecord> {
  return bilgeApiFetch<ProposalRecord>(apiKey, `/v1/improvements/${encodeURIComponent(researchId)}/proposal`, {
    method: "POST",
  });
}

export async function listProposals(apiKey: string): Promise<ProposalRecord[]> {
  return bilgeApiFetch<ProposalRecord[]>(apiKey, "/v1/improvements/proposals");
}

export async function approveProposal(apiKey: string, proposalId: string): Promise<ProposalRecord> {
  return bilgeApiFetch<ProposalRecord>(apiKey, `/v1/improvements/${encodeURIComponent(proposalId)}/approve`, {
    method: "POST",
  });
}

export async function runProposalGate(apiKey: string, proposalId: string): Promise<JsonValue> {
  return bilgeApiFetch<JsonValue>(apiKey, `/v1/improvements/${encodeURIComponent(proposalId)}/run-gate`, {
    method: "POST",
  });
}

export async function createDraftPr(apiKey: string, proposalId: string): Promise<PrDraftRecord> {
  return bilgeApiFetch<PrDraftRecord>(apiKey, `/v1/improvements/proposals/${encodeURIComponent(proposalId)}/draft-pr/create`, {
    method: "POST",
  });
}

export async function listDraftPrs(apiKey: string, proposalId: string): Promise<PrDraftRecord[]> {
  return bilgeApiFetch<PrDraftRecord[]>(apiKey, `/v1/improvements/proposals/${encodeURIComponent(proposalId)}/draft-prs`);
}

export async function verifyDraftPr(apiKey: string, draftId: string): Promise<PrVerificationRecord> {
  return bilgeApiFetch<PrVerificationRecord>(apiKey, `/v1/improvements/pr-drafts/${encodeURIComponent(draftId)}/verify`, {
    method: "POST",
  });
}

export async function getDraftVerification(apiKey: string, draftId: string): Promise<PrVerificationRecord> {
  return bilgeApiFetch<PrVerificationRecord>(apiKey, `/v1/improvements/pr-drafts/${encodeURIComponent(draftId)}/verification`);
}

export async function createReviewerFeedback(
  apiKey: string,
  draftId: string,
  reviewer_id: string,
  comment: string,
): Promise<ReviewerFeedbackRecord> {
  return bilgeApiFetch<ReviewerFeedbackRecord>(apiKey, `/v1/improvements/pr-drafts/${encodeURIComponent(draftId)}/feedback`, {
    method: "POST",
    body: JSON.stringify({ reviewer_id, comment }),
  });
}

export async function listReviewerFeedback(apiKey: string, draftId: string): Promise<ReviewerFeedbackRecord[]> {
  return bilgeApiFetch<ReviewerFeedbackRecord[]>(apiKey, `/v1/improvements/pr-drafts/${encodeURIComponent(draftId)}/feedback`);
}

export async function createPatchRevision(
  apiKey: string,
  draftId: string,
  revised_patch_code: string,
  feedback_id?: string | null,
): Promise<PatchRevisionRecord> {
  return bilgeApiFetch<PatchRevisionRecord>(apiKey, `/v1/improvements/pr-drafts/${encodeURIComponent(draftId)}/revisions`, {
    method: "POST",
    body: JSON.stringify({ feedback_id: feedback_id || null, revised_patch_code }),
  });
}

export async function listPatchRevisions(apiKey: string, draftId: string): Promise<PatchRevisionRecord[]> {
  return bilgeApiFetch<PatchRevisionRecord[]>(apiKey, `/v1/improvements/pr-drafts/${encodeURIComponent(draftId)}/revisions`);
}

export async function verifyPatchRevision(apiKey: string, revisionId: string): Promise<PrVerificationRecord> {
  return bilgeApiFetch<PrVerificationRecord>(apiKey, `/v1/improvements/revisions/${encodeURIComponent(revisionId)}/verify`, {
    method: "POST",
  });
}

export async function createAiPatchSuggestion(
  apiKey: string,
  draftId: string,
  instruction: string,
  feedback_id?: string | null,
  revision_id?: string | null,
): Promise<AIPatchSuggestionRecord> {
  return bilgeApiFetch<AIPatchSuggestionRecord>(apiKey, `/v1/improvements/pr-drafts/${encodeURIComponent(draftId)}/ai-suggestions`, {
    method: "POST",
    body: JSON.stringify({ instruction, feedback_id: feedback_id || null, revision_id: revision_id || null }),
  });
}

export async function listAiPatchSuggestions(apiKey: string, draftId: string): Promise<AIPatchSuggestionRecord[]> {
  return bilgeApiFetch<AIPatchSuggestionRecord[]>(apiKey, `/v1/improvements/pr-drafts/${encodeURIComponent(draftId)}/ai-suggestions`);
}

export async function getAiPatchSuggestion(apiKey: string, suggestionId: string): Promise<AIPatchSuggestionRecord> {
  return bilgeApiFetch<AIPatchSuggestionRecord>(apiKey, `/v1/improvements/ai-suggestions/${encodeURIComponent(suggestionId)}`);
}

export async function verifyAiPatchSuggestion(apiKey: string, suggestionId: string): Promise<PrVerificationRecord> {
  return bilgeApiFetch<PrVerificationRecord>(apiKey, `/v1/improvements/ai-suggestions/${encodeURIComponent(suggestionId)}/verify`, {
    method: "POST",
  });
}

export async function acceptAiPatchSuggestionForReview(apiKey: string, suggestionId: string): Promise<{ id: string; status: string; updated_at: string }> {
  return bilgeApiFetch<{ id: string; status: string; updated_at: string }>(apiKey, `/v1/improvements/ai-suggestions/${encodeURIComponent(suggestionId)}/accept-for-review`, {
    method: "POST",
  });
}

export async function rejectAiPatchSuggestion(apiKey: string, suggestionId: string, reason?: string | null): Promise<{ id: string; status: string; reason?: string | null; updated_at: string }> {
  return bilgeApiFetch<{ id: string; status: string; reason?: string | null; updated_at: string }>(apiKey, `/v1/improvements/ai-suggestions/${encodeURIComponent(suggestionId)}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason: reason || null }),
  });
}

export async function getProposalAuditReport(apiKey: string, proposalId: string): Promise<string> {
  return bilgeApiText(apiKey, `/v1/improvements/proposals/${encodeURIComponent(proposalId)}/audit-report`);
}

export async function getLatestReleaseCheck(apiKey: string): Promise<ReleaseCheckRecord> {
  return bilgeApiFetch<ReleaseCheckRecord>(apiKey, "/v1/release/readiness/latest");
}

export async function runReleaseReadiness(apiKey: string): Promise<ReleaseCheckRecord> {
  return bilgeApiFetch<ReleaseCheckRecord>(apiKey, "/v1/release/readiness", {
    method: "POST",
    body: JSON.stringify({ triggered_by: "bilgeapi_ops_console" }),
  });
}

export async function listAuditEvents(apiKey: string): Promise<AuditEventRecord[]> {
  return bilgeApiFetch<AuditEventRecord[]>(apiKey, "/v1/audit-events?limit=10");
}

export async function listReviewLedgerRecent(apiKey: string): Promise<ReviewLedgerEntryRecord[]> {
  return bilgeApiFetch<ReviewLedgerEntryRecord[]>(apiKey, "/v1/review-ledger/recent?limit=20");
}

export async function getReviewLedgerChain(apiKey: string, chainId: string): Promise<{ chain_id: string; entries: ReviewLedgerEntryRecord[] }> {
  return bilgeApiFetch<{ chain_id: string; entries: ReviewLedgerEntryRecord[] }>(apiKey, `/v1/review-ledger/chains/${encodeURIComponent(chainId)}`);
}

export async function verifyReviewLedgerChain(apiKey: string, chainId: string): Promise<ReviewLedgerVerifyRecord> {
  return bilgeApiFetch<ReviewLedgerVerifyRecord>(apiKey, `/v1/review-ledger/chains/${encodeURIComponent(chainId)}/verify`);
}

export async function exportReviewLedgerChain(apiKey: string, chainId: string): Promise<ReviewLedgerExportRecord> {
  return bilgeApiFetch<ReviewLedgerExportRecord>(apiKey, `/v1/review-ledger/chains/${encodeURIComponent(chainId)}/export`);
}

export async function listRemediationAttempts(apiKey: string, findingId?: string): Promise<RemediationAttemptRecord[]> {
  const path = findingId ? `/v1/watchdog/remediations?finding_id=${encodeURIComponent(findingId)}` : "/v1/watchdog/remediations";
  return bilgeApiFetch<RemediationAttemptRecord[]>(apiKey, path);
}

export async function getRemediationAttempt(apiKey: string, attemptId: string): Promise<RemediationAttemptRecord> {
  return bilgeApiFetch<RemediationAttemptRecord>(apiKey, `/v1/watchdog/remediations/${encodeURIComponent(attemptId)}`);
}

export async function triggerRemediation(apiKey: string, findingId: string, runbookId: string): Promise<RemediationAttemptRecord> {
  return bilgeApiFetch<RemediationAttemptRecord>(apiKey, `/v1/watchdog/findings/${encodeURIComponent(findingId)}/remediate`, {
    method: "POST",
    body: JSON.stringify({ runbook_id: runbookId }),
  });
}

export async function listRemediationRunbooks(apiKey: string): Promise<RemediationRunbookRecord[]> {
  return bilgeApiFetch<RemediationRunbookRecord[]>(apiKey, "/v1/watchdog/runbooks");
}

export async function enableRemediationRunbook(apiKey: string, runbookId: string): Promise<RemediationRunbookRecord> {
  return bilgeApiFetch<RemediationRunbookRecord>(apiKey, `/v1/watchdog/runbooks/${encodeURIComponent(runbookId)}/enable`, {
    method: "POST",
  });
}

export async function disableRemediationRunbook(apiKey: string, runbookId: string): Promise<RemediationRunbookRecord> {
  return bilgeApiFetch<RemediationRunbookRecord>(apiKey, `/v1/watchdog/runbooks/${encodeURIComponent(runbookId)}/disable`, {
    method: "POST",
  });
}

export async function runEmergencyRecovery(apiKey: string, findingId: string, actionType: string): Promise<RemediationAttemptRecord> {
  return bilgeApiFetch<RemediationAttemptRecord>(apiKey, "/v1/watchdog/emergency-recovery/run", {
    method: "POST",
    body: JSON.stringify({ finding_id: findingId, action_type: actionType }),
  });
}

export async function listWatchdogFindings(apiKey: string, status?: string): Promise<SystemFindingRecord[]> {
  const path = status ? `/v1/watchdog/findings?status=${encodeURIComponent(status)}` : "/v1/watchdog/findings";
  return bilgeApiFetch<SystemFindingRecord[]>(apiKey, path);
}

export async function acknowledgeFinding(apiKey: string, findingId: string): Promise<SystemFindingRecord> {
  return bilgeApiFetch<SystemFindingRecord>(apiKey, `/v1/watchdog/findings/${encodeURIComponent(findingId)}/acknowledge`, {
    method: "POST",
  });
}

export async function dismissFinding(apiKey: string, findingId: string): Promise<SystemFindingRecord> {
  return bilgeApiFetch<SystemFindingRecord>(apiKey, `/v1/watchdog/findings/${encodeURIComponent(findingId)}/dismiss`, {
    method: "POST",
  });
}

export async function getWatchdogStatus(apiKey: string): Promise<WatchdogStatusRecord> {
  return bilgeApiFetch<WatchdogStatusRecord>(apiKey, "/v1/watchdog/status");
}

export async function getManagementGate(apiKey: string): Promise<ManagementGateRecord> {
  return bilgeApiFetch<ManagementGateRecord>(apiKey, "/v1/system/management-gate");
}

export async function setManagementGate(apiKey: string, unlocked: boolean, reason?: string): Promise<ManagementGateRecord> {
  return bilgeApiFetch<ManagementGateRecord>(apiKey, "/v1/system/management-gate", {
    method: "POST",
    body: JSON.stringify({ unlocked, reason: reason || null }),
  });
}

export async function runWatchdogScan(apiKey: string): Promise<any> {
  return bilgeApiFetch<any>(apiKey, "/v1/watchdog/run", {
    method: "POST",
  });
}

export async function loadBilgeApiOpsSnapshot(apiKey: string): Promise<OpsSnapshot> {
  await verifyBilgeApiAccess(apiKey);
  const errors: string[] = [];

  const apiKeys = (await settle("api_keys", listBilgeApiKeys(apiKey), errors)) || [];
  const quotaUsage = (
    await Promise.all(
      apiKeys.slice(0, 30).map((key) => settle(`quota_usage:${key.id}`, getApiKeyQuotaUsage(apiKey, key.id), errors)),
    )
  ).filter((item): item is QuotaUsage => Boolean(item));

  const proposals = (await settle("proposals", listProposals(apiKey), errors)) || [];
  const draftGroups = await Promise.all(
    proposals.slice(0, 20).map((proposal) => settle(`draft_prs:${proposal.id}`, listDraftPrs(apiKey, proposal.id), errors)),
  );
  const drafts = draftGroups.flatMap((group) => group || []);

  const verificationGroups = await Promise.all(
    drafts.slice(0, 20).map((draft) => settle(`verification:${draft.id}`, getDraftVerification(apiKey, draft.id), errors)),
  );
  const verifications = verificationGroups.filter((item): item is PrVerificationRecord => Boolean(item));
  const aiSuggestionGroups = await Promise.all(
    drafts.slice(0, 20).map((draft) => settle(`ai_suggestions:${draft.id}`, listAiPatchSuggestions(apiKey, draft.id), errors)),
  );
  const aiSuggestions = aiSuggestionGroups.flatMap((group) => group || []);

  const releaseLatest = await settle("release_latest", getLatestReleaseCheck(apiKey), errors);
  const auditEvents = (await settle("audit_events", listAuditEvents(apiKey), errors)) || [];
  const ledgerRecent = (await settle("review_ledger", listReviewLedgerRecent(apiKey), errors)) || [];
  const remediationRunbooks = (await settle("remediation_runbooks", listRemediationRunbooks(apiKey), errors)) || [];
  const remediationAttempts = (await settle("remediation_attempts", listRemediationAttempts(apiKey), errors)) || [];
  const systemFindings = (await settle("system_findings", listWatchdogFindings(apiKey), errors)) || [];
  const watchdogStatus = await settle("watchdog_status", getWatchdogStatus(apiKey), errors);
  const managementGate = await settle("management_gate", getManagementGate(apiKey), errors);

  const agentPromotions = (await settle("agent_promotions", listAgentPromotions(apiKey), errors)) || [];
  const agentRuns = (await settle("agent_runs", listAgentRuns(apiKey), errors)) || [];
  const agentCapabilities = (await settle("agent_capabilities", listAgentCapabilities(apiKey), errors)) || [];

  return {
    apiKeys,
    quotaUsage,
    proposals,
    drafts,
    verifications,
    aiSuggestions,
    releaseLatest,
    auditEvents,
    ledgerRecent,
    remediationRunbooks,
    remediationAttempts,
    systemFindings,
    watchdogStatus,
    managementGate,
    agentPromotions,
    agentRuns,
    agentCapabilities,
    errors,
  };
}

export type AgentCapabilityRecord = {
  agent_key: string;
  agent_name: string;
  description: string;
  enabled: boolean;
  risk_level: string;
  sandbox_mode: string;
  max_cost_limit: number;
  requires_human_approval: boolean;
  network_policy: string;
  allowed_domains: string[];
  allowed_directories: string[];
  blocked_directories: string[];
  allowed_commands: string[];
  blocked_commands: string[];
};

export type AgentRunRecord = {
  run_id: string;
  agent_key: string;
  status: string;
  workspace_path?: string | null;
  exit_code?: number | null;
  cost: number;
  started_at?: string | null;
  completed_at?: string | null;
  sandbox_mode: string;
  network_policy: string;
  ledger_chain_id?: string | null;
};

export type AgentPromotionRecord = {
  promotion_id: string;
  run_id: string;
  artifact_type: string;
  sandbox_artifact_path: string;
  target_repo_path: string;
  artifact_hash: string;
  manifest_hash?: string | null;
  verified_artifact_hash?: string | null;
  approved_artifact_hash?: string | null;
  promoted_artifact_hash?: string | null;
  target_path_hash?: string | null;
  status: string;
  verification_score: number;
  verification_details: Record<string, any>;
  approved_by?: string | null;
  approved_at?: string | null;
  promoted_at?: string | null;
  ledger_event_hash?: string | null;
  created_at: string;
};

export type AgentPolicySimulationResponse = {
  decision: "ALLOW" | "BLOCK" | "HUMAN_GATE_REQUIRED";
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  reasons: string[];
  required_permissions: string[];
  blocked_actions: string[];
  ledger_context: Record<string, any>;
  simulation_result_hash?: string | null;
};

export async function listAgentCapabilities(_apiKey: string): Promise<AgentCapabilityRecord[]> {
  return agentApiFetch<AgentCapabilityRecord[]>("/capabilities");
}

export async function listAgentRuns(_apiKey: string): Promise<AgentRunRecord[]> {
  return agentApiFetch<AgentRunRecord[]>("/runs");
}

export async function getAgentRun(_apiKey: string, runId: string): Promise<AgentRunRecord> {
  return agentApiFetch<AgentRunRecord>(`/runs/${encodeURIComponent(runId)}`);
}

export async function retryAgentRun(
  _apiKey: string,
  runId: string,
): Promise<{ run_id: string; retried_from_run_id: string; success: boolean; output: string; workspace_path?: string | null }> {
  return agentApiFetch<{ run_id: string; retried_from_run_id: string; success: boolean; output: string; workspace_path?: string | null }>(
    `/runs/${encodeURIComponent(runId)}/retry`,
    { method: "POST" },
  );
}

export async function listAgentPromotions(_apiKey: string): Promise<AgentPromotionRecord[]> {
  return agentApiFetch<AgentPromotionRecord[]>("/promotions");
}

export async function getAgentPromotion(_apiKey: string, promotionId: string): Promise<AgentPromotionRecord> {
  return agentApiFetch<AgentPromotionRecord>(`/promotions/${encodeURIComponent(promotionId)}`);
}

export async function approveAgentPromotion(_apiKey: string, promotionId: string): Promise<{ status: string; message: string }> {
  return agentApiFetch<{ status: string; message: string }>(`/promotions/${encodeURIComponent(promotionId)}/approve`, {
    method: "POST"
  });
}

export async function rejectAgentPromotion(_apiKey: string, promotionId: string): Promise<{ status: string; message: string }> {
  return agentApiFetch<{ status: string; message: string }>(`/promotions/${encodeURIComponent(promotionId)}/reject`, {
    method: "POST"
  });
}

export async function executeAgentPromotion(_apiKey: string, promotionId: string): Promise<{ status: string; message: string }> {
  return agentApiFetch<{ status: string; message: string }>(`/promotions/${encodeURIComponent(promotionId)}/execute`, {
    method: "POST"
  });
}

export async function simulateAgentPromotion(_apiKey: string, promotionId: string): Promise<AgentPolicySimulationResponse> {
  return agentApiFetch<AgentPolicySimulationResponse>("/policy/simulate-promotion", {
    method: "POST",
    body: JSON.stringify({ promotion_id: promotionId })
  });
}

export async function simulateAgentRun(
  _apiKey: string,
  body: {
    agent_key: string;
    action_type: string;
    target_paths: string[];
    cost: number;
    network_request: boolean;
  }
): Promise<AgentPolicySimulationResponse> {
  return agentApiFetch<AgentPolicySimulationResponse>("/policy/simulate-run", {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export async function enableAgent(_apiKey: string, agentKey: string): Promise<{ status: string; message: string }> {
  return agentApiFetch<{ status: string; message: string }>(`/capabilities/${encodeURIComponent(agentKey)}/enable`, {
    method: "POST"
  });
}

export async function disableAgent(_apiKey: string, agentKey: string): Promise<{ status: string; message: string }> {
  return agentApiFetch<{ status: string; message: string }>(`/capabilities/${encodeURIComponent(agentKey)}/disable`, {
    method: "POST"
  });
}
