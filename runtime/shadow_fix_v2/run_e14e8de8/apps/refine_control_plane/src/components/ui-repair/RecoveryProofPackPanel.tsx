"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { 
    ShieldCheck, FileText, Download, Fingerprint, Calendar, ExternalLink
} from "lucide-react";
import { 
    Card, CardHeader, CardTitle, CardDescription, CardContent,
    Badge, Button
} from "./CommonUI";
import { useNotification } from "@refinedev/core";
import { safeFetchJson } from "@/lib/api";

export const RecoveryProofPackPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const { open } = useNotification();
    const [packs, setPacks] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchPacks = async () => {
        try {
            const data = await safeFetchJson<any[]>("/api/v1/ui-repair/proof-pack");
            setPacks(data);
        } catch (err) {
            console.error("Failed to fetch proof packs", err);
        }
    };

    useEffect(() => {
        fetchPacks();
    }, []);

    const generatePack = async () => {
        setLoading(true);
        try {
            await safeFetchJson("/api/v1/ui-repair/proof-pack/generate?name=Weekly Resilience Proof", {
                method: "POST"
            });
            open?.({
                type: "success",
                message: "Proof pack generated.",
                description: "Resilience evidence has been consolidated and signed."
            });
            fetchPacks();
        } catch (err) {
            console.error("Failed to generate proof pack", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <Card className="border-green-900/20 bg-black/40 backdrop-blur-md">
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle className="text-xl flex items-center gap-2 text-green-500">
                            <ShieldCheck className="w-5 h-5" />
                            {t("recoveryProofPacks")}
                        </CardTitle>
                        <CardDescription className="text-gray-400">
                            Consolidated audit reports proving system resilience and autonomous recovery capability.
                        </CardDescription>
                    </div>
                    <Button 
                        onClick={generatePack} 
                        disabled={loading}
                        className="bg-green-600 hover:bg-green-700 text-white"
                    >
                        <FileText className="w-4 h-4 mr-2" />
                        {loading ? "Generating..." : t("generateProofPack")}
                    </Button>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 gap-4">
                        {packs.map((p) => (
                            <Card key={p.id} className="bg-white/5 border-white/10 overflow-hidden">
                                <div className="p-6">
                                    <div className="flex justify-between items-start mb-6">
                                        <div className="flex items-center gap-4">
                                            <div className="p-3 bg-green-500/10 rounded-xl">
                                                <ShieldCheck className="w-6 h-6 text-green-500" />
                                            </div>
                                            <div>
                                                <h3 className="text-lg font-bold text-gray-200">{p.pack_name}</h3>
                                                <div className="flex items-center gap-3 mt-1">
                                                    <div className="flex items-center gap-1 text-[10px] text-gray-500 uppercase tracking-wider">
                                                        <Calendar className="w-3 h-3" />
                                                        {new Date(p.period_start).toLocaleDateString()} - {new Date(p.period_end).toLocaleDateString()}
                                                    </div>
                                                    <Badge variant="outline" className="text-[9px] bg-green-950/20 text-green-400 border-green-500/30">
                                                        SIF-01 SIGNED
                                                    </Badge>
                                                </div>
                                            </div>
                                        </div>
                                        <Button size="sm" variant="outline" className="border-white/10 hover:bg-white/5 text-gray-300">
                                            <Download className="w-3 h-3 mr-2" />
                                            {t("downloadReport")}
                                        </Button>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-2">
                                            <p className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">{t("executiveSummary")}</p>
                                            <div className="p-4 rounded-lg bg-black/40 border border-white/5 text-xs text-gray-400 leading-relaxed italic">
                                                {p.executive_summary}
                                            </div>
                                        </div>
                                        <div className="space-y-4">
                                            <div className="space-y-2">
                                                <p className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">{t("evidenceHash")}</p>
                                                <div className="p-3 rounded-lg bg-black/40 border border-white/5 flex items-center justify-between">
                                                    <code className="text-[10px] text-green-500/70 font-mono truncate mr-4">
                                                        {p.evidence_hash}
                                                    </code>
                                                    <Fingerprint className="w-4 h-4 text-green-500/40 shrink-0" />
                                                </div>
                                            </div>
                                            <div className="flex gap-2">
                                                <Button size="xs" variant="ghost" className="text-[10px] text-gray-500 hover:text-white">
                                                    <ExternalLink className="w-3 h-3 mr-1" /> View Drill Ledger
                                                </Button>
                                                <Button size="xs" variant="ghost" className="text-[10px] text-gray-500 hover:text-white">
                                                    <ExternalLink className="w-3 h-3 mr-1" /> View Soak Data
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="h-1 bg-gradient-to-r from-transparent via-green-500/20 to-transparent" />
                            </Card>
                        ))}
                        {packs.length === 0 && (
                            <div className="text-center py-12 bg-white/5 rounded-lg border border-dashed border-white/10">
                                <FileText className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                                <p className="text-gray-400">{t("noActiveRepairsDesc")}</p>
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
