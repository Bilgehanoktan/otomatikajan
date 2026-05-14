"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { 
    Flame, Snowflake, Activity, ShieldOff, PauseCircle, PlayCircle, ShieldCheck, FileSignature
} from "lucide-react";
import { 
    Card, CardHeader, CardTitle, CardDescription, CardContent,
    Badge, Button
} from "./CommonUI";
import { useNotification } from "@refinedev/core";

export const CrisisControlPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const { open } = useNotification();
    const [state, setState] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const fetchData = async () => {
        const res = await fetch("/api/v1/ui-repair/crisis/state");
        if (res.ok) setState(await res.json());
    };

    useEffect(() => {
        fetchData();
    }, []);

    const updateMode = async (mode: string) => {
        setLoading(true);
        try {
            const res = await fetch(`/api/v1/ui-repair/crisis/update?mode=${mode}&reason=Manual+intervention+via+Dashboard&operator_id=EgemenYAZ`, {
                method: "POST"
            });
            if (res.ok) {
                open?.({ 
                    type: "success", 
                    message: "Operational mode updated.",
                    description: `System transitioned to ${mode} mode.`
                });
                fetchData();
            }
        } finally {
            setLoading(false);
        }
    };

    if (!state) return null;

    return (
        <div className="space-y-6">
            <Card className={`border-2 ${state.mode === 'NORMAL' ? 'border-green-500/20' : 'border-rose-500 shadow-lg shadow-rose-500/10'} bg-black/40 backdrop-blur-md overflow-hidden transition-all duration-500`}>
                <div className={`h-1.5 w-full ${state.mode === 'NORMAL' ? 'bg-green-500' : 'bg-rose-500 animate-pulse'}`} />
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle className="text-2xl font-black flex items-center gap-3">
                            {state.mode === 'NORMAL' ? <ShieldCheck className="w-8 h-8 text-green-500" /> : <Flame className="w-8 h-8 text-rose-500 animate-bounce" />}
                            {t("crisisManagementConsole")}
                        </CardTitle>
                        <CardDescription className="text-gray-400 mt-1">
                            Override autonomous behaviors and freeze self-healing during active incidents.
                        </CardDescription>
                    </div>
                    <Badge variant={state.mode === 'NORMAL' ? 'success' : 'danger'} className="px-4 py-1 text-sm font-bold tracking-widest">
                        {state.mode}
                    </Badge>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className={`p-6 rounded-2xl border flex flex-col items-center gap-4 text-center transition-all ${state.self_healing_frozen ? 'bg-rose-500/10 border-rose-500/30' : 'bg-white/5 border-white/10'}`}>
                            {state.self_healing_frozen ? <Snowflake className="w-10 h-10 text-blue-400 animate-spin-slow" /> : <Activity className="w-10 h-10 text-green-500" />}
                            <div>
                                <h4 className="font-bold text-gray-200">Self-Healing</h4>
                                <p className="text-[10px] text-gray-500 uppercase mt-1">{state.self_healing_frozen ? "FROZEN" : "ACTIVE"}</p>
                            </div>
                        </div>
                        <div className={`p-6 rounded-2xl border flex flex-col items-center gap-4 text-center transition-all ${state.auto_repair_frozen ? 'bg-rose-500/10 border-rose-500/30' : 'bg-white/5 border-white/10'}`}>
                            {state.auto_repair_frozen ? <ShieldOff className="w-10 h-10 text-rose-400" /> : <ShieldCheck className="w-10 h-10 text-blue-500" />}
                            <div>
                                <h4 className="font-bold text-gray-200">Auto-Repair</h4>
                                <p className="text-[10px] text-gray-500 uppercase mt-1">{state.auto_repair_frozen ? "FROZEN" : "ACTIVE"}</p>
                            </div>
                        </div>
                        <div className={`p-6 rounded-2xl border flex flex-col items-center gap-4 text-center transition-all ${state.monitoring_frozen ? 'bg-rose-500/10 border-rose-500/30' : 'bg-white/5 border-white/10'}`}>
                            {state.monitoring_frozen ? <PauseCircle className="w-10 h-10 text-gray-500" /> : <PlayCircle className="w-10 h-10 text-blue-400" />}
                            <div>
                                <h4 className="font-bold text-gray-200">Monitoring</h4>
                                <p className="text-[10px] text-gray-500 uppercase mt-1">{state.monitoring_frozen ? "PAUSED" : "RUNNING"}</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-4 justify-center">
                        <Button 
                            variant={state.mode === 'NORMAL' ? 'secondary' : 'outline'}
                            onClick={() => updateMode("NORMAL")}
                            disabled={loading || state.mode === 'NORMAL'}
                            className="px-8"
                        >
                            <ShieldCheck className="w-4 h-4 mr-2" />
                            {t("resumeNormalMode")}
                        </Button>
                        <Button 
                            variant="outline"
                            onClick={() => updateMode("SELF_HEALING_FROZEN")}
                            disabled={loading || state.mode === 'SELF_HEALING_FROZEN'}
                            className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                        >
                            <Snowflake className="w-4 h-4 mr-2" />
                            {t("freezeSelfHealing")}
                        </Button>
                        <Button 
                            variant="outline"
                            onClick={() => updateMode("FULL_UI_REPAIR_FREEZE")}
                            disabled={loading || state.mode === 'FULL_UI_REPAIR_FREEZE'}
                            className="border-rose-500/30 text-rose-400 hover:bg-rose-500/10"
                        >
                            <Flame className="w-4 h-4 mr-2" />
                            {t("totalLockdown")}
                        </Button>
                    </div>

                    {state.reason && (
                        <div className="mt-8 p-4 bg-black/60 rounded-xl border border-white/10 text-xs text-gray-500 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <FileSignature className="w-4 h-4 text-gray-600" />
                                <span><strong>Last Update Reason:</strong> {state.reason}</span>
                            </div>
                            <div className="text-[10px] text-gray-700">
                                BY: {state.activated_by} • {new Date(state.activated_at).toLocaleString()}
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};
