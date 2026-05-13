export type RuntimeDiagnosticSeverity = "info" | "warning" | "error";

export interface RuntimeDiagnostic {
  id: string;
  severity: RuntimeDiagnosticSeverity;
  title: string;
  evidence: Record<string, unknown>;
  impact: string;
  recommended_action: string;
  auto_repairable: boolean;
  requires_operator_action: boolean;
  tags: string[];
}

export interface RuntimeDiagnosticsResponse {
  diagnostics: RuntimeDiagnostic[];
  count: number;
  timestamp: string;
}

export function compactRuntimeDiagnosticLabel(diagnostic: RuntimeDiagnostic): string {
  switch (diagnostic.id) {
    case "db_fallback_active":
      return "DB fallback";
    case "queue_workers_disabled":
      return "Queue disabled";
    case "redis_unavailable":
      return "Redis down";
    case "observer_write_denied":
      return "Auth role read-only";
    case "profile_mismatch":
      return "Profile mismatch";
    case "ephemeral_workflow_enabled":
      return "Ephemeral workflow";
    case "api_redirect_noise":
      return "API URL guard";
    default:
      return diagnostic.title;
  }
}

export function selectPrimaryRuntimeDiagnostic(diagnostics: RuntimeDiagnostic[]): RuntimeDiagnostic | undefined {
  return (
    diagnostics.find((item) => item.severity === "error") ||
    diagnostics.find((item) => item.severity === "warning") ||
    diagnostics.find((item) => item.id !== "api_redirect_noise")
  );
}
