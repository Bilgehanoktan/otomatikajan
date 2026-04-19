"use client";

import React from "react";
import { useMenu, useLogout, useGetIdentity } from "@refinedev/core";
import Link from "next/link";
import { 
    LayoutDashboard, 
    Workflow, 
    Zap, 
    ShieldCheck, 
    LogOut,
    Eye,
    CheckSquare,
    AlertTriangle,
    BarChart3,
    FileText,
    Boxes,
    Globe,
    ShieldAlert,
    Network,
    Cpu,
    History,
    Activity,
    Settings,
    Dna,
    Settings2,
    Scale,
    Signature,
    Rocket,
    FileArchive,
    Target
} from "lucide-react";

const icons: Record<string, React.ReactNode> = {
    workflows: <Workflow size={20} />,
    dashboard: <LayoutDashboard size={20} />,
    agents: <Zap size={20} />,
    improvements: <ShieldCheck size={20} />,
    security: <ShieldCheck size={20} />,
    observability: <Eye size={20} />,
    approvals: <CheckSquare size={20} />,
    incidents: <AlertTriangle size={20} />,
    costs: <BarChart3 size={20} />,
    audit: <FileText size={20} />,
    federation: <Network size={20} />,
    fleet: <Boxes size={20} />,
    mesh: <Globe size={20} />,
    safety: <ShieldAlert size={20} />,
    "repair-lab": <Cpu size={20} />,
    "repair-memory": <History size={20} />,
    verifiers: <Activity size={20} />,
    "self-tuning": <Settings size={20} />,
    "governance-lineage": <Settings2 size={20} />,
    training: <Dna size={20} />,
    compliance: <Scale size={20} />,
    "policy-proposals": <Signature size={20} />,
    "audit-bundles": <FileArchive size={20} />,
    "handover-status": <Rocket size={20} />,
    "launch-gates": <Target size={20} />,
};

const SidebarContent = () => {
    const { menuItems, selectedKey } = useMenu();
    const { mutate: logout } = useLogout();
    const { data: identity } = useGetIdentity<{ name: string }>();
    const [isCollapsed, setIsCollapsed] = React.useState(false);

    // Define Grouping
    const groups = [
        {
            title: "OPERASYONLAR",
            items: ["dashboard", "workflows", "agents", "incidents", "fleet"]
        },
        {
            title: "YÖNETİŞİM & GÜVENLİK",
            items: ["approvals", "audit", "compliance", "safety", "mesh", "federation", "governance-lineage", "policy-proposals"]
        },
        {
            title: "OTONOM GELİŞİM",
            items: ["improvements", "repair-lab", "repair-memory", "self-tuning", "verifiers", "training"]
        },
        {
            title: "RAPORLAMA",
            items: ["costs", "audit-bundles", "handover-status", "launch-gates"]
        }
    ];

    const renderMenuItem = (item: any) => (
        <Link
            key={item.key}
            href={item.route ?? "/"}
            title={isCollapsed ? item.label : ""}
            className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-400 group relative ${
                selectedKey === item.key
                    ? "bg-[var(--primary)]/8 text-[var(--primary)] border border-[var(--primary)]/15 shadow-[0_0_20px_rgba(102,252,241,0.06)]"
                    : "text-gray-400 hover:text-white hover:bg-white/5"
            } ${isCollapsed ? "justify-center px-0 w-12 mx-auto" : ""}`}
        >
            {/* Active Indicator Bar */}
            {selectedKey === item.key && (
                <div className={`absolute ${isCollapsed ? "-left-1" : "-left-4"} top-1/2 -translate-y-1/2 w-1.5 h-6 bg-[var(--primary)] rounded-r-full shadow-[0_0_12px_var(--primary)] animate-pulse`} />
            )}

            <span className={`transition-all duration-400 ${selectedKey === item.key ? "text-[var(--primary)] scale-110" : "text-gray-500 group-hover:text-gray-300"} ${isCollapsed ? "scale-125" : ""}`}>
                {icons[item.name] || <LayoutDashboard size={20} />}
            </span>
            {!isCollapsed && (
                <span className={`font-bold text-[11px] uppercase tracking-wider transition-all truncate ${selectedKey === item.key ? "tracking-[0.1em]" : "tracking-tight"}`}>
                    {item.label}
                </span>
            )}
            
            {/* Tooltip for Collapsed State */}
            {isCollapsed && (
                <div className="absolute left-16 bg-black border border-white/10 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 translate-x-1 group-hover:translate-x-0 transition-all pointer-events-none z-[100] whitespace-nowrap shadow-xl text-[var(--primary)]">
                    {item.label}
                </div>
            )}
        </Link>
    );

    return (
        <aside className={`${isCollapsed ? "w-20" : "w-64"} h-full glass border-r border-white/5 flex flex-col overflow-hidden transition-all duration-500 ease-in-out`}>
            <div className={`p-6 border-b border-white/5 bg-[#0b0c10]/40 relative group/header transition-all duration-500 ${isCollapsed ? "px-4" : ""}`}>
                <div className="flex items-center gap-3">
                    <div className="relative group">
                        <div className={`w-10 h-10 premium-gradient rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(102,252,241,0.25)] shrink-0 animate-breathe transition-all ${isCollapsed ? "w-12 h-12" : ""}`}>
                            <Cpu className="text-black" size={isCollapsed ? 28 : 24} />
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-[#0b0c10] shadow-[0_0_8px_#48bb78] z-10" />
                    </div>
                    {!isCollapsed && (
                        <div className="overflow-hidden animate-in fade-in slide-in-from-left-2 duration-500">
                            <h1 className="font-black text-lg tracking-tighter text-white leading-none">EGEMEN <span className="text-[var(--primary)]">YAZ</span></h1>
                            <p className="text-[8px] uppercase tracking-[0.3em] text-[#45a29e] font-black mt-1.5 opacity-80">SOVEREIGN CORE</p>
                        </div>
                    )}
                </div>

                {/* Collapse Toggle Button */}
                <button 
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className={`absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-black border border-white/10 flex items-center justify-center text-gray-500 hover:text-[var(--primary)] transition-all shadow-lg z-20 opacity-0 group-hover/header:opacity-100 ${isCollapsed ? "rotate-180" : ""}`}
                >
                    <LayoutDashboard size={12} />
                </button>
            </div>

            <nav className={`flex-1 px-4 py-6 space-y-9 overflow-y-auto overflow-x-hidden custom-scrollbar transition-all ${isCollapsed ? "px-2" : ""}`}>
                {groups.map((group) => {
                    const groupItems = menuItems.filter(item => group.items.includes(item.name));
                    if (groupItems.length === 0) return null;

                    return (
                        <div key={group.title} className="space-y-3">
                            {!isCollapsed && (
                                <div className="flex items-center gap-2 px-4 mb-1 animate-in fade-in duration-700">
                                    <div className="w-1 h-1 rounded-full bg-[var(--primary)]/30" />
                                    <h3 className="text-[9px] font-black text-gray-500 uppercase tracking-[0.25em]">
                                        {group.title}
                                    </h3>
                                </div>
                            )}
                            {isCollapsed && (
                                <div className="w-full flex justify-center mb-1">
                                    <div className="w-6 h-px bg-white/5" />
                                </div>
                            )}
                            <div className={`space-y-1 ${isCollapsed ? "flex flex-col items-center" : ""}`}>
                                {groupItems.map(renderMenuItem)}
                            </div>
                        </div>
                    );
                })}
                
                {/* Un-grouped items (Backup) */}
                {(() => {
                    const groupedNames = groups.flatMap(g => g.items);
                    const otherItems = menuItems.filter(item => !groupedNames.includes(item.name));
                    if (otherItems.length === 0) return null;
                    return (
                        <div className="space-y-2">
                            <h3 className="px-4 text-[9px] font-black text-gray-600 uppercase tracking-[0.2em]">DİĞER</h3>
                            <div className="space-y-1">{otherItems.map(renderMenuItem)}</div>
                        </div>
                    );
                })()}
            </nav>

            <div className={`p-4 border-t border-white/5 bg-[#0b0c10]/40 transition-all ${isCollapsed ? "p-2" : ""}`}>
                {!isCollapsed ? (
                    <div className="glass-card mb-4 p-3 flex items-center gap-3 !rounded-xl animate-in fade-in duration-500">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#66fcf1] to-[#45a29e] flex items-center justify-center text-[10px] font-black text-black">
                            {identity?.name?.charAt(0) || "M"}
                        </div>
                        <div className="overflow-hidden">
                            <p className="text-xs font-black text-white truncate">{identity?.name || "MİMAR"}</p>
                            <p className="text-[9px] text-[#45a29e] uppercase font-bold truncate tracking-widest">Sistem Operatörü</p>
                        </div>
                    </div>
                ) : (
                    <div className="flex justify-center mb-4 pt-1">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[#66fcf1] to-[#45a29e] flex items-center justify-center text-[12px] font-black text-black shadow-[0_0_15px_rgba(102,252,241,0.2)]">
                            {identity?.name?.charAt(0) || "M"}
                        </div>
                    </div>
                )}
                
                <button 
                    onClick={() => logout()}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-[10px] font-black text-red-400/70 hover:text-red-400 hover:bg-red-400/5 rounded-xl transition-all uppercase tracking-widest ${isCollapsed ? "justify-center px-0" : ""}`}
                >
                    <LogOut size={16} />
                    {!isCollapsed && <span>Oturumu Kapat</span>}
                </button>
            </div>
        </aside>
    );
};

export const Sidebar = () => {
    return <SidebarContent />;
};

export default Sidebar;
