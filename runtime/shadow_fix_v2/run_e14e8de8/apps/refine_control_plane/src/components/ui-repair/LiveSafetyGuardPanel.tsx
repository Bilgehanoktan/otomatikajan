"use client";

import React from "react";
import { Card, List, Tag, Typography, Space, Tooltip, Badge } from "antd";
import { SafetyCertificateOutlined, LockOutlined, StopOutlined, InfoCircleOutlined } from "@ant-design/icons";

const { Text } = Typography;

export const LiveSafetyGuardPanel: React.FC = () => {
    const rules = [
        { key: "AUTO_APPLY", status: "BLOCKED", desc: "Auto-apply is strictly disabled in Phase 11." },
        { key: "GOVERNANCE", status: "MANDATORY", desc: "Apply requires governance approval." },
        { key: "ROLLBACK", status: "MANDATORY", desc: "No apply without rollback snapshot." },
        { key: "CRISIS_MODE", status: "ACTIVE", desc: "Pipeline stops if crisis mode is triggered." },
        { key: "HIGH_RISK", status: "MANUAL", desc: "Auth/Budget routes require manual rationale." },
    ];

    const blockedActions = [
        { time: "10:24", action: "AUTO_APPLY", route: "/auth/login", reason: "Safety Policy Rule #1" },
        { time: "09:15", action: "GOVERNANCE_REQUEST", route: "/billing/invoice", reason: "Missing Verifier result" },
    ];

    return (
        <Space direction="vertical" style={{ width: "100%" }}>
            <Card title={<Space><SafetyCertificateOutlined /> Active Safety Rules</Space>} size="small">
                <List
                    size="small"
                    dataSource={rules}
                    renderItem={item => (
                        <List.Item style={{ display: "flex", justifyContent: "space-between" }}>
                            <Space>
                                <Text strong>{item.key}</Text>
                                <Tooltip title={item.desc}><InfoCircleOutlined /></Tooltip>
                            </Space>
                            <Tag color={item.status === "BLOCKED" ? "red" : item.status === "ACTIVE" ? "green" : "blue"}>
                                {item.status}
                            </Tag>
                        </List.Item>
                    )}
                />
            </Card>

            <Card title={<Space><LockOutlined /> Blocked Actions Log</Space>} size="small">
                <List
                    size="small"
                    dataSource={blockedActions}
                    renderItem={item => (
                        <List.Item>
                            <Space direction="vertical" size={0}>
                                <Space>
                                    <Badge status="error" />
                                    <Text delete>{item.action}</Text>
                                    <Tag color="volcano">{item.route}</Tag>
                                </Space>
                                <Text type="secondary" style={{ fontSize: "12px" }}>{item.time} - Reason: {item.reason}</Text>
                            </Space>
                        </List.Item>
                    )}
                />
            </Card>
        </Space>
    );
};
