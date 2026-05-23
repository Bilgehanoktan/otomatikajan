"use client";

import React from "react";
import {
    App as AntdApp,
    Button,
    Card,
    Col,
    Divider,
    Input,
    Row,
    Space,
    Tag,
    Typography,
    Checkbox,
    Radio,
    Alert,
} from "antd";
import { useNavigation } from "@refinedev/core";
import {
    ArrowLeft,
    CheckCircle2,
    AlertTriangle,
    FileText,
    Database,
    Lock,
    ShieldAlert,
    RotateCcw,
    FileCode,
    Cpu,
    Check,
    X,
    FileCheck,
    ExternalLink,
    Play,
    StopCircle,
    RefreshCw,
    Terminal,
    ListTodo,
    Activity,
    FileArchive,
    ShieldCheck,
} from "lucide-react";
import { safeFetchJson } from "@/lib/api";
import { getAuthHeaders } from "@/lib/auth";
import { getApiBaseUrl } from "@/lib/runtime";

const { Title, Text, Paragraph } = Typography;

interface ProjectBrief {
  project_id: string;
  source_suggestion_id: string;
  audit_run_id: string;
  title: string;
  problem_statement: string;
  recommended_action: string;
  affected_files: string[];
  suggested_scope: string;
  status: string;
  requires_operator_approval: boolean;
}

interface RequirementGate {
  gate: string;
  status: string;
  allowed_actions: string[];
  implementation_allowed: boolean;
  sandbox_ready: boolean;
  approved_by?: string | null;
  rationale?: string | null;
  resolved_at?: string | null;
  scope_adjustments?: string | null;
}

interface SandboxManifest {
  project_id: string;
  created_at: string;
  status: string;
  sandbox_path: string;
  copied_files: string[];
  skipped_files: Array<{ path: string; reason: string }>;
  placeholder_files: string[];
}

interface GateDecision {
  decision_id: string;
  project_id: string;
  action: string;
  operator_id: string;
  rationale: string;
  created_at: string;
  details?: Record<string, any>;
}

interface ProjectFactoryArtifacts {
  status: string;
  project_brief: ProjectBrief;
  requirement_gate: RequirementGate;
  sandbox_manifest?: SandboxManifest | null;
  decisions: GateDecision[];
}

interface TaskItem {
  task_id: string;
  description: string;
  status: string;
  estimated_minutes: number;
}

interface ImplementationEvent {
  event_id: string;
  project_id: string;
  event_type: string;
  timestamp: string;
  message: string;
  details?: Record<string, any> | null;
}

interface ImplementationRun {
  project_id: string;
  status: string;
  runner_mode: string;
  sandbox_path: string;
  started_by: string;
  started_at: string;
  completed_at: string | null;
  changed_files: string[];
  generated_files: string[];
  test_status: string;
}

interface VerificationReport {
  status: string;
  stdout: string;
  stderr: string;
  duration_seconds: number;
  error?: string | null;
}

interface CandidateFile {
  path: string;
  checksum: string;
  size_bytes: number;
}

interface CandidateManifest {
  project_id: string;
  candidate_id: string;
  status: string;
  files: CandidateFile[];
  tests: {
    status: string;
    commands: string[];
  };
  known_limitations: string[];
  requires_human_gate: boolean;
}

interface QualityScorecard {
  candidate_manifest_exists: boolean;
  verification_report_passed: boolean;
  sandbox_boundary_respected: boolean;
  score: number;
  max_score: number;
  passed: boolean;
}

interface RiskAssessment {
  risk_score: number;
  risk_level: string;
  blocking_risks: string[];
  warnings: string[];
}

interface CandidateReview {
  project_id: string;
  candidate_id: string;
  status: string;
  quality_score: number;
  risk_score: number;
  risk_level: string;
  limitations: string[];
  recommendations: string[];
  reviewed_at: string;
}

interface DeliveryFile {
  path: string;
  size_bytes: number;
  checksum: string;
}

interface DeliveryManifest {
  project_id: string;
  delivery_id: string;
  created_at: string;
  operator_id: string;
  files: DeliveryFile[];
  production_apply_allowed: boolean;
}

interface DeliveryDecisionLog {
  decision_id: string;
  project_id: string;
  action: string;
  operator_id: string;
  rationale: string;
  created_at: string;
  details?: Record<string, any>;
}

interface FinalOperatorDecision {
  project_id: string;
  decision: string;
  operator_id: string;
  rationale: string;
  risk_acknowledgement: boolean;
  release_id: string;
  revision_notes?: string | null;
  resolved_at?: string;
}

interface ReleaseManifest {
  project_id: string;
  release_id: string;
  status: string;
  final_decision: string;
  approved_by: string;
  production_apply_performed: boolean;
  merge_performed: boolean;
  deploy_performed: boolean;
  evidence_count: number;
  closure_report: string;
}

interface FinalDecisionLog {
  decision_id: string;
  project_id: string;
  action: string;
  operator_id: string;
  rationale: string;
  created_at: string;
  details?: Record<string, any>;
}

type ProjectFactoryClientProps = {
  projectId: string;
};

export default function ProjectFactoryClient({ projectId }: ProjectFactoryClientProps) {
  const { notification } = AntdApp.useApp();
  const { list } = useNavigation();
  
  const [data, setData] = React.useState<ProjectFactoryArtifacts | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isError, setIsError] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  
  // Operator inputs
  const [operatorId, setOperatorId] = React.useState("OPERATOR-01");
  const [rationale, setRationale] = React.useState("");
  const [approvedScope, setApprovedScope] = React.useState("mvp");
  const [riskAcknowledged, setRiskAcknowledged] = React.useState(false);
  const [revisionNotes, setRevisionNotes] = React.useState("");
  const [activeTab, setActiveTab] = React.useState<"approve" | "revision" | "reject">("approve");

  // Phase 7 States
  const [implRun, setImplRun] = React.useState<ImplementationRun | null>(null);
  const [taskBreakdown, setTaskBreakdown] = React.useState<TaskItem[]>([]);
  const [logs, setLogs] = React.useState<ImplementationEvent[]>([]);
  const [verificationReport, setVerificationReport] = React.useState<VerificationReport | null>(null);
  const [candidateManifest, setCandidateManifest] = React.useState<CandidateManifest | null>(null);
  const [isLoadingImpl, setIsLoadingImpl] = React.useState(false);

  const [runnerMode, setRunnerMode] = React.useState("template_first");
  const [implRationale, setImplRationale] = React.useState("Scope approved, begin sandbox implementation.");
  const [implRiskAcknowledged, setImplRiskAcknowledged] = React.useState(true);
  const [implActiveTab, setImplActiveTab] = React.useState<"control" | "breakdown" | "reports" | "candidate" | "telemetry">("control");

  // Phase 8 States
  const [candidateReview, setCandidateReview] = React.useState<CandidateReview | null>(null);
  const [qualityScorecard, setQualityScorecard] = React.useState<QualityScorecard | null>(null);
  const [riskAssessment, setRiskAssessment] = React.useState<RiskAssessment | null>(null);
  const [deliveryManifest, setDeliveryManifest] = React.useState<DeliveryManifest | null>(null);
  const [releaseNotes, setReleaseNotes] = React.useState<string>("");
  const [deliveryLogs, setDeliveryLogs] = React.useState<DeliveryDecisionLog[]>([]);

  // Phase 8 Interactive states
  const [reviewActiveTab, setReviewActiveTab] = React.useState<"details" | "risk" | "quality" | "decision" | "delivery">("details");
  const [gateOperatorId, setGateOperatorId] = React.useState("OPERATOR-01");
  const [gateRationale, setGateRationale] = React.useState("");
  const [gateRiskAcknowledged, setGateRiskAcknowledged] = React.useState(false);
  const [gateRevisionNotes, setGateRevisionNotes] = React.useState("");
  const [gateActiveActionTab, setGateActiveActionTab] = React.useState<"approve" | "revision" | "reject">("approve");

  // Phase 12 States
  const [finalDecision, setFinalDecision] = React.useState<FinalOperatorDecision | null>(null);
  const [releaseManifest, setReleaseManifest] = React.useState<ReleaseManifest | null>(null);
  const [closureReport, setClosureReport] = React.useState<string>("");
  const [finalDecisionLogs, setFinalDecisionLogs] = React.useState<FinalDecisionLog[]>([]);

  // Phase 12 Interactive states
  const [finalOperatorId, setFinalOperatorId] = React.useState("OPERATOR-01");
  const [finalRationale, setFinalRationale] = React.useState("");
  const [finalRiskAcknowledged, setFinalRiskAcknowledged] = React.useState(false);
  const [finalRevisionNotes, setFinalRevisionNotes] = React.useState("");
  const [finalActiveActionTab, setFinalActiveActionTab] = React.useState<"decision" | "archive">("decision");

  const apiBase = React.useMemo(() => getApiBaseUrl(), []);

  const loadData = React.useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    try {
      const authHeaders = await getAuthHeaders();
      const res = await safeFetchJson<ProjectFactoryArtifacts>(
        `${apiBase}/project-factory/${projectId}/artifacts`,
        {
          headers: authHeaders,
          useOfflineFallback: false,
        }
      );
      setData(res);

      if (res.requirement_gate.status !== "WAITING_FOR_OPERATOR") {
        setIsLoadingImpl(true);
        // Load status, breakdown, events
        try {
          const statusRes = await safeFetchJson<{
            implementation_run: ImplementationRun;
            task_breakdown: TaskItem[];
            events: ImplementationEvent[];
          }>(`${apiBase}/project-factory/${projectId}/implementation/status`, {
            headers: authHeaders,
            useOfflineFallback: false,
          });
          if (statusRes) {
            setImplRun(statusRes.implementation_run);
            setTaskBreakdown(statusRes.task_breakdown || []);
            setLogs(statusRes.events || []);
          }
        } catch (err) {
          console.log("[ProjectFactory] Implementation status fetch failed or not running:", err);
          setImplRun(null);
          setTaskBreakdown([]);
          setLogs([]);
        }

        // Load verification report
        try {
          const reportRes = await safeFetchJson<{
            verification_report: VerificationReport;
          }>(`${apiBase}/project-factory/${projectId}/implementation/report`, {
            headers: authHeaders,
            useOfflineFallback: false,
          });
          if (reportRes) {
            setVerificationReport(reportRes.verification_report);
          }
        } catch (err) {
          console.log("[ProjectFactory] Verification report fetch failed:", err);
          setVerificationReport(null);
        }

        // Load candidate package manifest
        try {
          const candRes = await safeFetchJson<{
            candidate_manifest: CandidateManifest;
          }>(`${apiBase}/project-factory/${projectId}/candidate-package`, {
            headers: authHeaders,
            useOfflineFallback: false,
          });
          if (candRes) {
            setCandidateManifest(candRes.candidate_manifest);
          }
        } catch (err) {
          console.log("[ProjectFactory] Candidate package fetch failed:", err);
          setCandidateManifest(null);
        }

        // Load candidate review details
        try {
          const revRes = await safeFetchJson<{
            candidate_review: CandidateReview;
            quality_scorecard: QualityScorecard;
            risk_assessment: RiskAssessment;
          }>(`${apiBase}/project-factory/${projectId}/candidate/review`, {
            headers: authHeaders,
            useOfflineFallback: false,
          });
          if (revRes) {
            setCandidateReview(revRes.candidate_review);
            setQualityScorecard(revRes.quality_scorecard);
            setRiskAssessment(revRes.risk_assessment);
          }
        } catch (err) {
          console.log("[ProjectFactory] Candidate review fetch failed:", err);
          setCandidateReview(null);
          setQualityScorecard(null);
          setRiskAssessment(null);
        }

        // Load delivery package details
        try {
          const delRes = await safeFetchJson<{
            delivery_manifest: DeliveryManifest;
            release_notes: string;
          }>(`${apiBase}/project-factory/${projectId}/delivery-package`, {
            headers: authHeaders,
            useOfflineFallback: false,
          });
          if (delRes) {
            setDeliveryManifest(delRes.delivery_manifest);
            setReleaseNotes(delRes.release_notes);
          }
        } catch (err) {
          console.log("[ProjectFactory] Delivery package fetch failed:", err);
          setDeliveryManifest(null);
          setReleaseNotes("");
        }

        // Load delivery decision logs
        try {
          const logRes = await safeFetchJson<{
            logs: DeliveryDecisionLog[];
          }>(`${apiBase}/project-factory/${projectId}/delivery/logs`, {
            headers: authHeaders,
            useOfflineFallback: false,
          });
          if (logRes) {
            setDeliveryLogs(logRes.logs || []);
          }
        } catch (err) {
          console.log("[ProjectFactory] Delivery logs fetch failed:", err);
          setDeliveryLogs([]);
        }

        // Phase 12: Load final decision details if past Phase 11
        const briefStatus = res.project_brief.status;
        const finalStatuses = [
          "READY_FOR_FINAL_OPERATOR_DECISION",
          "FINAL_APPROVED",
          "FINAL_REJECTED",
          "FINAL_REVISION_REQUESTED",
          "PROJECT_CLOSED",
        ];
        if (finalStatuses.includes(briefStatus)) {
          try {
            const finalRes = await safeFetchJson<{
              final_decision: FinalOperatorDecision;
            }>(`${apiBase}/project-factory/${projectId}/final-decision`, {
              headers: authHeaders,
              useOfflineFallback: false,
            });
            if (finalRes) {
              setFinalDecision(finalRes.final_decision);
            }
          } catch (err) {
            console.log("[ProjectFactory] Final decision fetch failed:", err);
            setFinalDecision(null);
          }

          try {
            const relRes = await safeFetchJson<{
              release_manifest: ReleaseManifest;
              closure_report: string;
            }>(`${apiBase}/project-factory/${projectId}/release-archive`, {
              headers: authHeaders,
              useOfflineFallback: false,
            });
            if (relRes) {
              setReleaseManifest(relRes.release_manifest);
              setClosureReport(relRes.closure_report);
            }
          } catch (err) {
            console.log("[ProjectFactory] Release archive fetch failed:", err);
            setReleaseManifest(null);
            setClosureReport("");
          }

          try {
            const fLogRes = await safeFetchJson<{
              logs: FinalDecisionLog[];
            }>(`${apiBase}/project-factory/${projectId}/release-archive/logs`, {
              headers: authHeaders,
              useOfflineFallback: false,
            });
            if (fLogRes) {
              setFinalDecisionLogs(fLogRes.logs || []);
            }
          } catch (err) {
            console.log("[ProjectFactory] Final decision logs fetch failed:", err);
            setFinalDecisionLogs([]);
          }
        }

        setIsLoadingImpl(false);
      }
    } catch (err) {
      console.error("[ProjectFactory] Load error:", err);
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  }, [apiBase, projectId]);

  React.useEffect(() => {
    if (projectId) {
      void loadData();
    }
  }, [projectId, loadData]);

  React.useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (implRun && (implRun.status === "IMPLEMENTATION_RUNNING" || implRun.status === "IMPLEMENTATION_READY")) {
      interval = setInterval(() => {
        void loadData();
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [implRun, loadData]);

  const handleApproveScope = async () => {
    if (!operatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (rationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }
    if (!riskAcknowledged) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Yapısal sınır riskini onaylamanız gerekiyor." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/requirement-gate/approve-scope`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: operatorId,
          rationale: rationale,
          approved_scope: approvedScope,
          risk_acknowledgement: riskAcknowledged,
        }),
      });

      notification.success({
        message: "Scope Approved",
        description: "The project scope has been approved and the sandbox folder scaffolded successfully.",
      });
      // Clear inputs
      setRationale("");
      setRiskAcknowledged(false);
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to approve scope.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestRevision = async () => {
    if (!operatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (rationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }
    if (!revisionNotes.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Revizyon notları zorunludur." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/requirement-gate/request-revision`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: operatorId,
          rationale: rationale,
          revision_notes: revisionNotes,
        }),
      });

      notification.success({
        message: "Revision Requested",
        description: "Scope revision request has been logged and the gate status updated.",
      });
      // Clear inputs
      setRationale("");
      setRevisionNotes("");
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to request revision.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!operatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (rationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/requirement-gate/reject`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: operatorId,
          rationale: rationale,
        }),
      });

      notification.success({
        message: "Intake reddedildi",
        description: "The project intake has been rejected and the gate closed.",
      });
      setRationale("");
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to reject intake.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartImplementation = async () => {
    if (!operatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (implRationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }
    if (!implRiskAcknowledged) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Güvenlik riskini onaylamanız gerekiyor." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/implementation/start`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: operatorId,
          rationale: implRationale,
          runner_mode: runnerMode,
          risk_acknowledgement: implRiskAcknowledged,
        }),
      });

      notification.success({
        message: "Implementation Started",
        description: "Sandbox implementation runner completed successfully.",
      });
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to start sandbox implementation.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelImplementation = async () => {
    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/implementation/cancel`, {
        method: "POST",
        headers: {
          ...authHeaders,
        },
      });

      notification.success({
        message: "Implementation Cancelled",
        description: "Sandbox implementation runner has been cancelled.",
      });
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to cancel implementation.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunCandidateReview = async () => {
    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/candidate/review`, {
        method: "POST",
        headers: {
          ...authHeaders,
        },
      });

      notification.success({
        message: "Review Executed",
        description: "Candidate review, risk assessment, and quality scorecard computed successfully.",
      });
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to run candidate review.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApproveDelivery = async () => {
    if (!gateOperatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (gateRationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }
    if (!gateRiskAcknowledged) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Teslimat riskini onaylamanız gerekiyor." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/human-gate/approve-delivery`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: gateOperatorId,
          rationale: gateRationale,
          risk_acknowledgement: gateRiskAcknowledged,
        }),
      });

      notification.success({
        message: "Delivery Approved",
        description: "Delivery package prepared and locked successfully under secure workspace container.",
      });
      setGateRationale("");
      setGateRiskAcknowledged(false);
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to approve delivery.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestCandidateRevision = async () => {
    if (!gateOperatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (gateRationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }
    if (!gateRevisionNotes.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Revizyon notları zorunludur." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/human-gate/request-revision`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: gateOperatorId,
          rationale: gateRationale,
          revision_notes: gateRevisionNotes,
        }),
      });

      notification.success({
        message: "Revision Requested",
        description: "Candidate revision request logged. State set back to REVISION_REQUESTED.",
      });
      setGateRationale("");
      setGateRevisionNotes("");
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to request candidate revision.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRejectCandidate = async () => {
    if (!gateOperatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (gateRationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/human-gate/reject`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: gateOperatorId,
          rationale: gateRationale,
        }),
      });

      notification.success({
        message: "Aday reddedildi",
        description: "Candidate permanently rejected.",
      });
      setGateRationale("");
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to reject candidate.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinalApprove = async () => {
    if (!finalOperatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (finalRationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }
    if (!finalRiskAcknowledged) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Final teslimat riskini onaylamanız gerekiyor." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/final-decision/approve`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: finalOperatorId,
          rationale: finalRationale,
          risk_acknowledgement: finalRiskAcknowledged,
        }),
      });

      notification.success({
        message: "Final Approval Recorded",
        description: "Release archive has been generated and project closed.",
      });
      setFinalRationale("");
      setFinalRiskAcknowledged(false);
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to finalize approval.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinalRequestRevision = async () => {
    if (!finalOperatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (finalRationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }
    if (!finalRevisionNotes.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Revizyon notları zorunludur." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/final-decision/request-revision`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: finalOperatorId,
          rationale: finalRationale,
          revision_notes: finalRevisionNotes,
        }),
      });

      notification.success({
        message: "Final Revision Requested",
        description: "Revision requested at final gate.",
      });
      setFinalRationale("");
      setFinalRevisionNotes("");
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API Error",
        description: err.message || "Failed to request final revision.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinalReject = async () => {
    if (!finalOperatorId.trim()) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Operator ID zorunludur." });
      return;
    }
    if (finalRationale.trim().length < 5) {
      notification.warning({ message: "Doğrulama uyarısı", description: "Gerekçe en az 5 karakter olmalıdır." });
      return;
    }

    setIsSubmitting(true);
    try {
      const authHeaders = await getAuthHeaders();
      await safeFetchJson(`${apiBase}/project-factory/${projectId}/final-decision/reject`, {
        method: "POST",
        headers: {
          ...authHeaders,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_id: finalOperatorId,
          rationale: finalRationale,
        }),
      });

      notification.success({
        message: "Proje reddedildi",
        description: "Proje final geçitte kalıcı olarak reddedildi.",
      });
      setFinalRationale("");
      await loadData();
    } catch (err: any) {
      notification.error({
        message: "API hatası",
        description: err.message || "Proje reddedilemedi.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#060a12] p-8 flex items-center justify-center">
        <div className="text-center">
          <Cpu className="h-12 w-12 text-cyan-400 animate-spin mx-auto mb-4" />
          <Text className="text-gray-400 font-mono text-xs uppercase tracking-widest">
            Project Factory bağlamı yükleniyor...
          </Text>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen bg-[#060a12] p-8">
        <Alert
          message="Bağlam yüklenemedi"
          description={`Project Factory ID '${projectId}' bulunamadı veya artifact dosyaları geçersiz.`}
          type="error"
          showIcon
          action={
            <Button size="small" type="primary" onClick={() => list("workflows")}>
              Dashboard'a dön
            </Button>
          }
        />
      </div>
    );
  }

  const { project_brief, requirement_gate, sandbox_manifest, decisions } = data;

  const getGateBadge = (status: string) => {
    const s = status.toUpperCase();
    switch (s) {
      case "WAITING_FOR_OPERATOR":
      case "REQUIREMENT_GATE_WAITING":
        return <Tag color="warning" className="px-3 py-1 font-black uppercase rounded-lg">WAITING FOR OPERATOR</Tag>;
      case "SCOPE_APPROVED":
        return <Tag color="cyan" className="px-3 py-1 font-black uppercase rounded-lg">SCOPE APPROVED</Tag>;
      case "IMPLEMENTATION_READY":
        return <Tag color="blue" className="px-3 py-1 font-black uppercase rounded-lg">IMPLEMENTATION READY</Tag>;
      case "IMPLEMENTATION_RUNNING":
        return <Tag color="purple" className="px-3 py-1 font-black uppercase rounded-lg animate-pulse">IMPLEMENTATION RUNNING</Tag>;
      case "IMPLEMENTATION_FAILED":
        return <Tag color="error" className="px-3 py-1 font-black uppercase rounded-lg">IMPLEMENTATION FAILED</Tag>;
      case "IMPLEMENTATION_SUCCEEDED":
        return <Tag color="success" className="px-3 py-1 font-black uppercase rounded-lg">IMPLEMENTATION SUCCEEDED</Tag>;
      case "CANDIDATE_READY":
        return <Tag color="gold" className="px-3 py-1 font-black uppercase rounded-lg">CANDIDATE READY</Tag>;
      case "HUMAN_GATE_WAITING":
        return <Tag color="orange" className="px-3 py-1 font-black uppercase rounded-lg">HUMAN GATE WAITING</Tag>;
      case "CANCELLED":
        return <Tag color="default" className="px-3 py-1 font-black uppercase rounded-lg">CANCELLED</Tag>;
      case "REVISION_REQUESTED":
        return <Tag color="orange" className="px-3 py-1 font-black uppercase rounded-lg">REVISION REQUESTED</Tag>;
      case "REJECTED":
        return <Tag color="error" className="px-3 py-1 font-black uppercase rounded-lg">REJECTED</Tag>;
      default:
        return <Tag color="default" className="px-3 py-1 font-black uppercase rounded-lg">{s}</Tag>;
    }
  };

  const getActionBadge = (action: string) => {
    switch (action) {
      case "APPROVE_SCOPE":
        return <Tag color="cyan" className="text-[10px] font-black uppercase rounded">APPROVE</Tag>;
      case "REQUEST_REVISION":
        return <Tag color="orange" className="text-[10px] font-black uppercase rounded">REVISION</Tag>;
      case "REJECT":
        return <Tag color="error" className="text-[10px] font-black uppercase rounded">REJECT</Tag>;
      default:
        return <Tag color="default" className="text-[10px] font-black uppercase rounded">{action}</Tag>;
    }
  };

  return (
    <div className="min-h-screen bg-[#060a12] p-8 text-gray-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8 border-b border-white/5 pb-6">
        <div>
          <button
            onClick={() => list("dashboard")}
            className="flex items-center gap-2 text-gray-500 hover:text-white transition-all text-xs font-mono uppercase mb-3 bg-transparent border-none cursor-pointer"
          >
            <ArrowLeft size={14} /> Dashboard'a dön
          </button>
          <div className="flex items-center gap-4">
            <Cpu className="text-cyan-400 h-8 w-8" />
            <div>
              <Title level={2} className="text-white m-0 font-black italic tracking-tighter">
                PROJECT FACTORY
              </Title>
              <Text className="text-gray-500 font-mono text-[10px] uppercase tracking-widest mt-1 block">
                ID: {project_brief.project_id}
              </Text>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-[9px] font-black uppercase leading-none tracking-widest text-gray-500">
              Requirement Gate durumu
            </span>
            <div className="mt-2">{getGateBadge(requirement_gate.status)}</div>
          </div>
          <button
            onClick={() => void loadData()}
            className="rounded-2xl border border-white/5 bg-white/5 p-4 text-gray-500 transition-all hover:bg-white/10 hover:text-white active:scale-90"
          >
            <RotateCcw size={18} />
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <Row gutter={[24, 24]}>
        {/* Left Column: Brief details, file list, and sandbox details */}
        <Col xs={24} lg={14} className="flex flex-col gap-6">
          {/* Project Brief Card */}
          <Card
            variant="borderless"
            className="glass-panel border-white/[0.03] bg-gradient-to-br from-white/[0.015] to-transparent rounded-[2rem] p-6 shadow-2xl relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 p-8 opacity-[0.02] text-cyan-400 pointer-events-none">
              <FileCode size={180} />
            </div>
            
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-6">
                <div className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.6)]" />
                <h2 className="text-xs font-black uppercase tracking-[0.3em] text-white">Proje özeti / Intake şartları</h2>
              </div>

              <Title level={3} className="text-white font-black tracking-tight mb-4">
                {project_brief.title}
              </Title>

              <div className="space-y-6">
                <div>
                  <Text className="text-xs font-black uppercase tracking-wider text-cyan-400 block mb-2">
                    Problem tanımı
                  </Text>
                  <Paragraph className="text-gray-400 text-sm leading-relaxed bg-black/30 p-4 rounded-xl border border-white/5 font-mono">
                    {project_brief.problem_statement}
                  </Paragraph>
                </div>

                <div>
                  <Text className="text-xs font-black uppercase tracking-wider text-cyan-400 block mb-2">
                    Önerilen eylem
                  </Text>
                  <Paragraph className="text-gray-400 text-sm leading-relaxed bg-black/30 p-4 rounded-xl border border-white/5">
                    {project_brief.recommended_action}
                  </Paragraph>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Text className="text-xs font-black uppercase tracking-wider text-cyan-400 block">
                      Target Affected Files ({project_brief.affected_files.length})
                    </Text>
                    <Tag className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 text-[9px] font-black uppercase px-2 py-0.5 rounded">
                      Sandbox Boundary
                    </Tag>
                  </div>
                  <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
                    {project_brief.affected_files.length === 0 ? (
                      <div className="text-center py-6 text-gray-500 text-xs font-mono uppercase bg-black/20 rounded-xl border border-white/5">
                        No target files registered.
                      </div>
                    ) : (
                      project_brief.affected_files.map((file, idx) => (
                        <div key={idx} className="flex items-center gap-3 bg-white/[0.01] hover:bg-white/[0.03] border border-white/5 px-4 py-2.5 rounded-xl transition-all">
                          <FileText size={14} className="text-cyan-400 flex-shrink-0" />
                          <span className="font-mono text-xs text-gray-400 truncate">{file}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Sandbox Scaffolding Manifest Card */}
          <Card
            variant="borderless"
            className="glass-panel border-white/[0.03] bg-gradient-to-br from-white/[0.015] to-transparent rounded-[2rem] p-6 shadow-2xl relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 p-8 opacity-[0.02] text-emerald-400 pointer-events-none">
              <Database size={180} />
            </div>

            <div className="relative z-10">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className={`h-2 w-2 rounded-full ${sandbox_manifest ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" : "bg-gray-500"}`} />
                  <h2 className="text-xs font-black uppercase tracking-[0.3em] text-white">Sandbox manifest & state</h2>
                </div>
                {sandbox_manifest ? (
                  <Tag color="success" className="font-black px-2 py-0.5 uppercase rounded text-[9px]">SCAFFOLD COMPLETE</Tag>
                ) : (
                  <Tag color="default" className="font-black px-2 py-0.5 uppercase rounded text-[9px]">NOT SCAFFOLDED</Tag>
                )}
              </div>

              {!sandbox_manifest ? (
                <div className="py-12 text-center bg-black/20 rounded-3xl border border-white/5">
                  <Lock className="h-8 w-8 text-gray-600 mx-auto mb-3" />
                  <div className="text-xs font-black uppercase tracking-wider text-gray-500">
                    Sandbox Locked
                  </div>
                  <div className="text-[10px] text-gray-600 mt-1 max-w-sm mx-auto font-mono">
                    Scaffolding process will automatically run once the operator approves the project brief scope.
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-black/40 p-4 rounded-2xl border border-white/5 font-mono text-[10px]">
                    <div>
                      <span className="text-gray-500 uppercase">Sandbox Path:</span>
                      <span className="text-white block mt-1 truncate">{sandbox_manifest.sandbox_path}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 uppercase">Scaffolded At:</span>
                      <span className="text-emerald-400 block mt-1">{new Date(sandbox_manifest.created_at).toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {/* Copied files */}
                    <div>
                      <span className="text-xs font-black uppercase tracking-wider text-emerald-400 block mb-2">
                        Successfully Scaffolded/Copied Files ({sandbox_manifest.copied_files.length})
                      </span>
                      <div className="max-h-40 overflow-y-auto space-y-1.5 pr-2">
                        {sandbox_manifest.copied_files.length === 0 ? (
                          <div className="text-xs font-mono text-gray-600 italic">No existing files copied.</div>
                        ) : (
                          sandbox_manifest.copied_files.map((file, idx) => (
                            <div key={idx} className="flex items-center gap-2 bg-emerald-500/[0.02] border border-emerald-500/10 px-3 py-1.5 rounded-lg text-[11px] font-mono text-emerald-400">
                              <Check size={12} />
                              <span>{file}</span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Placeholders */}
                    <div>
                      <span className="text-xs font-black uppercase tracking-wider text-cyan-400 block mb-2">
                        Initialized Safe Placeholders ({sandbox_manifest.placeholder_files.length})
                      </span>
                      <div className="max-h-40 overflow-y-auto space-y-1.5 pr-2">
                        {sandbox_manifest.placeholder_files.length === 0 ? (
                          <div className="text-xs font-mono text-gray-600 italic">No placeholders generated.</div>
                        ) : (
                          sandbox_manifest.placeholder_files.map((file, idx) => (
                            <div key={idx} className="flex items-center gap-2 bg-cyan-500/[0.02] border border-cyan-500/10 px-3 py-1.5 rounded-lg text-[11px] font-mono text-cyan-400">
                              <FileCheck size={12} />
                              <span>{file}</span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Skipped files */}
                    {sandbox_manifest.skipped_files.length > 0 && (
                      <div>
                        <span className="text-xs font-black uppercase tracking-wider text-amber-500 block mb-2">
                          Güvenli şekilde korunan/atlanmış dosyalar ({sandbox_manifest.skipped_files.length})
                        </span>
                        <div className="max-h-40 overflow-y-auto space-y-1.5 pr-2">
                          {sandbox_manifest.skipped_files.map((skip, idx) => (
                            <div key={idx} className="flex flex-col gap-1 bg-amber-500/[0.02] border border-amber-500/10 px-3 py-2 rounded-lg text-[11px] font-mono">
                              <div className="flex items-center gap-2 text-amber-500">
                                <X size={12} />
                                <span>{skip.path}</span>
                              </div>
                              <span className="text-gray-500 text-[10px] pl-5">{skip.reason}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </Col>

        {/* Right Column: Gate Review panel and append-only decision audit logs */}
        <Col xs={24} lg={10} className="flex flex-col gap-6">
          {/* Operator Decision Action Panel */}
          <Card
            variant="borderless"
            className="glass-panel border-white/[0.03] bg-gradient-to-br from-white/[0.015] to-transparent rounded-[2rem] p-6 shadow-2xl"
          >
            <div className="flex items-center gap-3 mb-6">
              <ShieldAlert className="text-cyan-400 h-5 w-5" />
              <h2 className="text-xs font-black uppercase tracking-[0.3em] text-white">Operatör karar paneli</h2>
            </div>

            {requirement_gate.status !== "WAITING_FOR_OPERATOR" ? (
              <div className="bg-black/30 border border-white/5 rounded-3xl p-6 text-center space-y-4">
                <CheckCircle2 className="h-10 w-10 text-cyan-400 mx-auto" />
                <div>
                  <div className="text-sm font-black uppercase text-white tracking-wider">Gate durumu çözüldü</div>
                  <div className="text-xs font-mono text-cyan-400 mt-1 uppercase tracking-widest">{requirement_gate.status}</div>
                </div>
                <Divider className="border-white/5 my-4" />
                <div className="space-y-4 text-left text-xs font-mono">
                  <div>
                    <span className="text-gray-500 uppercase">Karar veren:</span>
                    <span className="text-white block mt-0.5">{requirement_gate.approved_by || "SYSTEM"}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 uppercase">Karar zamanı:</span>
                    <span className="text-white block mt-0.5">
                      {requirement_gate.resolved_at ? new Date(requirement_gate.resolved_at).toLocaleString() : "-"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 uppercase">Gerekçe:</span>
                    <span className="text-gray-400 block mt-1 bg-black/20 p-3 rounded-xl border border-white/5">
                      {requirement_gate.rationale || "Gerekçe girilmedi."}
                    </span>
                  </div>
                  {requirement_gate.scope_adjustments && (
                    <div>
                      <span className="text-gray-500 uppercase">Detaylar/düzeltmeler:</span>
                      <span className="text-white block mt-0.5 font-bold">{requirement_gate.scope_adjustments}</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Inputs */}
                <div className="space-y-4">
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 block mb-1.5">
                      Operatör ID
                    </span>
                    <Input
                      value={operatorId}
                      onChange={(e) => setOperatorId(e.target.value)}
                      placeholder="örn. OPERATOR-01"
                      className="bg-black/40 border-white/10 hover:border-cyan-500/30 focus:border-cyan-500 text-white rounded-xl py-2 px-3 font-mono text-xs focus:shadow-none"
                    />
                  </div>

                  <div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 block mb-1.5">
                      Karar gerekçesi
                    </span>
                    <Input.TextArea
                      value={rationale}
                      onChange={(e) => setRationale(e.target.value)}
                      placeholder="Bu karar için gerekçe detaylarını yazın (min. 5 karakter)..."
                      rows={4}
                      className="bg-black/40 border-white/10 hover:border-cyan-500/30 focus:border-cyan-500 text-white rounded-xl py-2 px-3 font-mono text-xs focus:shadow-none"
                    />
                    <div className="text-[9px] text-gray-500 mt-1 uppercase font-mono text-right">
                      {rationale.trim().length} / 5 min. karakter
                    </div>
                  </div>

                  {/* Tabs / Actions */}
                  <div className="border-t border-b border-white/5 py-4 my-2">
                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 block mb-3">
                      Aksiyon modu seçimi
                    </span>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        onClick={() => setActiveTab("approve")}
                        className={`py-2 px-1 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer ${
                          activeTab === "approve"
                            ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                            : "bg-white/[0.01] border-white/5 text-gray-500 hover:text-white"
                        }`}
                      >
                        Kapsamı onayla
                      </button>
                      <button
                        onClick={() => setActiveTab("revision")}
                        className={`py-2 px-1 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer ${
                          activeTab === "revision"
                            ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                            : "bg-white/[0.01] border-white/5 text-gray-500 hover:text-white"
                        }`}
                      >
                        Revizyon gerekli
                      </button>
                      <button
                        onClick={() => setActiveTab("reject")}
                        className={`py-2 px-1 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer ${
                          activeTab === "reject"
                            ? "bg-red-500/10 border-red-500/30 text-red-400"
                            : "bg-white/[0.01] border-white/5 text-gray-500 hover:text-white"
                        }`}
                      >
                        Intake'i reddet
                      </button>
                    </div>
                  </div>

                  {/* Active mode contents */}
                  {activeTab === "approve" && (
                    <div className="space-y-4 bg-cyan-500/[0.02] border border-cyan-500/10 p-4 rounded-2xl">
                      <div>
                        <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-2">
                          Onaylanan kapsam seviyesi
                        </span>
                        <Radio.Group
                          value={approvedScope}
                          onChange={(e) => setApprovedScope(e.target.value)}
                          className="flex gap-4 font-mono text-xs text-white"
                        >
                          <Radio value="mvp" className="text-white">MVP modu</Radio>
                          <Radio value="full" className="text-white">Tam kapsam</Radio>
                        </Radio.Group>
                      </div>

                      <Divider className="border-cyan-500/10 my-2" />

                      <div className="flex items-start gap-3">
                        <Checkbox
                          checked={riskAcknowledged}
                          onChange={(e) => setRiskAcknowledged(e.target.checked)}
                          className="mt-0.5 text-white"
                        />
                        <div>
                          <span className="text-[10px] font-black uppercase tracking-widest text-white block">
                            Sınır koşullarını onayla
                          </span>
                          <span className="text-[9px] font-mono text-gray-500 mt-1 block leading-normal uppercase">
                            Bu onayın production yazma işlemlerine izin vermediğini ve kod sınırının korunduğunu doğruluyorum.
                          </span>
                        </div>
                      </div>

                      <Button
                        type="primary"
                        onClick={handleApproveScope}
                        loading={isSubmitting}
                        disabled={!riskAcknowledged || rationale.trim().length < 5 || !operatorId.trim()}
                        className="w-full bg-cyan-500 hover:bg-cyan-600 border-none font-black italic tracking-widest uppercase py-4 rounded-xl text-black shadow-lg"
                      >
                        Kapsam onayını çalıştır
                      </Button>
                    </div>
                  )}

                  {activeTab === "revision" && (
                    <div className="space-y-4 bg-amber-500/[0.02] border border-amber-500/10 p-4 rounded-2xl">
                      <div>
                        <span className="text-[10px] font-black uppercase tracking-widest text-amber-500 block mb-2">
                          Revizyon notları / yönergeler
                        </span>
                        <Input.TextArea
                          value={revisionNotes}
                          onChange={(e) => setRevisionNotes(e.target.value)}
                          placeholder="Kapsam onaylanmadan önce gereken net yönergeleri veya değişiklikleri yazın..."
                          rows={3}
                          className="bg-black/40 border-white/10 hover:border-amber-500/30 focus:border-amber-500 text-white rounded-xl py-2 px-3 font-mono text-xs focus:shadow-none"
                        />
                      </div>

                      <Button
                        type="primary"
                        onClick={handleRequestRevision}
                        loading={isSubmitting}
                        disabled={!revisionNotes.trim() || rationale.trim().length < 5 || !operatorId.trim()}
                        className="w-full bg-amber-500 hover:bg-amber-600 border-none font-black italic tracking-widest uppercase py-4 rounded-xl text-black shadow-lg"
                      >
                        Kapsam revizyonu iste
                      </Button>
                    </div>
                  )}

                  {activeTab === "reject" && (
                    <div className="space-y-4 bg-red-500/[0.02] border border-red-500/10 p-4 rounded-2xl">
                      <div className="flex gap-3 text-red-500 bg-red-500/[0.05] p-3 rounded-xl border border-red-500/20 text-[10px] font-mono uppercase leading-normal">
                        <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
                        <div>
                          <strong>Uyarı: Reddetme işlemi geri alınamaz.</strong>
                          <span className="block mt-1 text-gray-500">
                            Bu intake reddedildiğinde mevcut Requirement Gate döngüsü sonlanır.
                          </span>
                        </div>
                      </div>

                      <Button
                        type="primary"
                        danger
                        onClick={handleReject}
                        loading={isSubmitting}
                        disabled={rationale.trim().length < 5 || !operatorId.trim()}
                        className="w-full bg-red-500 hover:bg-red-600 border-none font-black italic tracking-widest uppercase py-4 rounded-xl text-white shadow-lg"
                      >
                        Project intake'i reddet
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>

          {/* Phase 7: Sandbox Implementation Runner Suite */}
          {requirement_gate.status !== "WAITING_FOR_OPERATOR" && (
            <Card
              variant="borderless"
              className="glass-panel border-white/[0.03] bg-gradient-to-br from-white/[0.015] to-transparent rounded-[2rem] p-6 shadow-2xl"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Cpu className="text-cyan-400 h-5 w-5 animate-pulse" />
                  <h2 className="text-xs font-black uppercase tracking-[0.3em] text-white">Sandbox Suite</h2>
                </div>
                {implRun && (
                  <Tag
                    color={
                      implRun.status === "IMPLEMENTATION_RUNNING" ? "purple" :
                      implRun.status === "IMPLEMENTATION_SUCCEEDED" ? "success" :
                      implRun.status === "IMPLEMENTATION_FAILED" ? "error" : "default"
                    }
                    className="font-black px-2 py-0.5 uppercase rounded text-[9px] tracking-widest font-mono"
                  >
                    {implRun.status}
                  </Tag>
                )}
              </div>

              {/* Navigation Tabs */}
              <div className="flex border-b border-white/5 pb-3 mb-6 gap-2 overflow-x-auto">
                <button
                  onClick={() => setImplActiveTab("control")}
                  className={`flex items-center gap-1.5 py-1 px-3 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                    implActiveTab === "control"
                      ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                      : "bg-transparent border-transparent text-gray-500 hover:text-white"
                  }`}
                >
                  <Play size={12} /> Runner Control
                </button>
                <button
                  onClick={() => setImplActiveTab("breakdown")}
                  className={`flex items-center gap-1.5 py-1 px-3 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                    implActiveTab === "breakdown"
                      ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                      : "bg-transparent border-transparent text-gray-500 hover:text-white"
                  }`}
                >
                  <ListTodo size={12} /> Task Checklist
                </button>
                <button
                  onClick={() => setImplActiveTab("reports")}
                  className={`flex items-center gap-1.5 py-1 px-3 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                    implActiveTab === "reports"
                      ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                      : "bg-transparent border-transparent text-gray-500 hover:text-white"
                  }`}
                >
                  <Terminal size={12} /> Verification & Files
                </button>
                <button
                  onClick={() => setImplActiveTab("candidate")}
                  className={`flex items-center gap-1.5 py-1 px-3 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                    implActiveTab === "candidate"
                      ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                      : "bg-transparent border-transparent text-gray-500 hover:text-white"
                  }`}
                >
                  <FileArchive size={12} /> Candidate Package
                </button>
                <button
                  onClick={() => setImplActiveTab("telemetry")}
                  className={`flex items-center gap-1.5 py-1 px-3 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                    implActiveTab === "telemetry"
                      ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                      : "bg-transparent border-transparent text-gray-500 hover:text-white"
                  }`}
                >
                  <Activity size={12} /> Telemetry
                </button>
              </div>

              {/* Tab Contents */}
              {implActiveTab === "control" && (
                <div className="space-y-4">
                  {(!implRun || implRun.status === "IMPLEMENTATION_FAILED" || implRun.status === "CANCELLED" || implRun.status === "IMPLEMENTATION_SUCCEEDED") && (
                    <div className="space-y-4">
                      {implRun?.status === "IMPLEMENTATION_FAILED" && (
                        <Alert
                          message="Sandbox Implementation Failed"
                          description="The previous sandboxed verification execution encountered errors or test failures. You can configure and relaunch the sandbox runner below."
                          type="error"
                          showIcon
                          className="rounded-2xl border-red-500/10 bg-red-500/[0.02] text-gray-400 text-xs font-mono"
                        />
                      )}
                      {implRun?.status === "CANCELLED" && (
                        <Alert
                          message="Sandbox Implementation Cancelled"
                          description="The runner execution was cancelled by operator command. You can restart execution below."
                          type="warning"
                          showIcon
                          className="rounded-2xl border-amber-500/10 bg-amber-500/[0.02] text-gray-400 text-xs font-mono"
                        />
                      )}
                      {implRun?.status === "IMPLEMENTATION_SUCCEEDED" && (
                        <Alert
                          message="Sandbox Implementation Succeeded"
                          description="Sandbox code generation and tests completed successfully. A candidate package is ready for Human Gate approval."
                          type="success"
                          showIcon
                          className="rounded-2xl border-emerald-500/10 bg-emerald-500/[0.02] text-gray-400 text-xs font-mono"
                        />
                      )}

                      <div className="bg-black/30 border border-white/5 p-4 rounded-2xl space-y-4">
                        <div>
                          <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-1.5">
                            Select Runner Mode
                          </span>
                          <Radio.Group
                            value={runnerMode}
                            onChange={(e) => setRunnerMode(e.target.value)}
                            className="flex flex-col gap-2 font-mono text-xs text-white"
                          >
                            <Radio value="template_first" className="text-white">
                              <span className="text-xs text-white font-bold block">Template First</span>
                              <span className="text-[10px] text-gray-500 block leading-tight">Scaffold pre-approved templates first (FastAPI service boilerplate)</span>
                            </Radio>
                            <Radio value="documentation_only" className="text-white">
                              <span className="text-xs text-white font-bold block">Documentation Only</span>
                              <span className="text-[10px] text-gray-500 block leading-tight">Generates architectural, README, and user manuals</span>
                            </Radio>
                            <Radio value="frontend_sandbox" className="text-white">
                              <span className="text-xs text-white font-bold block">Frontend Sandbox</span>
                              <span className="text-[10px] text-gray-500 block leading-tight">Scaffolds isolated Next.js layouts for visual preview</span>
                            </Radio>
                            <Radio value="backend_sandbox" className="text-white">
                              <span className="text-xs text-white font-bold block">Backend Sandbox</span>
                              <span className="text-[10px] text-gray-500 block leading-tight">Generates clean FastAPI endpoints with standard requirements</span>
                            </Radio>
                            <Radio value="data_project" className="text-white">
                              <span className="text-xs text-white font-bold block">Data Project</span>
                              <span className="text-[10px] text-gray-500 block leading-tight">Otomatik sheet ve Excel analitik dashboard iskeleti oluşturur</span>
                            </Radio>
                            <Radio value="agent_assisted" className="text-white">
                              <span className="text-xs text-white font-bold block">Agent Assisted</span>
                              <span className="text-[10px] text-gray-500 block leading-tight">İzole sandbox bağlamında uzman subagent'ları kullanır</span>
                            </Radio>
                          </Radio.Group>
                        </div>

                        <Divider className="border-white/5 my-2" />

                        <div>
                          <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-1.5">
                            Operatör ID
                          </span>
                          <Input
                            value={operatorId}
                            onChange={(e) => setOperatorId(e.target.value)}
                            className="bg-black/40 border-white/10 hover:border-cyan-500/30 focus:border-cyan-500 text-white rounded-xl py-2 px-3 font-mono text-xs focus:shadow-none"
                          />
                        </div>

                        <div>
                          <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-1.5">
                            Implementation gerekçesi
                          </span>
                          <Input.TextArea
                            value={implRationale}
                            onChange={(e) => setImplRationale(e.target.value)}
                            placeholder="Provide implementation details..."
                            rows={3}
                            className="bg-black/40 border-white/10 hover:border-cyan-500/30 focus:border-cyan-500 text-white rounded-xl py-2 px-3 font-mono text-xs focus:shadow-none"
                          />
                        </div>

                        <div className="flex items-start gap-3 mt-2">
                          <Checkbox
                            checked={implRiskAcknowledged}
                            onChange={(e) => setImplRiskAcknowledged(e.target.checked)}
                            className="mt-0.5 text-white"
                          />
                          <div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-white block">
                              Acknowledge Sandbox Boundaries
                            </span>
                            <span className="text-[9px] font-mono text-gray-500 mt-1 block leading-normal uppercase">
                              I acknowledge that this starts isolated implementation. Production codebase is safe and unmodified.
                            </span>
                          </div>
                        </div>

                        <Button
                          type="primary"
                          onClick={handleStartImplementation}
                          loading={isSubmitting}
                          disabled={!implRiskAcknowledged || implRationale.trim().length < 5 || !operatorId.trim()}
                          className="w-full bg-cyan-500 hover:bg-cyan-600 border-none font-black italic tracking-widest uppercase py-4 rounded-xl text-black shadow-lg flex items-center justify-center gap-2 mt-4"
                        >
                          <Play size={14} className="fill-black text-black" />
                          {implRun?.status ? "Relaunch Sandbox Implementation" : "Start Sandbox Implementation"}
                        </Button>
                      </div>
                    </div>
                  )}

                  {implRun && implRun.status === "IMPLEMENTATION_RUNNING" && (
                    <div className="bg-black/30 border border-white/5 p-6 rounded-3xl text-center space-y-6">
                      <Cpu className="h-12 w-12 text-purple-400 animate-spin mx-auto" />
                      <div>
                        <div className="text-sm font-black uppercase text-white tracking-wider animate-pulse font-mono">Sandbox Execution Active</div>
                        <div className="text-xs font-mono text-purple-400 mt-1 uppercase tracking-widest">
                          Running step-by-step milestones...
                        </div>
                      </div>

                      <div className="bg-black/40 p-4 rounded-2xl border border-white/5 text-left font-mono text-[10px] space-y-2">
                        <div>
                          <span className="text-gray-500">RUNNING MODE:</span>
                          <span className="text-white block font-bold">{implRun.runner_mode}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">STARTED BY:</span>
                          <span className="text-white block font-bold">{implRun.started_by}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">STARTED AT:</span>
                          <span className="text-white block font-bold">{new Date(implRun.started_at).toLocaleString()}</span>
                        </div>
                      </div>

                      <Button
                        danger
                        type="primary"
                        onClick={handleCancelImplementation}
                        loading={isSubmitting}
                        className="w-full bg-red-500 hover:bg-red-600 border-none font-black italic tracking-widest uppercase py-4 rounded-xl text-white shadow-lg flex items-center justify-center gap-2"
                      >
                        <StopCircle size={14} />
                        Cancel Execution
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {implActiveTab === "breakdown" && (
                <div className="space-y-4">
                  {taskBreakdown.length === 0 ? (
                    <div className="py-12 text-center bg-black/20 rounded-3xl border border-white/5">
                      <ListTodo className="h-8 w-8 text-gray-600 mx-auto mb-3" />
                      <div className="text-xs font-black uppercase tracking-wider text-gray-500">
                        No tasks generated yet
                      </div>
                      <div className="text-[10px] text-gray-600 mt-1 max-w-sm mx-auto font-mono">
                        Milestones will be planned and visualised here once the sandbox implementation starts.
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                      {taskBreakdown.map((task) => (
                        <div
                          key={task.task_id}
                          className="flex items-start justify-between bg-white/[0.01] hover:bg-white/[0.03] border border-white/5 px-4 py-3 rounded-2xl transition-all"
                        >
                          <div className="flex items-start gap-3">
                            <div className="mt-0.5">
                              {task.status === "completed" ? (
                                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                              ) : task.status === "in_progress" ? (
                                <RefreshCw className="h-4 w-4 text-purple-400 animate-spin" />
                              ) : (
                                <div className="h-4 w-4 rounded-full border-2 border-gray-600 bg-transparent flex items-center justify-center text-[8px] font-black text-gray-600 font-mono">P</div>
                              )}
                            </div>
                            <div>
                              <span className="text-xs font-mono text-white font-bold block">{task.task_id}</span>
                              <span className="text-[11px] text-gray-400 mt-0.5 block leading-normal">{task.description}</span>
                            </div>
                          </div>
                          <span className="text-[9px] font-mono text-gray-500 bg-white/5 px-2 py-0.5 rounded-lg border border-white/5 whitespace-nowrap">
                            {task.estimated_minutes} Min
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {implActiveTab === "reports" && (
                <div className="space-y-4">
                  {/* Verification Report */}
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-2">
                      Verification Suite Outcome
                    </span>
                    {!verificationReport ? (
                      <div className="py-6 text-center bg-black/20 rounded-2xl border border-white/5 text-gray-600 text-xs font-mono uppercase">
                        No verification report available
                      </div>
                    ) : (
                      <div className="bg-black/40 border border-white/5 p-4 rounded-2xl space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono text-gray-500 uppercase">Status:</span>
                          <Tag
                            color={verificationReport.status === "PASSED" ? "success" : "error"}
                            className="font-mono text-xs uppercase font-black tracking-widest rounded-lg px-2"
                          >
                            {verificationReport.status}
                          </Tag>
                        </div>
                        <div className="flex items-center justify-between text-[10px] font-mono text-gray-500">
                          <span>DURATION:</span>
                          <span className="text-white">{verificationReport.duration_seconds.toFixed(2)} SECONDS</span>
                        </div>

                        {verificationReport.error && (
                          <div className="bg-red-500/[0.02] border border-red-500/10 p-3 rounded-xl text-red-400 font-mono text-[10px] break-all">
                            <span className="font-bold text-[9px] block text-red-500 uppercase">Verification Error:</span>
                            {verificationReport.error}
                          </div>
                        )}

                        <div className="space-y-2">
                          <span className="text-[9px] font-black text-gray-500 uppercase font-mono block">Terminal Output log (stdout/stderr):</span>
                          <pre className="bg-[#030712] border border-white/5 rounded-xl p-3 font-mono text-[9px] text-emerald-400 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                            {verificationReport.stdout || "--- NO STDOUT PRINTED ---"}
                            {verificationReport.stderr && `\n\n--- STDERR ---\n${verificationReport.stderr}`}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Generated & Modified Sandbox Files */}
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-2">
                      Modified & Generated Files
                    </span>
                    {!implRun || (implRun.changed_files.length === 0 && implRun.generated_files.length === 0) ? (
                      <div className="py-6 text-center bg-black/20 rounded-2xl border border-white/5 text-gray-600 text-xs font-mono uppercase">
                        No generated codebase artifacts yet
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {implRun.generated_files.map((file, idx) => (
                          <div key={idx} className="flex items-center gap-2 bg-emerald-500/[0.02] border border-emerald-500/10 px-3 py-2 rounded-xl text-[11px] font-mono text-emerald-400">
                            <FileCode size={12} />
                            <span className="truncate flex-1">{file}</span>
                            <Tag color="success" className="text-[8px] font-black rounded uppercase px-1 m-0">NEW</Tag>
                          </div>
                        ))}
                        {implRun.changed_files.map((file, idx) => (
                          <div key={idx} className="flex items-center gap-2 bg-cyan-500/[0.02] border border-cyan-500/10 px-3 py-2 rounded-xl text-[11px] font-mono text-cyan-400">
                            <FileText size={12} />
                            <span className="truncate flex-1">{file}</span>
                            <Tag color="cyan" className="text-[8px] font-black rounded uppercase px-1 m-0">MODIFIED</Tag>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {implActiveTab === "candidate" && (
                <div className="space-y-4">
                  {!candidateManifest ? (
                    <div className="py-12 text-center bg-black/20 rounded-3xl border border-white/5">
                      <FileArchive className="h-8 w-8 text-gray-600 mx-auto mb-3" />
                      <div className="text-xs font-black uppercase tracking-wider text-gray-500">
                        No Implementation Candidate
                      </div>
                      <div className="text-[10px] text-gray-600 mt-1 max-w-sm mx-auto font-mono">
                        Once sandbox runner succeeds, the compiled candidate manifest will build here.
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Manifest details */}
                      <div className="bg-black/40 border border-white/5 p-4 rounded-2xl space-y-3 font-mono text-[10px]">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-500">CANDIDATE ID:</span>
                          <span className="text-cyan-400 font-bold">{candidateManifest.candidate_id}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-500">MANIFEST STATUS:</span>
                          <Tag color="gold" className="font-black text-[9px] uppercase tracking-widest rounded-lg px-2">{candidateManifest.status}</Tag>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-500">TEST STATUS:</span>
                          <Tag color={candidateManifest.tests.status === "PASSED" ? "success" : "error"} className="font-black text-[9px] uppercase tracking-widest rounded-lg px-2">
                            {candidateManifest.tests.status}
                          </Tag>
                        </div>
                      </div>

                      {/* Candidate Files Checklist */}
                      <div>
                        <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-2">
                          Packaged Files & Integrations
                        </span>
                        <div className="space-y-2 max-h-40 overflow-y-auto pr-2">
                          {candidateManifest.files.map((file, idx) => (
                            <div key={idx} className="bg-[#030712] border border-white/5 rounded-xl p-3 font-mono text-[9px] space-y-1">
                              <div className="flex items-center justify-between text-white font-bold">
                                <span>{file.path}</span>
                                <span className="text-gray-500">{(file.size_bytes / 1024).toFixed(2)} KB</span>
                              </div>
                              <div className="text-gray-600 text-[8px] truncate">
                                SHA256: {file.checksum}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Human Gate Alert */}
                      <Alert
                        message="Human Gate Security Lockdown"
                        description="Implementation Package is held strictly within sandbox boundary limits. Applying, merging, or committing changes to production code is locked until Phase 8 Operator review and delivery approval is resolved."
                        type="warning"
                        showIcon
                        icon={<ShieldCheck className="text-amber-400 mt-0.5" size={16} />}
                        className="rounded-2xl border-amber-500/10 bg-amber-500/[0.02] text-gray-400 text-xs font-mono leading-relaxed"
                      />
                    </div>
                  )}
                </div>
              )}

              {implActiveTab === "telemetry" && (
                <div className="space-y-4">
                  {logs.length === 0 ? (
                    <div className="py-12 text-center bg-black/20 rounded-3xl border border-white/5">
                      <Activity className="h-8 w-8 text-gray-600 mx-auto mb-3" />
                      <div className="text-xs font-black uppercase tracking-wider text-gray-500">
                        No telemetry logs yet
                      </div>
                      <div className="text-[10px] text-gray-600 mt-1 max-w-sm mx-auto font-mono">
                        Events stream will output live updates when implementation actions execute in the sandbox environment.
                      </div>
                    </div>
                  ) : (
                    <div className="bg-[#030712] border border-white/5 rounded-2xl p-4 font-mono text-[10px] space-y-3 max-h-[350px] overflow-y-auto pr-2">
                      {logs.map((log) => (
                        <div key={log.event_id} className="border-b border-white/5 pb-2.5 last:border-0 last:pb-0">
                          <div className="flex items-center justify-between text-[9px] text-gray-500">
                            <span className="text-cyan-400 font-bold uppercase">{log.event_type}</span>
                            <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                          </div>
                          <p className="text-gray-300 mt-1 leading-relaxed text-[10px]">{log.message}</p>
                          {log.details && (
                            <pre className="mt-1 bg-black/40 p-2 rounded-lg text-[8px] text-gray-500 overflow-x-auto whitespace-pre-wrap">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </Card>
          )}

          {/* Gate Decisions Append-Only Log History */}
          <Card
            variant="borderless"
            className="glass-panel border-white/[0.03] bg-gradient-to-br from-white/[0.015] to-transparent rounded-[2rem] p-6 shadow-2xl relative overflow-hidden"
          >
            <div className="flex items-center gap-3 mb-6">
              <Database className="text-cyan-400 h-5 w-5" />
              <h2 className="text-xs font-black uppercase tracking-[0.3em] text-white">Append-only Decision logs</h2>
            </div>

            <div className="relative z-10 max-h-80 overflow-y-auto space-y-4 pr-2">
              {decisions.length === 0 ? (
                <div className="py-8 text-center text-gray-600 font-mono text-[10px] uppercase">
                  No decisions logged for this intake.
                </div>
              ) : (
                decisions.map((dec, idx) => (
                  <div key={idx} className="bg-black/30 border border-white/5 rounded-2xl p-4 font-mono text-[10px] space-y-2 relative">
                    <div className="flex items-center justify-between">
                      {getActionBadge(dec.action)}
                      <span className="text-gray-500">{new Date(dec.created_at).toLocaleString()}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[9px] border-t border-b border-white/5 py-1.5 my-1 text-gray-500">
                      <div>
                        OPERATOR: <span className="text-white">{dec.operator_id}</span>
                      </div>
                      <div className="text-right">
                        ID: <span className="text-white font-mono">{dec.decision_id}</span>
                      </div>
                    </div>

                    <div className="text-gray-400 bg-black/10 p-2 rounded-lg">
                      <span className="text-gray-600 block uppercase font-bold text-[8px] mb-0.5">Rationale:</span>
                      {dec.rationale}
                    </div>

                    {dec.details && dec.details.revision_notes && (
                      <div className="text-amber-500 bg-amber-500/[0.02] border border-amber-500/10 p-2 rounded-lg">
                        <span className="text-amber-600 block uppercase font-bold text-[8px] mb-0.5">Revision Notes:</span>
                        {dec.details.revision_notes}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Phase 8 Candidate Review & Human Gate Console Card */}
      {candidateManifest && (
        <Row gutter={[24, 24]} className="mt-8">
          <Col span={24}>
            <Card
              variant="borderless"
              className="glass-panel border-white/[0.03] bg-gradient-to-br from-white/[0.015] to-transparent rounded-[2rem] p-6 shadow-2xl relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 p-8 opacity-[0.02] text-cyan-400 pointer-events-none">
                <ShieldCheck size={240} />
              </div>

              <div className="relative z-10">
                <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-4">
                  <div className="flex items-center gap-3">
                    <ShieldCheck className="text-cyan-400 h-6 w-6" />
                    <div>
                      <h2 className="text-sm font-black uppercase tracking-[0.2em] text-white m-0">
                        Candidate Review & Human Gate Console
                      </h2>
                      <span className="text-[10px] text-gray-500 font-mono mt-0.5 block">
                        AUTOMATED VERIFICATION SCORING & MANUAL DELIVERY AUTHORIZATION GATE
                      </span>
                    </div>
                  </div>

                  {candidateReview && (
                    <div className="flex gap-2">
                      <Tag color={
                        candidateReview.status === "APPROVED_FOR_DELIVERY" || candidateReview.status === "DELIVERY_PACKAGE_READY" ? "success" :
                        candidateReview.status === "REJECTED" ? "error" :
                        candidateReview.status === "REVISION_REQUESTED" ? "orange" : "gold"
                      } className="font-black px-3 py-1 font-mono uppercase rounded-lg">
                        {candidateReview.status.replace(/_/g, " ")}
                      </Tag>
                    </div>
                  )}
                </div>

                {/* Sub-tabs Navigation */}
                <div className="flex border-b border-white/5 pb-3 mb-6 gap-2 overflow-x-auto">
                  <button
                    onClick={() => setReviewActiveTab("details")}
                    className={`flex items-center gap-1.5 py-1.5 px-4 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                      reviewActiveTab === "details"
                        ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                        : "bg-transparent border-transparent text-gray-500 hover:text-white"
                    }`}
                  >
                    <FileText size={12} /> İnceleme detayları
                  </button>
                  <button
                    onClick={() => setReviewActiveTab("risk")}
                    className={`flex items-center gap-1.5 py-1.5 px-4 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                      reviewActiveTab === "risk"
                        ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                        : "bg-transparent border-transparent text-gray-500 hover:text-white"
                    }`}
                  >
                    <ShieldAlert size={12} /> Risk değerlendirmesi
                  </button>
                  <button
                    onClick={() => setReviewActiveTab("quality")}
                    className={`flex items-center gap-1.5 py-1.5 px-4 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                      reviewActiveTab === "quality"
                        ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                        : "bg-transparent border-transparent text-gray-500 hover:text-white"
                    }`}
                  >
                    <Activity size={12} /> Kalite skor kartı
                  </button>
                  <button
                    onClick={() => setReviewActiveTab("decision")}
                    className={`flex items-center gap-1.5 py-1.5 px-4 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                      reviewActiveTab === "decision"
                        ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                        : "bg-transparent border-transparent text-gray-500 hover:text-white"
                    }`}
                  >
                    <ListTodo size={12} /> Operatör kararı
                  </button>
                  <button
                    onClick={() => setReviewActiveTab("delivery")}
                    className={`flex items-center gap-1.5 py-1.5 px-4 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer whitespace-nowrap ${
                      reviewActiveTab === "delivery"
                        ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                        : "bg-transparent border-transparent text-gray-500 hover:text-white"
                    }`}
                  >
                    <FileArchive size={12} /> Teslimat paketi
                  </button>
                </div>

                {/* Sub-tab Contents */}
                {reviewActiveTab === "details" && (
                  <div className="space-y-6">
                    {!candidateReview ? (
                      <div className="py-12 text-center bg-black/20 rounded-3xl border border-white/5 space-y-4">
                        <ShieldAlert className="h-10 w-10 text-cyan-400 mx-auto animate-pulse" />
                        <div>
                          <div className="text-xs font-black uppercase tracking-wider text-white">
                            Aday incelemesi henüz yapılmadı
                          </div>
                          <div className="text-[10px] text-gray-600 mt-1 max-w-sm mx-auto font-mono">
                            Oluşturulan aday dosyaları değerlendirmek için otomatik skor kartını ve risk tarayıcılarını çalıştırın.
                          </div>
                        </div>
                        <Button
                          type="primary"
                          onClick={handleRunCandidateReview}
                          loading={isSubmitting}
                          className="bg-cyan-500 hover:bg-cyan-600 border-none font-black italic tracking-widest uppercase px-6 py-2.5 rounded-xl text-black shadow-lg"
                        >
                          Otomatik aday incelemesini çalıştır
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Scores KPI Panel */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                          <div className="bg-black/40 border border-white/5 p-4 rounded-2xl flex items-center justify-between">
                            <div>
                              <span className="text-[9px] font-mono text-gray-500 uppercase block mb-1">Kalite skoru</span>
                              <span className="text-2xl font-black text-emerald-400 font-mono">{candidateReview.quality_score * 100}%</span>
                            </div>
                            <CheckCircle2 className="text-emerald-400/20 h-10 w-10" />
                          </div>

                          <div className="bg-black/40 border border-white/5 p-4 rounded-2xl flex items-center justify-between">
                            <div>
                              <span className="text-[9px] font-mono text-gray-500 uppercase block mb-1">Risk skoru</span>
                              <span className="text-2xl font-black text-cyan-400 font-mono">{candidateReview.risk_score * 100}%</span>
                            </div>
                            <Activity className="text-cyan-400/20 h-10 w-10" />
                          </div>

                          <div className="bg-black/40 border border-white/5 p-4 rounded-2xl flex items-center justify-between">
                            <div>
                              <span className="text-[9px] font-mono text-gray-500 uppercase block mb-1">Risk seviyesi</span>
                              <span className={`text-xl font-black font-mono uppercase block ${
                                candidateReview.risk_level === "HIGH" ? "text-red-400" :
                                candidateReview.risk_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400"
                              }`}>{candidateReview.risk_level}</span>
                            </div>
                            <ShieldAlert className="text-white/5 h-10 w-10" />
                          </div>
                        </div>

                        {/* Scanned Details */}
                        <Row gutter={[24, 24]}>
                          <Col xs={24} md={12}>
                            <div className="bg-black/20 p-4 rounded-2xl border border-white/5 h-full">
                              <span className="text-xs font-black uppercase tracking-wider text-cyan-400 block mb-3">
                                Öneriler ve iyileştirmeler
                              </span>
                              <ul className="space-y-2 text-xs text-gray-400 pl-4 list-disc font-mono">
                                {candidateReview.recommendations.map((rec, idx) => (
                                  <li key={idx} className="leading-relaxed">{rec}</li>
                                ))}
                                {candidateReview.recommendations.length === 0 && (
                                  <span className="text-gray-500 italic block">Aktif öneri yok.</span>
                                )}
                              </ul>
                            </div>
                          </Col>

                          <Col xs={24} md={12}>
                            <div className="bg-black/20 p-4 rounded-2xl border border-white/5 h-full">
                              <span className="text-xs font-black uppercase tracking-wider text-amber-500 block mb-3">
                                Bilinen sınırlamalar ve kısıtlar
                              </span>
                              <ul className="space-y-2 text-xs text-gray-400 pl-4 list-disc font-mono">
                                {candidateReview.limitations.map((lim, idx) => (
                                  <li key={idx} className="leading-relaxed">{lim}</li>
                                ))}
                                {candidateReview.limitations.length === 0 && (
                                  <span className="text-gray-500 italic block">Tanımlanmış sınırlama yok.</span>
                                )}
                              </ul>
                            </div>
                          </Col>
                        </Row>

                        <div className="flex justify-end gap-3 mt-4">
                          <Button
                            type="dashed"
                            onClick={handleRunCandidateReview}
                            loading={isSubmitting}
                            className="bg-transparent border-white/10 hover:border-cyan-500/30 text-gray-400 hover:text-white rounded-xl text-xs"
                          >
                            Doğrulama incelemesini yeniden çalıştır
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {reviewActiveTab === "risk" && (
                  <div className="space-y-6">
                    {!riskAssessment ? (
                      <div className="py-8 text-center text-gray-500 font-mono text-[10px] uppercase">
                        Risk değerlendirmesi henüz hesaplanmadı. Önce Candidate Review çalıştırın.
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Risk Gauge */}
                        <div className="bg-black/40 border border-white/5 p-4 rounded-2xl">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-black uppercase tracking-widest text-white block">
                              Otomatik yapısal tarayıcı risk skoru: {riskAssessment.risk_score * 100}%
                            </span>
                            <Tag color={
                              riskAssessment.risk_level === "HIGH" ? "error" :
                              riskAssessment.risk_level === "MEDIUM" ? "warning" : "success"
                            } className="font-black rounded px-2 m-0 uppercase font-mono tracking-widest">{riskAssessment.risk_level}</Tag>
                          </div>
                          <div className="w-full bg-white/5 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-all ${
                                riskAssessment.risk_level === "HIGH" ? "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]" :
                                riskAssessment.risk_level === "MEDIUM" ? "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]" : "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                              }`}
                              style={{ width: `${riskAssessment.risk_score * 100}%` }}
                            />
                          </div>
                        </div>

                        {/* Scanner Alerts */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <span className="text-xs font-black uppercase tracking-wider text-red-400 block mb-3">
                              Engelleyici riskler ({riskAssessment.blocking_risks.length})
                            </span>
                            <div className="space-y-2">
                              {riskAssessment.blocking_risks.map((risk, idx) => (
                                <div key={idx} className="bg-red-500/[0.02] border border-red-500/10 p-3 rounded-xl text-red-400 font-mono text-[10px] flex items-start gap-2 uppercase leading-normal">
                                  <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" />
                                  <span>{risk}</span>
                                </div>
                              ))}
                              {riskAssessment.blocking_risks.length === 0 && (
                                <div className="text-[10px] text-gray-500 font-mono bg-black/20 p-3 rounded-xl border border-white/5 italic">
                                  Engelleyici risk bulunmadı. Doğrulama kontrolleri geçti.
                                </div>
                              )}
                            </div>
                          </div>

                          <div>
                            <span className="text-xs font-black uppercase tracking-wider text-amber-500 block mb-3">
                              Kod tarayıcı uyarıları ({riskAssessment.warnings.length})
                            </span>
                            <div className="space-y-2">
                              {riskAssessment.warnings.map((warn, idx) => (
                                <div key={idx} className="bg-amber-500/[0.02] border border-amber-500/10 p-3 rounded-xl text-amber-400 font-mono text-[10px] flex items-start gap-2 leading-normal">
                                  <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" />
                                  <span>{warn}</span>
                                </div>
                              ))}
                              {riskAssessment.warnings.length === 0 && (
                                <div className="text-[10px] text-gray-500 font-mono bg-black/20 p-3 rounded-xl border border-white/5 italic">
                                  Güvenlik veya containment uyarısı tespit edilmedi.
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {reviewActiveTab === "quality" && (
                  <div className="space-y-6">
                    {!qualityScorecard ? (
                      <div className="py-8 text-center text-gray-500 font-mono text-[10px] uppercase">
                        Kalite skor kartı henüz hesaplanmadı. Önce Candidate Review çalıştırın.
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Summary Scorecard */}
                        <div className="bg-black/40 border border-white/5 p-4 rounded-2xl flex items-center justify-between">
                          <div>
                            <span className="text-xs font-black uppercase tracking-widest text-white block mb-1">
                              Doğrulama kalite skor kartı: {qualityScorecard.score} / {qualityScorecard.max_score}
                            </span>
                            <span className="text-[10px] text-gray-500 font-mono uppercase block">
                              DETERMINISTIK AĞIRLIKLI DEĞERLENDİRME SKORLAYICISI
                            </span>
                          </div>
                          <Tag color={qualityScorecard.passed ? "success" : "error"} className="font-black rounded px-3 py-1 font-mono uppercase tracking-widest">
                            {qualityScorecard.passed ? "PASSED" : "FAILED"}
                          </Tag>
                        </div>

                        {/* Checks list */}
                        <div className="space-y-3 font-mono text-xs">
                          <div className="flex items-center justify-between bg-white/[0.01] hover:bg-white/[0.02] border border-white/5 p-3 rounded-xl transition-all">
                            <span className="text-gray-400 uppercase">1. Candidate manifest dosyası doğrulaması</span>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">Ağırlık: 40%</span>
                              {qualityScorecard.candidate_manifest_exists ? (
                                <Tag color="success" className="px-2 font-black rounded-lg m-0"><Check size={12} className="inline mr-1" /> VALID</Tag>
                              ) : (
                                <Tag color="error" className="px-2 font-black rounded-lg m-0"><X size={12} className="inline mr-1" /> MISSING</Tag>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center justify-between bg-white/[0.01] hover:bg-white/[0.02] border border-white/5 p-3 rounded-xl transition-all">
                            <span className="text-gray-400 uppercase">2. Doğrulama test paketi çalıştırması</span>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">Ağırlık: 40%</span>
                              {qualityScorecard.verification_report_passed ? (
                                <Tag color="success" className="px-2 font-black rounded-lg m-0"><Check size={12} className="inline mr-1" /> ALL PASSED</Tag>
                              ) : (
                                <Tag color="error" className="px-2 font-black rounded-lg m-0"><X size={12} className="inline mr-1" /> FAILED TESTS</Tag>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center justify-between bg-white/[0.01] hover:bg-white/[0.02] border border-white/5 p-3 rounded-xl transition-all">
                            <span className="text-gray-400 uppercase">3. Sandbox yapısal sınır containment kontrolü</span>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">Ağırlık: 20%</span>
                              {qualityScorecard.sandbox_boundary_respected ? (
                                <Tag color="success" className="px-2 font-black rounded-lg m-0"><Check size={12} className="inline mr-1" /> CONTAINED</Tag>
                              ) : (
                                <Tag color="error" className="px-2 font-black rounded-lg m-0"><X size={12} className="inline mr-1" /> BREACHED</Tag>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {reviewActiveTab === "decision" && (
                  <div className="space-y-6">
                    {candidateReview && (candidateReview.status === "APPROVED_FOR_DELIVERY" || candidateReview.status === "DELIVERY_PACKAGE_READY" || candidateReview.status === "REJECTED") ? (
                      <div className="bg-black/30 border border-white/5 rounded-3xl p-6 text-center space-y-4 font-mono">
                        <CheckCircle2 className="h-10 w-10 text-cyan-400 mx-auto" />
                        <div>
                          <div className="text-sm font-black uppercase text-white tracking-wider">İnsan kararı tamamlandı</div>
                          <div className="text-xs text-cyan-400 mt-1 uppercase tracking-widest">{candidateReview.status}</div>
                        </div>
                        <Divider className="border-white/5 my-2" />
                        <div className="text-xs text-gray-500 max-w-md mx-auto uppercase">
                          Manuel Human Gate bu aday paketini işledi. Sıralı kararlar Delivery Package alt sekmesindeki teslimat log akışında incelenebilir.
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Operator decision inputs */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-4">
                            <div>
                              <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 block mb-1.5">
                                Operatör ID
                              </span>
                              <Input
                                value={gateOperatorId}
                                onChange={(e) => setGateOperatorId(e.target.value)}
                                placeholder="örn. OPERATOR-01"
                                className="bg-black/40 border-white/10 hover:border-cyan-500/30 focus:border-cyan-500 text-white rounded-xl py-2 px-3 font-mono text-xs focus:shadow-none"
                              />
                            </div>

                            <div>
                              <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 block mb-1.5">
                                Karar gerekçesi
                              </span>
                              <Input.TextArea
                                value={gateRationale}
                                onChange={(e) => setGateRationale(e.target.value)}
                                placeholder="Bu aday onayı, revizyonu veya reddi için gerekçe yazın (min. 5 karakter)..."
                                rows={4}
                                className="bg-black/40 border-white/10 hover:border-cyan-500/30 focus:border-cyan-500 text-white rounded-xl py-2 px-3 font-mono text-xs focus:shadow-none"
                              />
                              <div className="text-[9px] text-gray-500 mt-1 uppercase font-mono text-right">
                                {gateRationale.trim().length} / 5 min. karakter
                              </div>
                            </div>
                          </div>

                          <div className="space-y-4">
                            <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 block mb-1">
                              Aksiyon modu seçimi
                            </span>
                            <div className="grid grid-cols-3 gap-2 border-b border-white/5 pb-4 mb-2">
                              <button
                                onClick={() => setGateActiveActionTab("approve")}
                                className={`py-2 px-1 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer ${
                                  gateActiveActionTab === "approve"
                                    ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                                    : "bg-white/[0.01] border-white/5 text-gray-500 hover:text-white"
                                }`}
                              >
                                Teslimatı onayla
                              </button>
                              <button
                                onClick={() => setGateActiveActionTab("revision")}
                                className={`py-2 px-1 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer ${
                                  gateActiveActionTab === "revision"
                                    ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                                    : "bg-white/[0.01] border-white/5 text-gray-500 hover:text-white"
                                }`}
                              >
                                Revizyon gerekli
                              </button>
                              <button
                                onClick={() => setGateActiveActionTab("reject")}
                                className={`py-2 px-1 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border cursor-pointer ${
                                  gateActiveActionTab === "reject"
                                    ? "bg-red-500/10 border-red-500/30 text-red-400"
                                    : "bg-white/[0.01] border-white/5 text-gray-500 hover:text-white"
                                }`}
                              >
                                Adayı reddet
                              </button>
                            </div>

                            {/* Approve Content */}
                            {gateActiveActionTab === "approve" && (
                              <div className="space-y-4 bg-cyan-500/[0.02] border border-cyan-500/10 p-4 rounded-2xl">
                                <div className="flex items-start gap-3">
                                  <Checkbox
                                    checked={gateRiskAcknowledged}
                                    onChange={(e) => setGateRiskAcknowledged(e.target.checked)}
                                    className="mt-0.5 text-white"
                                  />
                                  <div>
                                    <span className="text-[10px] font-black uppercase tracking-widest text-white block">
                                      Delivery manifest güvenlik kilidini onayla
                                    </span>
                                    <span className="text-[9px] font-mono text-gray-500 mt-1 block leading-normal uppercase">
                                      Bu onayın dosyaları yalnızca delivery container içinde paketlediğini doğruluyorum. MERGE ve doğrudan DEPLOY işlemleri engellenmiştir (Apply allowed = false).
                                    </span>
                                  </div>
                                </div>

                                <Button
                                  type="primary"
                                  onClick={handleApproveDelivery}
                                  loading={isSubmitting}
                                  disabled={!gateRiskAcknowledged || gateRationale.trim().length < 5 || !gateOperatorId.trim()}
                                  className="w-full bg-cyan-500 hover:bg-cyan-600 border-none font-black italic tracking-widest uppercase py-4 rounded-xl text-black shadow-lg"
                                >
                                  Teslimat onayını çalıştır
                                </Button>
                              </div>
                            )}

                            {/* Revision Content */}
                            {gateActiveActionTab === "revision" && (
                              <div className="space-y-4 bg-amber-500/[0.02] border border-amber-500/10 p-4 rounded-2xl">
                                <div>
                                  <span className="text-[10px] font-black uppercase tracking-widest text-amber-500 block mb-2">
                                    Aday revizyon yönergeleri
                                  </span>
                                  <Input.TextArea
                                    value={gateRevisionNotes}
                                    onChange={(e) => setGateRevisionNotes(e.target.value)}
                                    placeholder="Bu aday onaylanmadan önce gereken değişiklikleri veya yönergeleri yazın..."
                                    rows={3}
                                    className="bg-black/40 border-white/10 hover:border-amber-500/30 focus:border-amber-500 text-white rounded-xl py-2 px-3 font-mono text-xs focus:shadow-none"
                                  />
                                </div>

                                <Button
                                  type="primary"
                                  onClick={handleRequestCandidateRevision}
                                  loading={isSubmitting}
                                  disabled={!gateRevisionNotes.trim() || gateRationale.trim().length < 5 || !gateOperatorId.trim()}
                                  className="w-full bg-amber-500 hover:bg-amber-600 border-none font-black italic tracking-widest uppercase py-4 rounded-xl text-black shadow-lg"
                                >
                                  Aday revizyonu iste
                                </Button>
                              </div>
                            )}

                            {/* Reject Content */}
                            {gateActiveActionTab === "reject" && (
                              <div className="space-y-4 bg-red-500/[0.02] border border-red-500/10 p-4 rounded-2xl">
                                <div className="flex gap-3 text-red-500 bg-red-500/[0.05] p-3 rounded-xl border border-red-500/20 text-[10px] font-mono uppercase leading-normal">
                                  <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
                                  <div>
                                    <strong>Uyarı: Reddetme işlemi kalıcıdır.</strong>
                                    <span className="block mt-1 text-gray-500">
                                      Bu işlem aday değerlendirme geçidini kalıcı olarak kapatır.
                                    </span>
                                  </div>
                                </div>

                                <Button
                                  type="primary"
                                  danger
                                  onClick={handleRejectCandidate}
                                  loading={isSubmitting}
                                  disabled={gateRationale.trim().length < 5 || !gateOperatorId.trim()}
                                  className="w-full bg-red-500 hover:bg-red-600 border-none font-black italic tracking-widest uppercase py-4 rounded-xl text-white shadow-lg"
                                >
                                  Adayı kalıcı olarak reddet
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {reviewActiveTab === "delivery" && (
                  <div className="space-y-6">
                    {!deliveryManifest ? (
                      <div className="py-12 text-center bg-black/20 rounded-3xl border border-white/5">
                        <Lock className="h-8 w-8 text-gray-600 mx-auto mb-3" />
                        <div className="text-xs font-black uppercase tracking-wider text-gray-500">
                          Teslimat paketi kilitli
                        </div>
                        <div className="text-[10px] text-gray-600 mt-1 max-w-sm mx-auto font-mono">
                          Güvenli final çıktıları üretmek için Operator Decision formunda sandbox aday paketini onaylayın.
                        </div>
                      </div>
                    ) : (
                      <Row gutter={[24, 24]}>
                        {/* Delivery Specs */}
                        <Col xs={24} lg={14} className="space-y-6">
                          <div className="bg-black/40 border border-white/5 p-4 rounded-2xl space-y-3 font-mono text-[10px]">
                            <div className="flex justify-between items-center">
                              <span className="text-gray-500">DELIVERY ID:</span>
                              <span className="text-white font-bold">{deliveryManifest.delivery_id}</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-gray-500">OLUŞTURULMA:</span>
                              <span className="text-white">{new Date(deliveryManifest.created_at).toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-gray-500">OPERATOR ID:</span>
                              <span className="text-white">{deliveryManifest.operator_id}</span>
                            </div>
                            <div className="flex justify-between items-center border-t border-white/5 pt-2 mt-2">
                              <span className="text-gray-500 font-bold uppercase">Production Apply güvenlik durumu:</span>
                              {deliveryManifest.production_apply_allowed ? (
                                <Tag color="success" className="px-2 font-black rounded-lg m-0">ALLOWED</Tag>
                              ) : (
                                <Tag color="error" className="px-2 font-black rounded-lg m-0">BLOCKED (APPLY DISABLED)</Tag>
                              )}
                            </div>
                          </div>

                          {/* Copied files */}
                          <div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-2">
                              Kopyalanan release dosyaları ({deliveryManifest.files.length})
                            </span>
                            <div className="space-y-2">
                              {deliveryManifest.files.map((file, idx) => (
                                <div key={idx} className="bg-[#030712] border border-white/5 rounded-xl p-3 font-mono text-[9px] space-y-1">
                                  <div className="flex items-center justify-between text-white font-bold">
                                    <span>{file.path}</span>
                                    <span className="text-gray-500">{(file.size_bytes / 1024).toFixed(2)} KB</span>
                                  </div>
                                  <div className="text-gray-600 text-[8px] truncate">
                                    SHA256: {file.checksum}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Release notes */}
                          {releaseNotes && (
                            <div>
                              <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-2">
                                Generated Release Notes Document
                              </span>
                              <pre className="bg-[#030712] border border-white/5 rounded-xl p-4 font-mono text-[9px] text-gray-300 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                                {releaseNotes}
                              </pre>
                            </div>
                          )}
                        </Col>

                        {/* Sequential Delivery Decision logs */}
                        <Col xs={24} lg={10}>
                          <div className="bg-black/20 border border-white/5 p-4 rounded-2xl">
                            <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-3 border-b border-white/5 pb-2">
                              Candidate Gate Log Stream
                            </span>
                            <div className="space-y-4 max-h-[350px] overflow-y-auto pr-2">
                              {deliveryLogs.length === 0 ? (
                                <div className="text-[10px] text-gray-500 font-mono text-center italic py-4">No candidate actions logged.</div>
                              ) : (
                                deliveryLogs.map((log) => (
                                  <div key={log.decision_id} className="bg-[#030712] border border-white/5 p-3 rounded-xl font-mono text-[9px] space-y-1">
                                    <div className="flex items-center justify-between">
                                      <Tag color={
                                        log.action === "APPROVE_DELIVERY" ? "success" :
                                        log.action === "REQUEST_REVISION" ? "orange" : "error"
                                      } className="text-[8px] font-black rounded uppercase px-1 m-0">
                                        {log.action.replace(/_/g, " ")}
                                      </Tag>
                                      <span className="text-gray-500">{new Date(log.created_at).toLocaleTimeString()}</span>
                                    </div>
                                    <div className="text-gray-400 mt-1">
                                      OPERATOR: {log.operator_id}
                                    </div>
                                    <div className="text-gray-300 bg-black/30 p-1.5 rounded mt-1 border border-white/[0.02]">
                                      {log.rationale}
                                    </div>
                                    {log.details && log.details.revision_notes && (
                                      <div className="text-amber-500 bg-amber-500/[0.02] border border-amber-500/10 p-1.5 rounded mt-1">
                                        REVISION: {log.details.revision_notes}
                                      </div>
                                    )}
                                  </div>
                                ))
                              )}
                            </div>
                          </div>
                        </Col>
                      </Row>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* Phase 12 Final Decision Gate Console Card */}
      {["READY_FOR_FINAL_OPERATOR_DECISION", "FINAL_APPROVED", "FINAL_REJECTED", "FINAL_REVISION_REQUESTED", "PROJECT_CLOSED"].includes(project_brief.status) && (
        <Row className="mt-8">
          <Col span={24}>
            <Card
              className="bg-[#0b101a] border-white/5 rounded-3xl overflow-hidden shadow-2xl relative"
              styles={{ body: { padding: 0 } }}
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-blue-900/40 via-purple-900/30 to-[#0b101a] p-6 border-b border-white/5 relative">
                <div className="flex items-start justify-between">
                  <div className="space-y-2 relative z-10">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-2xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                        <FileArchive className="h-5 w-5 text-blue-400" />
                      </div>
                      <div>
                        <Title level={4} className="!text-white !m-0 font-black tracking-tight">
                          Final karar ve release arşivi
                        </Title>
                        <Text className="text-gray-400 font-mono text-[10px] uppercase tracking-widest">
                          Phase 12 / Terminal teslimat geçidi
                        </Text>
                      </div>
                    </div>
                  </div>
                  <div>
                    {releaseManifest ? (
                      <Tag color="success" className="px-4 py-1.5 font-black uppercase rounded-xl border-green-500/30 bg-green-500/10 shadow-[0_0_15px_rgba(34,197,94,0.15)] flex items-center gap-2">
                        <ShieldCheck size={14} /> RELEASE ARŞİVİ HAZIR
                      </Tag>
                    ) : (
                      <Tag color="warning" className="px-4 py-1.5 font-black uppercase rounded-xl border-amber-500/30 bg-amber-500/10 shadow-[0_0_15px_rgba(245,158,11,0.15)] flex items-center gap-2">
                        <ListTodo size={14} /> FINAL KARAR BEKLENİYOR
                      </Tag>
                    )}
                  </div>
                </div>
              </div>

              <div className="p-6">
                {/* Tabs */}
                <div className="flex gap-4 mb-6 border-b border-white/5 pb-4 overflow-x-auto custom-scrollbar">
                  {[
                    { key: "decision", label: "Final operatör kararı", icon: <ShieldAlert size={14} /> },
                    { key: "archive", label: "Release arşivi", icon: <FileArchive size={14} /> },
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setFinalActiveActionTab(tab.key as any)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-[10px] uppercase font-black transition-all duration-300 ${
                        finalActiveActionTab === tab.key
                          ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                          : "bg-transparent text-gray-500 hover:text-gray-300 hover:bg-white/5 border border-transparent"
                      }`}
                    >
                      {tab.icon} {tab.label}
                    </button>
                  ))}
                </div>

                {finalActiveActionTab === "decision" && (
                  <div className="space-y-6">
                    {finalDecision ? (
                      <div className="bg-black/30 p-6 rounded-2xl border border-white/5 font-mono text-[10px]">
                        <div className="flex justify-between items-center mb-6">
                          <span className="text-gray-500 font-bold uppercase">Final karar:</span>
                          <Tag color={
                            finalDecision.decision === "FINAL_APPROVED" ? "success" :
                            finalDecision.decision === "FINAL_REJECTED" ? "error" : "orange"
                          } className="m-0 font-black rounded-lg">
                            {finalDecision.decision}
                          </Tag>
                        </div>
                        <div className="space-y-4 text-gray-400">
                          <div className="flex justify-between">
                            <span>Operatör:</span>
                            <span className="text-white">{finalDecision.operator_id}</span>
                          </div>
                          <div>
                            <span className="block mb-1">Gerekçe:</span>
                            <div className="bg-black/50 p-3 rounded text-gray-300 border border-white/5">{finalDecision.rationale}</div>
                          </div>
                          {finalDecision.revision_notes && (
                            <div>
                              <span className="block mb-1 text-amber-500">Revizyon notları:</span>
                              <div className="bg-amber-500/10 p-3 rounded text-amber-500 border border-amber-500/20">{finalDecision.revision_notes}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <Row gutter={[24, 24]}>
                        <Col xs={24} lg={16}>
                          <div className="bg-[#030712] border border-white/5 rounded-2xl p-6">
                            <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-6">
                              Operatör onayı
                            </span>
                            
                            <div className="space-y-6">
                              <div>
                                <label className="text-[10px] font-mono text-gray-500 uppercase block mb-2">Operatör ID</label>
                                <Input 
                                  value={finalOperatorId}
                                  onChange={(e) => setFinalOperatorId(e.target.value)}
                                  className="bg-black/50 border-white/10 text-white font-mono"
                                  placeholder="örn. OPERATOR-01"
                                />
                              </div>
                              
                              <div>
                                <label className="text-[10px] font-mono text-gray-500 uppercase block mb-2">Karar gerekçesi</label>
                                <Input.TextArea 
                                  value={finalRationale}
                                  onChange={(e) => setFinalRationale(e.target.value)}
                                  className="bg-black/50 border-white/10 text-white font-mono min-h-[100px]"
                                  placeholder="Final onay, ret veya revizyon için detaylı gerekçe yazın..."
                                />
                              </div>

                              <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                                <Checkbox 
                                  checked={finalRiskAcknowledged}
                                  onChange={(e) => setFinalRiskAcknowledged(e.target.checked)}
                                  className="text-amber-500 font-mono text-[10px]"
                                >
                                  Bu final onayın release arşivini kilitlediğini ve production'a doğrudan merge yapmadığını onaylıyorum.
                                </Checkbox>
                              </div>

                              <div className="flex gap-4 pt-4 border-t border-white/5">
                                <Button 
                                  type="primary"
                                  onClick={handleFinalApprove}
                                  loading={isSubmitting}
                                  disabled={!finalOperatorId.trim() || finalRationale.length < 5 || !finalRiskAcknowledged}
                                  className="flex-1 bg-green-600 hover:bg-green-500 border-none font-black tracking-widest uppercase py-6 rounded-xl"
                                >
                                  Final Approve & Archive
                                </Button>
                              </div>
                              
                              <Divider className="border-white/5 my-2 text-gray-600 font-mono text-[10px]">OR</Divider>
                              
                              <div>
                                <label className="text-[10px] font-mono text-gray-500 uppercase block mb-2">Revision Notes (Required for Revision)</label>
                                <Input.TextArea 
                                  value={finalRevisionNotes}
                                  onChange={(e) => setFinalRevisionNotes(e.target.value)}
                                  className="bg-black/50 border-white/10 text-white font-mono min-h-[80px]"
                                  placeholder="Detail what needs to be fixed before final approval..."
                                />
                              </div>
                              
                              <div className="flex gap-4">
                                <Button 
                                  onClick={handleFinalRequestRevision}
                                  loading={isSubmitting}
                                  disabled={!finalOperatorId.trim() || finalRationale.length < 5 || !finalRevisionNotes.trim()}
                                  className="flex-1 bg-amber-500/10 text-amber-500 hover:text-amber-400 hover:bg-amber-500/20 border border-amber-500/30 font-black tracking-widest uppercase py-6 rounded-xl"
                                >
                                  Request Revision
                                </Button>
                                
                                <Button 
                                  onClick={handleFinalReject}
                                  loading={isSubmitting}
                                  disabled={!finalOperatorId.trim() || finalRationale.length < 5}
                                  className="flex-1 bg-red-500/10 text-red-500 hover:text-red-400 hover:bg-red-500/20 border border-red-500/30 font-black tracking-widest uppercase py-6 rounded-xl"
                                >
                                  Final Reject
                                </Button>
                              </div>
                            </div>
                          </div>
                        </Col>
                        
                        <Col xs={24} lg={8}>
                          <div className="bg-black/20 border border-white/5 p-4 rounded-2xl">
                            <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-3 border-b border-white/5 pb-2">
                              Decision Log Stream
                            </span>
                            <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                              {finalDecisionLogs.length === 0 ? (
                                <div className="text-[10px] text-gray-500 font-mono text-center italic py-4">No final decisions logged.</div>
                              ) : (
                                finalDecisionLogs.map((log) => (
                                  <div key={log.decision_id} className="bg-[#030712] border border-white/5 p-3 rounded-xl font-mono text-[9px] space-y-1">
                                    <div className="flex items-center justify-between">
                                      <Tag color={
                                        log.action === "FINAL_APPROVED" ? "success" :
                                        log.action === "FINAL_REVISION_REQUESTED" ? "orange" : "error"
                                      } className="text-[8px] font-black rounded uppercase px-1 m-0">
                                        {log.action.replace(/_/g, " ")}
                                      </Tag>
                                      <span className="text-gray-500">{new Date(log.created_at).toLocaleTimeString()}</span>
                                    </div>
                                    <div className="text-gray-400 mt-1">
                                      OPERATOR: {log.operator_id}
                                    </div>
                                    <div className="text-gray-300 bg-black/30 p-1.5 rounded mt-1 border border-white/[0.02]">
                                      {log.rationale}
                                    </div>
                                  </div>
                                ))
                              )}
                            </div>
                          </div>
                        </Col>
                      </Row>
                    )}
                  </div>
                )}

                {finalActiveActionTab === "archive" && (
                  <div className="space-y-6">
                    {!releaseManifest ? (
                      <div className="py-12 text-center bg-black/20 rounded-3xl border border-white/5">
                        <Lock className="h-8 w-8 text-gray-600 mx-auto mb-3" />
                        <div className="text-xs font-black uppercase tracking-wider text-gray-500">
                          Archive Not Generated
                        </div>
                        <div className="text-[10px] text-gray-600 mt-1 max-w-sm mx-auto font-mono">
                          Approve the final decision to generate the release archive and closure report.
                        </div>
                      </div>
                    ) : (
                      <Row gutter={[24, 24]}>
                        <Col xs={24} lg={12} className="space-y-6">
                          <div className="bg-black/40 border border-white/5 p-4 rounded-2xl space-y-3 font-mono text-[10px]">
                            <div className="flex justify-between items-center">
                              <span className="text-gray-500">RELEASE ID:</span>
                              <span className="text-white font-bold">{releaseManifest.release_id}</span>
                            </div>
                            <div className="flex justify-between items-center border-t border-white/5 pt-2 mt-2">
                              <span className="text-gray-500 font-bold uppercase">Archive Status:</span>
                              <Tag color="success" className="px-2 font-black rounded-lg m-0">LOCKED</Tag>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-gray-500">EVIDENCE COUNT:</span>
                              <span className="text-white">{releaseManifest.evidence_count} files</span>
                            </div>
                          </div>
                        </Col>

                        <Col xs={24} lg={12}>
                          {closureReport && (
                            <div>
                              <span className="text-[10px] font-black uppercase tracking-widest text-cyan-400 block mb-2">
                                Generated Closure Report
                              </span>
                              <pre className="bg-[#030712] border border-white/5 rounded-xl p-4 font-mono text-[9px] text-gray-300 overflow-x-auto max-h-96 overflow-y-auto whitespace-pre-wrap">
                                {closureReport}
                              </pre>
                            </div>
                          )}
                        </Col>
                      </Row>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
}
