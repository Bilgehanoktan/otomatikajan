import React from 'react';

interface ProjectElasticity {
  id: string;
  name: string;
  base_limit: number;
  current_limit: number;
  adjustment_status: string;
  load_pct: number;
}

export const QuotaElasticityDetails: React.FC<{ projects: any[] }> = ({ projects }) => {
  const expandedProjects = projects.filter(p => p.adjustment_status === 'Expanded');

  return (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          Mesh Elasticity Monitor
        </h3>
        <span className="text-sm text-cyan-400 font-mono bg-cyan-400/10 px-3 py-1 rounded-full">
          {expandedProjects.length} Active Expansions
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {expandedProjects.length === 0 ? (
          <div className="text-center py-8 text-white/40 italic">
            Mesh capacity is currently nominal. No active scaling events.
          </div>
        ) : (
          expandedProjects.map(p => (
            <div key={p.id} className="p-4 rounded-xl bg-white/5 border border-white/10 group hover:border-cyan-500/50 transition-all">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="text-white font-medium">{p.name || p.id}</div>
                  <div className="text-xs text-white/50 uppercase tracking-wider">Tier {p.tier} • Predictive Expansion</div>
                </div>
                <div className="text-right">
                  <div className="text-cyan-400 font-bold">+{p.current_limit - p.base_limit} Slots</div>
                  <div className="text-[10px] text-cyan-400/50 uppercase tracking-tighter">Budget Approved</div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-[10px] uppercase text-white/40">
                  <span>Current Capacity</span>
                  <span>{p.current_limit} Total</span>
                </div>
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden flex">
                    <div 
                        className="h-full bg-white/20" 
                        style={{ width: `${(p.base_limit / p.current_limit) * 100}%` }} 
                        title="Base Limit"
                    />
                    <div 
                        className="h-full bg-cyan-400 animate-pulse" 
                        style={{ width: `${((p.current_limit - p.base_limit) / p.current_limit) * 100}%` }} 
                        title="Adaptive Expansion"
                    />
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="pt-4 border-t border-white/5">
        <p className="text-[10px] text-white/30 uppercase leading-relaxed">
          Autonomous adjustment policy: Tier-0 (+50% headroom), Tier-1 (+20% headroom). 
          Hard ceiling enforced at 200% of base quota.
        </p>
      </div>
    </div>
  );
};
