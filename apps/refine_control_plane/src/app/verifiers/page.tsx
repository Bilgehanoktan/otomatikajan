
"use client";

import React, { useState, useEffect } from "react";

export default function VerifiersPage() {
  const [verifiers, setVerifiers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVerifiers = async () => {
      try {
        const response = await fetch('/api/v1/repair-lab/verifiers');
        const data = await response.json();
        setVerifiers(data);
      } catch (err) {
        console.error("Doğrulayıcı verileri alınamadı", err);
      } finally {
        setLoading(false);
      }
    };
    fetchVerifiers();
  }, []);

  if (loading) return (
    <div className="p-8 text-purple-400 font-mono animate-pulse bg-[#050510] min-h-screen">
      Doğrulama Katmanları Analiz Ediliyor... [VERIFIER_MESH]
    </div>
  );

  return (
    <div className="p-8 space-y-8 min-h-screen bg-[#050510] text-gray-200">
      <header className="border-b border-white/5 pb-6">
        <h1 className="text-4xl font-black bg-gradient-to-r from-purple-400 via-indigo-500 to-blue-600 bg-clip-text text-transparent uppercase">
          DOĞRULAMA AĞI (VERIFIER MESH) ANALİTİĞİ
        </h1>
        <p className="text-gray-500 mt-2 font-mono uppercase tracking-[0.2em] text-[10px]">
          Çok Katmanlı Doğrulama Güvenilirliği | Hassasiyet Metrikleri | Gecikme Bütçesi
        </p>
      </header>

      <div className="bg-gray-900/40 backdrop-blur-xl rounded-3xl border border-white/5 shadow-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-white/[0.02] text-gray-500 font-black text-[10px] uppercase tracking-widest border-b border-white/5">
              <tr>
                <th className="px-8 py-6">Katman Mimarisi</th>
                <th className="px-8 py-6">Güvenilirlik Skoru</th>
                <th className="px-8 py-6">Hassasiyet (Precision)</th>
                <th className="px-8 py-6">Ort. Gecikme</th>
                <th className="px-8 py-6">Engellenen Hatalar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {verifiers.length === 0 ? (
                <tr>
                   <td colSpan={5} className="px-8 py-12 text-center text-gray-600 font-mono text-xs italic">
                     Henüz verifier verisi toplanmadı.
                   </td>
                </tr>
              ) : verifiers.map((v, idx) => (
                <tr key={idx} className="hover:bg-white/[0.02] transition-all group">
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center font-bold text-purple-400 shadow-inner group-hover:scale-110 transition-transform">
                         {idx + 1}
                      </div>
                      <div>
                        <div className="font-bold text-base text-white group-hover:text-purple-400 transition-colors uppercase tracking-tight">{v.name}</div>
                        <div className="text-[10px] text-gray-600 font-mono">INTERNAL_VAL_{v.name.toUpperCase()}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-1 bg-white/5 rounded-full w-24 overflow-hidden">
                         <div 
                           className="h-full bg-gradient-to-r from-purple-600 to-indigo-400 transition-all duration-1000" 
                           style={{ width: `${v.reliability * 100}%` }}
                         ></div>
                      </div>
                      <span className="font-mono text-xs font-bold text-gray-300">{(v.reliability * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="px-8 py-6 font-mono text-xs text-gray-400">
                    <span className={v.precision > 0.9 ? 'text-green-500/80' : 'text-gray-400'}>
                      {(v.precision * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-8 py-6 font-mono text-xs text-gray-500 italic">
                    {v.latency}
                  </td>
                  <td className="px-8 py-6">
                     <span className="px-4 py-1.5 bg-red-500/10 text-red-500 text-[10px] font-black rounded-lg border border-red-500/10 uppercase tracking-tighter">
                       {v.detected_errors} Hatalı İndirgeme
                     </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
         <div className="bg-gray-900/40 p-6 rounded-2xl border border-white/5 space-y-2">
            <h4 className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Global Hassasiyet</h4>
            <div className="text-2xl font-black text-white font-mono">0.992 <span className="text-green-500 text-sm">↑</span></div>
         </div>
         <div className="bg-gray-900/40 p-6 rounded-2xl border border-white/5 space-y-2">
            <h4 className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Bütçelenmiş Gecikme</h4>
            <div className="text-2xl font-black text-white font-mono">1500ms</div>
         </div>
         <div className="bg-gray-900/40 p-6 rounded-2xl border border-white/5 space-y-2">
            <h4 className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Aktif Katman Sayısı</h4>
            <div className="text-2xl font-black text-primary font-mono text-purple-400">{verifiers.length}</div>
         </div>
      </div>
    </div>
  );
}
