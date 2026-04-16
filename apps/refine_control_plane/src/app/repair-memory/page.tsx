
"use client";

import React from "react";

export default function RepairMemoryPage() {
  const [subsystems, setSubsystems] = React.useState<any[]>([]);

  React.useEffect(() => {
    const fetchMemory = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/repair-lab/memory/patterns');
        const data = await response.json();
        setSubsystems(data.map((p: any) => ({
           name: p.subsystem,
           strategy: p.strategy,
           risk: 1 - p.rate, // Risk is inverse of success rate
           success: p.rate,
           failures: p.total - p.success
        })));
      } catch (err) {
        console.error("Failed to fetch memory", err);
      }
    };
    fetchMemory();
  }, []);

  return (
    <div className="p-8 space-y-8 min-h-screen bg-[#050510] text-gray-200">
      <header>
        <h1 className="text-4xl font-black bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
          REPAIR MEMORY & RISK HEATMAP
        </h1>
        <p className="text-gray-500 mt-2 font-mono uppercase tracking-widest text-xs">
          Historical Patterns | Subsystem Reliability | Failure Recurrence
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {subsystems.map((sub, idx) => (
          <div key={idx} className="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-white/5 shadow-2xl relative overflow-hidden group">
            <div 
              className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full -mr-16 -mt-16 blur-3xl group-hover:bg-red-500/20 transition-all"
              style={{ opacity: sub.risk }}
            ></div>
            
            <div className="relative z-10 space-y-4">
              <h3 className="text-lg font-bold text-white truncate">{sub.name}</h3>
              
              <div className="flex justify-between items-end">
                <div>
                  <div className="text-[10px] text-gray-500 uppercase font-black">Success Rate</div>
                  <div className={`text-2xl font-black ${
                    sub.success > 0.8 ? 'text-green-400' : sub.success > 0.5 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {(sub.success * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-gray-500 uppercase font-black">Risk Score</div>
                  <div className="text-xl font-bold text-white">{(sub.risk * 100).toFixed(0)}</div>
                </div>
              </div>

              <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-1000 ${
                    sub.risk > 0.7 ? 'bg-red-500' : sub.risk > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${sub.risk * 100}%` }}
                ></div>
              </div>

              <div className="flex justify-between text-xs font-mono text-gray-500">
                <span>{sub.failures} Recorded Failures</span>
                <span className="text-blue-400 cursor-pointer hover:underline">View Patterns →</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
