
import React from "react";

export const PatchTournamentBoard = ({ data }: { data: any }) => {
  return (
    <div className="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-blue-500/20 shadow-2xl">
      <h3 className="text-xl font-bold text-blue-400 mb-4 flex items-center gap-2">
        <span className="p-2 bg-blue-500/10 rounded-lg">🏆</span>
        Active Tournament Board
      </h3>
      <div className="space-y-4">
        {data?.candidates?.map((candidate: any, idx: number) => (
          <div 
            key={idx}
            className={`p-4 rounded-lg border flex justify-between items-center transition-all ${
              candidate.status === 'winner' 
                ? 'bg-green-500/10 border-green-500/30' 
                : 'bg-gray-800/50 border-gray-700/30'
            }`}
          >
            <div className="flex flex-col">
              <span className="text-sm font-medium text-gray-400 uppercase tracking-wider">{candidate.strategy} Strategy</span>
              <span className="text-lg font-bold text-white">{candidate.status === 'winner' ? '🏆 Champion Candidate' : 'Candidate'}</span>
            </div>
            <div className="text-right">
              <div className="text-2xl font-black text-blue-400">{(candidate.score * 100).toFixed(1)}%</div>
              <div className="text-xs text-gray-500">Trust Score</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const VerifierMatrix = ({ matrix }: { matrix: any }) => {
  return (
    <div className="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-purple-500/20 shadow-2xl overflow-x-auto">
      <h3 className="text-xl font-bold text-purple-400 mb-4 flex items-center gap-2">
        <span className="p-2 bg-purple-500/10 rounded-lg">🧬</span>
        Verifier Reliability Matrix
      </h3>
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="py-3 px-4 text-xs font-bold text-gray-500 uppercase">Strategy</th>
            {matrix?.verifiers?.map((v: string) => (
              <th key={v} className="py-3 px-4 text-xs font-bold text-gray-500 uppercase">{v}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix?.candidates?.map((c: any, idx: number) => (
            <tr key={idx} className="border-b border-gray-800/50 hover:bg-white/5 transition-colors">
              <td className="py-4 px-4 font-bold text-white">{c.name}</td>
              {c.results.map((res: number, i: number) => (
                <td key={i} className="py-4 px-4">
                  <div 
                    className={`w-full h-2 rounded-full ${
                      res > 0.8 ? 'bg-green-500' : res > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ opacity: 0.3 + res * 0.7 }}
                  ></div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
