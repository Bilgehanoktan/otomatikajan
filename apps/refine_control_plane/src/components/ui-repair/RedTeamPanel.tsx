"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Card, Table, Typography, Space, Tag, Button, List, Tooltip } from "antd";
import { BugOutlined, PlayCircleOutlined, ShieldOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;

export const RedTeamPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const [scenarios, setScenarios] = useState([]);
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const sRes = await fetch("/api/v1/ui-repair/red-team/generate", { method: "POST" });
            const sData = await sRes.json();
            setScenarios(sData);

            // Fetch runs
            // const rRes = await fetch("/api/v1/ui-repair/red-team/runs");
            // const rData = await rRes.json();
            // setRuns(rData);
        } catch (error) {
            console.error("Failed to fetch red team data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const runScenario = async (id: string) => {
        setLoading(true);
        try {
            await fetch(`/api/v1/ui-repair/red-team/scenarios/${id}/run`, { method: "POST" });
            // Refresh
            fetchData();
        } catch (error) {
            console.error("Run failed", error);
        } finally {
            setLoading(false);
        }
    };

    const columns = [
        {
            title: "Scenario Name",
            dataIndex: "name",
            key: "name",
            render: (text: string, record: any) => (
                <Space>
                    <BugOutlined />
                    <Text strong>{text}</Text>
                    {record.is_destructive && <Tag color="red">DESTRUCTIVE</Tag>}
                </Space>
            )
        },
        {
            title: "Risk Type",
            dataIndex: "risk_type",
            key: "risk_type",
            render: (type: string) => <Tag>{type.replace("_", " ")}</Tag>
        },
        {
            title: "Expected Detection",
            dataIndex: "expected_detection",
            key: "expected_detection",
        },
        {
            title: "Actions",
            key: "actions",
            render: (_: any, record: any) => (
                <Button 
                    icon={<PlayCircleOutlined />} 
                    onClick={() => runScenario(record.id)}
                    loading={loading}
                    disabled={record.is_destructive}
                >
                    Run Simulation
                </Button>
            )
        }
    ];

    return (
        <Space direction="vertical" style={{ width: "100%" }} size="large">
            <Card title={<Space><ShieldOutlined /> {t("red_team_scenarios")}</Space>} extra={<Button onClick={fetchData} loading={loading}>{t("generate_scenarios")}</Button>}>
                <Table 
                    dataSource={scenarios} 
                    columns={columns} 
                    rowKey="id" 
                    loading={loading}
                    pagination={false}
                />
            </Card>

            <AlertBanner />
        </Space>
    );
};

const AlertBanner = () => (
    <div style={{ backgroundColor: "#fffbe6", border: "1px solid #ffe58f", padding: "12px 16px", borderRadius: "8px" }}>
        <Space>
            <ShieldOutlined style={{ color: "#faad14" }} />
            <Text>Red team scenarios are executed in a sandbox environment. Destructive production tests are disabled by default.</Text>
        </Space>
    </div>
);
