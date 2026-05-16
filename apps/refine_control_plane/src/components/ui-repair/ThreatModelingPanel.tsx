"use client";

import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Target, 
  Network, 
  Activity, 
  ShieldCheck, 
  Zap, 
  Search,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Lock,
  ArrowRight
} from 'lucide-react';

interface Asset {
  id: string;
  asset_key: string;
  asset_type: string;
  exposure_level: string;
  criticality: string;
  metadata: any;
}

interface AttackPath {
  id: string;
  path_name: string;
  path_type: string;
  risk_score: number;
  severity: string;
  feasibility: number;
  impact: number;
  mitigation_status: string;
}

interface ThreatSummary {
  total_assets: int;
  critical_assets: int;
  attack_path_count: int;
  high_risk_paths: int;
  simulation_success_rate: float;
  mitigation_coverage: float;
}

export default function ThreatModelingPanel() {
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [paths, setPaths] = useState<AttackPath[]>([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sumRes, assetRes, pathRes] = await Promise.all([
        fetch('/api/v1/ui-repair/security/threat/summary'),
        fetch('/api/v1/ui-repair/security/threat/assets'),
        fetch('/api/v1/ui-repair/security/threat/attack-paths')
      ]);
      
      setSummary(await sumRes.json());
      setAssets(await assetRes.json());
      setPaths(await pathRes.json());
    } catch (error) {
      console.error("Failed to fetch threat modeling data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    try {
      await fetch('/api/v1/ui-repair/security/threat/inventory/scan', { method: 'POST' });
      await fetch('/api/v1/ui-repair/security/threat/models/generate', { method: 'POST' });
      await fetchData();
    } finally {
      setScanning(false);
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-emerald-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center gap-3 text-slate-400 mb-2">
            <Target className="w-4 h-4" />
            <span className="text-sm font-medium">Total Assets</span>
          </div>
          <div className="text-2xl font-bold text-white">{summary?.total_assets || 0}</div>
        </div>
        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center gap-3 text-red-400 mb-2">
            <ShieldAlert className="w-4 h-4" />
            <span className="text-sm font-medium">Critical Paths</span>
          </div>
          <div className="text-2xl font-bold text-white">{summary?.high_risk_paths || 0}</div>
        </div>
        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center gap-3 text-blue-400 mb-2">
            <Activity className="w-4 h-4" />
            <span className="text-sm font-medium">Simulation Rate</span>
          </div>
          <div className="text-2xl font-bold text-white">{Math.round((summary?.simulation_success_rate || 0) * 100)}%</div>
        </div>
        <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl">
          <div className="flex items-center gap-3 text-emerald-400 mb-2">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-sm font-medium">Mitigation Coverage</span>
          </div>
          <div className="text-2xl font-bold text-white">{Math.round((summary?.mitigation_coverage || 0) * 100)}%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Attack Surface List */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Search className="w-5 h-5 text-emerald-400" />
              Attack Surface
            </h3>
            <button 
              onClick={handleScan}
              disabled={scanning}
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
            </button>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="max-h-[600px] overflow-y-auto divide-y divide-slate-800">
              {assets.map((asset) => (
                <div key={asset.id} className="p-4 hover:bg-slate-800/50 transition-colors">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-emerald-400">{asset.asset_type}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      asset.criticality === 'CRITICAL' ? 'bg-red-500/20 text-red-400' :
                      asset.criticality === 'HIGH' ? 'bg-orange-500/20 text-orange-400' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {asset.criticality}
                    </span>
                  </div>
                  <div className="text-sm font-medium text-white truncate">{asset.asset_key}</div>
                  <div className="text-xs text-slate-500 mt-1 flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      asset.exposure_level === 'HIGH' ? 'bg-red-500' :
                      asset.exposure_level === 'MEDIUM' ? 'bg-orange-500' :
                      'bg-emerald-500'
                    }`} />
                    Exposure: {asset.exposure_level}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Attack Paths Graph/List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Network className="w-5 h-5 text-emerald-400" />
            High-Risk Attack Paths
          </h3>
          <div className="grid grid-cols-1 gap-4">
            {paths.map((path) => (
              <div key={path.id} className="bg-slate-900/50 border border-slate-800 p-5 rounded-2xl hover:border-emerald-500/30 transition-all group">
                <div className="flex items-start justify-between mb-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        path.severity === 'CRITICAL' ? 'bg-red-500 text-white' :
                        path.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {path.severity}
                      </span>
                      <span className="text-xs text-slate-500">{path.path_type}</span>
                    </div>
                    <h4 className="text-base font-semibold text-white group-hover:text-emerald-400 transition-colors">
                      {path.path_name}
                    </h4>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-500 mb-1">Risk Score</div>
                    <div className="text-xl font-mono font-bold text-emerald-400">
                      {(path.risk_score * 100).toFixed(0)}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="bg-slate-800/30 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Feasibility</div>
                    <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: `${path.feasibility * 100}%` }} />
                    </div>
                  </div>
                  <div className="bg-slate-800/30 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Impact</div>
                    <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-red-500" style={{ width: `${path.impact * 100}%` }} />
                    </div>
                  </div>
                  <div className="bg-slate-800/30 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Mitigation</div>
                    <div className="flex items-center gap-1.5 mt-1">
                      {path.mitigation_status === 'UNMITIGATED' ? (
                        <AlertTriangle className="w-3 h-3 text-red-400" />
                      ) : (
                        <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      )}
                      <span className={`text-[10px] font-bold ${
                        path.mitigation_status === 'UNMITIGATED' ? 'text-red-400' : 'text-emerald-400'
                      }`}>
                        {path.mitigation_status}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                      <Zap className="w-3 h-3 text-orange-400" />
                      Simulation Available
                    </div>
                  </div>
                  <button className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500 text-white text-xs font-bold rounded-lg hover:bg-emerald-600 transition-colors">
                    Simulate Attack
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
