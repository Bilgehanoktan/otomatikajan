"use client";

import React from "react";
import { useMenu, useLogout, useGetIdentity, useTranslate } from "@refinedev/core";
import Link from "next/link";
import { useTranslations } from "next-intl";
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
    Target,
    Fingerprint,
    Brain,
    Sparkles,
    ShieldOff,
    Search,
    FlaskConical,
    DollarSign,
    GraduationCap
} from "lucide-react";

const icons: Record<string, React.ReactNode> = {
    workflows: <Workflow size={20} />,
    dashboard: <LayoutDashboard size={20} />,
    "governance/governor/cases": <ShieldCheck size={20} />,
    "governance/governor/escalations": <AlertTriangle size={20} />,
    "governance/governor/scorecard": <BarChart3 size={20} />,
    "governance/governor/outcomes": <CheckSquare size={20} />,
    "governance/governor/calibrations": <Activity size={20} />,
    "governance/governor/resilience": <Dna size={20} />,
    "governance/ops/handover": <Rocket size={20} />,
    "governance/ops/launch-gates": <Target size={20} />,
    "governance/drills": <Dna size={20} />,
    mesh: <Globe size={20} />,
    verifiers: <Activity size={20} />,
    "governance/approvals": <CheckSquare size={20} />,
    "governance/incidents": <AlertTriangle size={20} />,
    "governance/proposals": <Signature size={20} />,
    learning: <Brain size={20} />,
    "learning/fingerprints": <Fingerprint size={20} />,
    "learning/strategy-memory": <Brain size={20} />,
    "learning/negative-patterns": <ShieldOff size={20} />,
    "adaptation-candidates": <Sparkles size={20} />,
    evolution: <Dna size={20} />,
    federation: <Network size={20} />,
    "federation/conflicts": <Activity size={20} />,
    "governance/safety": <ShieldAlert size={20} />,
    "governance/audit": <Eye size={20} />,
    axiology: <Search size={20} />,
    "repair-lab": <FlaskConical size={20} />,
    "meeting-room": <Boxes size={20} />,
    fleet: <Rocket size={20} />,
    identity: <Fingerprint size={20} />,
    costs: <DollarSign size={20} />,
    training: <GraduationCap size={20} />,
    "governance/compliance": <ShieldCheck size={20} />,
    "mcp-hub": <Boxes size={20} />,
    "prompt-studio": <Brain size={20} />,
    "system-health": <Activity size={20} />,
    "ui-repair": <ShieldCheck size={20} />,
};

const SidebarContent = () => {
    const { menuItems, selectedKey } = useMenu();
    const { mutate: logout } = useLogout();
    const { data: identity } = useGetIdentity<{ name: string }>();
    const translate = useTranslate();
    const [isCollapsed, setIsCollapsed] = React.useState(false);
    const [expandedMenus, setExpandedMenus] = React.useState<Record<string, boolean>>({});
    const t = useTranslations("sidebar");

    // Check if any child of a menu item is active
    const checkIsChildActive = (item: any): boolean => {
        if (!item.children || item.children.length === 0) return false;
        return item.children.some((child: any) => selectedKey === child.key || checkIsChildActive(child));
    };

    // Define Grouping
    const groups = [
        {
            title: t("groups.operations"),
            items: ["dashboard", "workflows", "fleet", "mcp-hub", "governance/ops/handover", "governance/ops/launch-gates", "governance/incidents"]
        },
        {
            title: t("groups.governance"),
            items: [
                "governance/governor/cases",
                "governance/governor/escalations",
                "governance/governor/scorecard",
                "governance/governor/outcomes",
                "governance/approvals", 
                "safety", 
                "identity",
                "compliance",
                "mesh", 
                "federation", 
                "governance/proposals"
            ]
        },
        {
            title: t("groups.autonomous"),
            items: [
                "repair-lab",
                "meeting-room",
                "governance/drills",
                "learning",
                "adaptation-candidates",
                "evolution",
                "ui-repair",
                "verifiers",
                "training",
                "prompt-studio"
            ]
        },
        {
            title: t("groups.reporting"),
            items: [
                "audit",
                "axiology",
                "costs",
                "system-health"
            ]
        }
    ];

    const renderMenuItem = (item: any) => {
        const hasChildren = item.children && item.children.length > 0;
        const isAnyChildActive = checkIsChildActive(item);
        const isDirectActive = selectedKey === item.key;
        const isParentActive = isDirectActive || isAnyChildActive;
        const isExpanded = expandedMenus[item.key] ?? isAnyChildActive;

        const toggleExpand = (e: React.MouseEvent) => {
            if (hasChildren) {
                setExpandedMenus(prev => ({
                    ...prev,
                    [item.key]: !isExpanded
                }));
            }
        };

        const menuHref = (item.key === "learning" || item.name === "learning") ? "/learning/fingerprints" : (item.route ?? "/");

        const menuItemElement = (
            <Link
                key={item.key}
                href={menuHref}
                onClick={toggleExpand}
                title={isCollapsed ? translate(item.label, item.label) : ""}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-400 group relative ${
                    isDirectActive
                        ? "bg-[var(--primary)]/8 text-[var(--primary)] border border-[var(--primary)]/15 shadow-[0_0_20px_rgba(102,252,241,0.06)]"
                        : isParentActive
                        ? "text-[var(--primary)] hover:text-white bg-white/2 border border-white/5"
                        : "text-gray-400 hover:text-white hover:bg-white/5"
                } ${isCollapsed ? "justify-center px-0 w-12 mx-auto" : ""}`}
            >
                {/* Active Indicator Bar */}
                {isDirectActive && (
                    <div className={`absolute ${isCollapsed ? "-left-1" : "-left-4"} top-1/2 -translate-y-1/2 w-1.5 h-6 bg-[var(--primary)] rounded-r-full shadow-[0_0_12px_var(--primary)] animate-pulse`} />
                )}

                <span className={`transition-all duration-400 ${isParentActive ? "text-[var(--primary)] scale-110" : "text-gray-500 group-hover:text-gray-300"} ${isCollapsed ? "scale-125" : ""}`}>
                    {icons[item.name] || <LayoutDashboard size={20} />}
                </span>
                {!isCollapsed && (
                    <span className={`font-bold text-[11px] uppercase tracking-wider transition-all truncate ${isDirectActive ? "tracking-[0.1em]" : "tracking-tight"}`}>
                        {translate(item.label, undefined, item.label)}
                    </span>
                )}
                
                {/* Chevron icon for items with children (Expanded mode only) */}
                {hasChildren && !isCollapsed && (
                    <span className={`ml-auto text-[8px] transition-transform duration-300 text-gray-500 group-hover:text-gray-300 ${isExpanded ? "rotate-90 text-[var(--primary)]" : ""}`}>
                        ▶
                    </span>
                )}

                {/* Floating submenu for collapsed state */}
                {isCollapsed && hasChildren && (
                    <div className="absolute left-[54px] top-0 ml-1 bg-[#0b0c10]/95 border border-white/10 p-2 rounded-xl flex flex-col gap-1 shadow-[0_0_30px_rgba(0,0,0,0.8)] opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto translate-x-2 group-hover:translate-x-0 transition-all duration-300 z-[100] w-52 backdrop-blur-md">
                        <div className="px-3 py-1.5 border-b border-white/5 mb-1 text-left">
                            <p className="text-[10px] font-black uppercase tracking-widest text-[var(--primary)]">
                                {translate(item.label, item.label)}
                            </p>
                        </div>
                        {item.children.map((child: any) => {
                            const isChildActive = selectedKey === child.key;
                            return (
                                <Link
                                    key={child.key}
                                    href={child.route ?? "/"}
                                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-200 text-left ${
                                        isChildActive
                                            ? "bg-[var(--primary)]/10 text-[var(--primary)] font-bold border border-[var(--primary)]/20"
                                            : "text-gray-400 hover:text-white hover:bg-white/5"
                                    }`}
                                >
                                    <span className={isChildActive ? "text-[var(--primary)]" : "text-gray-500"}>
                                        {icons[child.name] || <LayoutDashboard size={14} />}
                                    </span>
                                    <span className="text-[10px] uppercase tracking-wider truncate font-semibold">
                                        {translate(child.label, undefined, child.label)}
                                    </span>
                                </Link>
                            );
                        })}
                    </div>
                )}
                
                {/* Tooltip for Collapsed State (No children) */}
                {isCollapsed && !hasChildren && (
                    <div className="absolute left-16 bg-black border border-white/10 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 translate-x-1 group-hover:translate-x-0 transition-all pointer-events-none z-[100] whitespace-nowrap shadow-xl text-[var(--primary)]">
                        {translate(item.label, item.label)}
                    </div>
                )}
            </Link>
        );

        if (hasChildren && !isCollapsed) {
            return (
                <div key={item.key} className="flex flex-col gap-1 w-full">
                    {menuItemElement}
                    <div 
                        className={`flex flex-col gap-1 pl-4 ml-4 border-l border-white/5 transition-all duration-500 overflow-hidden ${
                            isExpanded ? "max-h-[300px] opacity-100 py-1" : "max-h-0 opacity-0 pointer-events-none"
                        }`}
                    >
                        {item.children.map((child: any) => {
                            const isChildActive = selectedKey === child.key;
                            return (
                                <Link
                                    key={child.key}
                                    href={child.route ?? "/"}
                                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-300 relative ${
                                        isChildActive
                                            ? "text-[var(--primary)] bg-[var(--primary)]/5 font-bold border border-[var(--primary)]/10"
                                            : "text-gray-400 hover:text-white hover:bg-white/5"
                                    }`}
                                >
                                    {isChildActive && (
                                        <div className="absolute -left-4 top-1/2 -translate-y-1/2 w-1.5 h-4 bg-[var(--primary)] rounded-r-full shadow-[0_0_8px_var(--primary)] animate-pulse" />
                                    )}
                                    <span className={`transition-all duration-300 ${isChildActive ? "text-[var(--primary)] scale-110" : "text-gray-500"}`}>
                                        {icons[child.name] || <LayoutDashboard size={14} />}
                                    </span>
                                    <span className="text-[10px] uppercase tracking-wider truncate font-semibold">
                                        {translate(child.label, undefined, child.label)}
                                    </span>
                                </Link>
                            );
                        })}
                    </div>
                </div>
            );
        }

        return menuItemElement;
    };

    return (
        <aside 
            className={`${isCollapsed ? "w-20" : "w-64"} h-full shrink-0 glass border-r border-white/5 flex flex-col overflow-hidden transition-all duration-500 ease-in-out`}
            style={{
                marginLeft: 0,
                minWidth: isCollapsed ? "80px" : "256px",
                width: isCollapsed ? "80px" : "256px"
            }}
        >
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

                <button 
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className={`absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-black border border-white/10 flex items-center justify-center text-gray-500 hover:text-[var(--primary)] transition-all shadow-lg z-20 opacity-0 group-hover/header:opacity-100 ${isCollapsed ? "rotate-180" : ""}`}
                >
                    <LayoutDashboard size={12} />
                </button>
            </div>

            <nav className={`flex-1 px-4 py-6 space-y-9 overflow-y-auto overflow-x-hidden custom-scrollbar transition-all ${isCollapsed ? "px-2" : ""}`}>
                {groups.map((group) => {
                    const groupItems = menuItems.filter(item => {
                        const normalizedName = item.name.toLowerCase();
                        const normalizedKey = item.key?.toLowerCase();
                        return group.items.some(gi => {
                            const lowGi = gi.toLowerCase();
                            return normalizedName === lowGi || 
                                   normalizedKey === lowGi || 
                                   normalizedName.endsWith(lowGi) ||
                                   (item.route && item.route.includes(lowGi));
                        });
                    });
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
                
                {(() => {
                    const groupedNames = groups.flatMap(g => g.items);
                    const otherItems = menuItems.filter(item => !groupedNames.includes(item.name));
                    if (otherItems.length === 0) return null;
                    return (
                        <div className="space-y-2">
                            <h3 className="px-4 text-[9px] font-black text-gray-600 uppercase tracking-[0.2em]">{t("groups.other")}</h3>
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
                            <p className="text-[9px] text-[#45a29e] uppercase font-bold truncate tracking-widest">{t("operatorTitle")}</p>
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
                    {!isCollapsed && <span>{t("logout")}</span>}
                </button>
            </div>
        </aside>
    );
};

export const Sidebar = () => {
    return <SidebarContent />;
};

export default Sidebar;
