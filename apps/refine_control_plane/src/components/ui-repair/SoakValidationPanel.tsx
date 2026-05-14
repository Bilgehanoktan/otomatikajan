"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { 
    Activity, Timer, BarChart3, TrendingUp, AlertTriangle, Layers
} from "lucide-react";
import { 
    Card, CardHeader, CardTitle, CardDescription, CardContent,
    Badge, Button
} from "./CommonUI";
import { useNotification } from "@refinedev/core";

export const SoakValidationPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const { open } = useNotification();
    const [recentSoaks, setRecentSoaks] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchRecentSoaks = async () => {
        const res = await fetch("/api/v1/ui-repair/soak/runs");
        if (res.ok) setRecentSoaks(await res.json());
    };

    useEffect(() => {
        fetchRecentSoaks();
    }, []);

    const startSoak = async () => {
        setLoading(true);
        try {
            const res = await fetch("/api/v1/ui-repair/soak/start", {
                method: "POST"
            });
            if (res.ok) {
                open?.({
                    type: "success",
                    message: "Soak validation started.",
                    description: "Autonomous monitoring stability is being tracked."
                });
                fetchRecentSoaks();
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-blue-950/10 border-blue-500/20">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-500/10 rounded-lg">
                                <Timer className="w-5 h-5 text-blue-400" />
                            </div>
                            <div>
                                <p className="text-[10px] text-blue-300 font-bold uppercase tracking-wider">Stability Target</p>
                                <p className="text-xl font-bold text-white">99.9%</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-purple-950/10 border-purple-500/20">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-500/10 rounded-lg">
                                <TrendingUp className="w-5 h-5 text-purple-400" />
                            </div>
                            <div>
                                <p className="text-[10px] text-purple-300 font-bold uppercase tracking-wider">Avg Latency</p>
                                <p className="text-xl font-bold text-white">12.5s</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-yellow-950/10 border-yellow-500/20">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-yellow-500/10 rounded-lg">
                                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                            </div>
                            <div>
                                <p className="text-[10px] text-yellow-300 font-bold uppercase tracking-wider">False Positive Rate</p>
                                <p className="text-xl font-bold text-white">0.02%</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-green-950/10 border-green-500/20">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-green-500/10 rounded-lg">
                                <Layers className="w-5 h-5 text-green-400" />
                            </div>
                            <div>
                                <p className="text-[10px] text-green-300 font-bold uppercase tracking-wider">Memory Drift</p>
                                <p className="text-xl font-bold text-white">Nominal</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-blue-900/20 bg-black/40 backdrop-blur-md">
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle className="text-xl flex items-center gap-2 text-blue-500">
                            <Activity className="w-5 h-5" />
                            {t("soakValidation")}
                        </CardTitle>
                        <CardDescription className="text-gray-400">
                            Long-term reliability validation of the autonomous repair pipeline.
                        </CardDescription>
                    </div>
                    <Button 
                        onClick={startSoak} 
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                        {loading ? "Starting..." : t("startSoak")}
                    </Button>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">
                            Recent Validation Sessions
                        </h3>
                        <div className="space-y-3">
                            {recentSoaks.map((s) => (
                                <div key={s.id} className="p-4 rounded-lg bg-white/5 border border-white/10 flex items-center justify-between group hover:border-blue-500/30 transition-all">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-2 rounded-full ${s.status === "COMPLETED" ? "bg-green-500/10" : "bg-blue-500/10 animate-pulse"}`}>
                                            <Activity className={`w-4 h-4 ${s.status === "COMPLETED" ? "text-green-500" : "text-blue-500"}`} />
                                        </div>
                                        <div>
                                            <p className="text-sm font-semibold text-gray-200">
                                                {s.duration_minutes}m Soak Session
                                            </p>
                                            <p className="text-[10px] text-gray-500 font-mono">
                                                {new Date(s.started_at).toLocaleString()}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-8">
                                        <div className="text-center">
                                            <p className="text-[10px] text-gray-500 uppercase">Runs</p>
                                            <p className="text-sm font-bold text-gray-300">{s.monitoring_runs_count}</p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-[10px] text-gray-500 uppercase">Alerts</p>
                                            <p className="text-sm font-bold text-gray-300">{s.total_failures_detected}</p>
                                        </div>
                                        <Badge variant="outline" className={s.status === "COMPLETED" ? "text-green-400 border-green-500/30" : "text-blue-400 border-blue-500/30"}>
                                            {s.status}
                                        </Badge>
                                    </div>
                                </div>
                            ))}
                            {recentSoaks.length === 0 && (
                                <div className="text-center py-8 text-gray-500 italic text-sm">
                                    No soak validation runs recorded yet.
                                </div>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
