"use client";

import React, { useState } from "react";
import { useTranslations } from "next-intl";
import { Card, Tabs, Typography, Space } from "antd";
import { 
    SafetyCertificateOutlined, 
    BugOutlined, 
    RocketOutlined, 
    AuditOutlined, 
    FileTextOutlined 
} from "@ant-design/icons";

import { EnterpriseReadinessSubPanel } from "./EnterpriseReadinessSubPanel";
import { RedTeamPanel } from "./RedTeamPanel";
import { ReleaseGatePanel } from "./ReleaseGatePanel";
import { FinalAuditPackPanel } from "./FinalAuditPackPanel";
import { HandoverPanel } from "./HandoverPanel";

const { Title } = Typography;

export const FinalReadinessPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const [activeSubTab, setActiveSubTab] = useState("readiness");

    const items = [
        {
            key: "readiness",
            label: (
                <span>
                    <SafetyCertificateOutlined />
                    {t("enterprise_readiness")}
                </span>
            ),
            children: <EnterpriseReadinessSubPanel />,
        },
        {
            key: "redteam",
            label: (
                <span>
                    <BugOutlined />
                    {t("red_team_scenarios")}
                </span>
            ),
            children: <RedTeamPanel />,
        },
        {
            key: "gate",
            label: (
                <span>
                    <RocketOutlined />
                    {t("release_gate")}
                </span>
            ),
            children: <ReleaseGatePanel />,
        },
        {
            key: "audit",
            label: (
                <span>
                    <AuditOutlined />
                    {t("final_audit_pack")}
                </span>
            ),
            children: <FinalAuditPackPanel />,
        },
        {
            key: "handover",
            label: (
                <span>
                    <FileTextOutlined />
                    {t("operator_handover")}
                </span>
            ),
            children: <HandoverPanel />,
        },
    ];

    return (
        <Card className="readiness-container" style={{ background: "transparent", border: "none" }}>
            <Tabs 
                activeKey={activeSubTab} 
                onChange={setActiveSubTab} 
                items={items} 
                type="card"
                className="premium-tabs"
            />
        </Card>
    );
};
