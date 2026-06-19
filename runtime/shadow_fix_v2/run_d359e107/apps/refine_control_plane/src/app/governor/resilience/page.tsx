"use client";

import React from "react";
import { List, Table, Tag, Space, Card, Typography, Statistic, Row, Col, Progress, Alert } from "antd";
import { useList } from "@refinedev/core";
import { 
    CheckCircleOutlined, 
    ExclamationCircleOutlined, 
    StopOutlined, 
    SafetyOutlined,
    WarningOutlined,
    ThunderboltOutlined
} from "@ant-design/icons";

const { Title, Text } = Typography;

export default function GovernorResiliencePage() {
    const { query: { data, isLoading } } = useList<any>({
        resource: "governance/governor/resilience/status",
    });

    const getStatusTag = (status: string) => {
        switch (status) {
            case "HEALTHY": return <Tag color="success" icon={<CheckCircleOutlined />}>HEALTHY</Tag>;
            case "DEGRADED": return <Tag color="warning" icon={<WarningOutlined />}>DEGRADED</Tag>;
            case "FAILED": return <Tag color="error" icon={<ExclamationCircleOutlined />}>FAILED</Tag>;
            case "FROZEN": return <Tag color="blue" icon={<SafetyOutlined />}>FROZEN</Tag>;
            case "ISOLATED": return <Tag color="magenta" icon={<StopOutlined />}>ISOLATED</Tag>;
            default: return <Tag>{status}</Tag>;
        }
    };

    const columns = [
        {
            title: "Domain",
            dataIndex: "domain",
            key: "domain",
            render: (text: string) => <Text strong>{text}</Text>,
        },
        {
            title: "Runtime Status",
            dataIndex: "runtime_status",
            key: "runtime_status",
            render: (status: string) => getStatusTag(status),
        },
        {
            title: "Failures",
            dataIndex: "failure_count",
            key: "failure_count",
            render: (count: number) => (
                <Text type={count > 0 ? "danger" : "secondary"}>
                    {count}
                </Text>
            ),
        },
        {
            title: "Mode",
            dataIndex: "advisory_only",
            key: "advisory_only",
            render: (advisory: boolean) => advisory ? <Tag color="orange">ADVISORY ONLY</Tag> : <Tag color="green">ENFORCING</Tag>,
        },
        {
            title: "Last Update",
            dataIndex: "updated_at",
            key: "updated_at",
            render: (date: string) => new Date(date).toLocaleString(),
        },
        {
            title: "Reason",
            dataIndex: "reason",
            key: "reason",
            render: (text: string) => text || "-",
        },
    ];

    const healthyCount = data?.data?.filter(i => i.runtime_status === "HEALTHY").length || 0;
    const totalCount = data?.data?.length || 0;
    const systemHealth = totalCount > 0 ? (healthyCount / totalCount) * 100 : 0;

    return (
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
            <Card style={{ background: "linear-gradient(135deg, #001529 0%, #003a8c 100%)", borderRadius: "12px" }}>
                <Row gutter={24} align="middle">
                    <Col span={16}>
                        <Title level={2} style={{ color: "#fff", margin: 0 }}>
                            <ThunderboltOutlined style={{ marginRight: "12px" }} />
                            Operational Resilience Dashboard
                        </Title>
                        <Text style={{ color: "rgba(255,255,255,0.85)" }}>
                            Monitoring self-healing states, circuit breakers, and SLO health across governor domains.
                        </Text>
                    </Col>
                    <Col span={8} style={{ textAlign: "right" }}>
                        <Statistic 
                            title={<span style={{ color: "#fff" }}>System Integrity</span>}
                            value={systemHealth}
                            precision={1}
                            suffix="%"
                            valueStyle={{ color: systemHealth > 80 ? "#52c41a" : "#faad14" }}
                        />
                        <Progress 
                            percent={systemHealth} 
                            showInfo={false} 
                            strokeColor={systemHealth > 80 ? "#52c41a" : "#faad14"}
                            trailColor="rgba(255,255,255,0.2)"
                        />
                    </Col>
                </Row>
            </Card>

            {systemHealth < 100 && (
                <Alert
                    message="Degraded Governance Detected"
                    description="One or more governor domains are operating in fail-safe mode. Meta-governor is applying default-block policies where applicable."
                    type="warning"
                    showIcon
                    action={
                        <Space>
                            <Tag color="warning">FAILOVER ACTIVE</Tag>
                        </Space>
                    }
                />
            )}

            <Card
                title="Governor Domain Runtime Status"
                loading={isLoading}
            >
                <Table 
                    dataSource={data?.data} 
                    columns={columns} 
                    pagination={false} 
                    rowKey="domain"
                />
            </Card>
        </Space>
    );
}
