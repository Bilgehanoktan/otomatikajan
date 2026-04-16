
"use client";

import React, { useState, useEffect } from "react";
import { PatchTournamentBoard, VerifierMatrix } from "@/components/repair/LabComponents";

export default function RepairLabPage() {
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [tournament, setTournament] = useState<any>(null);
  const [matrix, setMatrix] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      // 1. Fetch Benchmarks
      const benchRes = await fetch('/api/v1/repair-lab/benchmarks');
      const benchData = await benchRes.json();
      setBenchmarks(benchData);

      // 2. Fetch Latest Tournament
      const tourRes = await fetch('/api/v1/repair-lab/tournaments');
      const tourData = await tourRes.json();
      if (tourData && tourData.length > 0) {
        const latest = tourData[0];
        setTournament(latest);

        // 3. Fetch Matrix for this tournament
        const matrixRes = await fetch(`/api/v1/repair-lab/verifiers/matrix?tournament_id=${latest.id}`);
        const matrixData = await matrixRes.json();
        setMatrix(matrixData);
      }
    } catch (err) {
      console.error("Laboratuvar verileri alınamadı", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000); 
    return () => clearInterval(interval);
  }, []);

  const runLab = async () => {
    setLoading(true);
    try {
      // Trigger a benchmark run (Simulated for Phase 28)
      await fetch('/api/v1/repair-lab/run', { method: 'POST' });
      alert("Otonom Tamir Laboratuvarı başlatıldı! Sonuçlar birazdan yansıyacaktır.");
      setTimeout(fetchData, 2000);
    } catch (err) {
      alert("Laboratuvar başlatılamadı.");
    } finally {
      setLoading(false);
    }
  };

  if (loading && benchmarks.length === 0) return (
    <div className="p-8 text-blue-400 font-mono animate-pulse bg-[#050510] min-h-screen">
      Deneysel Ortam Hazırlanıyor... [OTONOM LABORATUVAR]
    </div>
  );

  return (
    <div className="p-8 space-y-8 min-h-screen bg-[#050510] text-gray-200">
      <header className="flex justify-between items-center border-b border-white/5 pb-6">
        <div>
          <h1 className="text-4xl font-black bg-gradient-to-r from-blue-400 via-purple-400 to-green-400 bg-clip-text text-transparent">
            OTONOM TAMİR LABORATUVARI
          </h1>
          <p className="text-gray-500 mt-2 font-mono uppercase tracking-[0.2em] text-[10px]">
            Aşama 28 | Bilimsel Kanıt Zinciri ve Yama Turnuvası Sistemi
          </p>
        </div>
        <div className="flex gap-4">
           <button 
             onClick={runLab}
             className="px-8 py-3 bg-gradient-to-br from-blue-600 to-blue-800 hover:from-blue-500 hover:to-blue-700 text-white rounded-xl font-bold transition-all shadow-xl shadow-blue-900/40 active:scale-95 border border-blue-400/20"
           >
             Benchmark Başlat
           </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Left Column: Benchmarks */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-gray-900/40 backdrop-blur-xl rounded-2xl p-6 border border-white/5 shadow-2xl">
            <h3 className="text-lg font-bold text-gray-400 mb-6 flex items-center gap-3">
              <span className="p-2 bg-gray-800/80 rounded-lg text-sm">📊</span>
              Sistem Benchmarkları
            </h3>
            <div className="space-y-3">
              {benchmarks.length === 0 && (
                <div className="text-xs text-gray-600 italic">Kayıtlı benchmark bulunamadı.</div>
              )}
              {benchmarks.map((b: any) => (
                <div key={b.id} className="p-4 bg-white/[0.02] rounded-xl border border-white/5 hover:border-blue-500/40 transition-all cursor-pointer group hover:bg-white/[0.05]">
                  <div className="flex justify-between items-start">
                    <span className="text-sm font-bold text-white group-hover:text-blue-400 transition-colors uppercase tracking-tight">
                      {b.name}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-tighter ${
                      b.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'
                    }`}>
                      {b.status === 'completed' ? 'TAMAM' : 'AKTİF'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-3">
                     <div className="text-[10px] text-gray-500 font-mono">
                        Başarı: <span className="text-gray-300">{(b.success_rate * 100).toFixed(0)}%</span>
                     </div>
                     <div className="text-[10px] text-gray-500 font-mono">
                        Skor: <span className="text-gray-300">{(b.avg_score * 100).toFixed(0)}</span>
                     </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Active Tournament & Verifiers */}
        <div className="lg:col-span-3 space-y-8">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
             <PatchTournamentBoard data={tournament} />
             <div className="space-y-4">
                <div className="bg-gray-900/40 backdrop-blur-xl rounded-2xl p-6 border border-white/5 h-full">
                  <h3 className="text-lg font-bold text-gray-400 mb-4">Turnuva Özeti</h3>
                  {tournament ? (
                    <div className="space-y-4">
                      <div className="flex justify-between text-sm py-2 border-b border-white/5">
                        <span className="text-gray-500">Incident ID</span>
                        <span className="text-blue-400 font-mono">{tournament.incident_id}</span>
                      </div>
                      <div className="flex justify-between text-sm py-2 border-b border-white/5">
                        <span className="text-gray-500">Toplam Adaylar</span>
                        <span className="text-white font-bold">{tournament.total_candidates}</span>
                      </div>
                      <div className="flex justify-between text-sm py-2 border-b border-white/5">
                         <span className="text-gray-500">Oluşturma</span>
                         <span className="text-gray-400">{new Date(tournament.created_at).toLocaleTimeString()}</span>
                      </div>
                      <div className="mt-4 p-4 bg-blue-500/5 rounded-lg border border-blue-500/10">
                        <p className="text-[11px] text-blue-300/60 leading-relaxed font-serif italic">
                          "Sistem, belirlenen 5 kriter üzerinden adayları sıraladı. 
                          Şampiyon aday, regresyon riski en düşük olan stratejidir."
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-48 text-gray-700 text-sm">
                      Veri bekleniyor...
                    </div>
                  )}
                </div>
             </div>
          </div>
          <VerifierMatrix matrix={matrix} />
        </div>
      </div>
    </div>
  );
}
