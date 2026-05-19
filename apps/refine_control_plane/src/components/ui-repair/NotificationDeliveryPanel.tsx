"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { 
    Send, Mail, MessageCircle, AlertTriangle, CheckCircle, XCircle, Clock
} from "lucide-react";
import { 
    Card, CardHeader, CardTitle, CardDescription, CardContent,
    Badge, Table
} from "./CommonUI";
import { safeFetchJson } from "@/lib/api";

export const NotificationDeliveryPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const [deliveries, setDeliveries] = useState<any[]>([]);

    const fetchData = async () => {
        try {
            const data = await safeFetchJson<any[]>("/api/v1/ui-repair/notifications/deliveries");
            setDeliveries(data);
        } catch (err) {
            console.error("Failed to fetch notification deliveries", err);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 15000);
        return () => clearInterval(interval);
    }, []);

    const getChannelIcon = (channel: string) => {
        switch (channel) {
            case 'EMAIL': return <Mail className="w-4 h-4" />;
            case 'TELEGRAM': return <MessageCircle className="w-4 h-4" />;
            default: return <Send className="w-4 h-4" />;
        }
    };

    return (
        <Card className="border-white/10 bg-black/40 backdrop-blur-md">
            <CardHeader>
                <CardTitle className="text-xl flex items-center gap-2 text-gray-300">
                    <Send className="w-5 h-5" />
                    {t("notificationDeliveryLogs")}
                </CardTitle>
                <CardDescription>
                    Tracking delivery status of urgent operator escalations across all channels.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="overflow-hidden rounded-xl border border-white/5">
                    <Table>
                        <thead className="bg-white/5">
                            <tr className="text-[10px] text-gray-500 uppercase tracking-widest text-left">
                                <th className="p-4">Channel</th>
                                <th className="p-4">Status</th>
                                <th className="p-4">Recipient</th>
                                <th className="p-4">Message</th>
                                <th className="p-4">Time</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {deliveries.map((d) => (
                                <tr key={d.id} className="text-xs text-gray-400 hover:bg-white/5 transition-colors">
                                    <td className="p-4">
                                        <div className="flex items-center gap-2 text-gray-300">
                                            {getChannelIcon(d.channel)}
                                            {d.channel}
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            {d.status === 'SENT' ? (
                                                <Badge variant="success" className="bg-green-500/10 text-green-400 border-none">SENT</Badge>
                                            ) : d.status === 'FAILED' ? (
                                                <Badge variant="danger" className="bg-rose-500/10 text-rose-400 border-none">FAILED</Badge>
                                            ) : (
                                                <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-none">PENDING</Badge>
                                            )}
                                        </div>
                                    </td>
                                    <td className="p-4 font-mono text-[10px]">{d.recipient}</td>
                                    <td className="p-4">
                                        <div className="truncate max-w-xs">{d.title}</div>
                                        {d.error_message && <div className="text-[10px] text-rose-500 mt-1">{d.error_message}</div>}
                                    </td>
                                    <td className="p-4 text-[10px] text-gray-600">
                                        <div className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {new Date(d.created_at).toLocaleTimeString()}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {deliveries.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="p-12 text-center text-gray-600 italic">
                                        No notification records found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </Table>
                </div>
            </CardContent>
        </Card>
    );
};
