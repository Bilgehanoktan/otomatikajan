import React from 'react';
import { ShieldCheck, TrendingDown, RefreshCcw, AlertTriangle } from 'lucide-react';

export const FinancialGovernancePanel: React.FC<{ projects: any[] }> = ({ projects }) => {
  const anomalies = projects.filter(p => p.anomaly_score > 0.5 || p.health_reason === 'SPEND_ANOMALY');
  const criticalBudget = projects.filter(p => p.current_budget < 20 && p.tier <= 1);

  return (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-green-400" />
          Financial Governance
        </h3>
        <div className="flex gap-2 text-[10px] font-mono">
            <span className="px-2 py-1 rounded bg-red-500/10 text-red-400 border border-red-500/20 uppercase">
                {anomalies.length} Anomalies
            </span>
            <span className="px-2 py-1 rounded bg-yellow-500/10 text-yellow-500 border border-yellow-500/20 uppercase">
                {criticalBudget.length} Critical Budget
            </span>
        </div>
      </div>

      <div className="space-y-4">
        {/* BUDGET ALERTS */}
        {criticalBudget.length > 0 && (
            <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20 flex items-center gap-3 animate-pulse">
                <TrendingDown className="text-yellow-500 w-4 h-4" />
                <div className="text-xs text-yellow-200">
                    <span className="font-bold">LOW BUDGET:</span> {criticalBudget.length} Mission-critical projects near exhaustion.
                </div>
            </div>
        )}

        {/* ANOMALY LIST */}
        <div className="grid grid-cols-1 gap-3 max-h-[250px] overflow-y-auto pr-2 custom-scrollbar">
            {anomalies.map(p => (
                <div key={p.id} className="p-3 rounded-xl bg-red-500/5 border border-red-500/20 flex justify-between items-center group hover:bg-red-500/10 transition-all">
                    <div className="flex items-center gap-3">
                        <AlertTriangle className="text-red-400 w-4 h-4" />
                        <div>
                            <div className="text-xs text-white font-bold">{p.name || p.id}</div>
                            <div className="text-[10px] text-red-300/60 uppercase">Anomaly Score: {(p.anomaly_score * 100).toFixed(0)}%</div>
                        </div>
                    </div>
                    <button className="px-3 py-1 bg-red-500/20 text-red-300 text-[10px] rounded border border-red-500/30 opacity-0 group-hover:opacity-100 transition-opacity">
                        FREEZE
                    </button>
                </div>
            ))}

            {anomalies.length === 0 && (
                <div className="text-center py-6 text-white/30 text-xs italic">
                    No active spend anomalies detected.
                </div>
            )}
        </div>
      </div>

      {/* REPLENISHMENT LOG PREVIEW */}
      <div className="pt-4 border-t border-white/5 space-y-3">
          <div className="text-[10px] font-black text-white/40 uppercase tracking-widest flex items-center gap-2">
            <RefreshCcw size={10} className="animate-spin-slow" /> Recent Governance Events
          </div>
          <div className="space-y-2">
             <GovernanceEvent msg="p-critical (Tier 0) Auto-Replenished ($1000)" time="14m ago" type="refill" />
             <GovernanceEvent msg="p-enterprise budget verification passed" time="2h ago" type="verify" />
             <GovernanceEvent msg="Global cost attribution report generated" time="4h ago" type="report" />
          </div>
      </div>
    </div>
  );
};

function GovernanceEvent({ msg, time, type }: { msg: string, time: string, type: string }) {
    return (
        <div className="flex justify-between items-center text-[11px]">
            <span className="text-white/70 font-medium truncate max-w-[180px]">{msg}</span>
            <span className="text-white/30 font-mono text-[9px]">{time}</span>
        </div>
    )
}
