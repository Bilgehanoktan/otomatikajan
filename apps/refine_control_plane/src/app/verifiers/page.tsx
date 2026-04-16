
"use client";

import React from "react";

export default function VerifiersPage() {
  const [verifiers, setVerifiers] = React.useState<any[]>([]);

  React.useEffect(() => {
    const fetchVerifiers = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/repair-lab/verifiers');
        const data = await response.json();
        setVerifiers(data);
      } catch (err) {
        console.error("Failed to fetch verifiers", err);
      }
    };
    fetchVerifiers();
  }, []);

  return (
    <div className="p-8 space-y-8 min-h-screen bg-[#050510] text-gray-200">
      <header>
        <h1 className="text-4xl font-black bg-gradient-to-r from-purple-400 to-indigo-500 bg-clip-text text-transparent">
          VERIFIER MESH ANALYTICS
        </h1>
        <p className="text-gray-500 mt-2 font-mono uppercase tracking-widest text-xs">
          Multi-Layer Validation Reliability | Precision Metrics | Latency Budget
        </p>
      </header>

      <div className="bg-gray-900/50 backdrop-blur-md rounded-2xl border border-white/5 shadow-2xl overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-white/5 text-gray-400 font-black text-xs uppercase tracking-widest">
            <tr>
              <th className="px-8 py-6">Layer Architecture</th>
              <th className="px-8 py-6">Reliability Score</th>
              <th className="px-8 py-6">False Positive Rate</th>
              <th className="px-8 py-6">Avg Latency</th>
              <th className="px-8 py-6">Interceptions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {verifiers.map((v, idx) => (
              <tr key={idx} className="hover:bg-white/5 transition-colors group">
                <td className="px-8 py-6">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center font-bold text-purple-400">
                       {idx + 1}
                    </div>
                    <div className="font-bold text-lg text-white group-hover:text-purple-400 transition-colors">{v.name}</div>
                  </div>
                </td>
                <td className="px-8 py-6">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-1.5 bg-gray-800 rounded-full w-24">
                       <div className="h-full bg-purple-500" style={{ width: `${v.reliability * 100}%` }}></div>
                    </div>
                    <span className="font-mono text-sm">{(v.reliability * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="px-8 py-6 font-mono text-sm text-gray-400">
                  {((1 - v.precision) * 100).toFixed(1)}%
                </td>
                <td className="px-8 py-6 font-mono text-sm text-gray-400">{v.latency}</td>
                <td className="px-8 py-6">
                   <span className="px-4 py-1 bg-red-500/10 text-red-400 text-xs font-bold rounded-full border border-red-500/20">
                     {v.detected_errors} ERRORS BLOCKED
                   </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
