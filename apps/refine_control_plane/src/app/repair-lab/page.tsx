
"use client";

import React, { useState, useEffect } from "react";
import { PatchTournamentBoard, VerifierMatrix } from "@/components/repair/LabComponents";

export default function RepairLabPage() {
  const [labData, setLabData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/repair-lab/dashboard');
        const data = await response.json();
        setLabData(data);
      } catch (err) {
        console.error("Failed to fetch lab data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 10000); // Polling for updates
    return () => clearInterval(interval);
  }, []);

  const runLab = async () => {
    setLoading(true);
    try {
      await fetch('http://localhost:8000/api/v1/repair-lab/run', { method: 'POST' });
      alert("Autonomous Repair Lab initiated! Results will appear shortly.");
    } catch (err) {
      alert("Failed to start the lab.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-blue-400">Initializing Lab Environment...</div>;

  return (
    <div className="p-8 space-y-8 min-h-screen bg-[#050510] text-gray-200">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-black bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            AUTONOMOUS REPAIR LAB
          </h1>
          <p className="text-gray-500 mt-2 font-mono uppercase tracking-widest text-xs">
            Phase 28 | Research Harness & Patch Tournament Engine
          </p>
        </div>
        <div className="flex gap-4">
           <button 
             onClick={runLab}
             className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold transition-all shadow-lg shadow-blue-500/20 active:scale-95"
           >
             Run Benchmarks
           </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Benchmarks */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-gray-800 shadow-2xl">
            <h3 className="text-xl font-bold text-gray-400 mb-4 items-center flex gap-2">
              <span className="p-2 bg-gray-800 rounded-lg">📋</span>
              Incident Benchmarks
            </h3>
            <div className="space-y-3">
              {labData.benchmarks.map((b: any) => (
                <div key={b.id} className="p-3 bg-white/5 rounded-lg border border-white/5 hover:border-blue-500/30 transition-all cursor-pointer group">
                  <div className="flex justify-between items-start">
                    <span className="font-bold text-white group-hover:text-blue-400 transition-colors">{b.name}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      b.risk === 'high' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {b.risk}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 font-mono">{b.module}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Active Tournament & Verifiers */}
        <div className="lg:col-span-2 space-y-8">
          <PatchTournamentBoard data={labData.tournament} />
          <VerifierMatrix matrix={labData.matrix} />
        </div>
      </div>
    </div>
  );
}
