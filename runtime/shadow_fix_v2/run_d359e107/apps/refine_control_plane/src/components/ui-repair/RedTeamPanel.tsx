import React, { useState, useEffect } from 'react';
import { 
  ShieldX, 
  Play, 
  Terminal, 
  Activity, 
  Clock, 
  AlertOctagon, 
  BarChart3,
  Search,
  Zap,
  Target
} from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

interface Scenario {
  id: string;
  scenario_key: string;
  scenario_name: string;
  description: string;
  scenario_type: string;
  target_domain: string;
  risk_level: string;
  enabled: boolean;
}

interface DriftEvent {
  id: string;
  domain: string;
  drift_type: string;
  drift_score: number;
  severity: string;
  description: string;
  created_at: string;
}

interface RedTeamOverview {
  total_scenarios: number;
  active_operations: number;
  success_rate: number;
  avg_detection_latency: number;
  critical_drifts: number;
  last_run_at: string;
}

export default function RedTeamPanel() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [driftEvents, setDriftEvents] = useState<DriftEvent[]>([]);
  const [overview, setOverview] = useState<RedTeamOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [overviewData, scenariosData, driftData] = await Promise.all([
        safeFetchJson<RedTeamOverview>('/api/v1/ui-repair/security/red-team/overview'),
        safeFetchJson<Scenario[]>('/api/v1/ui-repair/security/red-team/scenarios'),
        safeFetchJson<DriftEvent[]>('/api/v1/ui-repair/security/red-team/drift-events')
      ]);
      
      setOverview(overviewData);
      setScenarios(scenariosData);
      setDriftEvents(driftData);
    } catch (err) {
      console.error('Failed to fetch red team data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunOperation = async (scenarioId: string) => {
    setRunning(scenarioId);
    try {
      await safeFetchJson(`/api/v1/ui-repair/security/red-team/scenarios/${scenarioId}/run`, {
        method: 'POST',
      });
      await fetchData();
    } catch (err) {
      console.error('Operation failed', err);
    } finally {
      setRunning(null);
    }
  };

  if (loading && !overview) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-red-500/10 rounded-lg">
              <ShieldX className="w-5 h-5 text-red-500" />
            </div>
            <span className="text-slate-400 text-sm">Active Scenarios</span>
          </div>
          <div className="text-2xl font-bold text-white">{overview?.total_scenarios || 0}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Zap className="w-5 h-5 text-blue-500" />
            </div>
            <span className="text-slate-400 text-sm">Avg. Latency</span>
          </div>
          <div className="text-2xl font-bold text-white">{(overview?.avg_detection_latency ?? 0).toFixed(1)}ms</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-amber-500/10 rounded-lg">
              <Activity className="w-5 h-5 text-amber-500" />
            </div>
            <span className="text-slate-400 text-sm">Critical Drifts</span>
          </div>
          <div className="text-2xl font-bold text-amber-500">{overview?.critical_drifts || 0}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-emerald-500/10 rounded-lg">
              <BarChart3 className="w-5 h-5 text-emerald-500" />
            </div>
            <span className="text-slate-400 text-sm">Defense Success</span>
          </div>
          <div className="text-2xl font-bold text-emerald-500">{((1 - (overview?.success_rate || 0)) * 100).toFixed(1)}%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scenarios List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-red-500" />
            Autonomous Attack Scenarios
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {scenarios.map(scen => (
              <div key={scen.id} className="bg-slate-900/50 border border-slate-800 p-5 rounded-xl hover:border-red-500/30 transition-colors">
                <div className="flex justify-between items-start mb-3">
                  <div className="px-2 py-1 bg-red-500/10 text-red-500 rounded text-xs font-mono uppercase">
                    {scen.scenario_type.replace(/_/g, ' ')}
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-semibold ${
                    scen.risk_level === 'CRITICAL' ? 'bg-red-500 text-white' :
                    scen.risk_level === 'HIGH' ? 'bg-amber-600 text-white' :
                    'bg-blue-600 text-white'
                  }`}>
                    {scen.risk_level}
                  </div>
                </div>
                <h4 className="text-white font-medium mb-1">{scen.scenario_name}</h4>
                <p className="text-slate-400 text-sm mb-4 h-10 line-clamp-2">{scen.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-500">{scen.scenario_key} / {scen.target_domain}</span>
                  <button
                    onClick={() => handleRunOperation(scen.id)}
                    disabled={running !== null || !scen.enabled}
                    className="flex items-center gap-2 px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
                  >
                    {running === scen.id ? (
                      <RefreshCw className="w-3 h-3 animate-spin" />
                    ) : (
                      <Play className="w-3 h-3 fill-current" />
                    )}
                    EXECUTE
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Drift Monitor */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-slate-800/50 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Terminal className="w-4 h-4 text-blue-400" />
              Adversarial Drift
            </h3>
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
          <div className="p-4 space-y-4 max-h-[500px] overflow-y-auto">
            <div className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-2">Live Behavioral Drift</div>
            {driftEvents.length > 0 ? driftEvents.slice(0, 5).map((event) => (
              <div
                key={event.id}
                className={`p-3 rounded border-l-2 ${
                  event.severity === 'CRITICAL'
                    ? 'bg-red-500/5 border-red-500'
                    : event.severity === 'HIGH'
                      ? 'bg-amber-500/5 border-amber-500'
                      : 'bg-slate-800/50 border-slate-700'
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className={`text-xs font-bold ${
                    event.severity === 'CRITICAL'
                      ? 'text-red-400'
                      : event.severity === 'HIGH'
                        ? 'text-amber-400'
                        : 'text-slate-400'
                  }`}>
                    {event.drift_type}
                  </span>
                  <span className="text-slate-500 text-[10px]">{new Date(event.created_at).toLocaleString()}</span>
                </div>
                <p className="text-slate-300 text-xs mb-2">{event.description}</p>
                <div className="flex gap-2 font-mono">
                  <span className="text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded">DOMAIN: {event.domain}</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded">SCORE: {(event.drift_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            )) : (
              <div className="p-3 bg-slate-800/50 border-l-2 border-slate-700 rounded opacity-60">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-slate-400 text-xs font-bold">NO_ACTIVE_DRIFT</span>
                </div>
                <p className="text-slate-500 text-xs">No adversarial drift events recorded.</p>
              </div>
            )}
          </div>
          <div className="p-4 bg-slate-800/30 border-t border-slate-800">
            <button className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2">
              <Search className="w-3 h-3" />
              VIEW FULL DRIFT ANALYSIS
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const RefreshCw = (props: any) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
);
