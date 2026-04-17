"use client";

import React from "react";
import { useApiUrl, useCustom } from "@refinedev/core";
import { 
    Activity, 
    ShieldCheck, 
    Cpu, 
    Bell,
    Settings,
    Search
} from "lucide-react";

const SystemHeaderContent = () => {
    const apiUrl = useApiUrl();
    const { query: { data } } = useCustom({
        url: `${apiUrl}/workflows/stats/summary`,
        method: "get",
        queryOptions: {
            staleTime: 30000,
            refetchOnWindowFocus: false,
        }
    });

    const stats = data?.data as any;
    const running = stats?.running || 0;
    const pending = stats?.pending || 0;
    const failed = stats?.failed || 0;
    const successRate = stats?.success_rate_pct || 100;
    const isCrisisMode = (stats?.health || 100) < 70;

    return (
        <header className="h-16 border-b border-white/5 px-8 flex items-center justify-between glass sticky top-0 z-50">
            <div className="flex items-center gap-6">
                {!isCrisisMode && (
                    <div className="relative group animate-in fade-in duration-500">
                        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-[#66fcf1] transition-colors" />
                        <input 
                            type="text" 
                            placeholder="Search neural traces..." 
                            className="bg-white/5 border border-white/5 rounded-full pl-10 pr-4 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#66fcf1]/30 focus:bg-white/[0.08] transition-all w-64"
                        />
                    </div>
                )}
                {isCrisisMode && (
                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 animate-pulse">
                        <span className="w-2 h-2 bg-red-500 rounded-full" />
                        <span className="text-[10px] font-black text-red-500 uppercase tracking-tighter">Operational Crisis Mode Active</span>
                    </div>
                )}
            </div>

            <div className="flex items-center gap-6">
                {/* System Metrics */}
                <div className="hidden md:flex items-center gap-8 border-r border-white/10 pr-6">
                    <div className="flex items-center gap-2">
                        <Activity size={14} className={isCrisisMode ? "text-red-500" : "text-[#66fcf1]"} />
                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-400 uppercase tracking-tighter font-semibold">Aktif İşler</span>
                            <div className="text-xs font-bold text-white">{running}</div>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                        <ShieldCheck size={14} className="text-green-400" />
                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-400 uppercase tracking-tighter font-semibold">Başarı Oranı</span>
                            <div className="text-xs font-bold text-white">%{successRate}</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <Cpu size={14} className={isCrisisMode ? "text-red-500" : "text-[#45a29e]"} />
                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-400 uppercase tracking-tighter font-semibold">Hatalar</span>
                            <div className="text-xs font-bold text-red-400">{failed}</div>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3">
                    <button className="p-2 text-gray-500 hover:text-white hover:bg-white/5 rounded-lg transition-colors relative">
                        <Bell size={18} />
                        <span className="absolute top-2 right-2 w-2 h-2 bg-red-400 rounded-full border-2 border-[#0b0c10]" />
                    </button>
                    <button className="p-2 text-gray-500 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                        <Settings size={18} />
                    </button>
                </div>
            </div>
        </header>
    );
};

export const SystemHeader = () => {
    return <SystemHeaderContent />;
};

export default SystemHeader;
