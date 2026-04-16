
"use client";

import React, { useState, useEffect } from "react";

export default function RepairMemoryPage() {
  const [subsystems, setSubsystems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMemory = async () => {
      try {
        const response = await fetch('/api/v1/repair-lab/memory/heatmaps');
        const data = await response.json();
        setSubsystems(data);
      } catch (err) {
        console.error("Tamir hafızası alınamadı", err);
      } finally {
        setLoading(false);
      }
    };
    fetchMemory();
  }, []);

  if (loading) return (
    <div className="p-8 text-orange-400 font-mono animate-pulse bg-[#050510] min-h-screen">
      Hafıza Katmanları Simüle Ediliyor... [TANIMLAMA]
    </div>
  );

  return (
    <div className="p-8 space-y-8 min-h-screen bg-[#050510] text-gray-200">
      <header className="border-b border-white/5 pb-6">
        <h1 className="text-4xl font-black bg-gradient-to-r from-orange-400 via-red-500 to-purple-600 bg-clip-text text-transparent uppercase text-center md:text-left">
          TAMİR HAFIZASI & RİSK HARİTASI
        </h1>
        <p className="text-gray-500 mt-2 font-mono uppercase tracking-[0.2em] text-[10px] text-center md:text-left">
          Geçmiş Deneyimler | Alt Sistem Güvenilirliği | Tekrarlanan Hatalar
        </p>
      </header>

      {subsystems.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-96 border border-dashed border-white/5 rounded-3xl bg-white/[0.01]">
           <span className="text-6xl mb-6 grayscale opacity-20">🧠</span>
           <p className="text-gray-600 font-mono text-sm max-w-xs text-center">
             Hafızada henüz kayıtlı tamir deseni bulunmuyor. Sistem öğrendikçe burası dolacaktır.
           </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {subsystems.map((sub, idx) => {
            const risk = 1 - (sub.rate || 0);
            return (
              <div key={idx} className="bg-gray-900/40 backdrop-blur-xl rounded-2xl p-6 border border-white/5 shadow-2xl relative overflow-hidden group hover:border-orange-500/30 transition-all duration-500">
                <div 
                  className="absolute top-0 right-0 w-32 h-32 bg-orange-500/10 rounded-full -mr-16 -mt-16 blur-3xl group-hover:bg-orange-500/20 transition-all duration-700"
                  style={{ opacity: 0.1 + risk * 0.4 }}
                ></div>
                
                <div className="relative z-10 space-y-4">
                  <div className="flex justify-between items-start">
                    <h3 className="text-base font-bold text-white truncate w-2/3 uppercase tracking-tighter group-hover:text-orange-400 transition-colors">
                      {sub.subsystem}
                    </h3>
                    <span className="text-[9px] font-black py-0.5 px-1.5 bg-white/5 border border-white/5 rounded text-gray-400 font-mono">
                      #{idx+1}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-end">
                    <div>
                      <div className="text-[9px] text-gray-500 uppercase font-black tracking-widest mb-1">Başarı Oranı</div>
                      <div className={`text-3xl font-black ${
                        sub.rate > 0.8 ? 'text-green-400' : sub.rate > 0.5 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {(sub.rate * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[9px] text-gray-500 uppercase font-black tracking-widest mb-1">Risk Skoru</div>
                      <div className="text-xl font-bold text-white font-mono">{(risk * 100).toFixed(0)}</div>
                    </div>
                  </div>

                  <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-[2000ms] ease-out ${
                        risk > 0.7 ? 'bg-gradient-to-r from-red-600 to-red-400' : 
                        risk > 0.4 ? 'bg-gradient-to-r from-yellow-600 to-yellow-400' : 
                        'bg-gradient-to-r from-green-600 to-green-400'
                      }`}
                      style={{ width: `${risk * 100}%` }}
                    ></div>
                  </div>

                  <div className="flex justify-between text-[10px] font-mono text-gray-500 pt-3 border-t border-white/5">
                    <span>{sub.failure} Kayıtlı Hata</span>
                    <span className="text-orange-400/80 cursor-pointer hover:text-orange-300 transition-colors uppercase font-black tracking-tighter italic">Analiz Et →</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
