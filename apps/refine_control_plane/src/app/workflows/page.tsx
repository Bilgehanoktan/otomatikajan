"use client";

import React from "react";
import { useList, useNavigation } from "@refinedev/core";
import { 
    RefreshCcw, 
    ArrowRight, 
    Activity, 
    CheckCircle2, 
    XCircle, 
    Clock,
    MoreHorizontal
} from "lucide-react";

export default function WorkflowListPage() {
    const { show } = useNavigation();
    const { query: { data, isLoading, refetch } } = useList({
        resource: "workflows",
        pagination: { pageSize: 12 },
        sorters: [{ field: "created_at", order: "desc" }]
    });

    const { query: { data: statsData } } = useList({
        resource: "workflows/stats/summary",
        queryOptions: { retry: false }
    });
    const { query: { data: clustersData } } = useList({
        resource: "workflows/analytics/failure-clusters",
        queryOptions: { retry: false }
    });

    const stats = statsData?.data as any;
    const clusters = clustersData?.data || [];

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case "completed": return "text-green-400 bg-green-400/10 border-green-400/20";
            case "running": return "text-[#66fcf1] bg-[#66fcf1]/10 border-[#66fcf1]/20";
            case "failed":
            case "error": return "text-red-400 bg-red-400/10 border-red-400/20";
            case "pending": return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
            case "cancelled": return "text-gray-400 bg-gray-400/10 border-gray-400/20";
            default: return "text-white bg-white/10 border-white/20";
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status.toLowerCase()) {
            case "completed": return <CheckCircle2 size={14} />;
            case "running": return <Activity size={14} className="animate-pulse" />;
            case "failed":
            case "error": return <XCircle size={14} />;
            case "pending": return <Clock size={14} />;
            default: return <Activity size={14} />;
        }
    };

    return (
        <div className="p-8">
            <header className="flex justify-between items-end mb-10">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Workflow Management</h2>
                    <p className="text-gray-500 text-sm">Monitor and orchestrate your Sovereign AGI core processes.</p>
                </div>
                <button 
                    onClick={() => refetch()}
                    className="flex items-center gap-2 px-5 py-2.5 glass rounded-xl text-sm font-medium hover:bg-white/10 transition-colors"
                >
                    <RefreshCcw size={16} className={isLoading ? "animate-spin" : ""} />
                    Refresh Stats
                </button>
            </header>

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
                <div className="glass-card">
                    <p className="text-xs font-bold text-[#45a29e] uppercase tracking-wider mb-2">Total Workflows</p>
                    <h3 className="text-3xl font-bold text-white">{stats?.total || 0}</h3>
                </div>
                <div className="glass-card">
                    <p className="text-xs font-bold text-[#66fcf1] uppercase tracking-wider mb-2">Active Jobs</p>
                    <h3 className="text-3xl font-bold text-white">
                        {stats?.running || 0}
                    </h3>
                </div>
                <div className="glass-card border-green-500/10">
                    <p className="text-xs font-bold text-green-400 uppercase tracking-wider mb-2">Success Rate</p>
                    <h3 className="text-3xl font-bold text-white">{stats?.success_rate_pct || 0}%</h3>
                </div>
                <div className="glass-card border-red-500/10 group relative overflow-hidden">
                    <p className="text-xs font-bold text-red-400 uppercase tracking-wider mb-2">Failure Clusters</p>
                    <h3 className="text-3xl font-bold text-white">{clusters.length}</h3>
                    {clusters.length > 0 && (
                        <div className="absolute inset-x-0 bottom-0 p-2 bg-red-500/10 opacity-0 group-hover:opacity-100 transition-opacity">
                            <p className="text-[9px] text-red-300 truncate font-mono">Top: {clusters[0].pattern}</p>
                        </div>
                    )}
                </div>
            </div>

            <div className="glass rounded-[2rem] overflow-hidden">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-white/5 bg-white/[0.02]">
                            <th className="px-6 py-5 text-xs font-bold text-gray-500 uppercase tracking-widest">Title & ID</th>
                            <th className="px-6 py-5 text-xs font-bold text-gray-500 uppercase tracking-widest">Type</th>
                            <th className="px-6 py-5 text-xs font-bold text-gray-500 uppercase tracking-widest">Status</th>
                            <th className="px-6 py-5 text-xs font-bold text-gray-500 uppercase tracking-widest">Progress</th>
                            <th className="px-6 py-5 text-xs font-bold text-gray-500 uppercase tracking-widest">Started</th>
                            <th className="px-6 py-5 text-xs font-bold text-gray-500 uppercase tracking-widest outline-none"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.05]">
                        {isLoading ? (
                            <tr>
                                <td colSpan={6} className="px-6 py-10 text-center text-gray-500">Loading neural pathways...</td>
                            </tr>
                        ) : (data?.data as any[])?.map((workflow) => (
                            <tr 
                                key={workflow.id} 
                                className="group hover:bg-white/[0.02] cursor-pointer transition-colors"
                                onClick={() => show("workflows", workflow.id)}
                            >
                                <td className="px-6 py-6">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-white group-hover:text-[#66fcf1] transition-colors">
                                            {workflow.title}
                                        </span>
                                        <span className="text-[10px] text-gray-600 font-mono mt-1">
                                            {workflow.id}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-6 font-mono text-[11px] text-[#45a29e]">
                                    {workflow.workflow_type}
                                </td>
                                <td className="px-6 py-6">
                                    <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold border ${getStatusColor(workflow.status)}`}>
                                        {getStatusIcon(workflow.status)}
                                        <span className="uppercase tracking-wider">{workflow.status}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-6">
                                    <div className="flex items-center gap-3">
                                        <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden min-w-[100px]">
                                            <div 
                                                className="h-full premium-gradient transition-all duration-1000" 
                                                style={{ width: `${workflow.progress_pct}%` }}
                                            />
                                        </div>
                                        <span className="text-[10px] font-bold text-white w-8">
                                            {workflow.progress_pct}%
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-6">
                                    <div className="flex flex-col">
                                        <span className="text-xs text-gray-400">
                                            {workflow.started_at ? new Date(workflow.started_at).toLocaleTimeString() : "Pending"}
                                        </span>
                                        <span className="text-[10px] text-gray-600 mt-0.5">
                                            {workflow.started_at ? new Date(workflow.started_at).toLocaleDateString() : "-"}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-6 text-right">
                                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
                                            <MoreHorizontal size={18} />
                                        </button>
                                        <button className="p-2 hover:bg-[#66fcf1]/10 rounded-lg text-[#66fcf1] transition-colors">
                                            <ArrowRight size={18} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
