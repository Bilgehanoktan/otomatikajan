
"use client";

import React, { useState, useEffect } from "react";

export default function SelfTuningPage() {
  const [isClient, setIsClient] = useState(false);
  useEffect(() => setIsClient(true), []);

  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [evolutionFeed, setEvolutionFeed] = useState<any[]>([]);
  const [evolutionStatus, setEvolutionStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  if (!isClient) return <div className="p-8 bg-[#050510] min-h-screen" />;

  const fetchData = async () => {
    if (!isClient) return;
    try {
      const [sugRes, feedRes, statusRes] = await Promise.all([
        fetch('/api/v1/repair-lab/tuning/suggestions'),
        fetch('/api/v1/repair-lab/evolution/feed'),
        fetch('/api/v1/repair-lab/evolution/status')
      ]);

      const sugData = await sugRes.json();
      const feedData = await feedRes.json();
      const statusData = await statusRes.json();
      
      setSuggestions(Array.isArray(sugData) ? sugData : []);
      setEvolutionFeed(Array.isArray(feedData) ? feedData : []);
      setEvolutionStatus(statusData);
    } catch (err) {
      console.error("Veri alınamadı", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // 30 sn de bir güncelle
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (id: string, status: 'approved' | 'rejected') => {
    try {
      const response = await fetch(`/api/v1/repair-lab/tuning/suggestions/${id}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (response.ok) {
        setSuggestions(prev => prev.map(s => s.id === id ? { ...s, status } : s));
      }
    } catch (err) {
      console.error("İşlem başarısız", err);
    }
  };

  if (loading) return (
    <div className="p-8 text-teal-400 font-mono animate-pulse bg-[#050510] min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="text-4xl mb-4">🧬</div>
        KALİBRASYON VE EVRİM VERİLERİ YÜKLENİYOR...
      </div>
    </div>
  );

  return (
    <div className="p-8 space-y-12 min-h-screen bg-[#050510] text-gray-200">
      <header className="border-b border-white/5 pb-8 flex justify-between items-end">
        <div>
          <h1 className="text-5xl font-black bg-gradient-to-r from-teal-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent italic tracking-tighter uppercase">
            OTONOM GELİŞİM MERKEZİ
          </h1>
          <p className="text-gray-500 mt-3 font-mono uppercase tracking-[0.3em] text-[10px]">
            Continuous Evolution & Policy Calibration | Sovereign AGI v13.04
          </p>
        </div>
        <div className="flex gap-4">
           <div className="bg-white/5 px-6 py-3 rounded-2xl border border-white/10 text-right">
             <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest mb-1">Döngü Durumu</div>
             <div className="flex items-center gap-2">
               <span className={`w-2 h-2 rounded-full ${evolutionStatus?.is_running ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
               <span className="text-sm font-black font-mono uppercase">{evolutionStatus?.is_running ? 'AKTİF' : 'DURDURULDU'}</span>
             </div>
           </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* SOL KOLON: KALİBRASYON ÖNERİLERİ */}
        <div className="lg:col-span-2 space-y-8">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <span className="text-teal-400">01.</span> POLİTİKA OPTİMİZASYONU
            </h2>
            <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest">{suggestions.length} ÖNERİ</span>
          </div>

          {suggestions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 border border-dashed border-white/5 rounded-3xl bg-white/[0.01]">
              <p className="text-gray-600 font-mono text-xs italic text-center">
                Henüz bekleyen kalibrasyon önerisi bulunmuyor.<br/>Sistem performans verilerini topladıkça optimizasyon önerileri üretecektir.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {suggestions.map((s) => (
                <div key={s.id} className="bg-gradient-to-br from-gray-900/60 to-black/40 backdrop-blur-3xl rounded-3xl p-8 border border-white/5 shadow-2xl relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-teal-500/5 blur-[80px] group-hover:bg-teal-500/10 transition-all"></div>
                  
                  <div className="relative z-10 flex flex-col md:flex-row justify-between gap-8 items-start">
                    <div className="flex-1 space-y-4">
                      <div className="flex items-center gap-3">
                        <span className="text-teal-400 font-mono text-xs">[{s.id}]</span>
                        <h3 className="text-2xl font-black text-white uppercase tracking-tight">{s.parameter}</h3>
                      </div>
                      <p className="text-gray-400 text-sm leading-relaxed max-w-xl">{s.reason}</p>
                      
                      <div className="flex gap-8 pt-4">
                        <div>
                          <div className="text-[9px] text-gray-600 uppercase font-black mb-1 tracking-widest text-xs">Beklenen Etki</div>
                          <div className="text-teal-400 font-bold text-xs">{s.impact}</div>
                        </div>
                        <div>
                          <div className="text-[9px] text-gray-600 uppercase font-black mb-1 tracking-widest text-xs">Güven Oranı</div>
                          <div className="text-white font-bold text-xs">{(s.confidence * 100).toFixed(0)}%</div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-black/40 p-6 rounded-2xl border border-white/5 min-w-[280px] flex flex-col gap-4">
                      <div className="flex justify-between items-center px-2">
                        <div className="text-center">
                          <span className="block text-gray-600 text-[8px] uppercase font-bold mb-1">Mevcut</span>
                          <span className="text-xl font-mono text-gray-500">{s.current_value}</span>
                        </div>
                        <span className="text-teal-500/50">→</span>
                        <div className="text-center">
                          <span className="block text-teal-400 text-[8px] uppercase font-bold mb-1">Önerilen</span>
                          <span className="text-2xl font-mono text-white font-black">{s.proposed_value}</span>
                        </div>
                      </div>

                      {s.status === 'pending' ? (
                        <div className="flex gap-2">
                          <button 
                            onClick={() => handleAction(s.id, 'approved')}
                            className="flex-1 py-3 bg-teal-600 hover:bg-teal-500 text-black font-black rounded-xl transition-all text-[10px] uppercase shadow-lg shadow-teal-500/20"
                          >
                            Uygula
                          </button>
                          <button 
                            onClick={() => handleAction(s.id, 'rejected')}
                            className="px-4 py-3 border border-white/10 hover:bg-white/5 text-gray-400 font-bold rounded-xl transition-all text-[10px] uppercase"
                          >
                            Reddet
                          </button>
                        </div>
                      ) : (
                        <div className={`py-3 rounded-xl font-black text-center text-[9px] uppercase border ${
                          s.status === 'approved' ? 'bg-green-500/5 text-green-500 border-green-500/20' : 'bg-red-500/5 text-red-500 border-red-500/20'
                        }`}>
                          {s.status === 'approved' ? 'KALİBRASYON TAMAMLANDI' : 'ÖNERİ REDDEDİLDİ'}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SAĞ KOLON: CANLI GELİŞİM AKIŞI */}
        <div className="space-y-8">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <span className="text-blue-400">02.</span> CANLI EVRİM AKIŞI
            </h2>
            <div className="flex items-center gap-2">
               <span className="animate-ping w-1.5 h-1.5 rounded-full bg-blue-500"></span>
               <span className="text-[10px] font-mono text-blue-500 uppercase tracking-widest text-xs">LIVE</span>
            </div>
          </div>

          <div className="bg-gray-900/20 rounded-3xl border border-white/5 overflow-hidden flex flex-col h-[700px] shadow-inner shadow-black/50">
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
              {evolutionFeed.length === 0 ? (
                <div className="p-8 text-center text-gray-600 font-mono text-xs italic">
                  Gelişim verisi toplanıyor...
                </div>
              ) : (
                evolutionFeed.map((item) => (
                  <div key={item.id} className={`p-5 rounded-2xl border ${item.success ? 'bg-blue-500/[0.03] border-blue-500/10' : 'bg-red-500/[0.1] border-red-500/20'} group transition-all hover:bg-white/[0.02]`}>
                    <div className="flex justify-between items-start mb-2">
                      <span className={`text-[9px] font-black px-2 py-0.5 rounded-md ${item.success ? 'bg-blue-500/10 text-blue-400' : 'bg-red-500/10 text-red-400'}`}>
                        {item.success ? 'GÜNCELLEME BAŞARILI' : 'DENEME BAŞARISIZ'}
                      </span>
                      <span className="text-[8px] text-gray-600 font-mono italic">{new Date(item.created_at).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-xs font-bold text-gray-200 mb-1 font-mono truncate">{item.component}</div>
                    <p className="text-[10px] text-gray-500 leading-relaxed mb-3">{item.rationale}</p>
                    {!item.success && (
                      <div className="p-2 bg-red-900/10 rounded-lg border border-red-500/5 text-[9px] text-red-400/70 font-mono italic">
                         Hata: {item.output.slice(0, 100)}...
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
            
            <div className="p-6 bg-black/40 border-t border-white/5">
              <div className="flex items-center justify-between mb-4">
                 <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Takılma Durumu</span>
                 <span className="text-[10px] font-mono text-gray-400">{Object.keys(evolutionStatus?.failure_counts || {}).length} Aktif Vaka</span>
              </div>
              <div className="space-y-3">
                 {Object.entries(evolutionStatus?.failure_counts || {}).map(([file, count]: [string, any]) => (
                   count > 0 && (
                     <div key={file} className="flex items-center justify-between bg-white/[0.02] p-3 rounded-xl border border-white/5">
                        <span className="text-[9px] font-mono text-gray-500 truncate max-w-[150px]">{file}</span>
                        <div className="flex items-center gap-2">
                           <div className="flex gap-0.5">
                             {[...Array(evolutionStatus.stuck_threshold)].map((_, i) => (
                               <div key={i} className={`w-1.5 h-1.5 rounded-full ${i < count ? 'bg-red-500 shadow-[0_0_5px_rgba(239,68,68,0.5)]' : 'bg-gray-800'}`}></div>
                             ))}
                           </div>
                           <span className="text-[10px] font-black text-red-500 uppercase">{count >= evolutionStatus.stuck_threshold ? 'TIKANDI' : 'RİSK'}</span>
                        </div>
                     </div>
                   )
                 ))}
                 {(!evolutionStatus?.failure_counts || Object.values(evolutionStatus?.failure_counts).every(c => c === 0)) && (
                   <div className="text-[10px] text-green-500/30 italic text-center py-2">Frenleyici tıkanma tespit edilmedi.</div>
                 )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <footer className="pt-12 border-t border-white/5 flex justify-between items-center text-gray-600">
         <div className="text-[9px] font-mono uppercase tracking-widest italic opacity-50">Sovereign Governance Layer :: Verified by LineageEngine v2</div>
         <div className="flex gap-6 text-[9px] font-black uppercase tracking-widest">
            <span className="hover:text-white pointer-events-none transition-colors">Lab Stats</span>
            <span className="hover:text-white pointer-events-none transition-colors">Audit Bundle</span>
            <span className="hover:text-white pointer-events-none transition-colors">Risk Matrix</span>
         </div>
      </footer>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.1);
        }
      `}</style>
    </div>
  );
}
