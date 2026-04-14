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
    FileText
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
};

const SidebarContent = () => {
    const { menuItems, selectedKey } = useMenu();
    const { mutate: logout } = useLogout();
    const { data: identity } = useGetIdentity<{ name: string }>();

    return (
        <aside className="w-64 h-full glass border-r border-white/5 flex flex-col">
            <div className="p-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 premium-gradient rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(102,252,241,0.3)]">
                        <Zap className="text-black" size={24} />
                    </div>
                    <div>
                        <h1 className="font-bold text-lg tracking-tight text-white">SOVEREIGN</h1>
                        <p className="text-[10px] uppercase tracking-widest text-[#45a29e] font-semibold">AGI Control Plane</p>
                    </div>
                </div>
            </div>

            <nav className="flex-1 px-4 space-y-2 py-4">
                {menuItems.map((item) => (
                    <Link
                        key={item.key}
                        href={item.route ?? "/"}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                            selectedKey === item.key
                                ? "bg-white/10 text-[#66fcf1] border border-white/5"
                                : "text-gray-400 hover:text-white hover:bg-white/5"
                        }`}
                    >
                        <span className={selectedKey === item.key ? "text-[#66fcf1]" : "text-gray-500 group-hover:text-gray-300"}>
                            {icons[item.name] || <LayoutDashboard size={20} />}
                        </span>
                        <span className="font-medium text-sm capitalize">{item.label}</span>
                    </Link>
                ))}
            </nav>

            <div className="p-4 mt-auto">
                <div className="glass-card mb-4 p-4 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-[10px] font-bold">
                        {identity?.name?.charAt(0) || "A"}
                    </div>
                    <div className="overflow-hidden">
                        <p className="text-xs font-bold text-white truncate">{identity?.name || "Architect"}</p>
                        <p className="text-[10px] text-gray-500 underline truncate">Sovereign Admin</p>
                    </div>
                </div>
                
                <button 
                    onClick={() => logout()}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400/70 hover:text-red-400 hover:bg-red-400/5 rounded-xl transition-colors"
                >
                    <LogOut size={18} />
                    <span>Terminate Session</span>
                </button>
            </div>
        </aside>
    );
};

export const Sidebar = () => {
    const [mounted, setMounted] = React.useState(false);
    
    React.useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return <aside className="w-64 h-full glass border-r border-white/5 flex flex-col" />;
    }

    return <SidebarContent />;
};

export default Sidebar;
