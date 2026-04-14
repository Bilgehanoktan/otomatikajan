"use client";

import React from "react";
import Sidebar from "./Sidebar";
import { SystemHeader } from "./SystemHeader";

export default function LayoutWrapper({ children }: { children: React.ReactNode }) {
    const [mounted, setMounted] = React.useState(false);
    
    React.useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return (
            <div className="h-full flex bg-[#0b0c10] text-[#c5c6c7] overflow-hidden">
                {/* SSR Skeleton Shell */}
                <aside className="w-64 h-full glass border-r border-white/5 flex flex-col" />
                <div className="flex-1 flex flex-col h-full overflow-hidden relative">
                    <header className="h-16 border-b border-white/5 px-8 flex items-center justify-between glass" />
                    <main className="flex-1 overflow-y-auto overflow-x-hidden relative">
                        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#66fcf1]/5 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2" />
                        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-[#45a29e]/5 blur-[120px] rounded-full translate-y-1/2 -translate-x-1/2" />
                        <div className="relative z-10">
                            {children}
                        </div>
                    </main>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex bg-[#0b0c10] text-[#c5c6c7] overflow-hidden">
            <Sidebar />
            <div className="flex-1 flex flex-col h-full overflow-hidden relative">
                <SystemHeader />
                <main className="flex-1 overflow-y-auto overflow-x-hidden relative">
                    <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#66fcf1]/5 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2" />
                    <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-[#45a29e]/5 blur-[120px] rounded-full translate-y-1/2 -translate-x-1/2" />
                    <div className="relative z-10">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
