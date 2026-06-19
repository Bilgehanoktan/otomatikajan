"use client";

import React from "react";
import { useApiUrl, useCustom } from "@refinedev/core";
import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";
import { SystemHeader } from "./SystemHeader";
import { CommandPalette } from "./dashboard/CommandPalette";
import { RuntimeDiagnosticsHUD } from "./dashboard/RuntimeDiagnosticsHUD";
import { useTranslations } from "next-intl";

export default function LayoutWrapper({ children }: { children: React.ReactNode }) {
    const t = useTranslations("dashboard");
    const tErrors = useTranslations("errors");
    const pathname = usePathname();
    const isLoginPage = pathname?.startsWith("/login");
    
    const [mounted, setMounted] = React.useState(false);
    const apiUrl = useApiUrl();
    
    // R-06 Crisis Detection
    const { query: { data } } = useCustom({
        url: `${apiUrl}/workflows/stats/summary`,
        method: "get",
        queryOptions: {
            staleTime: 30000, // 30 seconds
            refetchOnWindowFocus: false,
        }
    });

    const isCrisis = ((data?.data as any)?.success_rate_pct || 100) < 10;
    
    React.useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return (
            <div className="h-screen overflow-hidden flex bg-[#0b0c10] text-[#c5c6c7]">
                {isLoginPage ? children : (
                    <>
                        {/* SSR Skeleton Shell */}
                        <aside className="w-64 h-full shrink-0 glass border-r border-white/5 flex flex-col" />
                        <div className="flex-1 min-w-0 flex flex-col relative h-screen overflow-hidden">
                            <header className="h-16 border-b border-white/5 px-8 flex items-center justify-between glass" />
                            <main className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden relative">
                                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#66fcf1]/5 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2" />
                                <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-[#45a29e]/5 blur-[120px] rounded-full translate-y-1/2 -translate-x-1/2" />
                                <div className="relative z-10">
                                    {children}
                                </div>
                            </main>
                        </div>
                    </>
                )}
            </div>
        );
    }

    if (isLoginPage) {
        return <>{children}</>;
    }

    return (
        <div className={`h-screen overflow-hidden flex bg-[#0b0c10] text-[#c5c6c7] transition-all duration-700 ${isCrisis ? 'ring-inset ring-[12px] ring-red-900/40 shadow-[inset_0_0_100px_rgba(153,27,27,0.4)]' : ''}`}>
            <Sidebar />
            <div className="flex-1 min-w-0 flex flex-col relative h-screen overflow-hidden">
                <SystemHeader />
                <main className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden relative">
                    {/* CRISIS OVERLAY HUD */}
                    {isCrisis && (
                        <div className="sticky top-0 z-[100] w-full bg-red-600/90 text-white py-1 px-4 flex items-center justify-between backdrop-blur-md animate-in slide-in-from-top duration-500 shadow-lg">
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] flex items-center gap-2">
                                <span className="w-2 h-2 bg-white rounded-full animate-ping" />
                                {t("criticalRisk", { defaultMessage: "Kritik Operasyonel Risk" })}: Focus Required
                            </span>
                            <span className="text-[10px] font-mono opacity-60" title="ERR_CRITICAL_HEALTH_BELOW_THRESHOLD">
                                {tErrors("ERR_CRITICAL_HEALTH_BELOW_THRESHOLD", { defaultMessage: "Sistem sağlığı kritik seviyede." })}
                            </span>
                        </div>
                    )}

                    <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#66fcf1]/5 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none" />
                    <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-[#45a29e]/5 blur-[120px] rounded-full translate-y-1/2 -translate-x-1/2 pointer-events-none" />
                    
                    <div className={`relative z-10 transition-all duration-500 ${isCrisis ? 'filter grayscale-[0.2] brightness-90' : ''}`}>
                        {children}
                    </div>
                </main>
            </div>

            {/* Global Services */}
            <CommandPalette />
            <RuntimeDiagnosticsHUD />
        </div>
    );
}
