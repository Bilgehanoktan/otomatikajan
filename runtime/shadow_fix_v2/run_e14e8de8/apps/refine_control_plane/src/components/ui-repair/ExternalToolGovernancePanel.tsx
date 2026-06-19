'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  Wrench,
  Activity,
  Lock,
  Server,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  ShieldAlert,
  Globe,
  Database,
  Terminal,
  Cpu,
  Clock,
  ExternalLink,
  ChevronRight,
  RefreshCw,
  Search
} from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

export default function ExternalToolGovernancePanel() {
  const [activeTab, setActiveTab] = useState('registry');
  const [tools, setTools] = useState<any[]>([]);
  const [mcpServers, setMcpServers] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [health, setHealth] = useState<any[]>([]);
  const [riskOverview, setRiskOverview] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === 'registry') {
        const data = await safeFetchJson<any[]>('/api/v1/ui-repair/tools/registry');
        setTools(data);
      } else if (activeTab === 'mcp') {
        const data = await safeFetchJson<any[]>('/api/v1/ui-repair/tools/mcp/servers');
        setMcpServers(data);
      } else if (activeTab === 'audit') {
        const data = await safeFetchJson<any[]>('/api/v1/ui-repair/tools/audit');
        setAuditLogs(data);
      } else if (activeTab === 'health') {
        const data = await safeFetchJson<any[]>('/api/v1/ui-repair/tools/provider-health');
        setHealth(data);
      } else if (activeTab === 'risk') {
        const data = await safeFetchJson<any>('/api/v1/ui-repair/tools/risk/overview');
        setRiskOverview(data);
      }
    } catch (e) {
      console.error('Fetch error:', e);
    }
    setLoading(false);
  }, [activeTab]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const tabs = [
    { id: 'registry', name: 'Tool Registry', icon: Wrench },
    { id: 'mcp', name: 'MCP Servers', icon: Cpu },
    { id: 'audit', name: 'Audit Ledger', icon: Lock },
    { id: 'health', name: 'Provider Health', icon: Activity },
    { id: 'risk', name: 'Risk Assessment', icon: ShieldAlert },
  ];

  return (
    <div className="flex flex-col h-full bg-[#0a0a0b] text-slate-200">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-white/5 bg-white/5 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-500/20 rounded-xl border border-indigo-500/30">
            <Shield className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-xl font-semibold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              External Tool Governance
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Phase 18 - Integration Safety & MCP Sovereignty
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-xs font-medium flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Governance Active
          </div>
          <button 
            onClick={fetchData}
            className="p-2 hover:bg-white/10 rounded-lg border border-white/10 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/5 px-6">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-4 text-sm font-medium transition-all relative ${
              activeTab === tab.id ? 'text-white' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.name}
            {activeTab === tab.id && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500 shadow-[0_-4px_12px_rgba(99,102,241,0.5)]" />
            )}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-4">
              <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
              <p className="text-slate-500 animate-pulse">Loading Governance State...</p>
            </div>
          </div>
        ) : (
          <div className="max-w-7xl mx-auto space-y-6">
            {activeTab === 'registry' && <ToolRegistryTable tools={tools} />}
            {activeTab === 'mcp' && <MCPServersTable servers={mcpServers} />}
            {activeTab === 'audit' && <AuditLedgerList logs={auditLogs} />}
            {activeTab === 'health' && <ProviderHealthGrid health={health} />}
            {activeTab === 'risk' && <RiskAssessmentPanel overview={riskOverview} />}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolRegistryTable({ tools }: { tools: any[] }) {
  return (
    <div className="bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-white/5 border-b border-white/10">
            <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Tool</th>
            <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Type</th>
            <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Risk</th>
            <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Constraints</th>
            <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-wider">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {tools.map((tool: any) => (
            <tr key={tool.id} className="hover:bg-white/[0.02] transition-colors group">
              <td className="px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/10 rounded-lg">
                    <Terminal className="w-4 h-4 text-slate-300" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{tool.tool_name}</div>
                    <div className="text-xs text-slate-500">{tool.tool_key}</div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4">
                <span className="text-xs font-mono text-indigo-400 px-2 py-1 bg-indigo-500/10 rounded border border-indigo-500/20">
                  {tool.tool_type}
                </span>
              </td>
              <td className="px-6 py-4">
                <span className={`text-xs font-bold px-2 py-1 rounded ${
                  tool.risk_level === 'HIGH' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                  tool.risk_level === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                  'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }`}>
                  {tool.risk_level}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="flex flex-wrap gap-2">
                  {tool.requires_approval && (
                    <span className="text-[10px] bg-white/5 border border-white/10 px-1.5 py-0.5 rounded text-slate-400 flex items-center gap-1">
                      <Lock className="w-2.5 h-2.5" /> APPROVAL
                    </span>
                  )}
                  {tool.requires_sandbox && (
                    <span className="text-[10px] bg-white/5 border border-white/10 px-1.5 py-0.5 rounded text-slate-400 flex items-center gap-1">
                      <Shield className="w-2.5 h-2.5" /> SANDBOX
                    </span>
                  )}
                </div>
              </td>
              <td className="px-6 py-4">
                <div className={`w-2 h-2 rounded-full ${tool.enabled ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-slate-600'}`} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MCPServersTable({ servers }: { servers: any[] }) {
  if (servers.length === 0) {
    return (
      <div className="p-12 border-2 border-dashed border-white/5 rounded-3xl flex flex-col items-center gap-4 text-slate-500">
        <Cpu className="w-12 h-12 opacity-20" />
        <p>No MCP Servers registered yet.</p>
        <button className="text-indigo-400 text-sm font-medium hover:underline">+ Register Server</button>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {servers.map((server: any) => (
        <div key={server.id} className="bg-white/5 border border-white/10 p-6 rounded-2xl hover:border-white/20 transition-all">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-amber-500/10 rounded-xl border border-amber-500/20">
                <Server className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">{server.server_name}</h3>
                <code className="text-[10px] text-slate-500">{server.endpoint}</code>
              </div>
            </div>
            <div className={`px-2 py-1 rounded text-[10px] font-bold ${
              server.health_status === 'HEALTHY' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
              (server.health_status === 'DEGRADED' || server.health_status === 'WARNING' || server.health_status === 'STALE') ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
              (server.health_status === 'UNAVAILABLE' || server.health_status === 'FAILED') ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
              server.health_status === 'SIMULATED' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
              'bg-slate-500/10 text-slate-400 border border-white/10'
            }`}>
              {server.health_status}
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Transport</span>
              <span className="text-slate-300 font-mono">{server.transport_type}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Allowed Tools</span>
              <span className="text-indigo-400">{server.allowed_tools_json.length || 'ALL'}</span>
            </div>
            <div className="pt-3 border-t border-white/5 flex items-center justify-between">
              <span className="text-[10px] text-slate-600">Last check: {new Date(server.last_checked_at || server.created_at).toLocaleTimeString()}</span>
              <button className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 uppercase tracking-wider flex items-center gap-1">
                Details <ChevronRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function AuditLedgerList({ logs }: { logs: any[] }) {
  return (
    <div className="space-y-4">
      {logs.map((log: any) => (
        <div key={log.id} className="bg-[#111112] border border-white/5 p-4 rounded-xl flex items-center justify-between group hover:border-white/10 transition-all">
          <div className="flex items-center gap-4">
            <div className={`p-2 rounded-lg ${
              log.policy_decision === 'ALLOW' ? 'bg-emerald-500/10' : 'bg-rose-500/10'
            }`}>
              {log.policy_decision === 'ALLOW' ? (
                <CheckCircle className="w-4 h-4 text-emerald-500" />
              ) : (
                <ShieldAlert className="w-4 h-4 text-rose-500" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white">{log.action_type}</span>
                <span className="text-[10px] px-1.5 py-0.5 bg-white/5 rounded text-slate-500 font-mono">{log.tool_key}</span>
              </div>
              <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-600">
                <span className="flex items-center gap-1"><User className="w-3 h-3" /> {log.caller_id}</span>
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(log.created_at).toLocaleTimeString()}</span>
                <span className="flex items-center gap-1 font-mono">HASH: {log.input_hash.substring(0, 8)}...</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Latency</div>
              <div className="text-xs text-slate-300">{log.latency_ms}ms</div>
            </div>
            <button className="p-2 opacity-0 group-hover:opacity-100 bg-white/5 rounded-lg hover:bg-white/10 transition-all">
              <Eye className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function ProviderHealthGrid({ health }: { health: any[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {health.map((p: any) => (
        <div key={p.id} className="bg-white/5 border border-white/10 p-6 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Activity className="w-12 h-12" />
          </div>
          <div className="flex items-center gap-3 mb-6">
            <div className={`w-2.5 h-2.5 rounded-full ${
              p.status === 'HEALTHY' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' :
              (p.status === 'DEGRADED' || p.status === 'WARNING' || p.status === 'STALE') ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]' :
              (p.status === 'UNAVAILABLE' || p.status === 'FAILED') ? 'bg-rose-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' :
              p.status === 'SIMULATED' ? 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]' :
              'bg-slate-500'
            }`} />
            <h3 className="font-bold text-white text-lg">{p.provider}</h3>
          </div>
          
          <div className="space-y-4 relative z-10">
            <div className="flex items-end justify-between">
              <div>
                <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1">Health Score</div>
                <div className="text-2xl font-bold text-white">{(p.health_score * 100).toFixed(0)}%</div>
              </div>
              <div className="h-8 w-24 bg-white/5 rounded-lg flex items-end gap-1 p-1">
                {[40, 70, 45, 90, 85, 95].map((h, i) => (
                  <div key={i} className="flex-1 bg-indigo-500/40 rounded-sm" style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
              <div>
                <div className="text-[10px] text-slate-500 uppercase font-bold">Latency</div>
                <div className="text-sm font-mono text-slate-300">{p.latency_ms}ms</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase font-bold">Error Rate</div>
                <div className="text-sm font-mono text-slate-300">{(p.error_rate * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function RiskAssessmentPanel({ overview }: { overview: any | null }) {
  if (!overview) {
    return (
      <div className="flex flex-col items-center justify-center p-20 bg-white/5 rounded-3xl border border-dashed border-white/10 text-center">
        <div className="w-16 h-16 bg-slate-500/10 rounded-2xl flex items-center justify-center mb-6 border border-slate-500/20">
          <ShieldAlert className="w-8 h-8 text-slate-400" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Risk Summary Unavailable</h2>
        <p className="text-slate-500 max-w-md mx-auto">
          Provider and tool risk evidence has not been generated yet.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <RiskStatCard label="Providers" value={overview.provider_count} tone="blue" />
        <RiskStatCard label="Degraded" value={overview.degraded_providers + overview.unavailable_providers} tone="amber" />
        <RiskStatCard label="Highest Risk" value={overview.highest_risk_level} tone="rose" />
        <RiskStatCard label="Critical Findings" value={overview.critical_findings} tone="purple" />
      </div>

      <div className="bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white">Latest Risk Assessments</h3>
            <p className="text-xs text-slate-500 mt-1">Generated from live provider health and tool capability metadata.</p>
          </div>
          <div className="text-xs text-slate-400 font-mono">Max score: {Number(overview.highest_risk_score ?? 0).toFixed(1)}</div>
        </div>
        <div className="divide-y divide-white/5">
          {(overview.latest_assessments || []).map((assessment: any) => (
            <div key={assessment.id} className="px-6 py-4 flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-white">{assessment.provider}</span>
                  {assessment.tool_key && (
                    <span className="text-[10px] font-mono bg-white/5 border border-white/10 rounded px-1.5 py-0.5 text-slate-400">
                      {assessment.tool_key}
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-1">{assessment.recommendation}</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(assessment.findings_json || []).slice(0, 3).map((finding: string, index: number) => (
                    <span key={index} className="text-[10px] rounded-full bg-white/5 border border-white/10 px-2 py-1 text-slate-300">
                      {finding}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Risk Score</div>
                  <div className="text-lg font-bold text-white">{Number(assessment.risk_score ?? 0).toFixed(1)}</div>
                </div>
                <span className={`text-xs font-bold px-2 py-1 rounded ${
                  assessment.risk_level === 'CRITICAL' ? 'bg-rose-500/15 text-rose-400 border border-rose-500/20' :
                  assessment.risk_level === 'HIGH' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20' :
                  assessment.risk_level === 'MEDIUM' ? 'bg-blue-500/15 text-blue-400 border border-blue-500/20' :
                  'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
                }`}>
                  {assessment.risk_level}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function RiskStatCard({ label, value, tone }: { label: string; value: string | number; tone: 'blue' | 'amber' | 'rose' | 'purple' }) {
  const toneMap = {
    blue: 'text-blue-400 border-blue-500/20 bg-blue-500/10',
    amber: 'text-amber-400 border-amber-500/20 bg-amber-500/10',
    rose: 'text-rose-400 border-rose-500/20 bg-rose-500/10',
    purple: 'text-purple-400 border-purple-500/20 bg-purple-500/10',
  } as const;

  return (
    <div className={`rounded-2xl border p-5 ${toneMap[tone]}`}>
      <div className="text-[10px] uppercase tracking-widest font-bold opacity-80">{label}</div>
      <div className="text-2xl font-black text-white mt-2">{value}</div>
    </div>
  );
}

function User(props: React.SVGProps<SVGSVGElement>) {
  return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>;
}
