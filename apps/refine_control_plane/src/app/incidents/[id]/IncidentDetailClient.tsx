"use client";

import React, { useState } from "react";
import { 
    Card, 
    Typography, 
    Divider, 
    Tag, 
    Button, 
    Space, 
    Alert,
    Input,
    notification,
    Row,
    Col,
    Statistic,
    Timeline
} from "antd";
import { useShow } from "@refinedev/core";

import ArrowLeftOutlined from "@ant-design/icons/lib/icons/ArrowLeftOutlined";
import InfoCircleOutlined from "@ant-design/icons/lib/icons/InfoCircleOutlined";
import CheckCircleOutlined from "@ant-design/icons/lib/icons/CheckCircleOutlined";
import WarningOutlined from "@ant-design/icons/lib/icons/WarningOutlined";
import HistoryOutlined from "@ant-design/icons/lib/icons/HistoryOutlined";
import ToolOutlined from "@ant-design/icons/lib/icons/ToolOutlined";
import DeploymentUnitOutlined from "@ant-design/icons/lib/icons/DeploymentUnitOutlined";
import BranchesOutlined from "@ant-design/icons/lib/icons/BranchesOutlined";
import NodeIndexOutlined from "@ant-design/icons/lib/icons/NodeIndexOutlined";
import { safeFetchJson } from "@/lib/api";

const { Title, Text, Paragraph } = Typography;

export default function IncidentDetailClient() {
    const { query: { data, isLoading, isError, refetch } } = useShow({
        resource: "incidents",
    });

    const [isSubmitting, setIsSubmitting] = useState(false);

    const incident = data?.data;

    const handleResolve = async () => {
        const notes = (document.getElementById("resolution-notes") as HTMLTextAreaElement)?.value || "Manually resolved";
        setIsSubmitting(true);
        try {
            const response = await safeFetchJson(`/api/v1/incidents/${incident.id}/resolve`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    resolution_notes: notes,
                    operator_id: "admin_human"
                })
            });

            if (response.status || response.resolved_by) {
                notification.success({
                    message: "Incident Resolved",
                    description: `Status updated and sealed in lineage ${response.lineage_id?.substring(0,8) || ''}.`,
                });
                refetch();
            } else {
                notification.error({
                    message: "Action Failed",
                    description: "Backend did not confirm resolution.",
                });
            }
        } catch (err: any) {
            notification.error({
                message: "Error",
                description: err.message || "Failed to contact API.",
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) return <Card loading />;

    if (isError || !incident) return (
        <Alert
            message="Error"
            description="Incident not found or record has been purged. Check the audit ledger for historical logs."
            type="error"
            showIcon
            action={
                <Button size="small" type="primary" onClick={() => window.history.back()}>
                    Back to Feed
                </Button>
            }
        />
    );

    const getSeverityTag = (sev: string) => {
        const s = (sev || "unknown").toUpperCase();
        switch (s) {
            case "CRITICAL": return <Tag color="error" style={{ fontWeight: 800 }}>CRITICAL</Tag>;
            case "WARNING": return <Tag color="warning" style={{ fontWeight: 800 }}>WARNING</Tag>;
            case "INFO": return <Tag color="blue" style={{ fontWeight: 800 }}>INFO</Tag>;
            default: return <Tag>{s}</Tag>;
        }
    };

    return (
        <div style={{ padding: "24px" }}>
            <Button 
                icon={<ArrowLeftOutlined />} 
                onClick={() => window.history.back()} 
                style={{ marginBottom: "16px", background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "#aaa" }}
            >
                Back to Incident Feed
            </Button>

            {/* PREMIUM HEADER BAND */}
            <Card variant="borderless" style={{ background: "linear-gradient(90deg, rgba(20,10,10,0.8) 0%, rgba(30,20,20,0.4) 100%)", borderRadius: "12px", border: "1px solid rgba(255, 77, 79, 0.15)", marginBottom: "20px" }}>
                <Row gutter={16} align="middle">
                    <Col span={8}>
                        <div style={{ paddingLeft: "10px" }}>
                            <Text type="secondary" style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>Anomaly Report</Text>
                            <Title level={3} style={{ color: "#fff", margin: 0, fontWeight: 900 }}>{incident.incident_type || "System Anomaly"}</Title>
                            <Space style={{ marginTop: "4px" }}>
                                {getSeverityTag(incident.severity)}
                                <Tag color={incident.status === 'resolved' ? 'success' : 'processing'}>{incident.status ? incident.status.toUpperCase() : "OPEN"}</Tag>
                            </Space>
                        </div>
                    </Col>
                    <Col span={4}>
                        <Statistic 
                            title={<span style={{ color: "#ff7875", fontSize: "10px" }}>IMPACT AREA</span>}
                            value={incident.project_id ? "PROJECT-SCOPE" : "SYSTEM-WIDE"}
                            valueStyle={{ color: "#fff", fontSize: "16px", fontWeight: "bold" }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic 
                            title={<span style={{ color: "#ff7875", fontSize: "10px" }}>REPORTED BY</span>}
                            value="CORTEX-V13"
                            valueStyle={{ color: "#aaa", fontSize: "16px", fontFamily: "monospace" }}
                        />
                    </Col>
                    <Col span={8} style={{ textAlign: "right" }}>
                        <Space>
                            <Button icon={<BranchesOutlined />} onClick={() => window.open('/governance-lineage', '_blank')} style={{ background: "rgba(255, 77, 79, 0.1)", color: "#ff4d4f", border: "1px solid rgba(255, 77, 79, 0.3)" }}>Drift Lineage</Button>
                            {incident?.project_id && (
                                <Button icon={<NodeIndexOutlined />} onClick={() => window.open(`/workflows/${incident.project_id}`, '_blank')} style={{ background: "rgba(255, 255, 255, 0.05)", color: "#c5c6c7", border: "1px solid rgba(255, 255, 255, 0.1)" }}>Analyze Workflow</Button>
                            )}
                        </Space>
                    </Col>
                </Row>
            </Card>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "20px" }}>
                <Card bordered={false} className="glass-card" style={{ background: "rgba(18, 10, 10, 0.6)", backdropFilter: "blur(20px)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px" }}>
                    <Title level={5} style={{ color: "#ff7875", display: "flex", alignItems: "center", gap: "8px" }}>
                        <WarningOutlined /> Manifest & Logs
                    </Title>
                    <Paragraph style={{ color: "#c5c6c7", background: "rgba(0,0,0,0.3)", padding: "24px", borderRadius: "12px", border: "1px solid rgba(255, 77, 79, 0.05)", fontSize: "16px", lineHeight: "1.6" }}>
                        {incident.message || "Anomaly detected in background process. No detail message captured."}
                    </Paragraph>

                    {incident.trace && (
                        <div style={{ marginTop: "24px" }}>
                            <Title level={5} style={{ color: "#8c8c8c", fontSize: "12px" }}>Raw Telemetry Output</Title>
                            <pre style={{ background: "rgba(0,0,0,0.5)", padding: "20px", borderRadius: "12px", overflowX: "auto", border: "1px solid rgba(255, 77, 79, 0.1)", color: "#ff7875", fontSize: "11px", fontFamily: "monospace" }}>
                                {typeof incident.trace === 'string' ? incident.trace : JSON.stringify(incident.trace, null, 2)}
                            </pre>
                        </div>
                    )}

                    {incident.status?.toLowerCase() !== "resolved" && (
                        <>
                            <Divider style={{ borderColor: "rgba(255,255,255,0.05)" }} />
                            <div style={{ marginTop: "24px", padding: "20px", background: "rgba(255, 77, 79, 0.03)", borderRadius: "12px", border: "1px dashed rgba(255, 77, 79, 0.2)" }}>
                                <Title level={5} style={{ color: "#ff7875" }}><DeploymentUnitOutlined /> Resolution Override</Title>
                                <Space direction="vertical" style={{ width: "100%" }}>
                                    <Input.TextArea 
                                        placeholder="Enter the resolution steps taken and justification for override..." 
                                        rows={4} 
                                        style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", borderRadius: "8px" }}
                                        id="resolution-notes"
                                    />
                                    <Button 
                                        type="primary" 
                                        danger
                                        icon={<ToolOutlined />} 
                                        style={{ marginTop: "12px", fontWeight: "bold", height: "40px", padding: "0 24px" }}
                                        onClick={handleResolve}
                                        loading={isSubmitting}
                                    >
                                        RESOLVE & CLOSE
                                    </Button>
                                </Space>
                            </div>
                        </>
                    )}
                </Card>

                {/* INCIDENT TIMELINE */}
                <Card bordered={false} className="glass-card" style={{ background: "rgba(11, 12, 16, 0.4)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px" }}>
                    <Title level={5} style={{ color: "#fff", marginBottom: "24px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <HistoryOutlined /> Incident Lifecycle
                    </Title>
                    <Timeline
                        mode="left"
                        items={[
                            {
                                label: <Text style={{ color: "#ff7875", fontSize: "11px" }}>{incident.created_at ? new Date(incident.created_at).toLocaleTimeString() : ""}</Text>,
                                children: (
                                    <div style={{ marginBottom: "10px" }}>
                                        <Text strong style={{ color: "#fff" }}>Detected</Text>
                                        <br /><Text type="secondary" style={{ fontSize: "11px" }}>Health Scan Failure</Text>
                                    </div>
                                ),
                                color: "#ff4d4f"
                            },
                            incident.status === 'resolved' && {
                                label: <Text style={{ color: "#52c41a", fontSize: "11px" }}>RESOLVED</Text>,
                                children: (
                                    <div>
                                        <Text strong style={{ color: "#fff" }}>State Closed</Text>
                                        <br /><Text type="secondary" style={{ fontSize: "11px" }}>Manual Intervention Complete</Text>
                                    </div>
                                ),
                                color: "#52c41a"
                            }
                        ].filter(Boolean) as any}
                    />
                </Card>
            </div>
        </div>
    );
}
