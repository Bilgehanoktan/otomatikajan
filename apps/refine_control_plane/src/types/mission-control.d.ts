
export interface SqvMeta {
  is_stale: boolean;
  age_seconds: number;
  source: string;
  endpoint: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  action: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  retries: number;
  max_retries: number;
  error?: string;
  dependencies: string[];
  output_summary?: string;
}

export interface Workflow {
  id: string;
  name: string;
  workflow_type: string;
  status: string;
  source: string;
  steps: WorkflowStep[];
  context_keys: string[];
  payload: Record<string, any>;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  final_report?: string;
  __sqv_meta?: SqvMeta;
}

export interface Incident {
  id: string;
  incident_type: string;
  status: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  project_id?: string;
  created_at: string;
  payload?: Record<string, any>;
  __sqv_meta?: SqvMeta;
}

export interface DeploymentProposal {
  id: string;
  parameter: string;
  current_value: string;
  proposed_value: string;
  reason: string;
  confidence: number;
  impact: string;
  status: 'pending' | 'approved' | 'rejected';
  __sqv_meta?: SqvMeta;
}
export interface ApprovalRequest {
  id: string;
  project_id: string;
  request_type: string;
  reason: string;
  status: string;
  created_at: string;
  agent_id?: string;
  decided_by?: string;
  decided_at?: string;
  comment?: string;
  __sqv_meta?: SqvMeta;
}

export interface SystemImprovement {
  id: string;
  opportunity_id: string;
  target_file: string;
  instruction: string;
  proposed_patch: string;
  status: string;
  created_at: string;
  risk_score?: number;
  test_results?: any;
  __sqv_meta?: SqvMeta;
}
