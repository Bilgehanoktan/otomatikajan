"use client";

import React, { useState } from "react";
import { 
    Card, 
    Typography, 
    Divider, 
    Tag, 
    Steps, 
    List, 
    Button, 
    Space, 
    Alert,
    Empty,
    Input,
    notification,
    Row,
    Col,
    Statistic
} from "antd";
import { useShow, useNavigation } from "@refinedev/core";

// Use direct imports for Ant Design Icons to avoid build resolution issues
import CheckCircleOutlined from "@ant-design/icons/lib/icons/CheckCircleOutlined";
import SyncOutlined from "@ant-design/icons/lib/icons/SyncOutlined";
import ExclamationCircleOutlined from "@ant-design/icons/lib/icons/ExclamationCircleOutlined";
import ClockCircleOutlined from "@ant-design/icons/lib/icons/ClockCircleOutlined";
import ArrowLeftOutlined from "@ant-design/icons/lib/icons/ArrowLeftOutlined";
import RocketOutlined from "@ant-design/icons/lib/icons/RocketOutlined";
import BranchesOutlined from "@ant-design/icons/lib/icons/BranchesOutlined";
import SafetyOutlined from "@ant-design/icons/lib/icons/SafetyOutlined";
import NodeIndexOutlined from "@ant-design/icons/lib/icons/NodeIndexOutlined";
import { safeFetchJson } from "@/lib/api";

const { Title, Text, Paragraph } = Typography;

export default function WorkflowDetailClient() {
    const { list } = useNavigation();
    const { query: { data, isLoading, isError, refetch } } = useShow({
        resource: "workflows",
    });

    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleApprove = async () => {
        const notes = (document.getElementById("approval-notes") as HTMLTextAreaElement)?.value || "";
        setIsSubmitting(true);
        try {
            const response = await safeFetchJson(`/api/v1/workflows/${workflow.id}/approve`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    operator_id: "admin_human",
                    notes: notes
                })
            });

            if (response.status || response.msg) {
                notification.success({
                    message: "Workflow Approved",
                    description: "The workflow has been authorized and re-queued for execution.",
                    placement: "topRight"
                });
                refetch();
            } else {
                notification.error({
                    message: "Approval Failed",
                    description: "System rejected the approval request. Check backend logs.",
                });
            }
        } catch (err: any) {
            notification.error({
                message: "Network Error",
                description: err.message || "Failed to connect to the Mission Control API.",
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    const workflow = data?.data;

    // Loading state
    if (isLoading) return <Card loading />;

    // Error state
    if (isError || !workflow) return (
        <Alert
            message="Error"
            description="Workflow not found or failed to load."
            type="error"
            showIcon
            action={
                <Button size="small" type="primary" onClick={() => list("workflows")}>
                    Return to Feed
                </Button>
            }
        />
    );

    const getStatusTag = (status: string) => {
        const s = status.toUpperCase();
        switch (s) {
            case "RUNNING": return <Tag icon={<SyncOutlined spin />} color="processing">RUNNING</Tag>;
            case "COMPLETED": return <Tag icon={<CheckCircleOutlined />} color="success">COMPLETED</Tag>;
            case "FAILED": return <Tag icon={<ExclamationCircleOutlined />} color="error">FAILED</Tag>;
            case "ERROR": return <Tag icon={<ExclamationCircleOutlined />} color="error">ERROR</Tag>;
            case "WAITING_APPROVAL":
            case "PENDING_APPROVAL":
                return <Tag icon={<ClockCircleOutlined />} color="warning">WAITING APPROVAL</Tag>;
            default: return <Tag color="default">{s}</Tag>;
        }
    };

    return (
        <div style={{ padding: "24px" }}>
            <Button 
                icon={<ArrowLeftOutlined />} 
                onClick={() => list("workflows")} 
                style={{ marginBottom: "16px", background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "#aaa" }}
            >
                Back to Mission Feed
            </Button>

            {/* PREMIUM HEADER BAND */}
            <Card variant="borderless" style={{ background: "linear-gradient(90deg, rgba(10,12,18,0.8) 0%, rgba(20,25,35,0.4) 100%)", borderRadius: "12px", border: "1px solid rgba(102, 252, 241, 0.15)", marginBottom: "20px" }}>
                <Row gutter={16} align="middle">
                    <Col span={8}>
                        <div style={{ paddingLeft: "10px" }}>
                            <Text type="secondary" style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>Operational Workflow</Text>
                            <Title level={3} style={{ color: "#fff", margin: 0, fontWeight: 900 }}>{workflow.name || "Unnamed Sequence"}</Title>
                            <Space style={{ marginTop: "4px" }}>
                                {getStatusTag(workflow.status)}
                                <Text type="secondary" style={{ fontSize: "11px", fontFamily: "monospace" }}>#{workflow.id.substring(0,8)}</Text>
                            </Space>
                        </div>
                    </Col>
                    <Col span={4}>
                        <Statistic 
                            title={<span style={{ color: "#45a29e", fontSize: "10px" }}>SOURCE</span>}
                            value={workflow.source?.toUpperCase() || 'MANUAL'}
                            valueStyle={{ color: "#fff", fontSize: "18px", fontWeight: "bold" }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic 
                            title={<span style={{ color: "#45a29e", fontSize: "10px" }}>CREATED AT</span>}
                            value={new Date(workflow.created_at).toLocaleTimeString()}
                            valueStyle={{ color: "#aaa", fontSize: "16px", fontFamily: "monospace" }}
                        />
                    </Col>
                    <Col span={8} style={{ textAlign: "right" }}>
                        <Space>
                            <Button icon={<BranchesOutlined />} onClick={() => window.open('/governance-lineage', '_blank')} style={{ background: "rgba(102, 252, 241, 0.1)", color: "#66fcf1", border: "1px solid rgba(102, 252, 241, 0.3)" }}>View Lineage</Button>
                        </Space>
                    </Col>
                </Row>
            </Card>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 400px", gap: "24px" }}>
                <div>
                    <Card variant="borderless" className="glass-card" style={{ background: "rgba(11, 12, 16, 0.6)", backdropFilter: "blur(20px)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px", marginBottom: "24px" }}>
                        <Title level={5} style={{ color: "#66fcf1" }}>Internal Configuration</Title>
                        <pre style={{ background: "rgba(0,0,0,0.5)", padding: "16px", borderRadius: "12px", border: "1px solid rgba(69, 162, 158, 0.1)", color: "#c5c6c7", overflowX: "auto" }}>
                            {JSON.stringify(workflow.payload, null, 2)}
                        </pre>
                    </Card>

                    {/* Step History */}
                    <Card variant="borderless" className="glass-card" style={{ background: "rgba(11, 12, 16, 0.4)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px" }}>
                        <Title level={5} style={{ color: "#fff", marginBottom: "24px" }}>Evolution Steps</Title>
                        <Steps
                            direction="vertical"
                            current={workflow.history?.length || 0}
                            items={(workflow.history || []).map((h: any, i: number) => ({
                                title: <span style={{ color: "#fff" }}>{h.step}</span>,
                                description: (
                                    <div style={{ color: "#aaa", fontSize: "12px" }}>
                                        {h.details || h.msg || "Executing autonomous sub-task..."}
                                        <div style={{ marginTop: "4px", opacity: 0.6 }}>{new Date(h.timestamp).toLocaleString()}</div>
                                    </div>
                                ),
                                status: i === (workflow.history?.length - 1) ? "process" : "finish"
                            }))}
                        />
                    </Card>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    {/* Governance Context Panel */}
                    <Card variant="borderless" className="glass-card" style={{ background: "linear-gradient(135deg, rgba(11,12,16,0.6) 0%, rgba(20,25,35,0.4) 100%)", border: "1px solid rgba(102, 252, 241, 0.1)", borderRadius: "16px" }}>
                        <Title level={5} style={{ color: "#66fcf1", display: "flex", alignItems: "center", gap: "8px" }}>
                            <SafetyOutlined /> Governance Context
                        </Title>
                        <Divider style={{ borderColor: "rgba(255,255,255,0.05)", margin: "12px 0" }} />
                        
                        <Space direction="vertical" style={{ width: "100%" }} size="large">
                            {/* Related Approvals */}
                            <div>
                                <Text strong style={{ color: "#45a29e", fontSize: "11px", textTransform: "uppercase" }}>Pending Quorum Requests</Text>
                                {(workflow.related_approvals && workflow.related_approvals.length > 0) ? (
                                    <List
                                        size="small"
                                        dataSource={workflow.related_approvals}
                                        renderItem={(item: any) => (
                                            <List.Item 
                                                actions={[<Button size="small" type="link" onClick={() => window.open(`/approvals/${item.id}`, '_blank')}>VIEW</Button>]}
                                                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
                                            >
                                                <List.Item.Meta
                                                    title={<Text style={{ color: "#fff", fontSize: "13px" }}>{item.request_type}</Text>}
                                                    description={<Tag color={item.status === 'APPROVED' ? 'success' : 'warning'}>{item.status}</Tag>}
                                                />
                                            </List.Item>
                                        )}
                                    />
                                ) : (
                                    <Paragraph style={{ color: "#666", fontSize: "12px", marginTop: "8px" }}>No active approval blocks detected.</Paragraph>
                                )}
                            </div>

                            {/* Related Incidents */}
                            <div>
                                <Text strong style={{ color: "#ff4d4f", fontSize: "11px", textTransform: "uppercase" }}>Operational Anomaly Logs</Text>
                                {(workflow.related_incidents && workflow.related_incidents.length > 0) ? (
                                    <List
                                        size="small"
                                        dataSource={workflow.related_incidents}
                                        renderItem={(item: any) => (
                                            <List.Item 
                                                actions={[<Button size="small" type="link" danger onClick={() => window.open(`/incidents/${item.id}`, '_blank')}>DEBUG</Button>]}
                                                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
                                            >
                                                <List.Item.Meta
                                                    title={<Text style={{ color: "#fff", fontSize: "13px" }}>{item.incident_type}</Text>}
                                                    description={<Tag color="error">{item.severity}</Tag>}
                                                />
                                            </List.Item>
                                        )}
                                    />
                                ) : (
                                    <Paragraph style={{ color: "#666", fontSize: "12px", marginTop: "8px" }}>Environment state nominal (no anomalies).</Paragraph>
                                )}
                            </div>
                        </Space>
                    </Card>

                    {/* Manual Approval Action (Only if waiting) */}
                    {(workflow.status?.toLowerCase() === 'waiting_approval' || workflow.status?.toLowerCase() === 'pending_approval') && (
                        <Card variant="borderless" style={{ background: "rgba(102, 252, 241, 0.05)", border: "1px dashed #66fcf1", borderRadius: "16px" }}>
                            <Title level={5} style={{ color: "#66fcf1" }}>Action Required</Title>
                            <Paragraph style={{ color: "#c5c6c7", fontSize: "13px" }}>
                                This workflow is currently suspended awaiting institutional sign-off.
                            </Paragraph>
                            <Space direction="vertical" style={{ width: "100%" }}>
                                <Input.TextArea 
                                    id="approval-notes"
                                    placeholder="Enter decision rationale for the audit ledger..." 
                                    rows={3} 
                                    style={{ background: "rgba(0,0,0,0.2)", color: "#fff", border: "1px solid rgba(102,252,241,0.2)" }}
                                />
                                <Button 
                                    type="primary" 
                                    icon={<RocketOutlined />} 
                                    block 
                                    style={{ background: "#66fcf1", color: "#060a12", fontWeight: "bold", border: "none" }}
                                    onClick={handleApprove}
                                    loading={isSubmitting}
                                >
                                    AUTHORIZE & RESUME
                                </Button>
                            </Space>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}
