"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldCheck, 
  Book, 
  History, 
  FileArchive, 
  Lock, 
  CheckCircle2, 
  Plus, 
  Download, 
  Search,
  Filter,
  Eye,
  Hash,
  Activity
} from "lucide-react";
import { useCustomMutation, useList } from "@refinedev/core";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";
import { Skeleton } from "@/components/dashboard/Skeleton";

export default function CompliancePage() {
  const [isClient, setIsClient] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  useEffect(() => setIsClient(true), []);

  const { data: policyData, isLoading: isPolicyLoading } = useList({
    resource: "compliance/policies",
  });

  const { data: bundleData, isLoading: isBundleLoading } = useList({
    resource: "compliance/audit-bundles",
  });

  const { mutate } = useCustomMutation();

  const handleCreateBundle = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    mutate({
      url: `/api/v1/compliance/audit-bundles`,
      method: "post",
      values: {
        name: formData.get("name"),
        purpose: formData.get("purpose"),
        creator: "operator_ui"
      },
      successNotification: {
        message: "Paket Oluşturuluyor",
        description: "Denetim paketi arka planda hazırlanıyor.",
        type: "success",
      },
    });
    setIsModalOpen(false);
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title="Compliance" 
        subtitle="Regulated Data Retention & Cryptographic Proof Sealing" 
        icon={<ShieldCheck size={32} />}
        badge="Regulatory Grade"
        actions={
          <div className="flex gap-4">
             <div className="glass-card !p-3 flex flex-col items-end border-green-500/20">
                <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest">Integrity Hash</span>
                <span className="text-sm font-black text-green-400">99.99% NOMINAL</span>
             </div>
             <button 
               onClick={() => setIsModalOpen(true)}
               className="flex items-center gap-2 px-8 py-3 bg-[var(--primary)] text-[#060a12] text-[10px] font-black uppercase tracking-widest rounded-2xl hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95 group"
             >
               <Plus size={14} className="group-hover:rotate-90 transition-transform" />
               <span>Yeni Denetim Paketi</span>
             </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* LEFT COLUMN - POLICIES & STATUS */}
        <div className="xl:col-span-4 space-y-8">
           {/* Active Policies */}
           <section className="glass-panel p-8 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.01] to-transparent">
              <div className="flex items-center gap-3 mb-8">
                 <Book size={18} className="text-[var(--primary)]" />
                 <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Active Retention Policies</h3>
              </div>
              
              <div className="space-y-4">
                {isPolicyLoading ? <Skeleton className="h-64 rounded-2xl" /> : (
                   policyData?.data.map((policy: any) => (
                     <div key={policy.id} className="p-5 rounded-2xl bg-white/[0.015] border border-white/5 hover:border-[var(--primary)]/20 transition-all group">
                        <div className="flex justify-between items-start mb-4">
                           <span className="text-[11px] font-black text-white uppercase tracking-tight group-hover:text-[var(--primary)] transition-colors">{policy.data_category}</span>
                           {policy.is_permanent && (
                             <span className="text-[8px] font-black bg-amber-500/10 text-amber-500 border border-amber-500/20 px-2 py-0.5 rounded uppercase tracking-widest">PERMANENT</span>
                           )}
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                           <div className="flex flex-col">
                              <span className="text-[8px] text-gray-600 font-black uppercase tracking-widest">Hot Storage</span>
                              <span className="text-[10px] font-bold text-gray-400 mt-1">{policy.hot_retention_days} Days</span>
                           </div>
                           <div className="flex flex-col items-end">
                              <span className="text-[8px] text-gray-600 font-black uppercase tracking-widest">Cold Retention</span>
                              <span className="text-[10px] font-bold text-gray-400 mt-1">{policy.warm_retention_days} Days</span>
                           </div>
                        </div>
                     </div>
                   ))
                )}
              </div>
           </section>

           {/* Proof Status Card */}
           <section className="glass-panel p-10 rounded-[2.5rem] border-[var(--primary)]/10 bg-[#060a12]/50 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
                 <CheckCircle2 size={140} />
              </div>
              <div className="flex items-center gap-3 mb-6 relative z-10">
                 <Activity size={18} className="text-green-400" />
                 <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Parity Monitor</h3>
              </div>
              <p className="text-[3rem] font-black text-white tracking-tighter leading-none mb-2">99.99<span className="text-xl text-green-500">%</span></p>
              <p className="text-[10px] font-black text-gray-600 uppercase tracking-widest mb-8">Decision Integrity Baseline</p>
              
              <div className="p-5 rounded-2xl bg-black/40 border border-white/5 relative z-10 group/pulse">
                 <div className="flex items-center gap-3 mb-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 group-hover/pulse:animate-ping" />
                    <span className="text-[9px] font-black text-green-400 uppercase tracking-[0.2em]">Mühürleme Aktif</span>
                 </div>
                 <p className="text-[10px] text-gray-500 leading-relaxed font-bold tracking-tight">
                    Tüm otonom kararlar ve denetim kayıtları her 5 dakikada bir mühürlenerek denetlenemez kılınır.
                 </p>
              </div>
           </section>
        </div>

        {/* RIGHT COLUMN - AUDIT BUNDLES TABLE */}
        <div className="xl:col-span-8">
           <section className="glass-panel p-8 rounded-[2.5rem] border-white/[0.03] bg-gradient-to-br from-white/[0.01] to-transparent overflow-hidden">
              <div className="flex items-center justify-between mb-8 px-4">
                 <div className="flex items-center gap-3">
                    <FileArchive size={18} className="text-[var(--primary)]" />
                    <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Sealed Evidence Packs</h3>
                 </div>
                 <div className="flex items-center gap-4">
                    <div className="relative">
                       <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                       <input 
                         type="text" 
                         placeholder="PAKET ARA..."
                         className="bg-black/40 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-[10px] font-black text-white placeholder:text-gray-700 focus:outline-none focus:border-[var(--primary)]/20 transition-all w-48"
                       />
                    </div>
                    <button className="p-2.5 bg-white/5 border border-white/5 rounded-xl text-gray-500 hover:text-white transition-all">
                       <Filter size={16} />
                    </button>
                 </div>
              </div>

              <div className="overflow-x-auto">
                 <table className="w-full text-left">
                    <thead>
                       <tr className="border-b border-white/[0.03] bg-black/10">
                          <th className="py-5 px-8 text-[9px] font-black text-gray-500 uppercase tracking-widest">Audit Evidence Pack</th>
                          <th className="py-5 px-6 text-[9px] font-black text-gray-500 uppercase tracking-widest">Purpose</th>
                          <th className="py-5 px-6 text-[9px] font-black text-gray-500 uppercase tracking-widest">Integrity Seal</th>
                          <th className="py-5 px-6 text-[9px] font-black text-gray-500 uppercase tracking-widest text-right">Actions</th>
                       </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.02]">
                       {isBundleLoading ? (
                          [1,2,3].map(i => (
                             <tr key={i}><td colSpan={4} className="py-8 px-8"><Skeleton className="h-12 w-full rounded-xl" /></td></tr>
                          ))
                       ) : bundleData?.data.map((bundle: any) => (
                          <tr key={bundle.id} className="group/row hover:bg-white/[0.015] transition-colors">
                             <td className="py-6 px-8">
                                <div className="flex items-center gap-4">
                                   <div className="p-3 bg-white/[0.02] border border-white/5 rounded-xl group-hover/row:border-[var(--primary)]/20 transition-all">
                                      <FileArchive size={18} className="text-gray-500 group-hover/row:text-[var(--primary)]" />
                                   </div>
                                   <div>
                                      <p className="text-[11px] font-black text-white uppercase tracking-tight group-hover/row:text-[var(--primary)] transition-colors">{bundle.bundle_name}</p>
                                      <p className="text-[9px] text-gray-600 font-mono mt-1 tracking-widest">{new Date(bundle.created_at).toLocaleDateString()}</p>
                                   </div>
                                </div>
                             </td>
                             <td className="py-6 px-6">
                                <span className="text-[10px] font-black text-gray-500 uppercase tracking-tight">{bundle.purpose}</span>
                             </td>
                             <td className="py-6 px-6">
                                <div className="flex items-center gap-3 group/hash">
                                   <Hash size={12} className="text-gray-700 group-hover/hash:text-green-500" />
                                   <span className="text-[10px] font-mono text-gray-600 group-hover/hash:text-white transition-colors">{bundle.integrity_hash?.substring(0, 16).toUpperCase()}...</span>
                                </div>
                             </td>
                             <td className="py-6 px-6 text-right">
                                <div className="flex justify-end gap-3 opacity-0 group-hover/row:opacity-100 transition-all group-hover/row:translate-x-[-10px]">
                                   <button className="p-2.5 bg-white/5 border border-white/5 rounded-xl text-gray-400 hover:text-[var(--primary)] transition-all">
                                      <Download size={14} />
                                   </button>
                                   <button className="p-2.5 bg-white/5 border border-white/5 rounded-xl text-gray-400 hover:text-white transition-all">
                                      <Eye size={14} />
                                   </button>
                                </div>
                             </td>
                          </tr>
                       ))}
                    </tbody>
                 </table>
              </div>
           </section>
        </div>
      </div>

      {/* CUSTOM MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-8 animate-in fade-in zoom-in duration-300">
           <div 
             className="absolute inset-0 bg-[#060a12]/80 backdrop-blur-md"
             onClick={() => setIsModalOpen(false)}
           />
           <div className="glass-panel w-full max-w-md p-10 rounded-[3rem] border-[var(--primary)]/20 bg-gradient-to-br from-[#0b0c10] to-[#060a12] relative z-10 shadow-[0_32px_128px_rgba(0,0,0,0.8)]">
              <div className="flex items-center gap-4 mb-8">
                 <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20">
                    <Lock size={20} className="text-[var(--primary)]" />
                 </div>
                 <h3 className="text-xl font-black text-white uppercase tracking-tighter">Mühürlü Kanıt Paketi</h3>
              </div>
              
              <form onSubmit={handleCreateBundle} className="space-y-6">
                 <div className="space-y-2">
                    <label className="text-[9px] font-black text-gray-600 uppercase tracking-widest ml-1">Paket Kimliği / Adı</label>
                    <input 
                      name="name"
                      required
                      placeholder="Örn: 2024 Q1 GÜVENLİK ÖZETİ"
                      className="w-full bg-black/40 border border-white/10 rounded-2xl py-4 px-6 text-[11px] font-black text-white focus:outline-none focus:border-[var(--primary)]/50 transition-all"
                    />
                 </div>
                 <div className="space-y-2">
                    <label className="text-[9px] font-black text-gray-600 uppercase tracking-widest ml-1">Kullanım Amacı</label>
                    <textarea 
                      name="purpose"
                      required
                      rows={3}
                      placeholder="Denetim, uyum veya stratejik inceleme..."
                      className="w-full bg-black/40 border border-white/10 rounded-2xl py-4 px-6 text-[11px] font-black text-white focus:outline-none focus:border-[var(--primary)]/50 transition-all resize-none"
                    />
                 </div>
                 
                 <div className="pt-4 flex gap-4">
                    <button 
                      type="button"
                      onClick={() => setIsModalOpen(false)}
                      className="flex-1 py-4 text-[10px] font-black uppercase text-gray-500 hover:text-white transition-all"
                    >
                       İptal
                    </button>
                    <button 
                      type="submit"
                      className="flex-grow py-4 bg-[var(--primary)] text-[#060a12] rounded-2xl text-[10px] font-black uppercase tracking-widest hover:shadow-[0_8px_32px_rgba(102,252,241,0.3)] transition-all active:scale-95"
                    >
                       Paketi Mühürle
                    </button>
                 </div>
              </form>
           </div>
        </div>
      )}
    </div>
  );
}
