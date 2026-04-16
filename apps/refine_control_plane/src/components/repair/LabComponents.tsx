
import React from "react";

export const PatchTournamentBoard = ({ data }: { data: any }) => {
  if (!data) return (
    <div className="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-gray-800 animate-pulse">
      <div className="h-6 w-48 bg-gray-800 rounded mb-4"></div>
      <div className="space-y-4">
        {[1, 2, 3].map(i => <div key={i} className="h-16 bg-gray-800 rounded"></div>)}
      </div>
    </div>
  );

  return (
    <div className="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-blue-500/20 shadow-2xl">
      <h3 className="text-xl font-bold text-blue-400 mb-4 flex items-center gap-2">
        <span className="p-2 bg-blue-500/10 rounded-lg">🏆</span>
        Aktif Turnuva Tablosu
      </h3>
      <div className="space-y-4">
        {data?.candidates?.length === 0 && (
          <div className="p-8 text-center text-gray-500 italic border border-dashed border-gray-800 rounded-lg">
            Henüz aktif aday bulunmuyor. Benchmark başlatın.
          </div>
        )}
        {data?.candidates?.map((candidate: any, idx: number) => (
          <div 
            key={idx}
            className={`p-4 rounded-lg border flex justify-between items-center transition-all ${
              candidate.status === 'winner' 
                ? 'bg-green-500/10 border-green-500/30 ring-1 ring-green-500/20' 
                : candidate.status === 'rejected'
                ? 'bg-red-500/5 border-red-500/10 opacity-60'
                : 'bg-gray-800/50 border-gray-700/30'
            }`}
          >
            <div className="flex flex-col">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-widest">{candidate.strategy} Stratejisi</span>
              <span className={`text-lg font-bold ${candidate.status === 'winner' ? 'text-green-400' : 'text-white'}`}>
                {candidate.status === 'winner' ? '🏆 Şampiyon Yama' : 
                 candidate.status === 'rejected' ? 'Reddedilen Aday' : 'Doğrulanmış Aday'}
              </span>
              <span className="text-[10px] text-gray-600 font-mono mt-1">TİP: {candidate.type.toUpperCase()}</span>
            </div>
            <div className="text-right">
              <div className={`text-2xl font-black ${candidate.status === 'winner' ? 'text-green-400' : 'text-blue-400'}`}>
                {(candidate.score * 100).toFixed(1)}%
              </div>
              <div className="text-[10px] text-gray-500 uppercase tracking-tighter">Güven Skoru</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const VerifierMatrix = ({ matrix }: { matrix: any }) => {
  if (!matrix || !matrix.verifiers || matrix.verifiers.length === 0) return (
    <div className="bg-gray-900/50 backdrop-blur-md rounded-xl p-12 text-center text-gray-600 border border-gray-800 italic">
      Matris verisi oluşturulması için bir turnuva seçin veya başlatın.
    </div>
  );

  return (
    <div className="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-purple-500/20 shadow-2xl overflow-x-auto">
      <h3 className="text-xl font-bold text-purple-400 mb-4 flex items-center gap-2">
        <span className="p-2 bg-purple-500/10 rounded-lg">🧬</span>
        Doğrulayıcı (Verifier) Güvenilirlik Matrisi
      </h3>
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="py-3 px-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Strateji</th>
            {matrix.verifiers.map((v: string) => (
              <th key={v} className="py-3 px-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest text-center">{v}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.candidates.map((c: any, idx: number) => (
            <tr key={idx} className="border-b border-gray-800/50 hover:bg-white/5 transition-colors">
              <td className="py-4 px-4 font-bold text-gray-300 text-sm">{c.name}</td>
              {c.results.map((res: number, i: number) => (
                <td key={i} className="py-4 px-4">
                  <div className="relative group flex justify-center">
                    <div 
                      className={`w-12 h-2 rounded-full ${
                        res > 0.8 ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]' : 
                        res > 0.5 ? 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.3)]' : 
                        'bg-red-500'
                      }`}
                      style={{ opacity: 0.2 + res * 0.8 }}
                    ></div>
                    <div className="absolute -top-8 bg-gray-800 text-white text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10 border border-gray-700">
                      Skor: {(res * 100).toFixed(0)}%
                    </div>
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
