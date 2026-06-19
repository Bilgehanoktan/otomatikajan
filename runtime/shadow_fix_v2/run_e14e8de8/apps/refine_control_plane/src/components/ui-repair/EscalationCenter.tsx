"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { 
    AlertOctagon, User, Bell, CheckSquare, ArrowUpRight, Clock, ShieldAlert, MessageSquare
} from "lucide-react";
import { 
    Card, CardHeader, CardTitle, CardDescription, CardContent,
    Badge, Button, Table
} from "./CommonUI";
import { useNotification } from "@refinedev/core";
import { safeFetchJson } from "@/lib/api";

export const EscalationCenter: React.FC = () => {
    const t = useTranslations("repair_lab");
    const { open } = useNotification();
    const [escalations, setEscalations] = useState<any[]>([]);

    const fetchData = async () => {
        try {
            const data = await safeFetchJson<any[]>("/api/v1/ui-repair/escalations");
            setEscalations(data);
        } catch (error) {
            console.error("Failed to fetch escalations", error);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    const ackEscalation = async (id: string) => {
        try {
            await safeFetchJson(`/api/v1/ui-repair/escalations/${id}/ack?operator_id=EgemenYAZ`, {
                method: "POST"
            });
            open?.({ type: "success", message: "Escalation acknowledged." });
            fetchData();
        } catch (error) {
            console.error("Ack failed", error);
        }
    };

    const resolveEscalation = async (id: string) => {
        try {
            await safeFetchJson(`/api/v1/ui-repair/escalations/${id}/resolve?operator_id=EgemenYAZ`, {
                method: "POST"
            });
            open?.({ type: "success", message: "Escalation marked as resolved." });
            fetchData();
        } catch (error) {
            console.error("Resolve failed", error);
        }
    };

    return (
        <div className="space-y-6">
            <Card className="border-rose-500/20 bg-black/40 backdrop-blur-md">
                <CardHeader>
                    <CardTitle className="text-xl flex items-center gap-2 text-rose-500">
                        <AlertOctagon className="w-5 h-5" />
                        {t("operatorEscalationCenter")}
                    </CardTitle>
                    <CardDescription>
                        Critical UI failures requiring human intervention and manual validation.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 gap-4">
                        {escalations.map((esc) => (
                            <div key={esc.id} className={`p-5 rounded-xl border ${esc.status === 'RESOLVED' ? 'bg-green-500/5 border-green-500/20' : 'bg-rose-500/5 border-rose-500/20 shadow-lg shadow-rose-500/5'}`}>
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-3 rounded-lg ${esc.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' : 'bg-orange-500/20 text-orange-400'}`}>
                                            <ShieldAlert className="w-6 h-6" />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h3 className="text-lg font-bold text-gray-200">{esc.route}</h3>
                                                <Badge variant="danger" className="text-[10px]">{esc.severity}</Badge>
                                            </div>
                                            <div className="flex items-center gap-3 mt-1">
                                                <div className="flex items-center gap-1 text-[10px] text-gray-500 uppercase tracking-widest">
                                                    <Clock className="w-3 h-3" />
                                                    {new Date(esc.created_at).toLocaleString()}
                                                </div>
                                                <Badge variant="outline" className="text-[10px] bg-black/40">{esc.status}</Badge>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        {esc.status === "OPEN" || esc.status === "NOTIFIED" ? (
                                            <Button size="sm" onClick={() => ackEscalation(esc.id)} className="bg-rose-600 hover:bg-rose-700 text-white">
                                                <Bell className="w-3 h-3 mr-2" />
                                                {t("acknowledge")}
                                            </Button>
                                        ) : esc.status === "ACKNOWLEDGED" ? (
                                            <Button size="sm" onClick={() => resolveEscalation(esc.id)} className="bg-green-600 hover:bg-green-700 text-white">
                                                <CheckSquare className="w-3 h-3 mr-2" />
                                                {t("markResolved")}
                                            </Button>
                                        ) : null}
                                    </div>
                                </div>
                                <div className="p-4 bg-black/40 rounded-lg border border-white/5 text-sm text-gray-400 leading-relaxed">
                                    <div className="flex items-center gap-2 mb-2 text-[10px] font-bold text-gray-500 uppercase tracking-tighter">
                                        <MessageSquare className="w-3 h-3" />
                                        Root Cause / Reason
                                    </div>
                                    {esc.reason}
                                </div>
                                <div className="mt-4 flex gap-4 text-[10px] text-gray-500">
                                    <div className="flex items-center gap-1">
                                        <User className="w-3 h-3" />
                                        {esc.assigned_to || "Unassigned"}
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <ArrowUpRight className="w-3 h-3" />
                                        ID: {esc.id.substring(0, 8)}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
