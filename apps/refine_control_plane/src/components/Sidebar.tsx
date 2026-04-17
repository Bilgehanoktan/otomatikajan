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
            className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-300 group relative ${
                selectedKey === item.key
                    ? "bg-[#66fcf1]/10 text-[#66fcf1] border border-[#66fcf1]/20 shadow-[0_0_15px_rgba(102,252,241,0.05)]"
                    : "text-gray-400 hover:text-white hover:bg-white/5"
            }`}
        >
            {/* Active Indicator Bar */}
            {selectedKey === item.key && (
                <div className="absolute left-[-1rem] top-1/2 -translate-y-1/2 w-1 h-6 bg-[#66fcf1] rounded-r-full shadow-[0_0_8px_#66fcf1]" />
            )}

            <span className={`transition-colors duration-300 ${selectedKey === item.key ? "text-[#66fcf1]" : "text-gray-500 group-hover:text-gray-300"}`}>
                {icons[item.name] || <LayoutDashboard size={18} />}
            </span>
            <span className="font-medium text-xs capitalize tracking-tight">{item.label}</span>

            {/* Premium Hover Tooltip (Only visible if needed or as extra hint) */}
            <div className="absolute left-full ml-4 px-2 py-1 bg-[#1f2833] text-[#66fcf1] text-[10px] font-bold rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 whitespace-nowrap border border-[#66fcf1]/20 shadow-xl">
                {item.label}
            </div>
        </Link>
    );

    return (
        <aside className="w-64 h-full glass border-r border-white/5 flex flex-col overflow-hidden">
            <div className="p-6 border-b border-white/5 bg-[#0b0c10]/20">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 premium-gradient rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(102,252,241,0.3)] shrink-0">
                        <Cpu className="text-black" size={24} />
                    </div>
                    <div className="overflow-hidden">
                        <h1 className="font-black text-lg tracking-tighter text-white leading-none">EGEMEN YAZ</h1>
                        <p className="text-[10px] uppercase tracking-[0.2em] text-[#45a29e] font-black mt-1">CORE ENGINE</p>
                    </div>
                </div>
            </div>

            <nav className="flex-1 px-4 py-6 space-y-8 overflow-y-auto overflow-x-hidden custom-scrollbar">
                {groups.map((group) => {
                    const groupItems = menuItems.filter(item => group.items.includes(item.name));
                    if (groupItems.length === 0) return null;

                    return (
                        <div key={group.title} className="space-y-2">
                            <h3 className="px-4 text-[9px] font-black text-gray-600 uppercase tracking-[0.2em]">
                                {group.title}
                            </h3>
                            <div className="space-y-1">
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

            <div className="p-4 border-t border-white/5 bg-[#0b0c10]/40">
                <div className="glass-card mb-4 p-3 flex items-center gap-3 !rounded-xl">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#66fcf1] to-[#45a29e] flex items-center justify-center text-[10px] font-black text-black">
                        {identity?.name?.charAt(0) || "M"}
                    </div>
                    <div className="overflow-hidden">
                        <p className="text-xs font-black text-white truncate">{identity?.name || "MİMAR"}</p>
                        <p className="text-[9px] text-[#45a29e] uppercase font-bold truncate tracking-widest">Sistem Operatörü</p>
                    </div>
                </div>
                
                <button 
                    onClick={() => logout()}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-[10px] font-black text-red-400/70 hover:text-red-400 hover:bg-red-400/5 rounded-xl transition-all uppercase tracking-widest"
                >
                    <LogOut size={16} />
                    <span>Oturumu Kapat</span>
                </button>
            </div>
        </aside>
    );
};

export const Sidebar = () => {
    return <SidebarContent />;
};

export default Sidebar;
