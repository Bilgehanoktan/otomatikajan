"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { 
    Zap, 
    Play, 
    Activity, 
    Shield, 
    AlertTriangle,
    ChevronRight,
    Clock,
    CheckCircle2,
    XCircle,
    BarChart3,
    Flame,
    ShieldAlert
} from 'lucide-react';
import { 
    Card, CardHeader, CardTitle, CardDescription, CardContent,
    Badge, Button,
    Table, TableHeader, TableRow, TableHead, TableBody, TableCell
} from "./CommonUI";
import { useNotification } from "@refinedev/core";

export const ChaosDrillsPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const { open } = useNotification();
    const [scenarios, setScenarios] = useState<any[]>([]);
    const [recentRuns, setRecentRuns] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchScenarios = async () => {
        const res = await fetch("/api/v1/ui-repair/chaos/scenarios");
        if (res.ok) setScenarios(await res.json());
    };

    const fetchRecentRuns = async () => {
        const res = await fetch("/api/v1/ui-repair/chaos/runs");
        if (res.ok) setRecentRuns(await res.json());
    };

    useEffect(() => {
        fetchScenarios();
        fetchRecentRuns();
    }, []);

    const runDrill = async (scenarioId: string) => {
        setLoading(scenarioId as any);
        try {
            const res = await fetch(`/api/v1/ui-repair/chaos/scenarios/${scenarioId}/run`, {
                method: "POST"
            });
            const data = await res.json();
            if (res.ok) {
                open?.({
                    type: "success",
                    message: "Chaos drill completed.",
                    description: `Result: ${data.status}`
                });
                fetchRecentRuns();
            } else {
                open?.({
                    type: "error",
                    message: "Drill failed",
                    description: data.message || "Unknown error"
                });
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <Card className="border-red-900/20 bg-black/40 backdrop-blur-md">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle className="text-xl flex items-center gap-2 text-red-500">
                                <ShieldAlert className="w-5 h-5" />
                                {t("chaosDrills")}
                            </CardTitle>
                            <CardDescription className="text-gray-400">
                                {t("subtitle")}
                            </CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="space-y-8">
                        <div className="space-y-4">
                            <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">
                                Available Scenarios
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {scenarios.map((s) => (
                                    <Card key={s.id} className="bg-white/5 border-white/10 hover:border-red-500/50 transition-all group">
                                        <CardContent className="pt-6">
                                            <div className="flex justify-between items-start mb-2">
                                                <h4 className="font-semibold text-gray-200">{s.name}</h4>
                                                <Badge variant="outline" className="text-[10px] bg-red-950/20 text-red-400 border-red-500/30">
                                                    {s.failure_type}
                                                </Badge>
                                            </div>
                                            <p className="text-xs text-gray-400 mb-4 line-clamp-2">
                                                {s.description}
                                            </p>
                                            <Button 
                                                size="sm" 
                                                className="w-full bg-red-600 hover:bg-red-700 text-white"
                                                onClick={() => runDrill(s.id)}
                                                disabled={!!loading}
                                            >
                                                {loading === s.id ? "Running..." : (
                                                    <>
                                                        <Play className="w-3 h-3 mr-2" />
                                                        {t("runDrill")}
                                                    </>
                                                )}
                                            </Button>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">
                                Recent Drill Results
                            </h3>
                            <Table>
                                <TableHeader className="bg-white/5">
                                    <TableRow className="border-white/10 hover:bg-transparent">
                                        <TableHead className="text-gray-400">{t("scenario")}</TableHead>
                                        <TableHead className="text-gray-400">{t("expectedDetection")}</TableHead>
                                        <TableHead className="text-gray-400">{t("detectedStatus")}</TableHead>
                                        <TableHead className="text-gray-400">Result</TableHead>
                                        <TableHead className="text-gray-400 text-right">Time</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {recentRuns.map((r) => (
                                        <TableRow key={r.id} className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-300">
                                                {r.injected_failure_type}
                                            </TableCell>
                                            <TableCell className="text-gray-400 text-xs">
                                                {r.target_route}
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className={r.detection_status === "DETECTED" ? "text-green-400 border-green-500/30" : "text-yellow-400 border-yellow-500/30"}>
                                                    {r.detection_status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                {r.passed ? (
                                                    <div className="flex items-center gap-1 text-green-500 text-xs font-bold uppercase">
                                                        <CheckCircle2 className="w-4 h-4" />
                                                        {t("passed")}
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-1 text-red-500 text-xs font-bold uppercase">
                                                        <XCircle className="w-4 h-4" />
                                                        {t("failed")}
                                                    </div>
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right text-gray-500 text-xs font-mono">
                                                {new Date(r.started_at).toLocaleTimeString()}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
