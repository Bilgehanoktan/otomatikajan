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
    });

    const stats = data?.data as any;

    return (
        <header className="h-16 border-b border-white/5 px-8 flex items-center justify-between glass sticky top-0 z-50">
            <div className="flex items-center gap-6">
                <div className="relative group">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-[#66fcf1] transition-colors" />
                    <input 
                        type="text" 
                        placeholder="Search neural traces..." 
                        className="bg-white/5 border border-white/5 rounded-full pl-10 pr-4 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#66fcf1]/30 focus:bg-white/[0.08] transition-all w-64"
                    />
                </div>
            </div>

            <div className="flex items-center gap-6">
                {/* System Metrics */}
                <div className="hidden md:flex items-center gap-4 border-r border-white/10 pr-6">
                    <div className="flex items-center gap-2">
                        <Activity size={14} className="text-[#66fcf1]" />
                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-500 leading-none">ACTIVE JOBS</span>
                            <span className="text-xs font-bold text-white">{stats?.running || 0}</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <ShieldCheck size={14} className="text-green-400" />
                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-500 leading-none">UPTIME</span>
                            <span className="text-xs font-bold text-white">99.9%</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Cpu size={14} className="text-[#45a29e]" />
                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-500 leading-none">LOAD</span>
                            <span className="text-xs font-bold text-white">12%</span>
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
    const [mounted, setMounted] = React.useState(false);
    
    React.useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return <header className="h-16 border-b border-white/5 px-8 flex items-center justify-between glass sticky top-0 z-50" />;
    }

    return <SystemHeaderContent />;
};

export default SystemHeader;
