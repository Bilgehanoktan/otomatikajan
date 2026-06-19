"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Card, Table, Typography, Space, Tag, Button, Progress, List, Alert } from "antd";
import { CheckCircleOutlined, ExclamationCircleOutlined, CloseCircleOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { safeFetchJson } from "@/lib/api";

const { Title, Text } = Typography;

export const EnterpriseReadinessSubPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const fetchReadiness = async () => {
        setLoading(true);
        try {
            const result = await safeFetchJson("/api/v1/ui-repair/readiness/overview");
            setData(result);
        } catch (error) {
            console.error("Failed to fetch readiness", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReadiness();
    }, []);

    const runAssessment = async () => {
        setLoading(true);
        try {
            await safeFetchJson("/api/v1/ui-repair/readiness/assess?assessor=Admin", { method: "POST" });
            await fetchReadiness();
        } catch (error) {
            console.error("Assessment failed", error);
        } finally {
            setLoading(false);
        }
    };

    if (!data || data.status === "NO_DATA") {
        return (
            <Card>
                <EmptyState onAssess={runAssessment} loading={loading} />
            </Card>
        );
    }

    const { assessment, gate } = data;

    return (
        <Space direction="vertical" style={{ width: "100%" }} size="large">
            <Card>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        <Title level={4}>{t("enterprise_readiness")}</Title>
                        <Text type="secondary">Last assessed: {new Date(assessment.created_at).toLocaleString()}</Text>
                    </div>
                    <Button type="primary" onClick={runAssessment} loading={loading}>
                        {t("generate_assessment")}
                    </Button>
                </div>

                <div style={{ display: "flex", gap: "40px", marginTop: "24px" }}>
                    <div style={{ textAlign: "center" }}>
                        <Progress 
                            type="dashboard" 
                            percent={assessment.overall_score} 
                            strokeColor={assessment.overall_score > 75 ? "#52c41a" : "#faad14"}
                        />
                        <div style={{ marginTop: "8px" }}>
                            <Tag color={assessment.overall_score > 75 ? "green" : "orange"} style={{ fontSize: "14px", padding: "4px 12px" }}>
                                {assessment.rating}
                            </Tag>
                        </div>
                    </div>

                    <div style={{ flex: 1 }}>
                        <Title level={5}>Decision Gate: {gate?.decision || "PENDING"}</Title>
                        <Alert 
                            message={gate?.rationale || "System awaiting final gate evaluation."}
                            type={gate?.decision === "GO" ? "success" : "warning"}
                            showIcon
                            icon={gate?.decision === "GO" ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                        />
                    </div>
                </div>
            </Card>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
                <Card title="Readiness Score Breakdown">
                    <List size="small">
                        <MetricItem label="Monitoring Coverage" value={assessment.monitoring_score} />
                        <MetricItem label="Governance Safety" value={assessment.governance_score} />
                        <MetricItem label="Resilience Status" value={assessment.resilience_score} />
                        <MetricItem label="Audit & Evidence" value={assessment.audit_score} />
                        <MetricItem label="Operations readiness" value={assessment.operations_score} />
                    </List>
                </Card>

                <Card title="Blockers & Warnings">
                    {assessment.blocker_list_json.length > 0 && (
                        <List
                            dataSource={assessment.blocker_list_json}
                            renderItem={(item: string) => (
                                <List.Item>
                                    <Text type="danger"><CloseCircleOutlined /> {item}</Text>
                                </List.Item>
                            )}
                        />
                    )}
                    <List
                        dataSource={assessment.warning_list_json}
                        renderItem={(item: string) => (
                            <List.Item>
                                <Text type="warning"><ExclamationCircleOutlined /> {item}</Text>
                            </List.Item>
                        )}
                    />
                </Card>
            </div>
        </Space>
    );
};

const MetricItem = ({ label, value }: { label: string; value: number }) => (
    <List.Item style={{ display: "flex", justifyContent: "space-between" }}>
        <Text>{label}</Text>
        <Progress percent={value} size="small" style={{ width: "120px" }} />
    </List.Item>
);

const EmptyState = ({ onAssess, loading }: any) => (
    <div style={{ textAlign: "center", padding: "40px" }}>
        <SafetyCertificateOutlined style={{ fontSize: "64px", color: "#d9d9d9" }} />
        <Title level={4} style={{ marginTop: "24px" }}>No Assessment Found</Title>
        <Text type="secondary">Run the enterprise readiness assessment to calculate production scores.</Text>
        <div style={{ marginTop: "24px" }}>
            <Button type="primary" onClick={onAssess} loading={loading}>Initialize Assessment</Button>
        </div>
    </div>
);
