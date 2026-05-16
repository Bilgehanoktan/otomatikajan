'use client';

import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  NoSymbol, 
  Beaker,
  Search,
  CheckCircle2,
  ClipboardCheck,
  RefreshCw,
  UserCircle,
  Check,
  X
} from 'lucide-react';

interface CognitiveCheck {
  id: string;
  source_type: string;
  source_id: string;
  agent_name: string;
  output_type: string;
  status: string;
  integrity_score: number;
  hallucination_score: number;
  evidence_grounding_score: number;
  semantic_drift_score: number;
  claim_verification_score: number;
  decision: string;
  reason: string;
  created_at: string;
}

interface Finding {
  id: string;
  finding_type: string;
  severity: string;
  description: string;
  unsupported_reference: string;
  suggested_action: string;
  blocked: boolean;
}

interface Claim {
  id: string;
  claim_text: string;
  claim_type: string;
  verification_status: string;
  confidence: number;
  failure_reason: string;
}

export default function CognitiveIntegrityCenterPanel() {
  const [checks, setChecks] = useState<CognitiveCheck[]>([]);
  const [selectedCheck, setSelectedCheck] = useState<CognitiveCheck | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'ALL' | 'BLOCKED' | 'REVIEW'>('ALL');
  const [reviewRationale, setReviewRationale] = useState('');
  const [acting, setActing] = useState(false);

  useEffect(() => {
    fetchChecks();
  }, []);

  useEffect(() => {
    // Phase 20: Reactive WebSocket Listener
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/events`;
    
    let socket: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout;

    const connect = () => {
      socket = new WebSocket(wsUrl);
      
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'COGNITIVE_INTEGRITY_CHECK_COMPLETED') {
            console.log('[WS] Cognitive integrity check completed, refreshing...');
            fetchChecks();
          }
        } catch (err) {
          console.error('[WS] Failed to parse message', err);
        }
      };

      socket.onclose = () => {
        console.log('[WS] Connection closed, reconnecting in 5s...');
        reconnectTimer = setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      if (socket) socket.close();
      clearTimeout(reconnectTimer);
    };
  }, []);

  useEffect(() => {
    if (selectedCheck) {
      fetchFindings(selectedCheck.id);
      fetchClaims(selectedCheck.id);
    }
  }, [selectedCheck]);

  const fetchChecks = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ui-repair/cognitive/checks');
      const data = await response.json();
      setChecks(data);
    } catch (error) {
      console.error('Error fetching cognitive checks:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFindings = async (checkId: string) => {
    try {
      const response = await fetch(`/api/v1/ui-repair/cognitive/findings/${checkId}`);
      const data = await response.json();
      setFindings(data);
    } catch (error) {
      console.error('Error fetching findings:', error);
    }
  };

  const fetchClaims = async (checkId: string) => {
    try {
      const response = await fetch(`/api/v1/ui-repair/cognitive/claims/${checkId}`);
      const data = await response.json();
      setClaims(data);
    } catch (error) {
      console.error('Error fetching claims:', error);
    }
  };

  const handleManualReview = async (checkId: string, action: 'approve' | 'reject') => {
    if (!reviewRationale) {
      alert('Please provide a rationale for manual review decision.');
      return;
    }
    setActing(true);
    try {
      const response = await fetch(`/api/v1/ui-repair/cognitive/manual-review/${checkId}/${action}?rationale=${encodeURIComponent(reviewRationale)}`, {
        method: 'POST'
      });
      if (response.ok) {
        setReviewRationale('');
        fetchChecks();
        // Refresh selected check
        if (selectedCheck?.id === checkId) {
          const updatedCheck = { ...selectedCheck, status: action === 'approve' ? 'PASSED' : 'BLOCKED', decision: action === 'approve' ? 'ALLOW' : 'BLOCK_ACTION' };
          setSelectedCheck(updatedCheck as any);
        }
      }
    } catch (error) {
      console.error('Error processing manual review:', error);
    } finally {
      setActing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PASSED': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
      case 'WARNING': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
      case 'FAILED':
      case 'BLOCKED': return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
      case 'MANUAL_REVIEW_REQUIRED': return 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20';
      default: return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-emerald-400';
    if (score >= 0.6) return 'text-amber-400';
    return 'text-rose-400';
  };

  const filteredChecks = checks.filter(c => {
    if (activeTab === 'BLOCKED') return c.status === 'BLOCKED';
    if (activeTab === 'REVIEW') return c.status === 'MANUAL_REVIEW_REQUIRED';
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            Cognitive Integrity Center
          </h2>
          <p className="text-slate-400 text-sm">Zero-trust verification and hallucination detection for agent outputs.</p>
        </div>
        <button 
          onClick={fetchChecks}
          className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
        >
          <RefreshCw className={`w-5 h-5 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Verification Queue */}
        <div className="lg:col-span-1 bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-[700px]">
          <div className="p-4 border-b border-slate-800 flex gap-2">
            {(['ALL', 'BLOCKED', 'REVIEW'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  activeTab === tab 
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {filteredChecks.length === 0 ? (
              <div className="text-center py-20 opacity-20">
                <ClipboardCheck className="w-12 h-12 mx-auto mb-2" />
                <p className="text-xs uppercase font-bold tracking-widest">Queue Empty</p>
              </div>
            ) : filteredChecks.map(check => (
              <button
                key={check.id}
                onClick={() => setSelectedCheck(check)}
                className={`w-full text-left p-4 rounded-xl border transition-all ${
                  selectedCheck?.id === check.id 
                    ? 'bg-slate-800 border-emerald-500/50 ring-1 ring-emerald-500/50' 
                    : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusColor(check.status)}`}>
                    {check.status.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {new Date(check.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-white truncate">{check.agent_name}</h4>
                <p className="text-xs text-slate-400 mb-3">{check.output_type.replace(/_/g, ' ')}</p>
                
                <div className="flex items-center gap-4">
                  <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-1000 ${
                        check.integrity_score >= 0.8 ? 'bg-emerald-500' : 
                        check.integrity_score >= 0.6 ? 'bg-amber-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${check.integrity_score * 100}%` }}
                    />
                  </div>
                  <span className={`text-xs font-mono font-bold ${getScoreColor(check.integrity_score)}`}>
                    {(check.integrity_score * 100).toFixed(0)}%
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Detailed Analysis */}
        <div className="lg:col-span-2 space-y-6 overflow-y-auto h-[700px] pr-2 custom-scrollbar">
          {selectedCheck ? (
            <>
              {/* Header Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Hallucination</p>
                  <p className={`text-xl font-mono font-bold ${getScoreColor(selectedCheck.hallucination_score)}`}>
                    {(selectedCheck.hallucination_score * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Evidence</p>
                  <p className={`text-xl font-mono font-bold ${getScoreColor(selectedCheck.evidence_grounding_score)}`}>
                    {(selectedCheck.evidence_grounding_score * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Semantics</p>
                  <p className={`text-xl font-mono font-bold ${getScoreColor(1 - selectedCheck.semantic_drift_score)}`}>
                    {((1 - selectedCheck.semantic_drift_score) * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Verification</p>
                  <p className={`text-xl font-mono font-bold ${getScoreColor(selectedCheck.claim_verification_score)}`}>
                    {(selectedCheck.claim_verification_score * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              {/* Decision Section */}
              <div className={`p-4 rounded-xl border ${getStatusColor(selectedCheck.status)} flex items-start gap-4`}>
                {selectedCheck.decision === 'BLOCK_ACTION' ? (
                  <NoSymbol className="w-6 h-6 shrink-0" />
                ) : selectedCheck.status === 'PASSED' ? (
                  <CheckCircle2 className="w-6 h-6 shrink-0" />
                ) : (
                  <AlertTriangle className="w-6 h-6 shrink-0" />
                )}
                <div className="flex-1">
                  <h3 className="font-bold text-lg leading-tight">Verification Decision: {selectedCheck.decision}</h3>
                  <p className="opacity-80 text-sm mt-1">{selectedCheck.reason}</p>
                </div>
                
                {selectedCheck.status === 'MANUAL_REVIEW_REQUIRED' && (
                  <div className="flex flex-col gap-2 min-w-[200px]">
                    <textarea 
                      placeholder="Rationale..."
                      value={reviewRationale}
                      onChange={(e) => setReviewRationale(e.target.value)}
                      className="w-full bg-slate-950/50 border border-slate-800 rounded-lg p-2 text-xs text-white focus:ring-1 focus:ring-emerald-500/50 outline-none"
                    />
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleManualReview(selectedCheck.id, 'approve')}
                        disabled={acting}
                        className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white py-1.5 rounded-lg text-xs font-bold flex items-center justify-center gap-1 transition-colors"
                      >
                        <Check className="w-3 h-3" /> Approve
                      </button>
                      <button 
                        onClick={() => handleManualReview(selectedCheck.id, 'reject')}
                        disabled={acting}
                        className="flex-1 bg-rose-600 hover:bg-rose-500 text-white py-1.5 rounded-lg text-xs font-bold flex items-center justify-center gap-1 transition-colors"
                      >
                        <X className="w-3 h-3" /> Reject
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Hallucination Findings */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
                <div className="p-4 border-b border-slate-800 bg-slate-800/30 flex items-center gap-2">
                  <Search className="w-5 h-5 text-rose-400" />
                  <h3 className="font-bold text-white">Hallucination Firewall Findings</h3>
                </div>
                <div className="p-4 space-y-4">
                  {findings.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <ShieldCheck className="w-12 h-12 mx-auto mb-2 opacity-20" />
                      <p>No hallucinations detected in this output.</p>
                    </div>
                  ) : (
                    findings.map(finding => (
                      <div key={finding.id} className="p-4 bg-slate-950/50 rounded-lg border border-slate-800 flex gap-4 animate-in slide-in-from-right-4 duration-300">
                        <div className={`w-1 shrink-0 rounded-full ${
                          finding.severity === 'CRITICAL' ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]' :
                          finding.severity === 'HIGH' ? 'bg-orange-500' : 'bg-amber-500'
                        }`} />
                        <div className="flex-1 space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">{finding.finding_type}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                              finding.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' : 'bg-orange-500/20 text-orange-400'
                            }`}>{finding.severity}</span>
                          </div>
                          <p className="text-sm text-white">{finding.description}</p>
                          {finding.unsupported_reference && (
                            <div className="bg-slate-800/50 p-2 rounded text-[11px] font-mono text-rose-300 border border-rose-500/10">
                              Ref: {finding.unsupported_reference}
                            </div>
                          )}
                          <div className="flex items-center gap-2 text-[11px] text-slate-400">
                            <Beaker className="w-4 h-4 text-blue-400" />
                            <span>Remediation: {finding.suggested_action}</span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Claims & Grounding */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
                <div className="p-4 border-b border-slate-800 bg-slate-800/30 flex items-center gap-2">
                  <ClipboardCheck className="w-5 h-5 text-emerald-400" />
                  <h3 className="font-bold text-white">Claim Verification Engine</h3>
                </div>
                <div className="p-4 space-y-3">
                  <p className="text-xs text-slate-500 mb-2">Automated decomposition and factual grounding of LLM claims.</p>
                  <div className="space-y-2">
                    {claims.length === 0 ? (
                      <div className="text-center py-8 text-slate-600 italic text-xs">
                        No explicit claims extracted for verification.
                      </div>
                    ) : claims.map((claim, i) => (
                      <div key={claim.id} className="flex flex-col gap-2 p-3 bg-slate-950/50 rounded-lg border border-slate-800/50 animate-in slide-in-from-left-4 duration-300">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${
                            claim.verification_status === 'VERIFIED' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 
                            claim.verification_status === 'CONTRADICTED' ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]' : 'bg-slate-600'
                          }`} />
                          <span className="text-xs text-white flex-1 leading-relaxed">{claim.claim_text}</span>
                          <span className={`text-[10px] font-bold ${
                            claim.verification_status === 'VERIFIED' ? 'text-emerald-400' : 
                            claim.verification_status === 'CONTRADICTED' ? 'text-rose-400' : 'text-slate-400'
                          }`}>
                            {claim.verification_status} ({(claim.confidence * 100).toFixed(0)}%)
                          </span>
                        </div>
                        {claim.failure_reason && (
                          <div className="ml-5 text-[10px] text-rose-400/70 italic">
                            Reason: {claim.failure_reason}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
              <div className="p-8 bg-slate-900/50 border border-slate-800 border-dashed rounded-3xl group">
                <ShieldCheck className="w-24 h-24 opacity-10 mx-auto group-hover:opacity-30 transition-opacity duration-1000" />
              </div>
              <p className="text-lg font-medium text-slate-300">Select a verification check to view detailed analysis</p>
              <p className="text-sm max-w-md text-center">Every agent output is audited for hallucinations, semantic drift, and factual grounding before being presented to operators.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
