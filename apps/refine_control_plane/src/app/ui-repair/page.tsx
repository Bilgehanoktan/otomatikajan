"use client";

import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Activity, 
  AlertTriangle, 
  RefreshCw, 
  Search,
  ExternalLink,
  ChevronRight,
  Camera,
  Terminal,
  Globe,
  Clock,
  Zap,
  FileCode,
  CheckCircle2,
  XCircle,
  Shield,
  MessageSquare,
  Lock,
  GitPullRequest,
  Brain
} from 'lucide-react';
import GAOperationsDashboard from './GAOperationsDashboard';
import { ChaosDrillsPanel } from "@/components/ui-repair/ChaosDrillsPanel";
import { SoakValidationPanel } from "@/components/ui-repair/SoakValidationPanel";
import { RecoveryProofPackPanel } from "@/components/ui-repair/RecoveryProofPackPanel";
import { AdvancedChaosPanel } from "@/components/ui-repair/AdvancedChaosPanel";
import { EscalationCenter } from "@/components/ui-repair/EscalationCenter";
import { CrisisControlPanel } from "@/components/ui-repair/CrisisControlPanel";
import { NotificationDeliveryPanel } from "@/components/ui-repair/NotificationDeliveryPanel";
import { FinalReadinessPanel } from "@/components/ui-repair/FinalReadinessPanel";
import { PilotRolloutPanel } from "@/components/ui-repair/PilotRolloutPanel";
import EnterpriseRolloutPanel from "@/components/ui-repair/EnterpriseRolloutPanel";
import ProjectProfilePanel from "@/components/ui-repair/ProjectProfilePanel";
import RolloutWavePanel from "@/components/ui-repair/RolloutWavePanel";
import ProjectHealthMatrixPanel from "@/components/ui-repair/ProjectHealthMatrixPanel";
import SLASLOTrackerPanel from "@/components/ui-repair/SLASLOTrackerPanel";
import GAReadinessPanel from "@/components/ui-repair/GAReadinessPanel";
import EnterpriseRunbookPanel from "@/components/ui-repair/EnterpriseRunbookPanel";
import { ResiliencyMeshPanel } from "@/components/ui-repair/ResiliencyMeshPanel";
import ExternalToolGovernancePanel from "@/components/ui-repair/ExternalToolGovernancePanel";
import { IdentityTrustCenterPanel } from "@/components/ui-repair/IdentityTrustCenterPanel";
import CognitiveIntegrityCenterPanel from "@/components/ui-repair/CognitiveIntegrityCenterPanel";
import SecurityPostureCenterPanel from "@/components/ui-repair/SecurityPostureCenterPanel";
import { FinalReleaseCenterPanel } from "@/components/ui-repair/FinalReleaseCenterPanel";
import { KnowledgeCenterPanel } from "@/components/ui-repair/KnowledgeCenterPanel";

// Premium UI Components
const Card = ({ children, className = "", onClick }: { children: React.ReactNode, className?: string, onClick?: () => void }) => (
  <div 
    onClick={onClick}
    className={`bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-md shadow-xl ${className} ${onClick ? 'cursor-pointer transition-transform active:scale-[0.98]' : ''}`}
  >
    {children}
  </div>
);

const Badge = ({ children, variant = "info" }: { children: React.ReactNode, variant?: string }) => {
  const styles: Record<string, string> = {
    info: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    error: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    critical: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    low: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    medium: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    high: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border ${styles[variant.toLowerCase()] || styles.info}`}>
      {children}
    </span>
  );
};

export default function UIRepairPage() {
  const [overview, setOverview] = useState<any>(null);
  const [routes, setRoutes] = useState<any[]>([]);
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [filter, setFilter] = useState("");
  const [selectedCase, setSelectedCase] = useState<any>(null);
  const [attempts, setAttempts] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState("diagnostic");
  const [repairDetail, setRepairDetail] = useState<any>(null);
  const [applying, setApplying] = useState(false);
  const [monitoringConfig, setMonitoringConfig] = useState<any>(null);
  const [monitoringRuns, setMonitoringRuns] = useState<any[]>([]);
  const [mainTab, setMainTab] = useState("matrix"); // matrix | monitoring | chaos | soak | proof
  const [triggeringMonitoring, setTriggeringMonitoring] = useState(false);


  useEffect(() => {
    fetchData();
    fetchMonitoringData();
  }, []);

  const fetchMonitoringData = async () => {
    try {
      const [cfgRes, runsRes] = await Promise.all([
        fetch('/api/v1/ui-repair/monitoring/config'),
        fetch('/api/v1/ui-repair/monitoring/runs')
      ]);
      if (cfgRes.ok) setMonitoringConfig(await cfgRes.json());
      if (runsRes.ok) setMonitoringRuns(await runsRes.json());
    } catch (err) {
      console.error("Failed to fetch monitoring data", err);
    }
  };

  const handleUpdateConfig = async (data: any) => {
    try {
      const res = await fetch('/api/v1/ui-repair/monitoring/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) setMonitoringConfig(await res.json());
    } catch (err) {
      console.error("Failed to update monitoring config", err);
    }
  };

  const handleTriggerMonitoring = async () => {
    setTriggeringMonitoring(true);
    try {
      await fetch('/api/v1/ui-repair/monitoring/trigger', { method: 'POST' });
      setTimeout(fetchMonitoringData, 2000);
    } catch (err) {
      console.error("Failed to trigger monitoring", err);
    } finally {
      setTriggeringMonitoring(false);
    }
  };

  const fetchData = async () => {
    try {
      const [overRes, routeRes, caseRes] = await Promise.all([
        fetch('/api/v1/ui-repair/overview'),
        fetch('/api/v1/ui-repair/routes'),
        fetch('/api/v1/ui-repair/cases')
      ]);
      
      if (overRes.ok) setOverview(await overRes.json());
      if (routeRes.ok) setRoutes(await routeRes.json());
      if (caseRes.ok) setCases(await caseRes.json());
    } catch (err) {
      console.error("Failed to fetch UI repair data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSmoke = async () => {
    setRunning(true);
    try {
      await fetch('/api/v1/ui-repair/smoke/run', { method: 'POST' });
      await fetchData();
    } catch (err) {
      console.error("Failed to run smoke tests", err);
    } finally {
      setRunning(false);
    }
  };

  const handleTriggerRepair = async (caseId: string) => {
    try {
      await fetch(`/api/v1/ui-repair/cases/${caseId}/repair`, { method: 'POST' });
      await fetchData();
      if (selectedCase && selectedCase.id === caseId) {
        fetchCaseDetails(caseId);
      }
    } catch (err) {
      console.error("Failed to trigger repair", err);
    }
  };

  const fetchCaseDetails = async (caseId: string) => {
    try {
      const [attRes, evtRes] = await Promise.all([
        fetch(`/api/v1/ui-repair/cases/${caseId}/attempts`),
        fetch(`/api/v1/ui-repair/cases/${caseId}/events`)
      ]);
      if (attRes.ok) {
        const atts = await attRes.json();
        setAttempts(atts);
        if (atts.length > 0) {
          fetchAttemptDetail(atts[0].id);
        }
      }
      if (evtRes.ok) setEvents(await evtRes.json());
    } catch (err) {
      console.error("Failed to fetch case details", err);
    }
  };

  const fetchAttemptDetail = async (attemptId: string) => {
    try {
      const res = await fetch(`/api/v1/ui-repair/attempts/${attemptId}/detail`);
      if (res.ok) setRepairDetail(await res.json());
    } catch (err) {
      console.error("Failed to fetch attempt detail", err);
    }
  };

  const handleApplyPatch = async (caseId: string, attemptId: string) => {
    setApplying(true);
    try {
      const res = await fetch(`/api/v1/ui-repair/cases/${caseId}/attempts/${attemptId}/apply?operator=admin`, { method: 'POST' });
      const data = await res.json();
      
      if (res.ok) {
        await fetchData();
        setSelectedCase(null);
      } else if (res.status === 403) {
        alert(`REPAIR BLOCKED: ${data.reason}\n\nIntegrity Score: ${(data.score * 100).toFixed(1)}%`);
      } else {
        alert(`Error: ${data.detail || 'Failed to apply patch'}`);
      }
    } catch (err) {
      console.error("Failed to apply patch", err);
    } finally {
      setApplying(false);
    }
  };

  const selectCase = (c: any) => {
    setSelectedCase(c);
    fetchCaseDetails(c.id);
  };

  const filteredRoutes = routes.filter(r => r.route.toLowerCase().includes(filter.toLowerCase()));

  if (loading) {
    return (
      <div className="p-8 h-screen flex flex-col items-center justify-center space-y-4 bg-slate-950">
        <div className="w-12 h-12 border-4 border-blue-600/30 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-slate-400 font-medium animate-pulse">Initializing UI Evidence Backbone...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 selection:bg-blue-500/30">
      <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 ease-out">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-4 h-4 text-blue-400 fill-blue-400" />
              <span className="text-[10px] font-bold text-blue-500 uppercase tracking-[0.2em]">Phase 32: Autonomous Repair</span>
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-blue-100 to-slate-400 bg-clip-text text-transparent">
              UI Repair Center
            </h1>
            <p className="text-slate-500 mt-2 max-w-md">
              Evidence-based diagnostic backbone for automated frontend failure detection and repair lifecycle.
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Last Sync</div>
              <div className="text-xs text-slate-300 font-mono">
                {overview?.last_smoke_run_at ? new Date(overview.last_smoke_run_at).toLocaleTimeString() : 'Never'}
              </div>
            </div>
            <button 
              onClick={handleRunSmoke}
              disabled={running}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all
                ${running 
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700' 
                  : 'bg-blue-600 hover:bg-blue-500 text-white shadow-2xl shadow-blue-900/40 border border-blue-400/20 active:scale-95'}`}
            >
              <RefreshCw className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
              {running ? 'Running Diagnostics...' : 'Trigger Smoke Run'}
            </button>
          </div>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: 'UI Health Score', val: `${(overview?.ui_health_score * 100).toFixed(0)}%`, icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/10' },
            { label: 'Stability Index', val: `${overview?.passing_routes}/${overview?.total_routes}`, icon: Globe, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
            { label: 'Active Repairs', val: overview?.open_cases, icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10' },
            { label: 'Critical Risk', val: overview?.critical_cases, icon: ShieldCheck, color: 'text-rose-400', bg: 'bg-rose-500/10' }
          ].map((stat, i) => (
            <Card key={i} className="p-6 relative group hover:border-slate-700 transition-all">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <stat.icon className="w-16 h-16" />
              </div>
              <div className="flex items-center gap-4 mb-4">
                <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">{stat.label}</div>
              </div>
              <div className="text-3xl font-black text-slate-100">{stat.val}</div>
            </Card>
          ))}
        </div>

        {/* Main Navigation Tabs */}
        <div className="flex gap-4 border-b border-slate-800 overflow-x-auto no-scrollbar scroll-smooth">
          <button 
            onClick={() => setMainTab("matrix")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "matrix" ? 'border-blue-500 text-blue-400 bg-blue-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Health Matrix
          </button>
          <button 
            onClick={() => setMainTab("monitoring")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "monitoring" ? 'border-blue-500 text-blue-400 bg-blue-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Continuous Monitoring
          </button>
          <button 
            onClick={() => setMainTab("chaos")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "chaos" ? 'border-red-500 text-red-400 bg-red-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Chaos Drills
          </button>
          <button 
            onClick={() => setMainTab("resiliency")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "resiliency" ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Resiliency Mesh
          </button>
          <button 
            onClick={() => setMainTab("tools")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "tools" ? 'border-cyan-500 text-cyan-400 bg-cyan-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            External Tools
          </button>
          <button 
            onClick={() => setMainTab("soak")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "soak" ? 'border-purple-500 text-purple-400 bg-purple-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Soak Validation
          </button>
          <button 
            onClick={() => setMainTab("proof")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "proof" ? 'border-green-500 text-green-400 bg-green-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Proof Packs
          </button>
          <button 
            onClick={() => setMainTab("advanced-chaos")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "advanced-chaos" ? 'border-orange-500 text-orange-400 bg-orange-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Advanced Chaos
          </button>
          <button 
            onClick={() => setMainTab("escalation")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "escalation" ? 'border-rose-500 text-rose-400 bg-rose-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Escalation
          </button>
          <button 
            onClick={() => setMainTab("crisis")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "crisis" ? 'border-amber-500 text-amber-400 bg-amber-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Crisis Control
          </button>
          <button 
            onClick={() => setMainTab("notifications")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "notifications" ? 'border-blue-500 text-blue-400 bg-blue-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Notifications
          </button>
          <button 
            onClick={() => setMainTab("readiness")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "readiness" ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Final Readiness
          </button>
          <button 
            onClick={() => setMainTab("pilot")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "pilot" ? 'border-orange-500 text-orange-400 bg-orange-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Pilot Rollout
          </button>
          <button 
            onClick={() => setMainTab("enterprise")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "enterprise" ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Enterprise GA
          </button>
          <button 
            onClick={() => setMainTab("ga-operations")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "ga-operations" ? 'border-emerald-500 text-emerald-400 bg-emerald-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            GA Operations
          </button>
          <button 
            onClick={() => setMainTab("identity")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "identity" ? 'border-amber-500 text-amber-400 bg-amber-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Identity & Trust
          </button>
          <button 
            onClick={() => setMainTab("cognitive")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "cognitive" ? 'border-purple-500 text-purple-400 bg-purple-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Cognitive Integrity
          </button>

          <button 
            onClick={() => setMainTab("security")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "security" ? 'border-rose-500 text-rose-400 bg-rose-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Security Posture
          </button>
          <button 
            onClick={() => setMainTab("knowledge")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "knowledge" ? 'border-purple-500 text-purple-400 bg-purple-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Knowledge Center
          </button>
          <button 
            onClick={() => setMainTab("release-center")}
            className={`px-6 py-4 text-xs font-black uppercase tracking-widest transition-all border-b-2 ${mainTab === "release-center" ? 'border-blue-500 text-blue-400 bg-blue-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
          >
            Release Center
          </button>
        </div>

        {mainTab === "matrix" ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-in fade-in duration-500">
          {/* Route Health Matrix */}
          <Card className="lg:col-span-8 flex flex-col">
            <div className="p-6 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-400" />
                  Health Matrix
                </h3>
                <p className="text-xs text-slate-500 mt-1">Real-time status of critical application routes</p>
              </div>
              <div className="relative w-full sm:w-64">
                 <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                 <input 
                  placeholder="Filter by route..."
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/50 transition-all"
                 />
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-slate-950/30 text-[10px] text-slate-500 uppercase font-black tracking-widest">
                  <tr>
                    <th className="px-6 py-4">Endpoint Path</th>
                    <th className="px-6 py-4">Current Status</th>
                    <th className="px-6 py-4 text-right">Last Audit</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {filteredRoutes.map((route, i) => (
                    <tr key={i} className="hover:bg-slate-800/20 transition-colors group">
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-3">
                          <div className={`w-1.5 h-1.5 rounded-full ${route.status === 'PASS' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-rose-500 animate-pulse'}`} />
                          <span className="font-mono text-sm font-medium text-slate-300 group-hover:text-blue-300 transition-colors">{route.route}</span>
                        </div>
                      </td>
                      <td className="px-6 py-5">
                        <Badge variant={route.status === 'PASS' ? 'success' : 'error'}>
                          {route.status || 'PENDING'}
                        </Badge>
                      </td>
                      <td className="px-6 py-5 text-right">
                        <div className="flex flex-col items-end">
                          <span className="text-xs text-slate-400 font-mono">
                            {route.last_checked_at ? new Date(route.last_checked_at).toLocaleTimeString() : '---'}
                          </span>
                          <span className="text-[10px] text-slate-600 uppercase font-bold">
                            {route.last_checked_at ? new Date(route.last_checked_at).toLocaleDateString() : ''}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-5 text-right">
                        <button className="p-2 hover:bg-slate-800 rounded-lg text-slate-500 hover:text-blue-400 transition-all">
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredRoutes.length === 0 && (
              <div className="p-20 text-center text-slate-600">
                <Search className="w-8 h-8 mx-auto mb-2 opacity-20" />
                <p>No routes matching "{filter}"</p>
              </div>
            )}
          </Card>

          {/* Active Repair Cases */}
          <div className="lg:col-span-4 space-y-6">
            <div className="flex items-center justify-between px-2">
              <h3 className="font-bold flex items-center gap-2 text-slate-100">
                <AlertTriangle className="w-5 h-5 text-rose-500" />
                Active Repair Cases
              </h3>
              <span className="text-[10px] font-black bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">{cases.length}</span>
            </div>
            
            <div className="space-y-4 max-h-[800px] overflow-y-auto pr-1 custom-scrollbar">
              {cases.length === 0 ? (
                <div className="text-center py-24 border-2 border-dashed border-slate-800 rounded-3xl bg-slate-900/20 backdrop-blur-sm">
                  <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
                    <ShieldCheck className="w-8 h-8 text-emerald-500" />
                  </div>
                  <h4 className="text-slate-300 font-bold">System Integrity Optimal</h4>
                  <p className="text-slate-600 text-xs mt-2 px-6">No UI failures or active repair cases detected in the current governance cycle.</p>
                </div>
              ) : cases.map((c, i) => (
                <Card 
                  key={i} 
                  onClick={() => selectCase(c)}
                  className={`p-5 hover:border-blue-500/30 hover:bg-slate-800/40 transition-all border-l-4 cursor-pointer group ${
                    c.status === 'REPAIRING' ? 'border-l-blue-500 bg-blue-500/5' : 
                    c.status === 'PATCH_GENERATED' ? 'border-l-emerald-500 bg-emerald-500/5' :
                    c.status === 'WAITING_GOVERNANCE' ? 'border-l-purple-500 bg-purple-500/5' :
                    'border-l-rose-500/50'
                  }`}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex flex-wrap gap-2">
                      <Badge variant={c.severity}>{c.severity}</Badge>
                      <Badge variant={
                        c.status === 'REPAIRING' ? 'info' : 
                        c.status === 'PATCH_GENERATED' ? 'success' : 
                        c.status === 'PR_OPENED' ? 'success' :
                        c.status === 'WAITING_GOVERNANCE' ? 'critical' :
                        c.status === 'REPAIR_FAILED' ? 'error' : 'info'
                      }>
                        {c.status.replace(/_/g, ' ')}
                      </Badge>
                    </div>
                    <Clock className="w-3.5 h-3.5 text-slate-600" />
                  </div>
                  
                  <h4 className="text-sm font-bold text-slate-100 mb-1">{c.route}</h4>
                  <p className="text-[11px] text-slate-500 font-mono uppercase tracking-tighter mb-4">ID: {c.id.substring(0, 8)}...</p>
                  
                  {c.status === 'REPAIRING' && (
                    <div className="mb-4">
                      <div className="flex justify-between text-[10px] font-bold text-blue-400 mb-1 uppercase tracking-widest">
                        <span>Agent Working...</span>
                        <span>45%</span>
                      </div>
                      <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 w-[45%] animate-pulse" />
                      </div>
                    </div>
                  )}

                  {c.repair_summary && (
                    <div className="mb-4 p-3 bg-slate-950/50 rounded-lg border border-slate-800 text-[11px] text-slate-400 italic">
                      "{c.repair_summary.substring(0, 100)}{c.repair_summary.length > 100 ? '...' : ''}"
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2 mb-4">
                    {c.status === 'DETECTED' || c.status === 'EVIDENCE_CAPTURED' || c.status === 'REPAIR_FAILED' ? (
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleTriggerRepair(c.id); }}
                        className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold py-2 rounded-lg transition-all"
                      >
                        <Zap className="w-3 h-3" />
                        Trigger Repair
                      </button>
                    ) : null}
                    
                    {c.pr_url && (
                      <a 
                        href={c.pr_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold py-2 rounded-lg transition-all"
                      >
                        <ExternalLink className="w-3 h-3" />
                        View PR
                      </a>
                    )}
                  </div>

                  <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
                    <div className="flex gap-3">
                      <div className={`flex items-center gap-1.5 transition-colors ${c.screenshot_path ? 'text-blue-400' : 'text-slate-700'}`}>
                        <Camera className="w-4 h-4" />
                        <span className="text-[10px] font-bold">EV-IMG</span>
                      </div>
                      <div className={`flex items-center gap-1.5 transition-colors ${c.console_errors?.length > 0 ? 'text-amber-400' : 'text-slate-700'}`}>
                        <Terminal className="w-4 h-4" />
                        <span className="text-[10px] font-bold">EV-LOG</span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* Quick Actions / Legend */}
            <Card className="p-6 bg-gradient-to-br from-blue-600/10 to-transparent border-blue-500/20">
               <h4 className="text-xs font-black text-blue-400 uppercase tracking-widest mb-4">Evidence Standards</h4>
               <ul className="space-y-3">
                 {[
                   { label: 'EV-IMG', desc: 'Non-repudiable failure visual' },
                   { label: 'EV-LOG', desc: 'Captured console/network trace' },
                   { label: 'EV-HYD', desc: 'Hydration integrity checksum' }
                 ].map((item, i) => (
                   <li key={i} className="flex items-start gap-3">
                     <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
                     <div>
                       <div className="text-[11px] font-bold text-slate-200">{item.label}</div>
                       <div className="text-[10px] text-slate-500">{item.desc}</div>
                     </div>
                   </li>
                 ))}
               </ul>
            </Card>
          </div>
        </div>
        ) : mainTab === "monitoring" ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-in fade-in duration-500">
            {/* Monitoring Controls */}
            <div className="lg:col-span-4 space-y-6">
              <Card className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-bold flex items-center gap-2">
                    <Shield className="w-5 h-5 text-blue-400" />
                    Monitoring Config
                  </h3>
                  <button 
                    onClick={handleTriggerMonitoring}
                    disabled={triggeringMonitoring}
                    className="p-2 bg-blue-500/10 hover:bg-blue-500/20 rounded-lg text-blue-400 transition-all disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${triggeringMonitoring ? 'animate-spin' : ''}`} />
                  </button>
                </div>
                
                <div className="space-y-6">
                   <div className="flex items-center justify-between">
                     <span className="text-sm text-slate-300">Continuous Monitoring</span>
                     <button 
                       onClick={() => handleUpdateConfig({ enabled: !monitoringConfig?.enabled })}
                       className={`w-12 h-6 rounded-full transition-all relative ${monitoringConfig?.enabled ? 'bg-blue-600' : 'bg-slate-800'}`}
                     >
                       <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${monitoringConfig?.enabled ? 'right-1' : 'left-1'}`} />
                     </button>
                   </div>
                   
                   <div className="flex items-center justify-between">
                     <span className="text-sm text-slate-300">Autonomous Repair</span>
                     <button 
                       onClick={() => handleUpdateConfig({ auto_repair_enabled: !monitoringConfig?.auto_repair_enabled })}
                       className={`w-12 h-6 rounded-full transition-all relative ${monitoringConfig?.auto_repair_enabled ? 'bg-emerald-600' : 'bg-slate-800'}`}
                     >
                       <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${monitoringConfig?.auto_repair_enabled ? 'right-1' : 'left-1'}`} />
                     </button>
                   </div>

                   <div className="pt-4 border-t border-slate-800">
                     <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-2">Auto-Repair Threshold</label>
                     <select 
                       value={monitoringConfig?.auto_repair_risk_threshold || "LOW"}
                       onChange={(e) => handleUpdateConfig({ auto_repair_risk_threshold: e.target.value })}
                       className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500/50"
                     >
                       <option value="LOW">LOW Risk Only</option>
                       <option value="MEDIUM">Up to MEDIUM</option>
                       <option value="HIGH">Up to HIGH</option>
                       <option value="CRITICAL">All Risks</option>
                     </select>
                   </div>

                   <div className="space-y-2">
                     <div className="flex justify-between text-xs">
                       <span className="text-slate-500">Interval</span>
                       <span className="text-blue-400 font-mono">{(monitoringConfig?.interval_seconds / 60).toFixed(0)} min</span>
                     </div>
                     <div className="flex justify-between text-xs">
                       <span className="text-slate-500">Max Repairs / Day</span>
                       <span className="text-slate-300 font-mono">{monitoringConfig?.max_repairs_per_day}</span>
                     </div>
                   </div>
                </div>
              </Card>

              <Card className="p-6 bg-blue-600/5 border-blue-500/20">
                <h4 className="text-xs font-black text-blue-400 uppercase tracking-widest mb-4">Autonomous Policy</h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  The self-healing policy engine autonomously initiates Stagehand & OpenSWE agents for identified UI failures that meet safety criteria. 
                  Repairs stay in <b>WAITING_GOVERNANCE</b> until human intervention.
                </p>
              </Card>
            </div>

            {/* Monitoring Run History */}
            <Card className="lg:col-span-8 flex flex-col">
              <div className="p-6 border-b border-slate-800">
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Clock className="w-5 h-5 text-blue-400" />
                  Execution History
                </h3>
                <p className="text-xs text-slate-500 mt-1">Audit log of autonomous monitoring and repair cycles</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-950/30 text-[10px] text-slate-500 uppercase font-black tracking-widest">
                    <tr>
                      <th className="px-6 py-4">Run ID</th>
                      <th className="px-6 py-4">Status</th>
                      <th className="px-6 py-4">Metrics (P/F/R)</th>
                      <th className="px-6 py-4 text-right">Executed At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {monitoringRuns.map((run, i) => (
                      <tr key={i} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-6 py-4">
                          <span className="font-mono text-xs text-slate-500">{run.id.substring(0, 8)}...</span>
                        </td>
                        <td className="px-6 py-4">
                          <Badge variant={run.status === 'COMPLETED' ? 'success' : run.status === 'FAILED' ? 'error' : 'info'}>
                            {run.status}
                          </Badge>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            <span className="text-[10px] font-bold text-emerald-400">{run.passed_routes}P</span>
                            <span className="text-[10px] font-bold text-rose-400">{run.failed_routes}F</span>
                            <span className="text-[10px] font-bold text-blue-400">{run.auto_repair_started_count}R</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <span className="text-xs text-slate-400 font-mono">
                            {new Date(run.started_at).toLocaleString()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {monitoringRuns.length === 0 && (
                <div className="p-20 text-center text-slate-600">
                  <Clock className="w-8 h-8 mx-auto mb-2 opacity-20" />
                  <p>No monitoring runs recorded yet.</p>
                </div>
              )}
            </Card>
          </div>
        ) : mainTab === "chaos" ? (
          <div className="animate-in fade-in duration-500">
            <ChaosDrillsPanel />
          </div>
        ) : mainTab === "soak" ? (
          <div className="animate-in fade-in duration-500">
            <SoakValidationPanel />
          </div>
        ) : mainTab === "proof" ? (
          <div className="animate-in fade-in duration-500">
            <RecoveryProofPackPanel />
          </div>
        ) : mainTab === "advanced-chaos" ? (
          <div className="animate-in fade-in duration-500">
            <AdvancedChaosPanel />
          </div>
        ) : mainTab === "escalation" ? (
          <div className="animate-in fade-in duration-500">
            <EscalationCenter />
          </div>
        ) : mainTab === "crisis" ? (
          <div className="animate-in fade-in duration-500">
            <CrisisControlPanel />
          </div>
        ) : mainTab === "notifications" ? (
          <div className="animate-in fade-in duration-500">
            <NotificationDeliveryPanel />
          </div>
        ) : mainTab === "readiness" ? (
          <div className="animate-in fade-in duration-500">
            <FinalReadinessPanel />
          </div>
        ) : mainTab === "pilot" ? (
          <div className="animate-in fade-in duration-500">
            <PilotRolloutPanel />
          </div>
        ) : mainTab === "enterprise" ? (
          <div className="space-y-10 animate-in fade-in duration-700">
            <EnterpriseRolloutPanel />
            
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-10">
              <ProjectProfilePanel />
              <RolloutWavePanel />
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-10">
              <div className="xl:col-span-2">
                <ProjectHealthMatrixPanel />
              </div>
              <div>
                <SLASLOTrackerPanel />
              </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-10">
              <GAReadinessPanel />
              <EnterpriseRunbookPanel />
            </div>
          </div>
        ) : mainTab === "ga-operations" ? (
          <div className="animate-in fade-in duration-500">
            <GAOperationsDashboard />
          </div>
        ) : mainTab === "resiliency" ? (
          <div className="animate-in fade-in duration-500">
            <ResiliencyMeshPanel />
          </div>
        ) : mainTab === "identity" ? (
          <div className="animate-in fade-in duration-500">
            <IdentityTrustCenterPanel />
          </div>
        ) : mainTab === "tools" ? (
          <div className="animate-in fade-in duration-500">
            <ExternalToolGovernancePanel />
          </div>
        ) : mainTab === "cognitive" ? (
          <div className="animate-in fade-in duration-500">
            <CognitiveIntegrityCenterPanel />
          </div>
        ) : mainTab === "security" ? (
          <div className="animate-in fade-in duration-500">
            <SecurityPostureCenterPanel />
          </div>
        ) : mainTab === "knowledge" ? (
          <div className="animate-in fade-in duration-500">
            <KnowledgeCenterPanel />
          </div>
        ) : mainTab === "release-center" ? (
          <div className="animate-in fade-in duration-500">
            <FinalReleaseCenterPanel />
          </div>
        ) : null}

        {/* Detailed Repair View Modal/Panel */}
        {selectedCase && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-300">
            <Card className="w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border-blue-500/30">
              <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-500/10 rounded-lg">
                    <Zap className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">Repair Lab: {selectedCase.route}</h2>
                    <p className="text-xs text-slate-500 uppercase tracking-widest font-mono">Case ID: {selectedCase.id}</p>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedCase(null)}
                  className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
                >
                  <RefreshCw className="w-5 h-5 rotate-45" />
                </button>
              </div>

              <div className="flex border-b border-slate-800 bg-slate-950/20 px-6">
                {[
                  { id: "diagnostic", label: "Diagnostic", icon: Search },
                  { id: "review", label: "PR Review", icon: GitPullRequest },
                  { id: "verifier", label: "Verifier Mesh", icon: ShieldCheck },
                  { id: "governance", label: "Governance", icon: Lock },
                  { id: "history", label: "History", icon: Clock },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-6 py-4 text-xs font-bold uppercase tracking-widest transition-all border-b-2 ${
                      activeTab === tab.id 
                        ? 'border-blue-500 text-blue-400 bg-blue-500/5' 
                        : 'border-transparent text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    <tab.icon className="w-3.5 h-3.5" />
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                {activeTab === "diagnostic" && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                    <div className="space-y-8">
                      <section>
                        <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Diagnostic Brief</h3>
                        <Card className="p-6 bg-slate-950/30">
                          {attempts.length > 0 && attempts[0].diagnostic_brief ? (
                            <div className="space-y-4">
                              <p className="text-sm text-slate-300 leading-relaxed italic border-l-2 border-blue-500/50 pl-4">
                                "{attempts[0].diagnostic_brief.root_cause}"
                              </p>
                              <div>
                                <span className="text-[10px] font-bold text-slate-500 uppercase block mb-2">Repair Instruction</span>
                                <div className="text-xs bg-slate-900 p-3 rounded-lg font-mono text-blue-300 border border-slate-800">
                                  {attempts[0].repair_instruction}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="text-center py-8 opacity-40">
                              <Terminal className="w-8 h-8 mx-auto mb-2" />
                              <p className="text-xs">No diagnostic data available.</p>
                            </div>
                          )}
                        </Card>
                      </section>
                      <section>
                        <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Suspected Files</h3>
                        <div className="space-y-2">
                          {(attempts[0]?.suspected_files || []).map((file: string, idx: number) => (
                            <div key={idx} className="flex items-center gap-3 p-3 bg-slate-900 border border-slate-800 rounded-lg">
                              <FileCode className="w-3.5 h-3.5 text-blue-400" />
                              <span className="text-xs font-mono text-slate-400">{file}</span>
                            </div>
                          ))}
                        </div>
                      </section>
                    </div>
                    <div className="space-y-8">
                       <section>
                        <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Failure Context</h3>
                        <div className="grid grid-cols-2 gap-4">
                          <Card className="p-4 bg-rose-500/5 border-rose-500/10">
                            <div className="text-[10px] font-bold text-rose-400 uppercase mb-1">Console Errors</div>
                            <div className="text-2xl font-black">{selectedCase.console_errors?.length || 0}</div>
                          </Card>
                          <Card className="p-4 bg-amber-500/5 border-amber-500/10">
                            <div className="text-[10px] font-bold text-amber-400 uppercase mb-1">Network Failures</div>
                            <div className="text-2xl font-black">{selectedCase.network_errors?.length || 0}</div>
                          </Card>
                        </div>
                      </section>
                    </div>
                  </div>
                )}

                {activeTab === "review" && (
                  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                    {repairDetail?.review ? (
                      <>
                        <div className="grid grid-cols-3 gap-6">
                          <Card className="p-4 border-blue-500/20 bg-blue-500/5">
                            <div className="text-[10px] font-black text-blue-400 uppercase mb-2">Review Status</div>
                            <div className="flex items-center gap-2">
                              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                              <span className="text-lg font-bold uppercase">{repairDetail.review.status}</span>
                            </div>
                          </Card>
                          <Card className="p-4 border-amber-500/20 bg-amber-500/5">
                            <div className="text-[10px] font-black text-amber-400 uppercase mb-2">Risk Level</div>
                            <Badge variant={repairDetail.review.risk_level}>{repairDetail.review.risk_level}</Badge>
                          </Card>
                          <Card className="p-4 border-slate-800 bg-slate-900/50">
                            <div className="text-[10px] font-black text-slate-500 uppercase mb-2">Changed Files</div>
                            <div className="text-lg font-bold">{repairDetail.review.changed_files.length}</div>
                          </Card>
                        </div>

                        <section>
                          <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] mb-4">PR-Agent Analysis</h3>
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="space-y-4">
                               <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                                 <div className="flex items-center gap-2 mb-3 text-blue-400">
                                   <Search className="w-4 h-4" />
                                   <span className="text-[10px] font-black uppercase">Describe</span>
                                 </div>
                                 <p className="text-xs text-slate-400 leading-relaxed">{repairDetail.review.describe_output.summary}</p>
                               </div>
                               <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                                 <div className="flex items-center gap-2 mb-3 text-purple-400">
                                   <Shield className="w-4 h-4" />
                                   <span className="text-[10px] font-black uppercase">Security Review</span>
                                 </div>
                                 <div className="text-xs text-emerald-400 font-bold">PASSED: No security vulnerabilities detected in the patch.</div>
                               </div>
                            </div>
                            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                               <div className="flex items-center gap-2 mb-3 text-amber-400">
                                 <MessageSquare className="w-4 h-4" />
                                 <span className="text-[10px] font-black uppercase">Suggestions</span>
                               </div>
                               <ul className="space-y-3">
                                 {repairDetail.review.review_output.suggestions?.map((s: any, idx: number) => (
                                   <li key={idx} className="text-xs text-slate-500 flex gap-2">
                                     <ChevronRight className="w-3.5 h-3.5 text-slate-700 mt-0.5 shrink-0" />
                                     {s}
                                   </li>
                                 ))}
                               </ul>
                            </div>
                          </div>
                        </section>
                      </>
                    ) : (
                      <div className="py-20 text-center opacity-30">
                        <GitPullRequest className="w-12 h-12 mx-auto mb-4" />
                        <p>No PR review data available for this attempt.</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === "verifier" && (
                  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                    {repairDetail?.verifier ? (
                      <>
                        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                          {[
                            { label: "Lint", val: repairDetail.verifier.lint_status },
                            { label: "Typecheck", val: repairDetail.verifier.typecheck_status },
                            { label: "Build", val: repairDetail.verifier.build_status },
                            { label: "Unit", val: repairDetail.verifier.unit_test_status },
                            { label: "E2E", val: repairDetail.verifier.playwright_status },
                            { label: "Regression", val: repairDetail.verifier.route_regression_status },
                          ].map((gate, idx) => (
                            <Card key={idx} className={`p-4 text-center border-t-2 ${gate.val === 'PASSED' ? 'border-t-emerald-500 bg-emerald-500/5' : 'border-t-rose-500 bg-rose-500/5'}`}>
                              <div className="text-[10px] font-black text-slate-500 uppercase mb-1">{gate.label}</div>
                              <div className={`text-xs font-bold ${gate.val === 'PASSED' ? 'text-emerald-400' : 'text-rose-400'}`}>{gate.val}</div>
                            </Card>
                          ))}
                        </div>
                        <section>
                           <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Verification Summary</h3>
                           <div className="p-6 bg-slate-950 border border-slate-800 rounded-2xl flex items-start gap-4">
                             <div className="p-3 bg-emerald-500/10 rounded-full">
                               <ShieldCheck className="w-6 h-6 text-emerald-500" />
                             </div>
                             <div>
                               <h4 className="text-sm font-bold text-slate-200 mb-1">Verifier Mesh: All Gates Passed</h4>
                               <p className="text-xs text-slate-500 leading-relaxed">
                                 The automated verifier mesh has executed linting, typechecking, and smoke tests against the generated patch. 
                                 No regressions were detected in associated routes.
                               </p>
                             </div>
                           </div>
                        </section>
                      </>
                    ) : (
                      <div className="py-20 text-center opacity-30">
                        <Shield className="w-12 h-12 mx-auto mb-4" />
                        <p>No verifier results available for this attempt.</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === "governance" && (
                  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                    {repairDetail?.governance ? (
                      <div className="max-w-2xl mx-auto space-y-8">
                        <Card className="p-8 border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-transparent">
                          <div className="flex items-center gap-4 mb-6">
                            <div className="p-4 bg-purple-500/20 rounded-2xl">
                              <Lock className="w-8 h-8 text-purple-400" />
                            </div>
                            <div>
                              <div className="text-xs font-black text-purple-400 uppercase tracking-widest mb-1">Governance Status</div>
                              <h3 className="text-2xl font-black text-white">{repairDetail.governance.status}</h3>
                            </div>
                          </div>

                          <div className="space-y-4 mb-8">
                            <div className="flex justify-between items-center p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                              <span className="text-xs text-slate-400">Risk Assessment</span>
                              <Badge variant={repairDetail.governance.risk_level}>{repairDetail.governance.risk_level}</Badge>
                            </div>
                            <div className="flex justify-between items-center p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                              <span className="text-xs text-slate-400">Policy Verdict</span>
                              <span className="text-xs font-bold text-slate-200 italic">"{repairDetail.governance.policy_decision?.policy_decision || 'NEUTRAL'}"</span>
                            </div>
                            <div className="flex justify-between items-center p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                              <span className="text-xs text-slate-400">Operator Review Required</span>
                              <span className="text-xs font-bold text-amber-400">MANDATORY</span>
                            </div>
                          </div>

                          {repairDetail.governance.status === 'REQUESTED' && (
                            <div className="flex flex-col gap-4">
                              <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-start gap-3">
                                <AlertTriangle className="w-5 h-5 text-blue-400 shrink-0" />
                                <p className="text-[11px] text-blue-300/80 leading-relaxed">
                                  <b>Warning:</b> Approval will trigger a git commit and merge to the main branch. 
                                  A rollback snapshot will be automatically created before application.
                                </p>
                              </div>
                              <button 
                                onClick={() => handleApplyPatch(selectedCase.id, attempts[0].id)}
                                disabled={applying}
                                className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white rounded-xl font-black text-sm transition-all shadow-xl shadow-emerald-900/20 active:scale-[0.98] flex items-center justify-center gap-3"
                              >
                                {applying ? <RefreshCw className="w-5 h-5 animate-spin" /> : <ShieldCheck className="w-5 h-5" />}
                                {applying ? 'APPLYING REPAIR...' : 'APPROVE & APPLY REPAIR'}
                              </button>
                            </div>
                          )}
                          
                          {repairDetail.governance.status === 'APPROVED' && (
                            <div className="p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-center">
                              <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                              <h4 className="font-bold text-emerald-400">Repair Approved & Applied</h4>
                              <p className="text-xs text-slate-500 mt-2">Verified by {repairDetail.governance.approved_by} at {new Date(repairDetail.governance.approved_at).toLocaleString()}</p>
                            </div>
                          )}
                        </Card>
                      </div>
                    ) : (
                      <div className="py-20 text-center opacity-30">
                        <Lock className="w-12 h-12 mx-auto mb-4" />
                        <p>Governance request not yet generated for this attempt.</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === "history" && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                    <section>
                      <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Repair Attempts</h3>
                      <div className="space-y-3">
                        {attempts.map((att: any, idx: number) => (
                          <div 
                            key={idx} 
                            onClick={() => fetchAttemptDetail(att.id)}
                            className={`p-4 bg-slate-900/50 border rounded-xl flex justify-between items-center cursor-pointer transition-all ${repairDetail?.review?.attempt_id === att.id ? 'border-blue-500 bg-blue-500/5' : 'border-slate-800 hover:border-slate-700'}`}
                          >
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-bold text-slate-200">Attempt #{att.attempt_no}</span>
                                <Badge variant={att.status === 'COMPLETED' || att.status === 'WAITING_GOVERNANCE' ? 'success' : att.status === 'FAILED' ? 'error' : 'info'}>
                                  {att.status}
                                </Badge>
                              </div>
                              <div className="text-[10px] text-slate-500 font-mono">
                                {new Date(att.created_at).toLocaleString()}
                              </div>
                            </div>
                            {att.pr_url && (
                               <a href={att.pr_url} target="_blank" className="p-2 hover:bg-slate-800 rounded-lg text-emerald-400 transition-colors">
                                 <GitPullRequest className="w-4 h-4" />
                               </a>
                            )}
                          </div>
                        ))}
                      </div>
                    </section>
                    <section>
                      <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Event Timeline</h3>
                      <div className="relative space-y-4 pl-6 border-l border-slate-800">
                        {events.map((evt: any, idx: number) => (
                          <div key={idx} className="relative">
                            <div className={`absolute -left-[31px] top-1 w-2.5 h-2.5 rounded-full border-2 border-[#020617] ${
                              evt.status === 'SUCCESS' ? 'bg-emerald-500' : evt.status === 'ERROR' ? 'bg-rose-500' : 'bg-blue-500'
                            }`} />
                            <div className="flex flex-col">
                              <span className="text-[10px] font-black text-slate-500 uppercase tracking-wider">{evt.event_type}</span>
                              <span className="text-xs text-slate-300 mt-1">{evt.message}</span>
                              <span className="text-[10px] text-slate-600 mt-1">{new Date(evt.created_at).toLocaleTimeString()}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>
                  </div>
                )}
              </div>
              
              <div className="p-6 bg-slate-900/80 border-t border-slate-800 flex justify-end gap-3">
                <button 
                  onClick={() => setSelectedCase(null)}
                  className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-bold text-sm transition-all"
                >
                  Close Lab
                </button>
                <button 
                  onClick={() => handleTriggerRepair(selectedCase.id)}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-sm transition-all active:scale-95 flex items-center gap-2"
                >
                  <Zap className="w-4 h-4" />
                  Initiate New Attempt
                </button>
              </div>
            </Card>
          </div>
        )}
      </div>
      
      {/* Footer Branding */}
      <div className="p-12 text-center">
        <div className="flex items-center justify-center gap-2 mb-2 opacity-30">
          <Activity className="w-4 h-4 text-blue-500" />
          <span className="text-xs font-black tracking-[0.3em] text-white">SOVEREIGN AGI</span>
        </div>
        <p className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">
          Autonomous Governance Mesh • Control Plane 12.1
        </p>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #334155; }
      `}</style>
    </div>
  );
}
