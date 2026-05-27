"use client";

import React, { useState, useEffect } from "react";
import {
  Boxes,
  Play,
  CheckCircle,
  XCircle,
  HelpCircle,
  User,
  MessageSquare,
  Shield,
  Activity,
  Cpu,
  Layers,
  CheckSquare,
  RefreshCcw,
  Sparkles,
  Info
} from "lucide-react";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { safeFetchJson } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/runtime";

interface Participant {
  id: string;
  name: string;
  emoji: string;
  role: string;
  description: string;
}

interface DebateMessage {
  agent: string;
  role: string;
  thought: string;
}

interface VoteDetail {
  approved: boolean;
  reason: string;
}

interface DebateResult {
  meeting_id: string;
  proposal: string;
  participants: string[];
  debate: DebateMessage[];
  consensus: boolean;
  votes: Record<string, VoteDetail>;
  final_decision: string;
}

export default function MeetingRoomPage() {
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([
    "architect",
    "qa_engineer",
    "security"
  ]);
  const [proposal, setProposal] = useState<string>(
    "Tüm veritabanı sorgularını async/await olmaksızın doğrudan senkron kütüphaneyle değiştirmek istiyoruz (Performans için)."
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<DebateResult | null>(null);
  const [activeTab, setActiveTab] = useState<"setup" | "history">("setup");
  const [isClient, setIsClient] = useState(false);

  const apiUrl = getApiBaseUrl();

  useEffect(() => {
    setIsClient(true);
  }, []);

  const fetchParticipants = async () => {
    try {
      const data: any = await safeFetchJson(`${apiUrl}/debate/participants`);
      if (Array.isArray(data)) {
        setParticipants(data);
      }
    } catch (err) {
      console.error("Katılımcılar alınamadı:", err);
    }
  };

  useEffect(() => {
    if (!isClient) return;
    fetchParticipants();
  }, [isClient]);

  const toggleParticipant = (id: string) => {
    if (selectedParticipants.includes(id)) {
      if (selectedParticipants.length > 2) {
        setSelectedParticipants(selectedParticipants.filter((p) => p !== id));
      }
    } else {
      setSelectedParticipants([...selectedParticipants, id]);
    }
  };

  const handleStartMeeting = async () => {
    if (!proposal.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const response: any = await safeFetchJson(`${apiUrl}/debate/meeting`, {
        method: "POST",
        body: JSON.stringify({
          proposal,
          participant_ids: selectedParticipants
        })
      });

      if (response && response.meeting_id) {
        setResult(response);
      }
    } catch (err) {
      console.error("Toplantı başlatılamadı:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      <ResourceHeader
        title="Ajan Toplantı Odası (Debate Room)"
        subtitle="MİSYON KRİTİK KARARLAR İÇİN ÇOKLU OTONOM UZMAN KONSENSÜS MOTORU"
        icon={<Boxes size={32} />}
        badge="Phase 12.1 — Multi-Agent Consensus"
        actions={
          <div className="flex bg-white/5 p-1 rounded-2xl border border-white/10">
            <button
              onClick={() => setActiveTab("setup")}
              className={`px-6 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                activeTab === "setup" ? "bg-[var(--primary)] text-[#060a12]" : "text-gray-500 hover:text-white"
              }`}
            >
              Toplantı Kurulumu
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`px-6 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                activeTab === "history" ? "bg-[var(--primary)] text-[#060a12]" : "text-gray-500 hover:text-white"
              }`}
              disabled
            >
              Arşiv
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        {/* LEFT PANEL: Setup or Active Debate */}
        <div className="xl:col-span-8 space-y-10">
          <section className="glass-panel p-8 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-[0.02] pointer-events-none">
              <Boxes size={120} />
            </div>

            <div className="flex items-center justify-between mb-8 relative z-10">
              <h3 className="text-xs font-black text-white uppercase tracking-[0.3em] italic">
                {result ? "Devam Eden Tartışma & Oylama" : "Konsensüs Gündemi ve Öneri"}
              </h3>
              <Activity size={16} className="text-gray-700" />
            </div>

            {!result && !loading && (
              <div className="space-y-8 relative z-10">
                <div>
                  <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-3">
                    MİMARİ VEYA POLİTİKA DEĞİŞİKLİĞİ ÖNERİSİ
                  </label>
                  <textarea
                    value={proposal}
                    onChange={(e) => setProposal(e.target.value)}
                    rows={4}
                    className="w-full bg-black/40 border border-white/10 rounded-2xl p-5 text-sm font-medium text-white focus:outline-none focus:border-[var(--primary)] transition-all font-mono"
                    placeholder="Tartışılacak öneriyi detaylıca yazın..."
                  />
                </div>

                <div className="flex gap-4">
                  {[
                    "Tüm veritabanı sorgularını async/await olmaksızın doğrudan senkron kütüphaneyle değiştirmek istiyoruz (Performans için).",
                    "FastAPI sunucusunda kimlik doğrulama kontrollerini pas geçip sadece IP tabanlı izin kontrolü yapmak istiyoruz.",
                    "Kod kalitesini garantilemek için minimum test coverage oranını otonom olarak %95'e kilitlemek istiyoruz."
                  ].map((tpl, i) => (
                    <button
                      key={i}
                      onClick={() => setProposal(tpl)}
                      className="px-4 py-3 bg-white/5 rounded-xl border border-white/5 text-[9px] font-black text-gray-500 hover:text-[var(--primary)] hover:border-[var(--primary)]/20 transition-all uppercase tracking-wider text-left line-clamp-1 flex-1"
                    >
                      Şablon {i + 1}
                    </button>
                  ))}
                </div>

                <div className="p-5 bg-amber-400/5 rounded-2xl border border-amber-400/10">
                  <div className="flex items-center gap-3 mb-3">
                    <Info size={14} className="text-amber-400" />
                    <span className="text-[9px] font-black text-amber-400 uppercase tracking-widest">
                      KONSENSÜS HÜKMÜ UYARISI
                    </span>
                  </div>
                  <p className="text-[10px] text-gray-500 leading-relaxed font-mono uppercase font-black">
                    Tüm katılımcı uzman ajanlar oy birliğiyle (Consensus) onay vermediği sürece mimari değişiklikler "BLOCKED" durumunda tutulur ve otomatik uygulanamaz.
                  </p>
                </div>

                <button
                  onClick={handleStartMeeting}
                  disabled={selectedParticipants.length < 2 || !proposal.trim()}
                  className="w-full flex items-center justify-center gap-3 py-5 bg-[var(--primary)] text-[#060a12] text-[11px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_48px_rgba(102,252,241,0.4)] transition-all active:scale-[0.98] disabled:opacity-30 disabled:pointer-events-none group"
                >
                  <Play size={16} className="fill-[#060a12] group-hover:scale-125 transition-transform" />
                  <span>Toplantıyı Başlat ve Ajanları Odada Topla</span>
                </button>
              </div>
            )}

            {loading && (
              <div className="py-24 text-center space-y-6 relative z-10">
                <RefreshCcw size={48} className="mx-auto text-[var(--primary)] animate-spin" />
                <h4 className="text-xs font-black text-white uppercase tracking-widest animate-pulse">
                  Ajanlar Toplanıyor ve Tartışma Başlıyor...
                </h4>
                <p className="text-[10px] font-black text-gray-600 uppercase tracking-widest leading-loose">
                  Uzmanlar odaya giriş yaptı. İlk tur fikir alışverişi ve analiz süreci otonom olarak gerçekleştiriliyor.
                </p>
              </div>
            )}

            {result && (
              <div className="space-y-10 relative z-10">
                {/* Proposal Detail Banner */}
                <div className="bg-black/40 border border-white/5 p-6 rounded-3xl space-y-3 font-mono">
                  <div className="text-[9px] text-gray-500 uppercase tracking-widest">Öneri Başlığı & Gündem</div>
                  <div className="text-sm font-semibold text-white leading-relaxed">{result.proposal}</div>
                  <div className="flex gap-4 pt-2 text-[9px] text-gray-500 uppercase font-black tracking-wider border-t border-white/[0.04]">
                    <span>MEETING ID: {result.meeting_id}</span>
                    <span>KATILIMCI SAYISI: {result.participants.length}</span>
                  </div>
                </div>

                {/* Debate Messages Timeline */}
                <div className="space-y-6">
                  <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <MessageSquare size={14} /> 1. TUR: UZMAN GÖRÜŞLERİ VE TARTIŞMA AKIŞI
                  </h4>

                  <div className="space-y-4">
                    {result.debate.map((d, index) => {
                      const agentMeta = participants.find((p) => p.id === d.agent);
                      return (
                        <div
                          key={index}
                          className="flex gap-6 p-6 bg-white/[0.015] rounded-3xl border border-white/5 hover:border-white/10 transition-all"
                        >
                          <div className="text-3xl flex items-center justify-center bg-white/5 w-16 h-16 rounded-2xl border border-white/10 shrink-0">
                            {agentMeta?.emoji || "🤖"}
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center gap-3">
                              <span className="text-xs font-black text-white uppercase">{agentMeta?.name || d.agent}</span>
                              <span className="text-[9px] font-black text-[var(--primary)] bg-[var(--primary)]/10 px-2 py-0.5 rounded-md uppercase">
                                {d.role}
                              </span>
                            </div>
                            <p className="text-xs text-gray-400 leading-relaxed font-semibold italic">
                              "{d.thought}"
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Voting & Decision Section */}
                <div className="space-y-6">
                  <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <CheckSquare size={14} /> 2. TUR: KONSENSÜS OYLAMASI VE KARAR
                  </h4>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {Object.entries(result.votes).map(([agentId, vote]) => {
                      const agentMeta = participants.find((p) => p.id === agentId);
                      return (
                        <div
                          key={agentId}
                          className={`p-6 rounded-3xl border ${
                            vote.approved
                              ? "bg-green-500/5 border-green-500/10 text-green-300"
                              : "bg-red-500/5 border-red-500/10 text-red-300"
                          } space-y-4`}
                        >
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-3">
                              <span className="text-2xl">{agentMeta?.emoji || "🤖"}</span>
                              <span className="text-[10px] font-black uppercase text-white truncate max-w-[100px]">
                                {agentMeta?.name || agentId}
                              </span>
                            </div>
                            <span
                              className={`px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border ${
                                vote.approved
                                  ? "text-green-400 border-green-400/20 bg-green-500/10"
                                  : "text-red-400 border-red-400/20 bg-red-500/10"
                              }`}
                            >
                              {vote.approved ? "ONAY" : "RED"}
                            </span>
                          </div>
                          <p className="text-[10px] leading-relaxed uppercase font-black opacity-80 text-gray-400 font-mono">
                            {vote.reason}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Reset Form Button */}
                <div className="pt-6 border-t border-white/[0.04]">
                  <button
                    onClick={() => setResult(null)}
                    className="flex items-center justify-center gap-2 px-8 py-3 bg-white/5 border border-white/10 hover:bg-white/10 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all"
                  >
                    Yeni Tartışma Gündemi Oluştur
                  </button>
                </div>
              </div>
            )}
          </section>
        </div>

        {/* RIGHT PANEL: Participant Selection & Status */}
        <div className="xl:col-span-4 space-y-10">
          <section className="glass-panel p-8 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.012] to-transparent shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-[0.02] pointer-events-none">
              <Shield size={120} />
            </div>

            <div className="flex items-center gap-4 mb-8 relative z-10 px-2">
              <div className="p-3 bg-white/5 rounded-xl border border-white/10 text-[var(--primary)]">
                <User size={20} />
              </div>
              <div>
                <h3 className="text-xl font-black text-white tracking-tighter uppercase">Katılımcı Uzmanlar</h3>
                <p className="text-[9px] font-black text-gray-600 uppercase tracking-widest mt-1">
                  Toplantı odasında bulunacak uzmanları seçin
                </p>
              </div>
            </div>

            {result ? (
              /* Active Meeting Summary Dashboard */
              <div className="space-y-8 relative z-10 px-2">
                <div className="p-8 rounded-[2rem] border border-white/5 bg-black/40 text-center space-y-4">
                  <div className="mx-auto w-16 h-16 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                    {result.consensus ? (
                      <CheckCircle size={32} className="text-green-500" />
                    ) : (
                      <XCircle size={32} className="text-red-500" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-xs font-black text-white uppercase tracking-widest">Toplantı Sonucu</h4>
                    <p
                      className={`text-sm font-black mt-2 font-mono ${
                        result.consensus ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {result.consensus ? "KONSENSÜS SAĞLANDI" : "KONSENSÜS REDDEDİLDİ"}
                    </p>
                  </div>
                </div>

                <div className="space-y-1">
                  {[
                    {
                      label: "Consensus",
                      val: result.consensus ? "APPROVED" : "BLOCKED",
                      icon: <Shield size={14} className={result.consensus ? "text-green-500" : "text-red-500"} />
                    },
                    {
                      label: "Decision Status",
                      val: result.consensus ? "READY FOR DEPLOY" : "REALIGNMENT REQUIRED",
                      icon: <Cpu size={14} />
                    },
                    {
                      label: "Verdict Policy",
                      val: result.final_decision,
                      icon: <Layers size={14} />
                    }
                  ].map((item, idx) => (
                    <div
                      key={idx}
                      className="flex flex-col py-4 border-b border-white/[0.03] last:border-0 hover:bg-white/[0.012] transition-colors rounded-xl px-2 space-y-2"
                    >
                      <div className="flex items-center gap-3 text-gray-600">
                        {item.icon}
                        <span className="text-[8px] font-black uppercase tracking-widest">{item.label}</span>
                      </div>
                      <span className="text-[10px] font-black text-white font-mono uppercase leading-relaxed">
                        {item.val}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* Participant Setup Selector List */
              <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 relative z-10">
                {participants.length === 0 ? (
                  <div className="space-y-4">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className="h-20 bg-white/5 rounded-2xl animate-pulse" />
                    ))}
                  </div>
                ) : (
                  participants.map((p) => {
                    const isSelected = selectedParticipants.includes(p.id);
                    return (
                      <div
                        key={p.id}
                        onClick={() => toggleParticipant(p.id)}
                        className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between group ${
                          isSelected
                            ? "bg-[var(--primary)]/5 border-[var(--primary)]/30 text-white"
                            : "bg-white/[0.015] border-white/5 hover:border-white/20 text-gray-500 hover:text-gray-300"
                        }`}
                      >
                        <div className="flex items-center gap-4">
                          <span className="text-2xl">{p.emoji}</span>
                          <div>
                            <div className="text-[11px] font-black uppercase tracking-wider">{p.name}</div>
                            <div className="text-[9px] text-gray-600 font-mono mt-0.5 truncate max-w-[200px]">
                              {p.role}
                            </div>
                          </div>
                        </div>

                        <div
                          className={`w-6 h-6 rounded-lg border flex items-center justify-center transition-all ${
                            isSelected
                              ? "bg-[var(--primary)] border-[var(--primary)] text-[#060a12]"
                              : "border-white/10 group-hover:border-white/30"
                          }`}
                        >
                          {isSelected && <CheckSquare size={14} strokeWidth={3} />}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
