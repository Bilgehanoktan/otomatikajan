"use client";

import React, { useState, useEffect } from "react";
import { 
    Typography, 
    Row, 
    Col, 
    Card, 
    Tag, 
    Button, 
    Space, 
    Table,
    Tooltip,
    Badge
} from "antd";
import { 
    RefreshCcw, 
    Boxes, 
    Server, 
    Terminal, 
    Globe, 
    Cpu,
    Activity,
    ShieldCheck,
    ChevronRight,
    Info
} from "lucide-react";
import { useCustom } from "@refinedev/core";
import { useTranslations } from "next-intl";

const { Title, Text, Paragraph } = Typography;

interface McpServerConfig {
    enabled: boolean;
    type: "stdio" | "sse" | "http";
    command?: string;
    args?: string[];
    env?: Record<string, string>;
    url?: string;
    headers?: Record<string, string>;
    description?: string;
}

interface McpConfigResponse {
    mcp_servers: Record<string, McpServerConfig>;
}

export default function McpHubPage() {
    const t = useTranslations("mcp");
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    // Refine's useCustom returns a query result from React Query
    const { query } = useCustom<McpConfigResponse>({
        url: `/api/v1/mcp/config`,
        method: "get",
        config: {
            headers: {
                "X-Refresh-Trigger": refreshTrigger.toString()
            }
        }
    });

    const { data, isLoading, isFetching, error, refetch } = query;
    
    // Safety: React Query might not always expose refetch directly in some Refine versions
    // or it might be named differently. We'll use the one from the result.
    const manualRefetch = async () => {
        console.log("[McpHub] Manual refresh triggered. Current trigger:", refreshTrigger);
        if (typeof refetch === "function") {
            try {
                await refetch();
            } catch (err) {
                console.error("[McpHub] Refetch failed, using state trigger fallback:", err);
                setRefreshTrigger(prev => prev + 1);
            }
        } else {
            console.warn("[McpHub] refetch is not a function in this context, using state trigger");
            setRefreshTrigger(prev => prev + 1);
        }
    };

    useEffect(() => {
        if (error) {
            console.error("[McpHub] API Communication Error:", error);
        }
    }, [error]);

    const servers = (data?.data as any)?.data?.mcp_servers || (data?.data as any)?.mcp_servers || {};
    const serverList = Object.entries(servers).map(([name, config]) => ({
        key: name,
        name,
        ...(config as any)
    }));

    return (
        <div className="p-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-2">
                    <div className="flex items-center gap-3">
                        <div className="p-3 premium-gradient rounded-2xl shadow-[0_0_30px_rgba(102,252,241,0.2)]">
                            <Boxes className="text-black w-8 h-8" />
                        </div>
                        <Title level={1} className="!m-0 !text-white !font-black !tracking-tighter uppercase">
                            {t("title")}
                        </Title>
                    </div>
                    <Text className="text-gray-400 font-medium tracking-wide block max-w-2xl">
                        {t("subtitle")}
                    </Text>
                </div>
                
                <Button 
                    type="primary"
                    icon={<RefreshCcw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />}
                    onClick={() => manualRefetch()}
                    className="premium-button h-12 px-8 font-black uppercase tracking-widest"
                >
                    {t("refresh")}
                </Button>
            </div>

            {/* Quick Stats */}
            <Row gutter={[24, 24]}>
                <Col xs={24} md={8}>
                    <Card className="glass-panel overflow-hidden relative group">
                        <div className="absolute top-0 left-0 w-1 h-full bg-[var(--primary)] group-hover:w-2 transition-all" />
                        <div className="flex items-center gap-4">
                            <div className="p-4 bg-white/5 rounded-2xl">
                                <Server className="text-[var(--primary)] w-6 h-6" />
                            </div>
                            <div>
                                <Text className="text-gray-500 uppercase font-black text-[10px] tracking-[0.2em] block mb-1">
                                    {t("servers")}
                                </Text>
                                <Title level={2} className="!m-0 !text-white !font-black tracking-tight">
                                    {serverList.length}
                                </Title>
                            </div>
                        </div>
                    </Card>
                </Col>
                <Col xs={24} md={8}>
                    <Card className="glass-panel overflow-hidden relative group">
                        <div className="absolute top-0 left-0 w-1 h-full bg-green-500 group-hover:w-2 transition-all" />
                        <div className="flex items-center gap-4">
                            <div className="p-4 bg-white/5 rounded-2xl">
                                <Activity className="text-green-500 w-6 h-6" />
                            </div>
                            <div>
                                <Text className="text-gray-500 uppercase font-black text-[10px] tracking-[0.2em] block mb-1">
                                    Active Nodes
                                </Text>
                                <Title level={2} className="!m-0 !text-white !font-black tracking-tight">
                                    {serverList.filter(s => s.enabled).length}
                                </Title>
                            </div>
                        </div>
                    </Card>
                </Col>
                <Col xs={24} md={8}>
                    <Card className="glass-panel overflow-hidden relative group">
                        <div className="absolute top-0 left-0 w-1 h-full bg-purple-500 group-hover:w-2 transition-all" />
                        <div className="flex items-center gap-4">
                            <div className="p-4 bg-white/5 rounded-2xl">
                                <ShieldCheck className="text-purple-500 w-6 h-6" />
                            </div>
                            <div>
                                <Text className="text-gray-500 uppercase font-black text-[10px] tracking-[0.2em] block mb-1">
                                    Security Layer
                                </Text>
                                <Title level={2} className="!m-0 !text-white !font-black tracking-tight">
                                    V18.2
                                </Title>
                            </div>
                        </div>
                    </Card>
                </Col>
            </Row>

            {/* Main Content */}
            <Card className="glass-panel !p-0 overflow-hidden" loading={isLoading}>
                <div className="p-6 border-b border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-pulse" />
                        <h3 className="text-xs font-black text-gray-300 uppercase tracking-[0.2em] m-0">
                            {t("servers")}
                        </h3>
                    </div>
                </div>

                <div className="p-6">
                    {serverList.length > 0 ? (
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                            {serverList.map((server) => (
                                <div 
                                    key={server.key} 
                                    className="group relative bg-[#0b0c10]/40 border border-white/5 rounded-2xl p-6 hover:border-[var(--primary)]/30 transition-all duration-500 hover:shadow-[0_0_40px_rgba(102,252,241,0.03)]"
                                >
                                    <div className="flex items-start justify-between mb-6">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 rounded-xl ${server.enabled ? 'bg-[var(--primary)]/10' : 'bg-red-500/10'}`}>
                                                {server.type === 'stdio' ? <Terminal className={server.enabled ? 'text-[var(--primary)]' : 'text-red-500'} size={24} /> : <Globe className={server.enabled ? 'text-[var(--primary)]' : 'text-red-500'} size={24} />}
                                            </div>
                                            <div>
                                                <h4 className="text-lg font-black text-white uppercase tracking-tighter m-0">
                                                    {server.name}
                                                </h4>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <Tag className="!border-none bg-white/5 !text-gray-400 !text-[9px] font-black uppercase px-2 py-0.5">
                                                        {server.type}
                                                    </Tag>
                                                    <Badge 
                                                        status={server.enabled ? "success" : "error"} 
                                                        text={
                                                            <span className={`text-[9px] font-black uppercase tracking-widest ${server.enabled ? 'text-green-500' : 'text-red-500'}`}>
                                                                {server.enabled ? t("enabled") : t("disabled")}
                                                            </span>
                                                        } 
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                        <Button 
                                            icon={<ChevronRight size={18} />} 
                                            className="bg-white/5 border-none text-gray-500 hover:text-[var(--primary)] hover:bg-[var(--primary)]/10"
                                        />
                                    </div>

                                    <div className="space-y-4">
                                        <div className="bg-black/40 rounded-xl p-4 border border-white/5">
                                            <Text className="text-[10px] text-gray-500 uppercase font-black tracking-widest block mb-2">
                                                {t("description")}
                                            </Text>
                                            <Paragraph className="text-gray-300 text-sm m-0 leading-relaxed italic">
                                                {server.description || "No description provided for this server."}
                                            </Paragraph>
                                        </div>

                                        {server.type === 'stdio' && (
                                            <div className="bg-black/60 rounded-xl p-3 font-mono text-xs overflow-x-auto border border-white/10 group-hover:border-[var(--primary)]/20 transition-colors">
                                                <div className="flex items-center gap-2 mb-2 text-gray-500">
                                                    <Terminal size={12} />
                                                    <span className="text-[10px] uppercase font-black tracking-widest">Entry Command</span>
                                                </div>
                                                <code className="text-[var(--primary)] block whitespace-nowrap">
                                                    {server.command} {server.args?.join(' ')}
                                                </code>
                                            </div>
                                        )}

                                        {server.url && (
                                            <div className="bg-black/60 rounded-xl p-3 font-mono text-xs overflow-x-auto border border-white/10">
                                                <div className="flex items-center gap-2 mb-2 text-gray-500">
                                                    <Globe size={12} />
                                                    <span className="text-[10px] uppercase font-black tracking-widest">Endpoint URL</span>
                                                </div>
                                                <code className="text-blue-400 block whitespace-nowrap">
                                                    {server.url}
                                                </code>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-20 bg-white/5 rounded-3xl border border-dashed border-white/10">
                            <Boxes className="mx-auto w-16 h-16 text-gray-700 mb-6 opacity-20" />
                            <Title level={4} className="!text-gray-500 uppercase font-black tracking-widest">
                                {t("noServers")}
                            </Title>
                        </div>
                    )}
                </div>
            </Card>
        </div>
    );
}
