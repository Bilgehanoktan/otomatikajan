"use client";

import React, { useState, useEffect } from "react";
import { 
  Fingerprint, 
  Key, 
  ShieldAlert, 
  RefreshCw, 
  Trash2, 
  Plus, 
  Copy, 
  Check,
  AlertTriangle,
  Cpu,
  Lock
} from "lucide-react";
import { useCustomMutation, useGetIdentity, useList } from "@refinedev/core";
import { useTranslations } from "next-intl";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";

export default function IdentityManagerPage() {
  const [isClient, setIsClient] = useState(false);
  const [newKey, setNewKey] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const { data: identity } = useGetIdentity<any>();

  useEffect(() => setIsClient(true), []);

  const t = useTranslations("identity");
  const identityRoles = React.useMemo(() => {
    const roles = Array.isArray(identity?.roles) ? identity.roles : identity?.role ? [identity.role] : [];
    return roles.map((role: unknown) => String(role).toUpperCase());
  }, [identity]);
  const canManageIdentities = identityRoles.some((role: string) => role === "SOVEREIGN_PRIME" || role === "ADMIN");

  const { query: { data: identities, isLoading } } = useList({
    resource: "auth/identities",
    queryOptions: { enabled: isClient && Boolean(identity) && canManageIdentities }
  });

  const { mutate } = useCustomMutation();

  const generateKey = (id: string) => {
    mutate({
      url: `/api/v1/auth/identity/keys/generate?target_id=${id}`,
      method: "post",
      values: {},
      successNotification: (data: any) => {
        setNewKey(data.data);
        return {
          message: "API Key Üretildi",
          description: "Yeni sistem anahtarı başarıyla oluşturuldu.",
          type: "success",
        };
      },
    });
  };

  const copyToClipboard = () => {
    if (newKey?.api_key) {
      navigator.clipboard.writeText(newKey.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isClient) return null;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300">
      <ResourceHeader 
        title={t("title")} 
        subtitle={t("subtitle")} 
        icon={<Fingerprint size={32} />}
        badge="SIF-02 Standard"
      />

      <div className="grid grid-cols-1 gap-8 mt-10">
        <section className="glass-panel p-10 rounded-[3rem] border-white/10 bg-[#0b0f19]/60 backdrop-blur-md">
          <div className="flex items-center justify-between mb-10">
             <div className="flex items-center gap-4">
                <Cpu size={20} className="text-[var(--primary)]" />
                <h2 className="text-xs font-black text-white uppercase tracking-[0.3em]">{t("authorizedIdentities")}</h2>
             </div>
             <button
               disabled={!canManageIdentities}
               className="flex items-center gap-2 px-6 py-2 bg-white/5 border border-white/10 rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-white/10 transition-all text-gray-400 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
             >
                <Plus size={14} /> {t("newIdentity")}
             </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {!identity ? (
              <div className="p-8 rounded-[2rem] border border-white/5 bg-black/40 text-[10px] font-black uppercase tracking-widest text-gray-500">
                Loading identity context
              </div>
            ) : !canManageIdentities ? (
              <div className="p-8 rounded-[2rem] border border-amber-500/20 bg-amber-500/5 text-amber-400">
                <div className="flex items-center gap-3 text-[10px] font-black uppercase tracking-widest">
                  <AlertTriangle size={16} /> ADMIN OR SOVEREIGN_PRIME REQUIRED
                </div>
              </div>
            ) : isLoading ? (
              <div className="p-8 rounded-[2rem] border border-white/5 bg-black/40 text-[10px] font-black uppercase tracking-widest text-gray-500">
                Loading identities
              </div>
            ) : identities?.data?.map((id: any) => (
              <div key={id.id} className="p-8 rounded-[2rem] border border-white/5 bg-black/40 group hover:border-[var(--primary)]/30 transition-all relative overflow-hidden">
                <div className="flex justify-between items-start mb-6">
                  <div className="p-3 bg-white/5 rounded-xl text-gray-500 group-hover:text-[var(--primary)] transition-colors">
                    <Fingerprint size={24} />
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    {id.quarantined_at ? (
                      <div className="px-3 py-1 rounded bg-red-500/20 text-red-500 text-[8px] font-black uppercase border border-red-500/40 animate-pulse">QUARANTINED</div>
                    ) : (
                      <div className={`px-3 py-1 rounded text-[8px] font-black uppercase border
                        ${id.risk_level === 'LOW' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 
                          id.risk_level === 'MEDIUM' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' :
                          'bg-orange-500/10 text-orange-500 border-orange-500/20 animate-bounce'}
                      `}>
                        {id.risk_level || 'LOW'} RISK
                      </div>
                    )}
                    <span className="text-[8px] text-gray-600 font-mono italic">
                      {id.last_used_at ? `Last: ${new Date(id.last_used_at).toLocaleTimeString()}` : "Never Used"}
                    </span>
                  </div>
                </div>

                <h3 className="text-sm font-black text-white uppercase tracking-tight mb-2">{id.name}</h3>
                
                {/* SIF-04: Trust Score Bar */}
                <div className="mb-6 space-y-2">
                   <div className="flex justify-between text-[8px] font-black uppercase tracking-widest text-gray-600">
                      <span>Identity Trust Score</span>
                      <span className={id.trust_score < 50 ? "text-red-500" : "text-[var(--primary)]"}>{id.trust_score}%</span>
                   </div>
                   <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-1000 ${id.trust_score < 50 ? 'bg-red-500' : 'bg-[var(--primary)]'}`}
                        style={{ width: `${id.trust_score}%` }}
                      />
                   </div>
                </div>

                <p className="text-[10px] text-gray-600 font-mono mb-6">{id.id}</p>

                <div className="pt-6 border-t border-white/5 flex gap-4">
                  <button 
                    onClick={() => generateKey(id.id)}
                    className="flex-1 flex items-center justify-center gap-2 py-3 bg-[var(--primary)]/10 text-[var(--primary)] border border-[var(--primary)]/20 rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-[var(--primary)] hover:text-[#060a12] transition-all"
                  >
                    <RefreshCw size={14} /> {t("rotate")}
                  </button>
                  <button 
                    onClick={() => {
                      if(id.quarantined_at) {
                         if(confirm("SIF-04: Bu ajanın güvenini tazelemek ve karantinadan çıkarmak istiyor musunuz?")) {
                            mutate({
                               url: `/api/v1/auth/identity/${id.id}/recover`,
                               method: "post",
                               values: {},
                               successNotification: () => ({ message: "Trust Restored", type: "success" })
                            });
                         }
                      } else {
                         if(confirm("SIF-04: Bu ajanı karantinaya almak istediğinize emin misiniz? Tüm erişimi anında kesilecektir.")) {
                            mutate({
                               url: `/api/v1/auth/identity/${id.id}/quarantine`,
                               method: "post",
                               values: {},
                               successNotification: () => ({ message: "Agent Quarantined", type: "error" })
                            });
                         }
                      }
                    }}
                    className={`p-3 rounded-xl transition-all border z-20
                      ${id.quarantined_at ? 'bg-orange-500/20 text-orange-500 border-orange-500/30 hover:bg-orange-500 hover:text-white' : 'bg-red-500/10 text-red-500 border-red-500/20 hover:bg-red-500 hover:text-white'}
                    `}
                    title={id.quarantined_at ? "Recover Trust" : "Quarantine Agent"}
                  >
                    {id.quarantined_at ? <RefreshCw size={14} /> : <ShieldAlert size={14} />}
                  </button>
                </div>
                
                {id.quarantined_at && (
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-[2px] flex items-center justify-center z-10 rounded-[2rem]">
                     <div className="flex flex-col items-center gap-2">
                        <Lock size={32} className="text-red-500 opacity-60" />
                        <span className="text-[8px] font-black text-red-500 uppercase tracking-widest">{t("isolated")}</span>
                     </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* KEY DISCOVERY MODAL */}
      {newKey && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-8 animate-in fade-in zoom-in">
          <div className="absolute inset-0 bg-[#060a12]/95 backdrop-blur-3xl" />
          <div className="glass-panel w-full max-w-xl p-12 rounded-[3.5rem] border-[var(--primary)]/30 bg-black relative z-10 text-center">
            <div className="w-20 h-20 bg-orange-500/10 rounded-full flex items-center justify-center mx-auto mb-8 border border-orange-500/20">
               <ShieldAlert size={32} className="text-orange-500" />
            </div>
            
            <h3 className="text-2xl font-black text-white uppercase tracking-tighter mb-4">{t("secretUnsealed")}</h3>
            <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-10 leading-relaxed">
              Bu anahtar veritabanında mühürlü (hashed) olarak saklanır. <br/>
              <span className="text-orange-500">{t("sealedWarning")}</span>
            </p>

            <div className="relative group">
              <div className="bg-white/5 border border-white/10 rounded-2xl py-6 px-10 text-sm font-mono font-black text-[var(--primary)] break-all mb-10">
                {newKey.api_key}
              </div>
              <button 
                onClick={copyToClipboard}
                className="absolute -right-3 -top-3 p-4 bg-[var(--primary)] text-[#060a12] rounded-2xl shadow-2xl active:scale-90 transition-all"
              >
                {copied ? <Check size={20} /> : <Copy size={20} />}
              </button>
            </div>

            <button 
              onClick={() => setNewKey(null)}
              className="w-full py-5 border border-white/10 rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] hover:bg-white/5 transition-all"
            >
              SECRET SEALED (KAPAT)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


