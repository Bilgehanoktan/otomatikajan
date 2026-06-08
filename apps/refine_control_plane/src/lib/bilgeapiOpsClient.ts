export const BILGEAPI_PROXY_BASE = "/bilgeapi";

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

export type OpsSnapshot = {
  apiKeys: ApiKeyRecord[];
  quotaUsage: QuotaUsage[];
  proposals: ProposalRecord[];
  drafts: PrDraftRecord[];
  verifications: PrVerificationRecord[];
  releaseLatest: ReleaseCheckRecord | null;
  auditEvents: AuditEventRecord[];
  ledgerRecent: ReviewLedgerEntryRecord[];
  errors: string[];
};

type JsonValue = Record<string, unknown> | Array<unknown>;

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
    throw new Error(await readError(response));
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
    throw new Error(await readError(response));
  }

  return response.text();
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

export async function loadBilgeApiOpsSnapshot(apiKey: string): Promise<OpsSnapshot> {
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

  const releaseLatest = await settle("release_latest", getLatestReleaseCheck(apiKey), errors);
  const auditEvents = (await settle("audit_events", listAuditEvents(apiKey), errors)) || [];
  const ledgerRecent = (await settle("review_ledger", listReviewLedgerRecent(apiKey), errors)) || [];

  return {
    apiKeys,
    quotaUsage,
    proposals,
    drafts,
    verifications,
    releaseLatest,
    auditEvents,
    ledgerRecent,
    errors,
  };
}
