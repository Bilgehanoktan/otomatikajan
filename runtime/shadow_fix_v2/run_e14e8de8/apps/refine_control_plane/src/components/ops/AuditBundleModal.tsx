"use client";

import React from "react";
import { 
    X, 
    ShieldCheck, 
    FileText, 
    Download, 
    Lock, 
    CheckCircle2,
    Search,
    Fingerprint
} from "lucide-react";

interface AuditBundleModalProps {
    isOpen: boolean;
    onClose: () => void;
    rollout: any;
}

export const AuditBundleModal: React.FC<AuditBundleModalProps> = ({ isOpen, onClose, rollout }) => {
    if (!isOpen) return null;

    const bundleContents = [
        { name: "sovereignty_proof.pkg", type: "Security", size: "1.2 MB", icon: <Fingerprint size={16} /> },
        { name: "signed_metadata.json", type: "Metadata", size: "14 KB", icon: <FileText size={16} /> },
        { name: "vulnerability_scan_report.pdf", type: "Security", size: "4.5 MB", icon: <Search size={16} /> },
        { name: "consensus_log.db", type: "Consensus", size: "890 KB", icon: <CheckCircle2 size={16} /> }
    ];

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-black/80 backdrop-blur-md transition-opacity"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div className="relative w-full max-w-2xl glass-panel rounded-[3rem] border-white/10 bg-[#060a12]/90 shadow-[0_0_50px_rgba(102,252,241,0.1)] overflow-hidden animate-in zoom-in-95 duration-300">
                {/* Header */}
                <div className="p-10 border-b border-white/5 flex items-start justify-between bg-gradient-to-br from-white/[0.03] to-transparent">
                    <div className="flex items-center gap-6">
                        <div className="p-5 bg-[#66fcf1]/10 rounded-2xl border border-[#66fcf1]/20 shadow-[0_0_20px_rgba(102,252,241,0.2)]">
                            <ShieldCheck className="text-[#66fcf1]" size={32} />
                        </div>
                        <div>
                            <h3 className="text-2xl font-black text-white uppercase tracking-tighter italic">Audit Bundle Detail</h3>
                            <p className="text-[10px] text-[#45a29e] font-black tracking-[0.3em] uppercase mt-1">Verification Package: {rollout.id}</p>
                        </div>
                    </div>
                    <button 
                        onClick={onClose}
                        className="p-3 hover:bg-white/5 rounded-full text-gray-500 hover:text-white transition-all border border-transparent hover:border-white/10"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-10 space-y-8">
                    {/* Bundle ID Card */}
                    <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div className="flex items-center gap-4">
                            <Lock size={18} className="text-[#45a29e]" />
                            <div className="text-xs font-mono text-gray-400 truncate max-w-[300px]">
                                {rollout.auditBundle}
                            </div>
                        </div>
                        <button className="flex items-center gap-2 px-6 py-3 bg-[#66fcf1] text-[#060a12] rounded-xl text-[10px] font-black uppercase tracking-widest hover:shadow-[0_0_20px_rgba(102,252,241,0.4)] transition-all active:scale-95 group">
                            <Download size={14} className="group-hover:translate-y-0.5 transition-transform" />
                            Download Full Bundle
                        </button>
                    </div>

                    {/* Content List */}
                    <div>
                        <h4 className="text-[10px] text-[#45a29e] font-black tracking-[0.3em] uppercase mb-4 px-2">Artifact Integrity Check</h4>
                        <div className="space-y-3">
                            {bundleContents.map((file, idx) => (
                                <div key={idx} className="flex items-center justify-between p-4 rounded-2xl bg-white/[0.01] border border-white/5 hover:bg-white/[0.03] transition-all group/row">
                                    <div className="flex items-center gap-4">
                                        <div className="p-2 bg-white/5 rounded-lg text-gray-500 group-hover/row:text-[#66fcf1] transition-colors">
                                            {file.icon}
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-white tracking-tight">{file.name}</p>
                                            <p className="text-[9px] text-gray-600 font-black uppercase tracking-widest">{file.type} • {file.size}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="flex gap-0.5">
                                            {[...Array(8)].map((_, i) => (
                                                <div key={i} className="w-1 h-3 bg-green-500/30 rounded-full" />
                                            ))}
                                        </div>
                                        <span className="text-[8px] font-black text-green-500 uppercase tracking-widest">Signed</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-10 py-8 bg-black/40 border-t border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        <span className="text-[9px] font-black text-white uppercase tracking-widest">Hash Verified: SHA256 VALID</span>
                    </div>
                    <p className="text-[9px] text-gray-600 font-bold uppercase italic">Sovereign Proof Engine v4.2.0</p>
                </div>
            </div>
        </div>
    );
};
