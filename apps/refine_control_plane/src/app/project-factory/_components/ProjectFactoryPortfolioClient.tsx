"use client";

import React from "react";
import { 
  Row, Col, Card, Typography, Spin, notification, Button, Tag, Input, Select, Pagination, Tooltip, Tabs, List, Space
} from "antd";
import { 
  FolderArchive, Activity, ShieldAlert, CheckCircle, Clock, Search, Lock, ShieldCheck, ChevronRight, Brain, AlertTriangle, FileCode, Users, FileSignature, Zap, Check, X, Pause, RefreshCw
} from "lucide-react";
import Link from "next/link";

const { Title, Text } = Typography;
const { Option } = Select;

function getApiBaseUrl() {
  return "/api/v1";
}

async function safeFetchJson(url: string, options?: RequestInit) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    let msg = `HTTP ${res.status}`;
    try {
      const j = JSON.parse(text);
      if (j.detail) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function getAuthHeaders() {
  return {
    "X-Agent-Identity": JSON.stringify({
      agent_id: "human-operator",
      roles: ["governor.view", "governor.override"],
    }),
  };
}

export default function ProjectFactoryPortfolioClient() {
  const apiBase = React.useMemo(() => getApiBaseUrl(), []);
  
  const [loading, setLoading] = React.useState(true);
  const [metrics, setMetrics] = React.useState<any>(null);
  const [results, setResults] = React.useState<any[]>([]);
  const [total, setTotal] = React.useState(0);
  
  // Phase 14 states
  const [intelligence, setIntelligence] = React.useState<any>(null);
  const [intelLoading, setIntelLoading] = React.useState(false);
  
  // Phase 15 states
  const [policyProposals, setPolicyProposals] = React.useState<any[]>([]);
  const [policyLoading, setPolicyLoading] = React.useState(false);
  
  // Phase 16 states
  const [boardPackage, setBoardPackage] = React.useState<any>(null);
  const [boardLoading, setBoardLoading] = React.useState(false);
  const [applyPreviews, setApplyPreviews] = React.useState<any>({});
  const [prPlans, setPrPlans] = React.useState<any>({});
  const [evidenceManifests, setEvidenceManifests] = React.useState<any>({});
  
  // Phase 18 states
  const [prCreations, setPrCreations] = React.useState<any>({});
  const [prCreationLoading, setPrCreationLoading] = React.useState(false);

  // Phase 19 states
  const [prReviews, setPrReviews] = React.useState<any>({});
  const [reviewLoading, setReviewLoading] = React.useState(false);

  // Phase 20 states
  const [releaseManifests, setReleaseManifests] = React.useState<any>({});
  const [finalDecisionLoading, setFinalDecisionLoading] = React.useState(false);

  const [query, setQuery] = React.useState("");  const [status, setStatus] = React.useState<string | undefined>(undefined);
  const [riskLevel, setRiskLevel] = React.useState<string | undefined>(undefined);
  const [sort, setSort] = React.useState("updated_at_desc");
  const [page, setPage] = React.useState(1);
  const limit = 10;

  const loadData = React.useCallback(async () => {
    setLoading(true);
    try {
      const headers = await getAuthHeaders();
      const mRes = await safeFetchJson(`${apiBase}/project-factory/portfolio/metrics`, { headers });
      setMetrics(mRes.metrics);

      const offset = (page - 1) * limit;
      let url = `${apiBase}/project-factory/portfolio/search?sort=${sort}&limit=${limit}&offset=${offset}`;
      if (query) url += `&q=${encodeURIComponent(query)}`;
      if (status) url += `&status=${encodeURIComponent(status)}`;
      if (riskLevel) url += `&risk_level=${encodeURIComponent(riskLevel)}`;

      const sRes = await safeFetchJson(url, { headers });
      setResults(sRes.search_results.items || []);
      setTotal(sRes.search_results.total || 0);
      
      // Load intelligence
      try {
        const iRes = await safeFetchJson(`${apiBase}/project-factory/portfolio/intelligence`, { headers });
        if (iRes && iRes.intelligence) {
          setIntelligence(iRes.intelligence);
        }
      } catch (err) {
        console.log("No intelligence found yet.");
      }
      
      // Load policy proposals
      try {
        const pRes = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-autopilot`, { headers });
        if (pRes && pRes.proposals) {
          setPolicyProposals(pRes.proposals);
          // Try to fetch previews, pr plans, and manifests for each
          const previews: any = {};
          const plans: any = {};
          const manifests: any = {};
          const creations: any = {};
          const reviews: any = {};
          const relManifests: any = {};
          for (const p of pRes.proposals) {
              if (p.status === "POLICY_BOARD_APPROVED_FOR_PREVIEW" || p.status === "POLICY_APPLY_PREVIEW_READY" || p.status === "POLICY_DRAFT_PR_PLAN_READY" || p.status === "POLICY_GOVERNANCE_EVIDENCE_READY" || p.status === "POLICY_PR_PLAN_WAITING_APPROVAL" || p.status === "POLICY_DRAFT_PR_CREATED" || p.status === "POLICY_PR_CREATION_BLOCKED" || p.status === "POLICY_PR_CREATED_WAITING_REVIEW" || p.status === "POLICY_PR_REVIEW_PASSED" || p.status === "POLICY_PR_REVIEW_BLOCKED" || p.status === "POLICY_PR_REVIEW_REQUEST_CHANGES" || p.status === "POLICY_PR_REVIEW_DEFERRED" || p.status === "POLICY_READY_FOR_FINAL_DECISION" || p.status === "POLICY_LIFECYCLE_CLOSED") {
                  try {
                      const pr = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-board/${p.proposal_id}/apply-preview`, { headers });
                      if (pr && pr.preview) {
                          previews[p.proposal_id] = pr.preview;
                      }
                  } catch (e) { }
              }
              
              if (p.status === "POLICY_DRAFT_PR_PLAN_READY" || p.status === "POLICY_GOVERNANCE_EVIDENCE_READY" || p.status === "POLICY_PR_PLAN_WAITING_APPROVAL" || p.status === "POLICY_APPLY_PREVIEW_READY" || p.status === "POLICY_DRAFT_PR_CREATED" || p.status === "POLICY_PR_CREATION_BLOCKED" || p.status === "POLICY_PR_CREATED_WAITING_REVIEW" || p.status === "POLICY_PR_REVIEW_PASSED" || p.status === "POLICY_PR_REVIEW_BLOCKED" || p.status === "POLICY_PR_REVIEW_REQUEST_CHANGES" || p.status === "POLICY_PR_REVIEW_DEFERRED" || p.status === "POLICY_READY_FOR_FINAL_DECISION") {
                  try {
                      const pl = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-pr-plan/${p.proposal_id}`, { headers });
                      if (pl && pl.plan) {
                          plans[p.proposal_id] = pl.plan;
                      }
                  } catch (e) { }
                  try {
                      const mf = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-pr-plan/${p.proposal_id}/evidence-pack`, { headers });
                      if (mf && mf.manifest) {
                          manifests[p.proposal_id] = mf.manifest;
                      }
                  } catch (e) { }
              }
              
              if (p.status === "POLICY_DRAFT_PR_CREATED" || p.status === "POLICY_PR_CREATION_BLOCKED" || p.status === "POLICY_PR_CREATED_WAITING_REVIEW" || p.status === "POLICY_PR_CREATION_FAILED" || p.status === "POLICY_GOVERNANCE_EVIDENCE_READY" || p.status === "POLICY_PR_REVIEW_PASSED" || p.status === "POLICY_PR_REVIEW_BLOCKED" || p.status === "POLICY_PR_REVIEW_REQUEST_CHANGES" || p.status === "POLICY_PR_REVIEW_DEFERRED" || p.status === "POLICY_READY_FOR_FINAL_DECISION") {
                  try {
                      const cr = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-pr-plan/${p.proposal_id}/creation-status`, { headers });
                      if (cr && cr.creation_data) {
                          creations[p.proposal_id] = cr.creation_data;
                      }
                  } catch (e) { }
              }
              
              if (p.status === "POLICY_PR_CREATED_WAITING_REVIEW" || p.status === "POLICY_PR_REVIEW_PASSED" || p.status === "POLICY_PR_REVIEW_BLOCKED" || p.status === "POLICY_PR_REVIEW_REQUEST_CHANGES" || p.status === "POLICY_PR_REVIEW_DEFERRED" || p.status === "POLICY_READY_FOR_FINAL_DECISION" || p.status === "POLICY_LIFECYCLE_CLOSED") {
                  try {
                      const rv = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-pr-review/${p.proposal_id}`, { headers });
                      if (rv && rv.report) {
                          reviews[p.proposal_id] = rv.report;
                      }
                  } catch (e) { }
              }
              
              if (p.status === "POLICY_LIFECYCLE_CLOSED") {
                  try {
                      const rm = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-final/${p.proposal_id}/release-archive`, { headers });
                      if (rm && rm.manifest) {
                          relManifests[p.proposal_id] = rm.manifest;
                      }
                  } catch (e) { }
              }
          }
          setApplyPreviews(previews);
          setPrPlans(plans);
          setEvidenceManifests(manifests);
          setPrCreations(creations);
          setPrReviews(reviews);
          setReleaseManifests(relManifests);
        }
      } catch (err) {
        console.log("No policy proposals found yet.");
      }
      
      // Load board package
      try {
          const bpRes = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-board/package`, { headers });
          if (bpRes && bpRes.package) {
              setBoardPackage(bpRes.package);
          }
      } catch (err) {
          console.log("No board package found.");
      }
    } catch (err: any) {
      notification.error({ message: "Failed to load portfolio", description: err.message });
    } finally {
      setLoading(false);
    }
  }, [apiBase, page, limit, query, status, riskLevel, sort]);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRebuild = async () => {
    try {
      setLoading(true);
      const headers = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/archive-index/rebuild`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          operator_id: "PORTFOLIO-ADMIN",
          rationale: "Manual rebuild from UI"
        })
      });
      notification.success({ message: "Archive Index Rebuilt" });
      await loadData();
    } catch (err: any) {
      notification.error({ message: "Rebuild failed", description: err.message });
      setLoading(false);
    }
  };

  const handleRunIntelligence = async () => {
    try {
      setIntelLoading(true);
      const headers = await getAuthHeaders();
      const res = await safeFetchJson(`${apiBase}/project-factory/portfolio/intelligence/run`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          operator_id: "PORTFOLIO-ADMIN",
          rationale: "Run intelligence from UI"
        })
      });
      setIntelligence(res.intelligence);
      notification.success({ message: "Portfolio Intelligence Generated" });
    } catch (err: any) {
      notification.error({ message: "Intelligence Run Failed", description: err.message });
    } finally {
      setIntelLoading(false);
    }
  };

  const handlePublishSuggestions = async () => {
    try {
      setIntelLoading(true);
      const headers = await getAuthHeaders();
      const res = await safeFetchJson(`${apiBase}/project-factory/portfolio/intelligence/publish-ceo-suggestions`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          operator_id: "PORTFOLIO-ADMIN",
          rationale: "Publish CEO suggestions from UI"
        })
      });
      notification.success({ message: "CEO Suggestions Published", description: `${res.published_count} suggestions created.` });
    } catch (err: any) {
      notification.error({ message: "Publish Failed", description: err.message });
    } finally {
      setIntelLoading(false);
    }
  };

  const handleRunPolicyAutopilot = async () => {
    try {
      setPolicyLoading(true);
      const headers = await getAuthHeaders();
      const res = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-autopilot/run`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          operator_id: "PORTFOLIO-ADMIN",
          rationale: "Generate policy proposals from UI"
        })
      });
      if (res && res.proposals && res.proposals.proposals) {
        setPolicyProposals(res.proposals.proposals);
      }
      notification.success({ message: "Policy Proposals Generated" });
    } catch (err: any) {
      notification.error({ message: "Policy Autopilot Run Failed", description: err.message });
    } finally {
      setPolicyLoading(false);
    }
  };

  const handlePolicyDecision = async (proposalId: string, action: string) => {
    try {
      setPolicyLoading(true);
      const headers = await getAuthHeaders();
      let endpoint = "";
      const body: any = {
        operator_id: "PORTFOLIO-ADMIN",
        rationale: `UI action: ${action}`
      };
      
      if (action === "approve") {
        endpoint = "approve-for-policy-board";
        body.risk_acknowledgement = true;
      } else if (action === "defer") {
        endpoint = "defer";
      } else if (action === "reject") {
        endpoint = "reject";
      }

      await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-autopilot/${proposalId}/${endpoint}`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      
      notification.success({ message: `Proposal ${proposalId} ${action}d.` });
      // Reload proposals
      await loadData();
    } catch (err: any) {
      notification.error({ message: `Failed to ${action} proposal`, description: err.message });
    } finally {
      setPolicyLoading(false);
    }
  };

  const handleBoardDecision = async (proposalId: string, action: string) => {
    try {
      setBoardLoading(true);
      const headers = await getAuthHeaders();
      let endpoint = "";
      const body: any = {
        operator_id: "BOARD-OPERATOR-ID",
        rationale: `Board action: ${action}`
      };
      
      if (action === "approve") {
        endpoint = "approve-for-preview";
        body.risk_acknowledgement = true;
      } else if (action === "revision") {
        endpoint = "request-revision";
        body.revision_notes = "Revision requested via UI";
      } else if (action === "reject") {
        endpoint = "reject";
      }

      await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-board/${proposalId}/${endpoint}`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      
      notification.success({ message: `Board decision ${action} applied to ${proposalId}.` });
      await loadData();
    } catch (err: any) {
      notification.error({ message: `Failed to apply board decision`, description: err.message });
    } finally {
      setBoardLoading(false);
    }
  };

  const handleApplyPreview = async (proposalId: string) => {
    try {
      setBoardLoading(true);
      const headers = await getAuthHeaders();
      const res = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-board/${proposalId}/apply-preview`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" }
      });
      notification.success({ message: `Apply preview generated for ${proposalId}.` });
      
      // Update local preview state
      setApplyPreviews((prev: any) => ({
          ...prev,
          [proposalId]: res
      }));
      
      await loadData();
    } catch (err: any) {
      notification.error({ message: `Failed to generate apply preview`, description: err.message });
    } finally {
      setBoardLoading(false);
    }
  };

  const preparePolicyPrPlan = async (proposalId: string, title: string) => {
    try {
      setBoardLoading(true);
      const headers = await getAuthHeaders();
      const body = {
        operator_id: "BOARD-OPERATOR-ID",
        rationale: "Prepare policy draft PR plan from UI.",
        target_branch: "main",
        draft_title: `Policy PR: ${title}`,
        risk_acknowledgement: true
      };
      
      const res = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-pr-plan/${proposalId}/prepare`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      
      notification.success({ message: `Draft PR Plan prepared for ${proposalId}.` });
      await loadData();
    } catch (err: any) {
      notification.error({ message: `Failed to prepare Draft PR Plan`, description: err.message });
    } finally {
      setBoardLoading(false);
    }
  };

  const handleCreatePr = async (proposalId: string) => {
    try {
      setPrCreationLoading(true);
      const headers = await getAuthHeaders();
      const body = {
        operator_id: "PORTFOLIO-ADMIN",
        rationale: "Approved policy draft PR creation from governance evidence pack.",
        risk_acknowledgement: true,
        remote: "origin",
        mode: "safe_local_or_mock"
      };
      
      const res = await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-pr-plan/${proposalId}/create-pr`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      
      notification.success({ message: `Draft PR Creation executed for ${proposalId}.` });
      await loadData();
    } catch (err: any) {
      notification.error({ message: `Failed to create Draft PR`, description: err.message });
    } finally {
      setPrCreationLoading(false);
    }
  };

  const handleRunPrReview = async (proposalId: string) => {
    try {
      setReviewLoading(true);
      const headers = await getAuthHeaders();
      const body = {
        operator_id: "PORTFOLIO-ADMIN",
        rationale: "Run PR Review Gate from UI.",
        risk_acknowledgement: true
      };
      
      await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-pr-review/${proposalId}/run`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      
      notification.success({ message: `PR Review executed for ${proposalId}.` });
      await loadData();
    } catch (err: any) {
      notification.error({ message: `Failed to run PR Review`, description: err.message });
    } finally {
      setReviewLoading(false);
    }
  };

  const handleReviewDecision = async (proposalId: string, decision: string) => {
    try {
      setReviewLoading(true);
      const headers = await getAuthHeaders();
      const body = {
        operator_id: "PORTFOLIO-ADMIN",
        decision: decision,
        rationale: `Decision ${decision} from UI`,
        risk_acknowledgement: true
      };
      
      await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-pr-review/${proposalId}/decision`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      
      notification.success({ message: `Decision ${decision} applied for ${proposalId}.` });
      await loadData();
    } catch (err: any) {
      notification.error({ message: `Failed to apply decision`, description: err.message });
    } finally {
      setReviewLoading(false);
    }
  };

  const handleFinalDecision = async (proposalId: string, decision: 'approve' | 'reject' | 'request-revision') => {
    try {
      setFinalDecisionLoading(true);
      const headers = await getAuthHeaders();
      const body: any = {
        operator_id: "PORTFOLIO-ADMIN",
        rationale: `Final decision ${decision} from UI`,
      };
      
      if (decision === 'approve') {
          body.risk_acknowledgement = true;
      }
      if (decision === 'request-revision') {
          body.revision_notes = "Revision requested from UI.";
      }
      
      await safeFetchJson(`${apiBase}/project-factory/portfolio/policy-final/${proposalId}/${decision}`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      
      notification.success({ message: `Final decision ${decision} applied for ${proposalId}.` });
      await loadData();
    } catch (err: any) {
      notification.error({ message: `Failed to apply final decision`, description: err.message });
    } finally {
      setFinalDecisionLoading(false);
    }
  };

  const getStatusColor = (s: string) => {
    if (!s) return "default";
    if (s.includes("CLOSED") || s.includes("APPROVED")) return "success";
    if (s.includes("WAITING") || s.includes("READY")) return "processing";
    if (s.includes("BLOCKED") || s.includes("REJECTED")) return "error";
    if (s.includes("REVISION")) return "warning";
    return "default";
  };

  return (
    <div className="min-h-screen bg-[#060a12] p-8 font-sans text-gray-200">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                <FolderArchive className="h-6 w-6 text-cyan-400" />
              </div>
              <div>
                <Title level={2} className="!text-white !m-0 font-black tracking-tighter">
                  Project Factory Portfolio
                </Title>
                <Text className="text-gray-400 font-mono text-[10px] uppercase tracking-widest block mt-1">
                  Global Archive Index & Portfolio Metrics
                </Text>
              </div>
            </div>
          </div>
          <Button 
            type="primary" 
            onClick={handleRebuild}
            loading={loading}
            className="bg-cyan-600 hover:bg-cyan-500 border-none font-black uppercase tracking-widest text-[10px] px-6 h-10 rounded-xl shadow-[0_0_15px_rgba(6,182,212,0.4)]"
          >
            Rebuild Archive Index
          </Button>
        </div>

        {/* Metrics Strip */}
        {metrics && (
          <Row gutter={[16, 16]}>
            <Col xs={12} md={6}>
              <div className="bg-[#0b101a] border border-white/5 rounded-2xl p-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10"><FolderArchive size={40} /></div>
                <div className="text-gray-500 font-mono text-[10px] uppercase tracking-widest mb-1">Total Projects</div>
                <div className="text-3xl font-black text-white">{metrics.total_projects}</div>
              </div>
            </Col>
            <Col xs={12} md={6}>
              <div className="bg-[#0b101a] border border-white/5 rounded-2xl p-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10"><CheckCircle size={40} /></div>
                <div className="text-gray-500 font-mono text-[10px] uppercase tracking-widest mb-1">Closed & Archived</div>
                <div className="text-3xl font-black text-green-400">{metrics.by_status?.PROJECT_CLOSED || 0}</div>
              </div>
            </Col>
            <Col xs={12} md={6}>
              <div className="bg-[#0b101a] border border-white/5 rounded-2xl p-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10"><Clock size={40} /></div>
                <div className="text-gray-500 font-mono text-[10px] uppercase tracking-widest mb-1">Open Human Gates</div>
                <div className="text-3xl font-black text-blue-400">{metrics.open_human_gates}</div>
              </div>
            </Col>
            <Col xs={12} md={6}>
              <div className="bg-[#0b101a] border border-white/5 rounded-2xl p-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10"><ShieldAlert size={40} /></div>
                <div className="text-gray-500 font-mono text-[10px] uppercase tracking-widest mb-1">Blocked Pipelines</div>
                <div className="text-3xl font-black text-red-500">{metrics.blocked_count}</div>
              </div>
            </Col>
          </Row>
        )}

        {/* Intelligence Strip */}
        <Card className="bg-[#0b101a] border-white/5 rounded-3xl overflow-hidden shadow-2xl" styles={{ body: { padding: '24px' } }}>
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-3">
              <Brain className="text-purple-400" size={24} />
              <Title level={4} className="!text-white !m-0 font-black">Portfolio Intelligence</Title>
              {intelligence?.generated_at && (
                <Text className="text-gray-500 font-mono text-[10px] ml-2">Last run: {new Date(intelligence.generated_at).toLocaleString()}</Text>
              )}
            </div>
            <Space>
              <Button type="primary" onClick={handleRunIntelligence} loading={intelLoading} className="bg-purple-600 hover:bg-purple-500 border-none font-bold">
                Run Intelligence
              </Button>
              <Button type="default" onClick={handlePublishSuggestions} loading={intelLoading} className="bg-white/5 text-white border-white/10 hover:border-purple-400">
                Publish CEO Suggestions
              </Button>
            </Space>
          </div>
          
          {intelligence ? (
            <Tabs defaultActiveKey="1" className="custom-tabs">
              <Tabs.TabPane tab={<span><AlertTriangle size={14} className="inline mr-2"/>Risk Patterns</span>} key="1">
                <List
                  dataSource={intelligence.recurring_risks}
                  renderItem={(r: any) => (
                    <List.Item className="border-white/5">
                      <div className="w-full">
                        <div className="flex justify-between mb-1">
                          <Text className="text-white font-bold">{r.pattern}</Text>
                          <Tag color={r.severity === "HIGH" ? "error" : "warning"}>{r.severity}</Tag>
                        </div>
                        <Text className="text-gray-400 text-xs block mb-2">{r.recommended_action}</Text>
                        <div className="text-[10px] font-mono text-gray-500">
                          Occurrences: <span className="text-white">{r.count}</span> | Workflow: {r.suggested_workflow}
                        </div>
                      </div>
                    </List.Item>
                  )}
                />
              </Tabs.TabPane>
              
              <Tabs.TabPane tab={<span><FileCode size={14} className="inline mr-2"/>Templates</span>} key="2">
                <List
                  dataSource={intelligence.template_performance}
                  renderItem={(t: any) => (
                    <List.Item className="border-white/5">
                      <div className="w-full">
                        <Text className="text-cyan-400 font-bold mb-1 block">{t.template}</Text>
                        <Row gutter={[16,16]} className="text-[10px] font-mono text-gray-400">
                          <Col span={6}>Uses: <span className="text-white">{t.uses}</span></Col>
                          <Col span={6}>Success: <span className="text-white">{(t.success_rate*100).toFixed(0)}%</span></Col>
                          <Col span={6}>Avg Q-Score: <span className="text-white">{t.average_quality_score}</span></Col>
                          <Col span={6}>Avg R-Score: <span className="text-white">{t.average_risk_score}</span></Col>
                        </Row>
                      </div>
                    </List.Item>
                  )}
                />
              </Tabs.TabPane>

              <Tabs.TabPane tab={<span><Users size={14} className="inline mr-2"/>Agents</span>} key="3">
                <List
                  dataSource={intelligence.agent_performance}
                  renderItem={(a: any) => (
                    <List.Item className="border-white/5">
                      <div className="w-full">
                        <Text className="text-purple-400 font-bold mb-1 block">{a.agent}</Text>
                        <Row gutter={[16,16]} className="text-[10px] font-mono text-gray-400">
                          <Col span={6}>Uses: <span className="text-white">{a.uses}</span></Col>
                          <Col span={6}>Success: <span className="text-white">{(a.success_rate*100).toFixed(0)}%</span></Col>
                          <Col span={6}>Blocked: <span className="text-red-400">{a.blocked_count}</span></Col>
                          <Col span={6}>Issues: <span className="text-white">{a.common_failure_modes.join(", ") || "None"}</span></Col>
                        </Row>
                      </div>
                    </List.Item>
                  )}
                />
              </Tabs.TabPane>

              <Tabs.TabPane tab={<span><FileSignature size={14} className="inline mr-2"/>Recommendations</span>} key="4">
                <List
                  dataSource={intelligence.learning_recommendations}
                  renderItem={(l: any) => (
                    <List.Item className="border-white/5">
                      <div className="w-full">
                        <div className="flex justify-between mb-1">
                          <Text className="text-white font-bold">{l.title}</Text>
                          <Tag color="processing">{l.priority}</Tag>
                        </div>
                        <Text className="text-gray-400 text-[10px] font-mono block">
                          Target: {l.target} | Workflow: {l.suggested_workflow}
                        </Text>
                      </div>
                    </List.Item>
                  )}
                />
              </Tabs.TabPane>
            </Tabs>
          ) : (
            <div className="py-8 text-center text-gray-500 font-mono text-xs">
              No intelligence generated yet. Click Run Intelligence to analyze the portfolio.
            </div>
          )}
        </Card>

        {/* Policy Autopilot */}
        <Card className="bg-[#0b101a] border-white/5 rounded-3xl overflow-hidden shadow-2xl mb-8" 
          styles={{ body: { padding: '0' } }}
          title={
            <div className="flex items-center justify-between px-6 py-5 border-b border-white/5">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center">
                  <ShieldCheck size={16} className="text-indigo-400" />
                </div>
                <div>
                  <Title level={5} className="!m-0 !text-gray-200">Policy Autopilot Suggestions</Title>
                  <Text className="text-gray-500 text-xs">Advisory layer for policy modifications</Text>
                </div>
              </div>
              <Button 
                type="primary" 
                icon={<ShieldAlert size={14}/>} 
                onClick={handleRunPolicyAutopilot}
                loading={policyLoading}
                className="bg-indigo-500 hover:bg-indigo-400 border-none rounded-xl text-xs font-semibold h-8"
              >
                Run Policy Autopilot
              </Button>
            </div>
          }>
          {policyProposals.length > 0 ? (
            <List
              className="px-6 py-4"
              dataSource={policyProposals}
              renderItem={(p: any) => (
                <List.Item className="border-white/5 block">
                  <div className="w-full bg-black/40 rounded-xl p-4 border border-white/5">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <Text className="text-white font-bold">{p.title}</Text>
                          <Tag color={p.status.includes("APPROVED") ? "success" : p.status.includes("REJECTED") ? "error" : "processing"}>{p.status}</Tag>
                          <Tag color={p.risk_level === "HIGH" ? "error" : p.risk_level === "MEDIUM" ? "warning" : "success"}>{p.risk_level} RISK</Tag>
                        </div>
                        <Text className="text-gray-400 text-xs">{p.description}</Text>
                      </div>
                      <div className="flex gap-2">
                        {p.status === "POLICY_SUGGESTIONS_READY" || p.status === "POLICY_PROPOSAL_DRAFTED" ? (
                          <>
                            <Button size="small" type="primary" className="bg-green-600 hover:bg-green-500 border-none" icon={<Check size={14}/>} onClick={() => handlePolicyDecision(p.proposal_id, 'approve')}>Approve</Button>
                            <Button size="small" className="bg-yellow-600 hover:bg-yellow-500 border-none text-white" icon={<Pause size={14}/>} onClick={() => handlePolicyDecision(p.proposal_id, 'defer')}>Defer</Button>
                            <Button size="small" danger icon={<X size={14}/>} onClick={() => handlePolicyDecision(p.proposal_id, 'reject')}>Reject</Button>
                          </>
                        ) : (
                          <Text className="text-gray-500 text-xs italic">Decision made</Text>
                        )}
                      </div>
                    </div>
                    
                    <div className="mt-3 text-[10px] font-mono text-gray-400 grid grid-cols-2 gap-4">
                      <div>
                        <div className="mb-1 text-gray-500">Targets:</div>
                        {p.target_files.map((tf: string) => <div key={tf}>• {tf}</div>)}
                      </div>
                      <div>
                        <div className="mb-1 text-gray-500">Proposed Changes:</div>
                        {p.recommended_changes?.map((rc: any, idx: number) => (
                          <div key={idx}>• {rc.field}: {rc.add ? `+${rc.add.join(",")}` : "Update"}</div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="mt-3 pt-3 border-t border-white/5 flex gap-4 text-[10px]">
                      <div>Auto Apply: <span className={p.auto_apply_allowed ? "text-red-400" : "text-green-400"}>{p.auto_apply_allowed ? "YES" : "NO"}</span></div>
                      <div>Requires Human Gate: <span className={p.requires_human_gate ? "text-green-400" : "text-red-400"}>{p.requires_human_gate ? "YES" : "NO"}</span></div>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          ) : (
            <div className="py-8 text-center text-gray-500 font-mono text-xs">
              No policy proposals generated yet. Click Run Policy Autopilot.
            </div>
          )}
        </Card>

        {/* Phase 16: Policy Board Decision & Apply Preview */}
        <Card className="bg-[#0b101a] border-white/5 rounded-3xl overflow-hidden shadow-2xl" styles={{ body: { padding: '24px' } }}>
          <div className="flex justify-between items-center mb-6 border-b border-white/5 pb-4">
            <div>
              <div className="text-xl text-white font-mono flex items-center gap-3">
                <ShieldCheck className="text-indigo-400" size={24} />
                Policy Board Decision & Apply Preview
              </div>
              <div className="text-xs text-gray-500 font-mono mt-1">Review proposals, approve for preview, request revisions, or reject. Generate safe previews without applying to production.</div>
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={loadData}
                loading={boardLoading}
                className="bg-black/50 border-white/10 text-white hover:text-indigo-400 hover:border-indigo-500 h-10 rounded-xl font-mono text-xs flex items-center gap-2"
              >
                <RefreshCw size={14} /> Refresh Board
              </Button>
            </div>
          </div>

          <div className="mb-4 grid grid-cols-1 md:grid-cols-4 gap-4">
             <div className="bg-black/40 border border-white/5 rounded-xl p-4 flex flex-col justify-center">
                 <div className="text-gray-500 text-[10px] uppercase tracking-widest font-mono mb-1">Total Proposals</div>
                 <div className="text-2xl text-white font-mono">{boardPackage?.proposal_count || 0}</div>
             </div>
             <div className="bg-black/40 border border-indigo-500/30 rounded-xl p-4 flex flex-col justify-center">
                 <div className="text-gray-500 text-[10px] uppercase tracking-widest font-mono mb-1">Approved for Preview</div>
                 <div className="text-2xl text-indigo-400 font-mono">{boardPackage?.approved_for_preview || 0}</div>
             </div>
             <div className="bg-black/40 border border-cyan-500/30 rounded-xl p-4 flex flex-col justify-center">
                 <div className="text-gray-500 text-[10px] uppercase tracking-widest font-mono mb-1">Preview Ready</div>
                 <div className="text-2xl text-cyan-400 font-mono">{boardPackage?.preview_ready || 0}</div>
             </div>
             <div className="bg-black/40 border border-red-500/30 rounded-xl p-4 flex flex-col justify-center">
                 <div className="text-gray-500 text-[10px] uppercase tracking-widest font-mono mb-1">Blocked / Rejected</div>
                 <div className="text-2xl text-red-400 font-mono">{boardPackage?.blocked || 0}</div>
             </div>
          </div>

          {policyProposals.length > 0 ? (
            <List
              dataSource={policyProposals}
              renderItem={(p: any) => (
                <List.Item className="border-b border-white/5 last:border-0 p-0 py-4">
                  <div className="w-full">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <Tag color={getStatusColor(p.status)} className="font-mono text-[10px] m-0 border-0">{p.status}</Tag>
                        <span className="text-white font-mono text-sm">{p.proposal_id}</span>
                      </div>
                      <div className="flex gap-2">
                        {(p.status === "POLICY_PROPOSAL_DRAFTED" || p.status === "POLICY_SUGGESTIONS_READY") ? (
                          <>
                            <Button 
                              size="small" 
                              onClick={() => handleBoardDecision(p.proposal_id, "approve")}
                              loading={boardLoading}
                              className="bg-indigo-500/20 text-indigo-400 border-indigo-500/50 text-[10px] font-mono hover:bg-indigo-500/40"
                            >Approve for Preview</Button>
                            <Button 
                              size="small"
                              onClick={() => handleBoardDecision(p.proposal_id, "revision")}
                              loading={boardLoading}
                              className="bg-yellow-500/10 text-yellow-500 border-yellow-500/30 text-[10px] font-mono hover:bg-yellow-500/20"
                            >Request Revision</Button>
                            <Button 
                              size="small" 
                              onClick={() => handleBoardDecision(p.proposal_id, "reject")}
                              loading={boardLoading}
                              className="bg-red-500/10 text-red-500 border-red-500/30 text-[10px] font-mono hover:bg-red-500/20"
                            >Reject</Button>
                          </>
                        ) : p.status === "POLICY_BOARD_APPROVED_FOR_PREVIEW" ? (
                            <Button 
                              size="small" 
                              onClick={() => handleApplyPreview(p.proposal_id)}
                              loading={boardLoading}
                              className="bg-cyan-500/20 text-cyan-400 border-cyan-500/50 text-[10px] font-mono hover:bg-cyan-500/40"
                            >Run Apply Preview</Button>
                        ) : (
                          <Text className="text-gray-500 text-xs italic font-mono">Action taken</Text>
                        )}
                      </div>
                    </div>
                    
                    {applyPreviews[p.proposal_id] && (
                        <div className="mt-3 bg-[#070b14] border border-cyan-500/30 p-4 rounded-xl font-mono text-xs">
                           <div className="text-cyan-400 mb-2 font-bold uppercase tracking-wide text-[10px]">Apply Preview Results</div>
                           <div className="grid grid-cols-2 gap-4 mb-3">
                               <div>Production Apply Performed: <span className={applyPreviews[p.proposal_id].production_apply_performed ? "text-red-400" : "text-green-400"}>{String(applyPreviews[p.proposal_id].production_apply_performed)}</span></div>
                               <div>Policy Files Modified: <span className={applyPreviews[p.proposal_id].policy_files_modified ? "text-red-400" : "text-green-400"}>{String(applyPreviews[p.proposal_id].policy_files_modified)}</span></div>
                           </div>
                           <div className="text-gray-400 mb-1 mt-2">Preview Changes:</div>
                           {applyPreviews[p.proposal_id].preview_changes?.map((c: any, idx: number) => (
                               <div key={idx} className="pl-3 border-l border-white/10 ml-1 mb-1">
                                   <div className="text-white">{c.change_type} {c.target_file}</div>
                                   <div className="text-gray-500 pl-2">Field: {c.field} | Risk: {c.risk}</div>
                               </div>
                           ))}
                           {applyPreviews[p.proposal_id].blocking_risks?.length > 0 && (
                               <div className="mt-3 text-red-400">
                                   <div className="font-bold">Blocking Risks:</div>
                                   {applyPreviews[p.proposal_id].blocking_risks.map((r: string, idx: number) => <div key={idx}>- {r}</div>)}
                               </div>
                           )}
                        </div>
                    )}
                  </div>
                </List.Item>
              )}
            />
          ) : (
            <div className="py-8 text-center text-gray-500 font-mono text-xs">
              No policy board packages generated yet.
            </div>
          )}
        </Card>

        {/* Phase 17: Policy Draft PR Plan & Governance Evidence */}
        <Card className="bg-[#0b101a] border-white/5 rounded-3xl overflow-hidden shadow-2xl mb-8" styles={{ body: { padding: '24px' } }}>
          <div className="flex justify-between items-center mb-6 border-b border-white/5 pb-4">
            <div>
              <div className="text-xl text-white font-mono flex items-center gap-3">
                <ShieldCheck className="text-green-400" size={24} />
                Policy Draft PR Plan & Governance Evidence
              </div>
              <div className="text-xs text-gray-500 font-mono mt-1">Convert approved apply previews into a formal draft PR plan and collect governance evidence. No production modifications are made.</div>
            </div>
          </div>

          {Object.keys(applyPreviews).length > 0 ? (
             <div className="space-y-4">
               {policyProposals.filter(p => applyPreviews[p.proposal_id] != null).map((p: any) => (
                   <div key={`plan-${p.proposal_id}`} className="bg-[#070b14] border border-green-500/30 p-4 rounded-xl font-mono text-xs">
                       <div className="flex justify-between items-start mb-3">
                           <div>
                               <div className="text-green-400 font-bold uppercase tracking-wide text-sm mb-1">{p.proposal_id} - {p.title}</div>
                               <Tag color={getStatusColor(p.status)} className="m-0 border-0">{p.status}</Tag>
                           </div>
                           <div className="flex gap-2">
                               {p.status === "POLICY_APPLY_PREVIEW_READY" && (
                                   <Button 
                                      size="small" 
                                      onClick={() => preparePolicyPrPlan(p.proposal_id, p.title)}
                                      loading={boardLoading}
                                      className="bg-green-500/20 text-green-400 border-green-500/50 text-[10px] font-mono hover:bg-green-500/40"
                                    >Prepare Policy Draft PR Plan</Button>
                               )}
                           </div>
                       </div>
                       
                       {prPlans[p.proposal_id] && (
                           <div className="mt-4 border-t border-white/5 pt-4">
                               <div className="text-white font-bold mb-2">Draft PR Plan</div>
                               <div className="grid grid-cols-2 gap-4 text-gray-400">
                                   <div>Branch: <span className="text-green-400">{prPlans[p.proposal_id].branch_name}</span></div>
                                   <div>Target: <span className="text-white">{prPlans[p.proposal_id].target_branch}</span></div>
                                   <div>Git Operations Performed: <span className="text-green-400">{String(prPlans[p.proposal_id].git_operations_performed)}</span></div>
                                   <div>Policy Files Modified: <span className="text-green-400">{String(prPlans[p.proposal_id].policy_files_modified)}</span></div>
                               </div>
                               <div className="mt-2 text-gray-500">
                                   Title: {prPlans[p.proposal_id].draft_title}
                               </div>
                           </div>
                       )}
                       
                       {evidenceManifests[p.proposal_id] && (
                           <div className="mt-4 border-t border-white/5 pt-4">
                               <div className="text-white font-bold mb-2">Governance Evidence Pack</div>
                               <div className="flex gap-4 text-gray-400 mb-3">
                                   <div>Evidence Count: <span className="text-cyan-400 font-bold">{evidenceManifests[p.proposal_id].evidence_count} files</span></div>
                                   <div>Ready for Operator PR Creation: <span className="text-green-400">{String(evidenceManifests[p.proposal_id].ready_for_operator_pr_creation)}</span></div>
                               </div>
                               {evidenceManifests[p.proposal_id].ready_for_operator_pr_creation && p.status === "POLICY_GOVERNANCE_EVIDENCE_READY" && (
                                   <Button 
                                      size="small" 
                                      onClick={() => handleCreatePr(p.proposal_id)}
                                      loading={prCreationLoading}
                                      className="bg-indigo-500 hover:bg-indigo-400 border-none text-xs font-semibold h-8"
                                    >Execute Policy Draft PR Creation</Button>
                               )}
                           </div>
                       )}

                       {prCreations[p.proposal_id] && (
                            <div className="mt-4 border-t border-white/5 pt-4 bg-[#0a101f] p-4 rounded-xl border border-indigo-500/30">
                                <div className="text-indigo-400 font-bold mb-2">Draft PR Creation Result</div>
                                <div className="grid grid-cols-2 gap-4 text-gray-400">
                                    <div>Status: <Tag color={getStatusColor(prCreations[p.proposal_id].status)}>{prCreations[p.proposal_id].status}</Tag></div>
                                    <div>Branch: <span className="text-cyan-400">{prCreations[p.proposal_id].branch_name}</span></div>
                                    <div>PR URL: <a href={prCreations[p.proposal_id].pr_url} target="_blank" rel="noreferrer" className="text-indigo-400 underline">{prCreations[p.proposal_id].pr_url || "N/A"}</a></div>
                                    <div>Files Modified: <span className="text-green-400">{String(prCreations[p.proposal_id].policy_files_modified)}</span></div>
                                </div>
                                
                                {p.status === "POLICY_PR_CREATED_WAITING_REVIEW" && (
                                    <div className="mt-4 border-t border-white/10 pt-3 flex justify-end">
                                        <Button 
                                          size="small" 
                                          onClick={() => handleRunPrReview(p.proposal_id)}
                                          loading={reviewLoading}
                                          className="bg-purple-500 hover:bg-purple-400 border-none text-xs font-semibold h-8"
                                        >Run Policy PR Review Gate</Button>
                                    </div>
                                )}
                            </div>
                        )}
                        
                        {prReviews[p.proposal_id] && (
                            <div className="mt-4 border-t border-white/5 pt-4 bg-[#0a0515] p-4 rounded-xl border border-purple-500/30">
                                <div className="text-purple-400 font-bold mb-2 flex justify-between">
                                    <span>PR Review Report</span>
                                    <Tag color={getStatusColor(prReviews[p.proposal_id].status)}>{prReviews[p.proposal_id].status}</Tag>
                                </div>
                                <div className="grid grid-cols-2 gap-4 text-gray-400">
                                    <div>Safety Verified: <span className={prReviews[p.proposal_id].mesh_safety_verified ? "text-green-400" : "text-red-400"}>{String(prReviews[p.proposal_id].mesh_safety_verified)}</span></div>
                                    <div>Scorecard Score: <span className="text-yellow-400">{prReviews[p.proposal_id].scorecard?.total_score || 0}/100</span></div>
                                </div>
                                
                                {prReviews[p.proposal_id].blocking_findings && prReviews[p.proposal_id].blocking_findings.length > 0 && (
                                    <div className="mt-3 bg-red-900/20 border border-red-500/30 p-2 rounded text-red-300 text-xs">
                                        <div className="font-bold mb-1">Blocking Findings:</div>
                                        <ul className="list-disc pl-4">
                                            {prReviews[p.proposal_id].blocking_findings.map((f: string, i: number) => <li key={i}>{f}</li>)}
                                        </ul>
                                    </div>
                                )}
                                
                                {(p.status === "POLICY_PR_REVIEW_PASSED" || p.status === "POLICY_PR_REVIEW_BLOCKED") && (
                                    <div className="mt-4 border-t border-white/10 pt-3 flex gap-2 justify-end">
                                        <Button 
                                          size="small" 
                                          onClick={() => handleReviewDecision(p.proposal_id, "REQUEST_CHANGES")}
                                          loading={reviewLoading}
                                          className="bg-red-500/20 text-red-400 border-red-500/50 hover:bg-red-500/40 text-xs h-8"
                                        >Request Changes</Button>
                                        <Button 
                                          size="small" 
                                          onClick={() => handleReviewDecision(p.proposal_id, "DEFER")}
                                          loading={reviewLoading}
                                          className="bg-gray-700 hover:bg-gray-600 border-none text-xs h-8 text-white"
                                        >Defer</Button>
                                        <Button 
                                          size="small" 
                                          onClick={() => handleReviewDecision(p.proposal_id, "MARK_REVIEWED")}
                                          loading={reviewLoading}
                                          disabled={!prReviews[p.proposal_id].mesh_safety_verified}
                                          className="bg-green-500 hover:bg-green-400 border-none text-xs font-semibold h-8 text-black"
                                        >Mark Reviewed</Button>
                                    </div>
                                )}
                            </div>
                        )}
                   </div>
               ))}
             </div>
          ) : (
            <div className="py-8 text-center text-gray-500 font-mono text-xs">
              No apply previews available. Approve and run apply previews first.
            </div>
          )}
        </Card>

        <Card className="bg-[#0b101a] border-white/5 rounded-3xl overflow-hidden shadow-2xl" styles={{ body: { padding: '20px 24px' } }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} md={8}>
              <Input 
                prefix={<Search className="text-gray-500" size={16} />}
                placeholder="Search projects by ID, title, release..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                onPressEnter={() => setPage(1)}
                className="bg-black/50 border-white/10 text-white hover:border-cyan-500 focus:border-cyan-500 h-10 rounded-xl"
              />
            </Col>
            <Col xs={12} md={5}>
              <Select
                placeholder="Status"
                value={status}
                onChange={v => { setStatus(v); setPage(1); }}
                allowClear
                className="w-full h-10"
                popupClassName="bg-[#0b101a] border border-white/10 text-white"
              >
                <Option value="PROJECT_CLOSED">Closed</Option>
                <Option value="READY_FOR_FINAL_OPERATOR_DECISION">Final Gate</Option>
                <Option value="HUMAN_GATE_WAITING">Review Gate</Option>
                <Option value="REQUIREMENT_GATE_WAITING">Requirement Gate</Option>
                <Option value="PR_CREATION_BLOCKED">Blocked</Option>
              </Select>
            </Col>
            <Col xs={12} md={4}>
              <Select
                placeholder="Risk"
                value={riskLevel}
                onChange={v => { setRiskLevel(v); setPage(1); }}
                allowClear
                className="w-full h-10"
              >
                <Option value="LOW">Low</Option>
                <Option value="MEDIUM">Medium</Option>
                <Option value="HIGH">High</Option>
              </Select>
            </Col>
            <Col xs={12} md={5}>
              <Select
                value={sort}
                onChange={v => { setSort(v); setPage(1); }}
                className="w-full h-10"
              >
                <Option value="updated_at_desc">Recent First</Option>
                <Option value="updated_at_asc">Oldest First</Option>
                <Option value="quality_score_desc">Highest Quality</Option>
                <Option value="risk_score_desc">Highest Risk</Option>
              </Select>
            </Col>
            <Col xs={12} md={2}>
              <Button type="primary" onClick={loadData} className="w-full h-10 bg-cyan-600 border-none rounded-xl font-bold">
                Apply
              </Button>
            </Col>
          </Row>
        </Card>

        {/* Results */}
        <div className="space-y-4 relative min-h-[400px]">
          {loading && (
            <div className="absolute inset-0 bg-[#060a12]/50 backdrop-blur-sm z-10 flex items-center justify-center rounded-3xl">
              <Spin size="large" />
            </div>
          )}

          {results.length === 0 && !loading ? (
            <div className="py-20 text-center bg-[#0b101a] rounded-3xl border border-white/5">
              <FolderArchive className="h-12 w-12 text-gray-700 mx-auto mb-4" />
              <div className="text-sm font-black uppercase tracking-widest text-gray-400">No Projects Found</div>
              <div className="text-[11px] text-gray-600 mt-2">Adjust your filters or rebuild the archive index.</div>
            </div>
          ) : (
            results.map((project) => (
              <div key={project.project_id} className="bg-[#0b101a] border border-white/5 rounded-2xl p-5 hover:border-cyan-500/30 transition-colors group relative overflow-hidden">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                  
                  {/* Left Block */}
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-cyan-400 font-bold text-sm">{project.project_id}</span>
                      <Tag color={getStatusColor(project.status)} className="m-0 font-black uppercase text-[9px] px-2 py-0.5 rounded-lg border-white/10">
                        {project.status.replace(/_/g, " ")}
                      </Tag>
                      {project.risk_level === "HIGH" && (
                        <Tag color="error" className="m-0 font-black uppercase text-[9px] px-2 py-0.5 rounded-lg border-white/10"><ShieldAlert size={10} className="inline mr-1" />HIGH RISK</Tag>
                      )}
                    </div>
                    <div className="text-xl font-black text-white tracking-tight leading-tight">
                      {project.title}
                    </div>
                    <div className="flex items-center gap-4 font-mono text-[9px] text-gray-500 uppercase tracking-wider pt-2">
                      <span>Updated: {new Date(project.updated_at).toLocaleString()}</span>
                      {project.quality_score !== null && (
                        <span><span className="text-gray-600">Q-Score:</span> <span className={project.quality_score > 80 ? "text-green-400" : "text-amber-400"}>{project.quality_score}</span></span>
                      )}
                      {project.risk_score !== null && (
                        <span><span className="text-gray-600">R-Score:</span> <span className={project.risk_score > 20 ? "text-red-400" : "text-white"}>{project.risk_score}</span></span>
                      )}
                    </div>
                  </div>

                  {/* Right Block */}
                  <div className="flex items-center gap-6 self-stretch">
                    {project.release_id && (
                      <div className="text-right hidden md:block">
                        <div className="font-mono text-[9px] text-gray-500 uppercase tracking-widest mb-1">Release Archive</div>
                        <div className="font-mono font-bold text-green-400 flex items-center justify-end gap-1 text-[11px]">
                          <ShieldCheck size={12} /> {project.release_id}
                        </div>
                      </div>
                    )}
                    
                    <div className="border-l border-white/5 pl-6 flex items-center justify-center">
                      <Link href={`/project-factory/${project.project_id}`}>
                        <Button 
                          type="text" 
                          className="bg-white/5 hover:bg-cyan-500/20 text-white border border-white/10 hover:border-cyan-500/50 h-12 w-12 rounded-xl flex items-center justify-center transition-all group-hover:bg-cyan-500 group-hover:border-cyan-400 group-hover:shadow-[0_0_15px_rgba(6,182,212,0.4)]"
                        >
                          <ChevronRight size={20} className="group-hover:text-black" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                  
                </div>
              </div>
            ))
          )}

          {total > limit && (
            <div className="flex justify-center pt-8">
              <Pagination
                current={page}
                pageSize={limit}
                total={total}
                onChange={p => setPage(p)}
                showSizeChanger={false}
              />
            </div>
          )}
        </div>

        {/* Phase 20: Final Policy Release Archive */}
        <Card className="bg-[#0b101a] border-white/5 rounded-3xl overflow-hidden shadow-2xl mb-8" styles={{ body: { padding: '24px' } }}>
          <div className="flex justify-between items-center mb-6 border-b border-white/5 pb-4">
            <div>
              <div className="text-xl text-white font-mono flex items-center gap-3">
                <FolderArchive className="text-pink-400" size={24} />
                Final Policy Release Archive
              </div>
              <div className="text-xs text-gray-500 font-mono mt-1">Final closure of the policy lifecycle. Generates secure release archive and learning memory sync without applying to production.</div>
            </div>
          </div>

          {policyProposals.filter(p => p.status === "POLICY_READY_FOR_FINAL_DECISION" || p.status === "POLICY_LIFECYCLE_CLOSED" || p.status === "FINAL_POLICY_REJECTED" || p.status === "FINAL_POLICY_REVISION_REQUESTED").length > 0 ? (
             <div className="space-y-4">
               {policyProposals.filter(p => p.status === "POLICY_READY_FOR_FINAL_DECISION" || p.status === "POLICY_LIFECYCLE_CLOSED" || p.status === "FINAL_POLICY_REJECTED" || p.status === "FINAL_POLICY_REVISION_REQUESTED").map((p: any) => (
                   <div key={`final-${p.proposal_id}`} className="bg-[#070b14] border border-pink-500/30 p-4 rounded-xl font-mono text-xs">
                       <div className="flex justify-between items-start mb-3">
                           <div>
                               <div className="text-pink-400 font-bold uppercase tracking-wide text-sm mb-1">{p.proposal_id} - {p.title}</div>
                               <Tag color={getStatusColor(p.status)} className="m-0 border-0">{p.status}</Tag>
                           </div>
                           
                           {p.status === "POLICY_READY_FOR_FINAL_DECISION" && (
                               <div className="flex gap-2">
                                   <Button 
                                      size="small" 
                                      onClick={() => handleFinalDecision(p.proposal_id, 'request-revision')}
                                      loading={finalDecisionLoading}
                                      className="bg-yellow-500/10 text-yellow-500 border-yellow-500/30 text-[10px] font-mono hover:bg-yellow-500/20"
                                    >Request Revision</Button>
                                   <Button 
                                      size="small" 
                                      onClick={() => handleFinalDecision(p.proposal_id, 'reject')}
                                      loading={finalDecisionLoading}
                                      className="bg-red-500/10 text-red-500 border-red-500/30 text-[10px] font-mono hover:bg-red-500/20"
                                    >Reject</Button>
                                    <Button 
                                      size="small" 
                                      onClick={() => handleFinalDecision(p.proposal_id, 'approve')}
                                      loading={finalDecisionLoading}
                                      className="bg-pink-500/20 text-pink-400 border-pink-500/50 text-[10px] font-mono hover:bg-pink-500/40"
                                    >Final Approve Policy</Button>
                               </div>
                           )}
                       </div>
                       
                       {releaseManifests[p.proposal_id] && (
                            <div className="mt-4 border-t border-white/5 pt-4 bg-[#0a0515] p-4 rounded-xl border border-pink-500/30">
                                <div className="text-pink-400 font-bold mb-2 flex justify-between">
                                    <span>Policy Release Archive Generated</span>
                                    <Tag color="success">LIFECYCLE CLOSED</Tag>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-gray-400 mb-3">
                                    <div>Release ID: <span className="text-cyan-400 font-bold">{releaseManifests[p.proposal_id].release_id}</span></div>
                                    <div>Evidence Count: <span className="text-white">{releaseManifests[p.proposal_id].evidence_count} files</span></div>
                                    <div>Learning Synced: <span className="text-green-400">{String(releaseManifests[p.proposal_id].learning_memory_synced)}</span></div>
                                    <div>Final Decision: <span className="text-pink-400">{releaseManifests[p.proposal_id].final_decision}</span></div>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-[10px] text-gray-500">
                                    <div>Production Apply: <span className="text-green-400">{String(releaseManifests[p.proposal_id].production_apply_performed)}</span></div>
                                    <div>Policy Modified: <span className="text-green-400">{String(releaseManifests[p.proposal_id].policy_files_modified)}</span></div>
                                    <div>Merge Performed: <span className="text-green-400">{String(releaseManifests[p.proposal_id].merge_performed)}</span></div>
                                    <div>Deploy Performed: <span className="text-green-400">{String(releaseManifests[p.proposal_id].deploy_performed)}</span></div>
                                </div>
                            </div>
                        )}
                   </div>
               ))}
             </div>
          ) : (
            <div className="py-8 text-center text-gray-500 font-mono text-xs">
              No policies ready for final decision yet. Complete PR Review Gate first.
            </div>
          )}
        </Card>

      </div>
    </div>
  );
}
