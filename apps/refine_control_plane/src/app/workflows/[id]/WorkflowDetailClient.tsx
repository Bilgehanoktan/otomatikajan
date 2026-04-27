"use client";

import React, { useState, useEffect } from "react";
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
    App,
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
import ThunderboltOutlined from "@ant-design/icons/lib/icons/ThunderboltOutlined";
import { safeFetchJson } from "@/lib/api";

const { Title, Text, Paragraph } = Typography;

export default function WorkflowDetailClient() {
    const { notification } = App.useApp();
    const { list } = useNavigation();
    const { query: { data, isLoading, isError, refetch } } = useShow({
        resource: "workflows",
    });

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [autoRefresh, setAutoRefresh] = useState(true);

    const workflow = data?.data;

    // Auto-Refresh Logic for Running Workflows
    useEffect(() => {
        let interval: any;
        if (autoRefresh && workflow && (workflow.status === "RUNNING" || workflow.status === "WAITING_APPROVAL")) {
            interval = setInterval(() => {
                refetch();
            }, 5000); // 5s refresh interval
        }
        return () => clearInterval(interval);
    }, [autoRefresh, workflow?.status, refetch]);

    const handleApprove = async () => {
        const notes = (document.getElementById("approval-notes") as HTMLTextAreaElement)?.value || "";
        setIsSubmitting(true);
        if (!workflow?.id) {
            notification.error({ message: "Error", description: "Workflow not found." });
            return;
        }

        try {
            const response = await safeFetchJson(`/api/v1/workflows/${workflow.id}/approve`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    operator_id: "admin_human",
                    notes: notes
                })
            });

            if (response.status === "success" || response.message || response.msg) {
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
        if (!status) return <Tag color="default">UNKNOWN</Tag>;
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

    const steps = workflow.steps || [];
    // Find the current active step index
    const currentStepIndex = steps.findIndex((s: any) => 
        s.status === "running" || s.status === "processing" || s.status === "pending" || s.status === "queued"
    );
    // If all are completed, current index is steps.length
    const activeIndex = currentStepIndex === -1 ? steps.length : currentStepIndex;

    return (
        <div style={{ padding: "24px", minHeight: "100%", backgroundColor: "#060a12", display: "flex", flexDirection: "column", gap: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px" }}>
                <Button 
                    icon={<ArrowLeftOutlined />} 
                    onClick={() => list("workflows")} 
                    style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "#aaa" }}
                >
                    Back to Mission Feed
                </Button>
                <Space>
                    {workflow.status === "RUNNING" && (
                        <Tag color="cyan" style={{ border: "1px solid rgba(102, 252, 241, 0.4)", background: "rgba(102, 252, 241, 0.05)" }}>
                           <SyncOutlined spin /> LIVE UPDATING
                        </Tag>
                    )}
                    <Button 
                       size="small" 
                       type={autoRefresh ? "primary" : "default"} 
                       onClick={() => setAutoRefresh(!autoRefresh)}
                       style={{ fontSize: "10px", height: "24px" }}
                    >
                        Auto-Sync: {autoRefresh ? "ON" : "OFF"}
                    </Button>
                </Space>
            </div>

            {/* PREMIUM HEADER BAND */}
            <Card variant="borderless" style={{ background: "linear-gradient(90deg, rgba(10,12,18,0.8) 0%, rgba(20,25,35,0.4) 100%)", borderRadius: "12px", border: "1px solid rgba(102, 252, 241, 0.15)", marginBottom: "20px" }}>
                <Row gutter={16} align="middle">
                    <Col span={8}>
                        <div style={{ paddingLeft: "10px" }}>
                            <Text type="secondary" style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>Operational Workflow</Text>
                            <Title level={3} style={{ color: "#fff", margin: 0, fontWeight: 900 }}>{workflow.name || "Unnamed Sequence"}</Title>
                            <Space style={{ marginTop: "4px" }}>
                                {getStatusTag(workflow.status)}
                                <Text type="secondary" style={{ fontSize: "11px", fontFamily: "monospace" }}>#{String(workflow.id).substring(0,8)}</Text>
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
                            title={<span style={{ color: "#45a29e", fontSize: "10px" }}>TYPE</span>}
                            value={workflow.workflow_type?.toUpperCase() || 'GENERIC'}
                            valueStyle={{ color: "#66fcf1", fontSize: "18px", fontWeight: "bold" }}
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
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    {/* Execution Plan View */}
                    <Card 
                        variant="borderless" 
                        className="glass-card" 
                        style={{ background: "rgba(11, 12, 16, 0.6)", backdropFilter: "blur(20px)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px" }}
                        title={<span style={{ color: "#fff", fontSize: "14px", fontWeight: "bold", textTransform: "uppercase", letterSpacing: "1px" }}><ThunderboltOutlined style={{ color: "#66fcf1" }} /> Execution Plan</span>}
                    >
                        {steps.length === 0 ? (
                            <Empty description={<span style={{ color: "#666" }}>No execution steps defined.</span>} />
                        ) : (
                            <Steps
                                direction="vertical"
                                current={activeIndex}
                                items={steps.map((s: any, i: number) => {
                                    const isCurrent = i === activeIndex;
                                    const isError = s.status === "failed" || s.status === "error";
                                    const isFinished = s.status === "completed" || s.status === "success";
                                    
                                    return {
                                        title: (
                                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                                <span style={{ color: isCurrent ? "#66fcf1" : isError ? "#f5222d" : "#fff", fontWeight: isCurrent ? "900" : "bold" }}>
                                                    {s.name}
                                                </span>
                                                <Tag color={isFinished ? "green" : isError ? "red" : isCurrent ? "blue" : "default"} style={{ fontSize: "9px", borderRadius: "4px" }}>
                                                    {s.status.toUpperCase()}
                                                </Tag>
                                            </div>
                                        ),
                                        description: (
                                            <div style={{ marginTop: "8px", padding: "12px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "8px" }}>
                                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                                                    <Text type="secondary" style={{ fontSize: "11px", color: "#666" }}>Action: <span style={{ color: "#aaa" }}>{s.action}</span></Text>
                                                    {s.completed_at && <Text type="secondary" style={{ fontSize: "10px" }}>{new Date(s.completed_at).toLocaleTimeString()}</Text>}
                                                </div>
                                                
                                                {s.output_summary && (
                                                    <Paragraph style={{ color: "#45a29e", fontSize: "12px", background: "rgba(69,162,158,0.05)", padding: "8px", borderRadius: "4px", margin: 0 }}>
                                                        <Text strong style={{ color: "#66fcf1", fontSize: "10px", display: "block", marginBottom: "4px" }}>OUTPUT SUMMARY</Text>
                                                        {s.output_summary}
                                                    </Paragraph>
                                                )}

                                                {s.error && (
                                                    <Alert
                                                        type="error"
                                                        message={<span style={{ fontSize: "11px", fontWeight: "bold" }}>FAILURE DETECTED</span>}
                                                        description={<span style={{ fontSize: "11px", fontFamily: "monospace" }}>{s.error}</span>}
                                                        style={{ marginTop: "8px", border: "none", background: "rgba(245,34,45,0.1)" }}
                                                    />
                                                )}
                                            </div>
                                        ),
                                        icon: isCurrent && s.status === "running" ? <SyncOutlined spin style={{ color: "#66fcf1" }} /> : undefined,
                                        status: isError ? "error" : isFinished ? "finish" : isCurrent ? "process" : "wait"
                                    };
                                })}
                            />
                        )}
                    </Card>

                    {/* Technical Payload (JSON) */}
                    <Card variant="borderless" className="glass-card" style={{ background: "rgba(11, 12, 16, 0.4)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px" }}>
                        <Title level={5} style={{ color: "#45a29e", fontSize: "12px", textTransform: "uppercase" }}>Core Context Payload</Title>
                        <pre style={{ background: "rgba(0,0,0,0.5)", padding: "16px", borderRadius: "12px", border: "1px solid rgba(69, 162, 158, 0.1)", color: "#c5c6c7", overflowX: "auto", fontSize: "11px", fontFamily: "monospace" }}>
                            {JSON.stringify(workflow.payload, null, 2)}
                        </pre>
                    </Card>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    {/* Manual Approval Action */}
                    {(workflow.status?.toLowerCase() === 'waiting_approval' || workflow.status?.toLowerCase() === 'pending_approval') && (
                        <Card variant="borderless" style={{ background: "rgba(102, 252, 241, 0.05)", border: "1px dashed #66fcf1", borderRadius: "16px" }}>
                            <Title level={5} style={{ color: "#66fcf1" }}>Action Required</Title>
                            <Paragraph style={{ color: "#c5c6c7", fontSize: "13px" }}>
                                This mission is currently suspended awaiting institutional authorization. Enter rationale and sign-off to proceed.
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

                    {/* Governance Context Panel */}
                    <Card variant="borderless" className="glass-card" style={{ background: "linear-gradient(135deg, rgba(11,12,16,0.6) 0%, rgba(20,25,35,0.4) 100%)", border: "1px solid rgba(102, 252, 241, 0.1)", borderRadius: "16px" }}>
                        <Title level={5} style={{ color: "#66fcf1", fontSize: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
                            <SafetyOutlined /> Governance Integrity
                        </Title>
                        <Divider style={{ borderColor: "rgba(255,255,255,0.05)", margin: "12px 0" }} />
                        
                        <Space direction="vertical" style={{ width: "100%" }} size="large">
                            {/* Related Approvals */}
                            <div>
                                <Text strong style={{ color: "#45a29e", fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>QUORUM REQUESTS</Text>
                                {(workflow.related_approvals && workflow.related_approvals.length > 0) ? (
                                    <List
                                        size="small"
                                        dataSource={workflow.related_approvals}
                                        renderItem={(item: any) => (
                                            <List.Item 
                                                actions={[<Button key="view-approval" size="small" type="link" onClick={() => window.open(`/approvals/${item.id}`, '_blank')}>VIEW</Button>]}
                                                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", padding: "8px 0" }}
                                            >
                                                <List.Item.Meta
                                                    title={<Text style={{ color: "#fff", fontSize: "12px" }}>{item.request_type}</Text>}
                                                    description={<Tag color={item.status === 'APPROVED' ? 'success' : 'warning'} style={{ fontSize: "9px" }}>{item.status}</Tag>}
                                                />
                                            </List.Item>
                                        )}
                                    />
                                ) : (
                                    <Paragraph style={{ color: "#555", fontSize: "11px", marginTop: "12px", fontStyle: "italic" }}>No blocking approvals.</Paragraph>
                                )}
                            </div>

                            {/* Related Incidents */}
                            <div>
                                <Text strong style={{ color: "#ff4d4f", fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>ANOMALY LOGS</Text>
                                {(workflow.related_incidents && workflow.related_incidents.length > 0) ? (
                                    <List
                                        size="small"
                                        dataSource={workflow.related_incidents}
                                        renderItem={(item: any) => (
                                            <List.Item 
                                                actions={[<Button key="debug-incident" size="small" type="link" danger onClick={() => window.open(`/incidents/${item.id}`, '_blank')}>DEBUG</Button>]}
                                                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", padding: "8px 0" }}
                                            >
                                                <List.Item.Meta
                                                    title={<Text style={{ color: "#fff", fontSize: "12px" }}>{item.incident_type}</Text>}
                                                    description={<Tag color="error" style={{ fontSize: "9px" }}>{item.severity} SEVERITY</Tag>}
                                                />
                                            </List.Item>
                                        )}
                                    />
                                ) : (
                                    <Paragraph style={{ color: "#555", fontSize: "11px", marginTop: "12px", fontStyle: "italic" }}>Environment state nominal.</Paragraph>
                                )}
                            </div>
                        </Space>
                    </Card>
                </div>
            </div>
        </div>
    );
}


