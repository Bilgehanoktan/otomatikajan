"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { 
    Zap, Play, Shield, AlertTriangle, Network, Globe, Layers, CheckCircle2, XCircle, RefreshCw, Eye
} from "lucide-react";
import { 
    Card, CardHeader, CardTitle, CardDescription, CardContent,
    Badge, Button, Table
} from "./CommonUI";
import { useNotification } from "@refinedev/core";
import { safeFetchJson } from "@/lib/api";

export const AdvancedChaosPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const { open } = useNotification();
    const [scenarios, setScenarios] = useState<any[]>([]);
    const [runs, setRuns] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchData = async () => {
        try {
            const [scenariosData, runsData] = await Promise.all([
                safeFetchJson<any[]>("/api/v1/ui-repair/advanced-chaos/scenarios"),
                safeFetchJson<any[]>("/api/v1/ui-repair/advanced-chaos/runs")
            ]);
            setScenarios(scenariosData);
            setRuns(runsData);
        } catch (err) {
            console.error("Failed to fetch advanced chaos data", err);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    const runDrill = async (id: string) => {
        setLoading(true);
        try {
            await safeFetchJson(`/api/v1/ui-repair/advanced-chaos/scenarios/${id}/run`, {
                method: "POST"
            });
            open?.({
                type: "success",
                message: "Advanced drill initiated.",
                description: "Failure injection started in sandbox environment."
            });
            fetchData();
        } catch (err) {
            console.error("Failed to initiate advanced drill", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="border-orange-500/20 bg-black/40 backdrop-blur-md">
                    <CardHeader>
                        <CardTitle className="text-xl flex items-center gap-2 text-orange-400">
                            <Zap className="w-5 h-5" />
                            {t("advancedChaosScenarios")}
                        </CardTitle>
                        <CardDescription>
                            Network and browser-level failure injection for resilience testing.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {scenarios.map((s) => (
                                <div key={s.id} className="p-4 rounded-lg bg-white/5 border border-white/10 hover:border-orange-500/30 transition-all group">
                                    <div className="flex justify-between items-start">
                                        <div className="flex items-start gap-3">
                                            <div className="p-2 bg-orange-500/10 rounded-lg">
                                                {s.chaos_type.includes("NETWORK") ? <Network className="w-4 h-4 text-orange-400" /> : <Globe className="w-4 h-4 text-orange-400" />}
                                            </div>
                                            <div>
                                                <h4 className="text-sm font-bold text-gray-200">{s.name}</h4>
                                                <p className="text-[10px] text-gray-500 mt-1">{s.description}</p>
                                                <div className="flex gap-2 mt-2">
                                                    <Badge variant="outline" className="text-[9px] uppercase">{s.chaos_type}</Badge>
                                                    {s.requires_sandbox && <Badge variant="secondary" className="text-[9px] bg-blue-500/10 text-blue-400 border-none">SANDBOX ONLY</Badge>}
                                                </div>
                                            </div>
                                        </div>
                                        <Button 
                                            size="sm" 
                                            onClick={() => runDrill(s.id)}
                                            disabled={loading}
                                            className="bg-orange-600 hover:bg-orange-700 text-white opacity-0 group-hover:opacity-100 transition-all"
                                        >
                                            <Play className="w-3 h-3 mr-2" />
                                            {t("runDrill")}
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-blue-500/20 bg-black/40 backdrop-blur-md">
                    <CardHeader>
                        <CardTitle className="text-xl flex items-center gap-2 text-blue-400">
                            <Layers className="w-5 h-5" />
                            {t("activeChaosRuns")}
                        </CardTitle>
                        <CardDescription>
                            Real-time status of active and recent advanced drills.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {runs.map((r) => (
                                <div key={r.id} className="p-3 rounded-lg bg-black/20 border border-white/5 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        {r.status === "COMPLETED" ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : r.status === "FAILED" ? <XCircle className="w-4 h-4 text-rose-500" /> : <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />}
                                        <div>
                                            <div className="text-xs font-bold text-gray-300">{r.chaos_type}</div>
                                            <div className="text-[10px] text-gray-500">{r.target_route}</div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <Badge variant={r.passed ? "success" : "danger"} className="text-[9px]">
                                            {r.passed ? "DETECTED" : "MISSED"}
                                        </Badge>
                                        <div className="text-[9px] text-gray-600 mt-1">
                                            {new Date(r.started_at).toLocaleTimeString()}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};
