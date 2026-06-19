'use client';

import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  ClipboardCheck,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Fingerprint,
  Key,
  Server,
  Lock,
  Globe,
  Shield
} from 'lucide-react';
import { safeFetchJson } from '@/lib/api';
import ThreatModelingPanel from './ThreatModelingPanel';
import RedTeamCenterPanel from './RedTeamCenterPanel';
import AutonomousShieldCenterPanel from './AutonomousShieldCenterPanel';
import { ShieldOff, ShieldCheck as ShieldCheckIcon } from 'lucide-react';

interface PostureScore {
  overall_score: number;
  identity_score: number;
  policy_score: number;
  isolation_score: number;
  governance_score: number;
  evidence_score: number;
  posture_level: string;
  created_at: string;
}

interface Control {
  control_key: string;
  domain: string;
  title: string;
  description: string;
  severity: string;
}

interface Finding {
  id: string;
  control_key: string;
  status: string;
  rationale: string;
  last_check_at: string;
}

interface Certification {
  id: string;
  cert_id: string;
  overall_score: number;
  compliance_score: number;
  posture_level: string;
  certified_by: string;
  created_at: string;
}

export default function SecurityPostureCenterPanel() {
  const [posture, setPosture] = useState<PostureScore | null>(null);
  const [controls, setControls] = useState<Control[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [certs, setCerts] = useState<Certification[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [certifying, setCertifying] = useState(false);
  const [remediating, setRemediating] = useState<Record<string, boolean>>({});
  const [remediationPlans, setRemediationPlans] = useState<any[]>([]);
  const [fixAttempts, setFixAttempts] = useState<any[]>([]);
  const [remediationSummary, setRemediationSummary] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'posture' | 'threat' | 'redteam' | 'shield'>('posture');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [postureData, controlsData, findingsData, certsData] = await Promise.all([
        safeFetchJson<PostureScore>('/api/v1/ui-repair/security/posture'),
        safeFetchJson<Control[]>('/api/v1/ui-repair/security/controls'),
        safeFetchJson<Finding[]>('/api/v1/ui-repair/security/findings'),
        safeFetchJson<Certification[]>('/api/v1/ui-repair/security/certifications')
      ]);
      
      setPosture(postureData);
      setControls(controlsData);
      setFindings(findingsData);
      setCerts(certsData);
      
      fetchRemediationData();
    } catch (err) {
      console.error('Failed to fetch security data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunScan = async () => {
    setScanning(true);
    try {
      const data = await safeFetchJson<PostureScore>('/api/v1/ui-repair/security/scan', { method: 'POST' });
      setPosture(data);
      // Refresh findings
      const findingsData = await safeFetchJson<Finding[]>('/api/v1/ui-repair/security/findings');
      setFindings(findingsData);
    } catch (err) {
      console.error('Scan failed', err);
    } finally {
      setScanning(false);
    }
  };

  const handleCertify = async () => {
    setCertifying(true);
    try {
      await safeFetchJson('/api/v1/ui-repair/security/certify?operator_name=Admin', { method: 'POST' });
      const certsData = await safeFetchJson<Certification[]>('/api/v1/ui-repair/security/certifications');
      setCerts(certsData);
    } catch (err) {
      console.error('Certification failed', err);
    } finally {
      setCertifying(false);
    }
  };

  const fetchRemediationData = async () => {
    try {
      const [plansData, attemptsData, summaryData] = await Promise.all([
        safeFetchJson<any[]>('/api/v1/ui-repair/security/remediation/plans'),
        safeFetchJson<any[]>('/api/v1/ui-repair/security/remediation/attempts'),
        safeFetchJson<any>('/api/v1/ui-repair/security/remediation/summary')
      ]);
      setRemediationPlans(plansData);
      setFixAttempts(attemptsData);
      setRemediationSummary(summaryData);
    } catch (err) {
      console.error('Failed to fetch remediation data', err);
    }
  };

  const handleTriggerRemediation = async (findingId: string) => {
    setRemediating(prev => ({ ...prev, [findingId]: true }));
    try {
      await safeFetchJson(`/api/v1/ui-repair/security/remediation/plan/${findingId}`, { method: 'POST' });
      await fetchRemediationData();
    } catch (err) {
      console.error('Remediation trigger failed', err);
    } finally {
      setRemediating(prev => ({ ...prev, [findingId]: false }));
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'SECURE': return 'text-emerald-400 border-emerald-500/50 bg-emerald-500/10';
      case 'RELIABLE': return 'text-blue-400 border-blue-500/50 bg-blue-500/10';
      case 'DEGRADED': return 'text-amber-400 border-amber-500/50 bg-amber-500/10';
      case 'CRITICAL': return 'text-rose-400 border-rose-500/50 bg-rose-500/10';
      default: return 'text-slate-400 border-slate-500/50 bg-slate-500/10';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.95) return 'text-emerald-400';
    if (score >= 0.8) return 'text-blue-400';
    if (score >= 0.6) return 'text-amber-400';
    return 'text-rose-400';
  };

  if (loading && !posture) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-emerald-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Tab Switcher */}
      <div className="flex border-b border-slate-800 gap-8">
        <button 
          onClick={() => setActiveTab('posture')}
          className={`pb-4 text-sm font-bold transition-all relative ${
            activeTab === 'posture' ? 'text-emerald-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Security Posture & Remediation
          {activeTab === 'posture' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />}
        </button>
        <button 
          onClick={() => setActiveTab('threat')}
          className={`pb-4 text-sm font-bold transition-all relative ${
            activeTab === 'threat' ? 'text-emerald-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Autonomous Threat Modeling
          {activeTab === 'threat' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />}
        </button>
        <button 
          onClick={() => setActiveTab('redteam')}
          className={`pb-4 text-sm font-bold transition-all relative ${
            activeTab === 'redteam' ? 'text-rose-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Red Team Center
          {activeTab === 'redteam' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]" />}
        </button>
        <button 
          onClick={() => setActiveTab('shield')}
          className={`pb-4 text-sm font-bold transition-all relative ${
            activeTab === 'shield' ? 'text-emerald-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Autonomous Shield
          {activeTab === 'shield' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />}
        </button>
      </div>

      {activeTab === 'posture' && (
        <>
          {/* Posture Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-slate-900/50 border border-slate-800 p-6 rounded-2xl flex items-center gap-8">
          <div className="relative">
            <svg className="w-32 h-32 transform -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="currentColor"
                strokeWidth="8"
                fill="transparent"
                className="text-slate-800"
              />
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="currentColor"
                strokeWidth="8"
                fill="transparent"
                strokeDasharray={351.8}
                strokeDashoffset={351.8 * (1 - (posture?.overall_score || 0))}
                className={`${getScoreColor(posture?.overall_score || 0)} transition-all duration-1000`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-black text-white">{( (posture?.overall_score || 0) * 100).toFixed(0)}%</span>
              <span className="text-[10px] text-slate-500 uppercase font-bold">Posture Score</span>
            </div>
          </div>
          
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-2xl font-black text-white">Security Posture</h2>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getLevelColor(posture?.posture_level || 'UNKNOWN')}`}>
                {posture?.posture_level}
              </span>
            </div>
            <p className="text-sm text-slate-400 max-w-md">
              Continuous compliance and security posture assessment of the Sovereign AGI platform. 
              The score represents aggregated health across 5 critical domains.
            </p>
            <div className="flex gap-3 mt-4">
              <button 
                onClick={handleRunScan}
                disabled={scanning}
                className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2 transition-all"
              >
                <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
                {scanning ? 'Scanning...' : 'Trigger Scan'}
              </button>
              <button 
                onClick={handleCertify}
                disabled={certifying}
                className="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white px-4 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2 transition-all border border-slate-700"
              >
                <ClipboardCheck className="w-4 h-4" />
                {certifying ? 'Certifying...' : 'Certify Compliance'}
              </button>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest">Domain Breakdown</h3>
          {[
            { label: 'Identity', score: posture?.identity_score, icon: Fingerprint },
            { label: 'Policy', score: posture?.policy_score, icon: Key },
            { label: 'Governance', score: posture?.governance_score, icon: ShieldCheck },
            { label: 'Isolation', score: posture?.isolation_score, icon: Server },
            { label: 'Evidence', score: posture?.evidence_score, icon: Lock },
          ].map(domain => (
            <div key={domain.label} className="flex items-center gap-3">
              <domain.icon className="w-4 h-4 text-slate-400" />
              <span className="text-xs text-slate-300 flex-1">{domain.label}</span>
              <div className="w-24 h-1 bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${getScoreColor(domain.score || 0)}`} 
                  style={{ width: `${(domain.score || 0) * 100}%` }}
                />
              </div>
              <span className={`text-[10px] font-mono font-bold w-8 text-right ${getScoreColor(domain.score || 0)}`}>
                {((domain.score || 0) * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compliance Matrix */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex justify-between items-center">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-400" />
              Compliance Control Matrix
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/50 text-slate-500 uppercase font-black">
                <tr>
                  <th className="px-4 py-3">Control</th>
                  <th className="px-4 py-3">Domain</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {controls.map(ctrl => {
                  const finding = findings.find(f => f.control_key === ctrl.control_key);
                  return (
                    <tr key={ctrl.control_key} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-4">
                        <div className="font-bold text-slate-200">{ctrl.title}</div>
                        <div className="text-[10px] text-slate-500">{ctrl.control_key}</div>
                      </td>
                      <td className="px-4 py-4 text-slate-400">{ctrl.domain}</td>
                      <td className="px-4 py-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          ctrl.severity === 'CRITICAL' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}>
                          {ctrl.severity}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        {finding ? (
                          <div className="flex items-center gap-2">
                            {finding.status === 'PASSED' ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            ) : (
                              <AlertTriangle className="w-4 h-4 text-rose-500" />
                            )}
                            <span className={finding.status === 'PASSED' ? 'text-emerald-400' : 'text-rose-400'}>
                              {finding.status}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-600">NOT CHECKED</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Findings & Certifications */}
        <div className="space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-900/80">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                Active Posture Findings
              </h3>
            </div>
            <div className="p-4 space-y-4 max-h-[300px] overflow-y-auto custom-scrollbar">
              {findings.filter(f => f.status !== 'PASSED').length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-slate-500">
                  <ShieldCheck className="w-12 h-12 mb-2 opacity-20" />
                  <p className="text-xs">No active posture findings. Platform is secure.</p>
                </div>
              ) : (
                findings.filter(f => f.status !== 'PASSED').map(f => (
                  <div key={f.control_key} className="p-3 rounded-lg bg-rose-500/5 border border-rose-500/20 group relative overflow-hidden">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-bold text-rose-400">{f.control_key}</span>
                      <span className="text-[10px] text-slate-500">{new Date(f.last_check_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed mb-3">{f.rationale}</p>
                    <div className="flex justify-end">
                      <button 
                        onClick={() => handleTriggerRemediation(f.id)}
                        disabled={remediating[f.id]}
                        className="px-3 py-1 bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 text-[10px] font-black uppercase tracking-widest rounded border border-emerald-500/20 transition-all flex items-center gap-1.5"
                      >
                        <RefreshCw className={`w-3 h-3 ${remediating[f.id] ? 'animate-spin' : ''}`} />
                        {remediating[f.id] ? 'Remediating...' : 'Trigger Remediation'}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-900/80">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ClipboardCheck className="w-5 h-5 text-emerald-400" />
                Certification History
              </h3>
            </div>
            <div className="divide-y divide-slate-800 max-h-[300px] overflow-y-auto custom-scrollbar">
              {certs.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-xs">
                  No certifications generated yet.
                </div>
              ) : certs.map(cert => (
                <div key={cert.id} className="p-4 flex items-center gap-4 hover:bg-slate-800/30 transition-colors">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getLevelColor(cert.posture_level)}`}>
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">{cert.cert_id}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getLevelColor(cert.posture_level)}`}>
                        {cert.posture_level}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      Certified by {cert.certified_by} • {new Date(cert.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-black text-white">{(cert.overall_score * 100).toFixed(0)}%</div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase">Compliance Score</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Remediation Dashboard Section */}
      <div className="pt-8 border-t border-slate-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-black text-white flex items-center gap-3">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
              Autonomous Remediation & Auto-Fix
            </h2>
            <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">
              Phase 22: Self-Healing Security Infrastructure
            </p>
          </div>
          <div className="flex gap-4">
            <div className="bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl flex items-center gap-3">
              <div className="text-right">
                <div className="text-[10px] text-slate-500 font-bold uppercase">Success Rate</div>
                <div className="text-sm font-black text-emerald-400">
                  {remediationSummary ? (remediationSummary.success_rate * 100).toFixed(1) : '0'}%
                </div>
              </div>
              <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Remediation Plans List */}
          <div className="xl:col-span-2 bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex justify-between items-center">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <RefreshCw className="w-5 h-5 text-blue-400" />
                Active Remediation Plans
              </h3>
            </div>
            <div className="divide-y divide-slate-800">
              {remediationPlans.length === 0 ? (
                <div className="p-12 text-center text-slate-500 text-xs italic">
                  No active remediation plans in progress.
                </div>
              ) : remediationPlans.map(plan => (
                <div key={plan.id} className="p-4 hover:bg-slate-800/30 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-black tracking-tighter border ${
                        plan.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                        plan.status === 'MANUAL_REQUIRED' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                        'bg-blue-500/10 text-blue-400 border-blue-500/20'
                      }`}>
                        {plan.status}
                      </span>
                      <span className="text-xs font-bold text-white uppercase tracking-wider">{plan.remediation_type}</span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-500">{new Date(plan.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-slate-300 mb-3 bg-slate-950 p-3 rounded-lg border border-slate-800 italic">
                    "{plan.strategy_summary}"
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex flex-col">
                        <span className="text-[9px] text-slate-500 font-bold uppercase">Residual Risk</span>
                        <span className={`text-[10px] font-black ${
                          plan.residual_risk_level === 'CRITICAL' ? 'text-rose-500' :
                          plan.residual_risk_level === 'HIGH' ? 'text-amber-500' : 'text-emerald-500'
                        }`}>{plan.residual_risk_level}</span>
                      </div>
                      <div className="h-6 w-[1px] bg-slate-800" />
                      <div className="flex flex-col">
                        <span className="text-[9px] text-slate-500 font-bold uppercase">Finding ID</span>
                        <span className="text-[10px] font-mono text-slate-400">{plan.finding_id.substring(0, 8)}...</span>
                      </div>
                    </div>
                    {plan.status === 'PLAN_GENERATED' && (
                      <button className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold rounded transition-all">
                        Execute Fix
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Fix Attempt History */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-800 bg-slate-900/80">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Server className="w-5 h-5 text-purple-400" />
                Auto-Fix Execution Log
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar">
              {fixAttempts.length === 0 ? (
                <div className="p-12 text-center text-slate-500 text-xs italic">
                  No execution logs recorded.
                </div>
              ) : fixAttempts.map(attempt => (
                <div key={attempt.id} className="p-4 border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                      Attempt #{attempt.id.substring(0, 4)}
                    </span>
                    <span className={`text-[10px] font-black ${
                      attempt.status === 'SUCCESS' ? 'text-emerald-400' : 'text-rose-400'
                    }`}>{attempt.status}</span>
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${attempt.status === 'SUCCESS' ? 'bg-emerald-500' : 'bg-rose-500'}`}
                        style={{ width: `${(attempt.verification_score || 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">
                      {((attempt.verification_score || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="text-[9px] text-slate-600 font-bold uppercase">
                    Execution: {new Date(attempt.created_at).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
            <div className="p-4 bg-slate-950/50 border-t border-slate-800">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                <span className="text-[10px] text-slate-500 leading-tight">
                  <b>Safety Notice:</b> CRITICAL findings are automatically blocked from autonomous execution. 
                  Manual operator intervention is required for all Level-3 overrides.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
        </>
      )}

      {activeTab === 'threat' && (
        <ThreatModelingPanel />
      )}

      {activeTab === 'redteam' && <RedTeamCenterPanel />}
      {activeTab === 'shield' && <AutonomousShieldCenterPanel />}
    </div>
  );
}
