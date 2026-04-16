
"use client";

import React, { useState, useEffect } from "react";

export default function SelfTuningPage() {
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSuggestions = async () => {
    try {
      const response = await fetch('/api/v1/repair-lab/tuning/suggestions');
      const data = await response.json();
      
      if (!Array.isArray(data)) {
        console.error("Self-Tuning: Beklenen dizi gelmedi", data);
        setSuggestions([]);
        return;
      }

      setSuggestions(data);
    } catch (err) {
      console.error("Öneriler alınamadı", err);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuggestions();
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
    <div className="p-8 text-teal-400 font-mono animate-pulse bg-[#050510] min-h-screen">
      Kalibrasyon Önerileri Hesaplanıyor... [OPTIMIZER]
    </div>
  );

  return (
    <div className="p-8 space-y-8 min-h-screen bg-[#050510] text-gray-200">
      <header className="border-b border-white/5 pb-6">
        <h1 className="text-4xl font-black bg-gradient-to-r from-teal-400 to-blue-500 bg-clip-text text-transparent uppercase">
          OTONOM AYAR KONSOLU
        </h1>
        <p className="text-gray-500 mt-2 font-mono uppercase tracking-[0.2em] text-[10px]">
          Politika Kalibrasyonu | Parametre Optimizasyonu | Veri Odaklı Karar Hattı
        </p>
      </header>

      {suggestions.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-96 border border-dashed border-teal-500/10 rounded-3xl bg-teal-500/[0.02]">
           <span className="text-6xl mb-6 grayscale opacity-20">⚙️</span>
           <p className="text-gray-600 font-mono text-sm max-w-xs text-center">
             Henüz bekleyen kalibrasyon önerisi bulunmuyor. Sistem performans verilerini topladıkça optimizasyon önerileri üretecektir.
           </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {suggestions.map((s) => (
            <div key={s.id} className={`bg-gray-900/40 backdrop-blur-xl rounded-2xl p-8 border ${s.status === 'pending' ? 'border-teal-500/20 shadow-teal-500/5' : 'border-white/5'} shadow-2xl flex flex-col xl:flex-row justify-between gap-8 items-center transition-all`}>
              <div className="flex-1 space-y-5">
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 text-[10px] font-black rounded-full border ${
                    s.status === 'approved' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 
                    s.status === 'rejected' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 
                    'bg-teal-500/10 text-teal-400 border-teal-500/20'
                  } uppercase tracking-widest`}>
                    ÖNERİ {s.id.slice(0,8)} | {s.status === 'pending' ? 'BEKLİYOR' : (s.status === 'approved' ? 'ONAYLANDI' : 'REDDEDİLDİ')}
                  </span>
                  <h3 className="text-2xl font-bold text-white tracking-tight">{s.parameter}</h3>
                </div>
                <p className="text-gray-400 text-sm leading-relaxed max-w-3xl italic">"{s.reason}"</p>
                <div className="flex gap-8 pt-2">
                  <div className="bg-white/[0.02] p-3 rounded-lg border border-white/5">
                    <div className="text-[9px] text-gray-500 uppercase font-black mb-1 tracking-widest">Beklenen Etki</div>
                    <div className="text-teal-400 font-mono font-bold text-xs uppercase">{s.impact}</div>
                  </div>
                  <div className="bg-white/[0.02] p-3 rounded-lg border border-white/5">
                    <div className="text-[9px] text-gray-500 uppercase font-black mb-1 tracking-widest">Güven Skoru</div>
                    <div className="text-white font-mono font-bold text-base">%85</div>
                  </div>
                </div>
              </div>

              <div className="flex flex-col items-center gap-6 bg-black/40 p-8 rounded-3xl border border-white/5 min-w-[350px]">
                <div className="flex items-center gap-10">
                   <div className="text-center">
                     <div className="text-gray-500 text-[9px] uppercase font-black mb-2 tracking-widest">Mevcut</div>
                     <div className="text-2xl font-black text-gray-500 font-mono">{s.current_value}</div>
                   </div>
                   <div className="text-teal-500 text-2xl animate-pulse">→</div>
                   <div className="text-center">
                     <div className="text-teal-400 text-[9px] uppercase font-black mb-2 tracking-widest">Önerilen</div>
                     <div className="text-3xl font-black text-white font-mono">{s.proposed_value}</div>
                   </div>
                </div>
                
                {s.status === 'pending' ? (
                  <div className="flex gap-3 w-full">
                    <button 
                      onClick={() => handleAction(s.id, 'approved')}
                      className="flex-1 py-3 bg-teal-600 hover:bg-teal-500 text-black font-black rounded-xl transition-all shadow-lg shadow-teal-500/10 active:scale-95 text-xs uppercase"
                    >
                      Uygula
                    </button>
                    <button 
                      onClick={() => handleAction(s.id, 'rejected')}
                      className="px-6 py-3 border border-white/10 hover:bg-white/5 text-gray-400 font-bold rounded-xl transition-all active:scale-95 text-xs uppercase"
                    >
                      Yoksay
                    </button>
                  </div>
                ) : (
                  <div className={`w-full py-3 rounded-xl font-black text-center text-xs uppercase border ${
                    s.status === 'approved' ? 'bg-green-500/5 text-green-500 border-green-500/20' : 'bg-red-500/5 text-red-500 border-red-500/20'
                  }`}>
                    {s.status === 'approved' ? 'KALİBRASYON TAMAMLANDI' : 'ÖNERİ REDDEDİLDİ'}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
