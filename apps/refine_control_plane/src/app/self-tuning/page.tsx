
"use client";

import React, { useState, useEffect } from "react";

export default function SelfTuningPage() {
  const [suggestions, setSuggestions] = useState<any[]>([]);

  useEffect(() => {
    const fetchSuggestions = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/repair-lab/suggestions');
        const data = await response.json();
        // Map database model names to UI keys if necessary, but keep it agile
        setSuggestions(data.map((s: any) => ({
           id: s.suggestion_id || s.id,
           parameter: s.parameter_name,
           from: s.current_value,
           to: s.suggested_value,
           reason: s.rationale,
           impact: s.expected_impact,
           confidence: s.confidence_score,
           status: s.status
        })));
      } catch (err) {
        console.error("Failed to fetch suggestions", err);
      }
    };
    fetchSuggestions();
  }, []);

  const handleApply = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/repair-lab/apply/${id}`, {
        method: 'POST'
      });
      if (response.ok) {
        setSuggestions(prev => prev.map(s => s.id === id ? { ...s, status: 'approved' } : s));
      }
    } catch (err) {
      console.error("Failed to apply suggestion", err);
    }
  };

  return (
    <div className="p-8 space-y-8 min-h-screen bg-[#050510] text-gray-200">
      <header>
        <h1 className="text-4xl font-black bg-gradient-to-r from-teal-400 to-blue-500 bg-clip-text text-transparent">
          SELF-TUNING CONSOLE
        </h1>
        <p className="text-gray-500 mt-2 font-mono uppercase tracking-widest text-xs">
          Policy Calibration & Parameter Optimization
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6">
        {suggestions.map((s) => (
          <div key={s.id} className="bg-gray-900/50 backdrop-blur-md rounded-xl p-8 border border-teal-500/20 shadow-2xl flex flex-col md:flex-row justify-between gap-8 items-center">
            <div className="flex-1 space-y-4">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 bg-teal-500/10 text-teal-400 text-xs font-bold rounded-full border border-teal-500/20">
                  SUGGESTION {s.id}
                </span>
                <h3 className="text-2xl font-bold text-white">{s.parameter}</h3>
              </div>
              <p className="text-gray-400 max-w-2xl">{s.reason}</p>
              <div className="flex gap-6">
                <div>
                  <div className="text-xs text-gray-500 uppercase font-black mb-1">Impact</div>
                  <div className="text-teal-400 font-bold">{s.impact}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase font-black mb-1">Confidence</div>
                  <div className="text-white font-bold">{(s.confidence * 100).toFixed(0)}%</div>
                </div>
              </div>
            </div>

            <div className="flex flex-col items-center gap-4 bg-black/40 p-6 rounded-2xl border border-white/5 min-w-[300px]">
              <div className="flex items-center gap-8">
                 <div className="text-center">
                   <div className="text-gray-500 text-xs uppercase mb-1">Current</div>
                   <div className="text-2xl font-black text-gray-400">{s.from}</div>
                 </div>
                 <div className="text-teal-500 text-2xl">→</div>
                 <div className="text-center">
                   <div className="text-teal-400 text-xs uppercase mb-1">Proposed</div>
                   <div className="text-3xl font-black text-white">{s.to}</div>
                 </div>
              </div>
              <button 
                onClick={() => handleApply(s.id)}
                disabled={s.status === 'approved'}
                className={`w-full py-3 rounded-xl font-black transition-all shadow-xl active:scale-95 mt-2 ${
                  s.status === 'approved' 
                    ? 'bg-gray-800 text-gray-400 cursor-not-allowed border border-white/5' 
                    : 'bg-teal-600 hover:bg-teal-500 text-white shadow-teal-500/20'
                }`}
              >
                {s.status === 'approved' ? 'APPROVED & APPLIED' : 'APPLY CALIBRATION'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
