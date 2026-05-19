"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Card, Space, Row, Col, Tabs } from "antd";
import { safeFetchJson } from "@/lib/api";
import { 
    RocketOutlined, 
    BarChartOutlined, 
    AuditOutlined, 
    FileTextOutlined, 
    SafetyCertificateOutlined,
    EyeOutlined
} from "@ant-design/icons";

import { PilotModePanel } from "./PilotModePanel";
import { ShadowModeStatusPanel } from "./ShadowModeStatusPanel";
import { PilotMetricsPanel } from "./PilotMetricsPanel";
import { OperatorActionLedgerPanel } from "./OperatorActionLedgerPanel";
import { PilotReportPanel } from "./PilotReportPanel";
import { LiveSafetyGuardPanel } from "./LiveSafetyGuardPanel";

export const PilotRolloutPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const [rollout, setRollout] = useState<any>(null);

    const fetchStatus = async () => {
        try {
            const data = await safeFetchJson("/api/v1/ui-repair/pilot/status");
            setRollout(data);
        } catch (e) {}
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    const items = [
        {
            key: "overview",
            label: (
                <span>
                    <RocketOutlined />
                    Overview
                </span>
            ),
            children: (
                <Row gutter={[24, 24]}>
                    <Col span={16}>
                        <PilotModePanel />
                    </Col>
                    <Col span={8}>
                        <ShadowModeStatusPanel />
                    </Col>
                </Row>
            ),
        },
        {
            key: "metrics",
            label: (
                <span>
                    <BarChartOutlined />
                    {t("pilot_metrics")}
                </span>
            ),
            children: <PilotMetricsPanel rolloutId={rollout?.id} />,
        },
        {
            key: "ledger",
            label: (
                <span>
                    <AuditOutlined />
                    {t("operator_actions")}
                </span>
            ),
            children: <OperatorActionLedgerPanel rolloutId={rollout?.id} />,
        },
        {
            key: "safety",
            label: (
                <span>
                    <SafetyCertificateOutlined />
                    Safety Guard
                </span>
            ),
            children: <LiveSafetyGuardPanel />,
        },
        {
            key: "report",
            label: (
                <span>
                    <FileTextOutlined />
                    Final Report
                </span>
            ),
            children: <PilotReportPanel rolloutId={rollout?.id} />,
        },
    ];

    return (
        <div className="pilot-rollout-container">
            <Tabs 
                items={items} 
                type="line" 
                className="premium-tabs-line"
                defaultActiveKey="overview"
            />
        </div>
    );
};
