"use client";

import React, { useState } from "react";
import { useParams } from "next/navigation";
import { 
    Card, 
    Typography, 
    Divider, 
    Tag, 
    List, 
    Button, 
    Space, 
    Alert,
    Input,
    App,
    Row,
    Col,
    Statistic,
    Timeline
} from "antd";
import { useShow } from "@refinedev/core";

import CheckCircleOutlined from "@ant-design/icons/lib/icons/CheckCircleOutlined";
import SyncOutlined from "@ant-design/icons/lib/icons/SyncOutlined";
import ArrowLeftOutlined from "@ant-design/icons/lib/icons/ArrowLeftOutlined";
import SafetyCertificateOutlined from "@ant-design/icons/lib/icons/SafetyCertificateOutlined";
import StopOutlined from "@ant-design/icons/lib/icons/StopOutlined";
import BranchesOutlined from "@ant-design/icons/lib/icons/BranchesOutlined";
import SafetyOutlined from "@ant-design/icons/lib/icons/SafetyOutlined";
import NodeIndexOutlined from "@ant-design/icons/lib/icons/NodeIndexOutlined";
import ExclamationCircleOutlined from "@ant-design/icons/lib/icons/ExclamationCircleOutlined";
import ClockCircleOutlined from "@ant-design/icons/lib/icons/ClockCircleOutlined";
import HistoryOutlined from "@ant-design/icons/lib/icons/HistoryOutlined";
import DeploymentUnitOutlined from "@ant-design/icons/lib/icons/DeploymentUnitOutlined";
import { safeFetchJson } from "@/lib/api";
import { getAuthHeaders } from "@/lib/auth";

const { Title, Text, Paragraph } = Typography;

export default function ApprovalDetailClient() {
    const { notification } = App.useApp();
    const params = useParams<{ id?: string | string[] }>();
    const approvalId = Array.isArray(params?.id) ? params.id[0] : params?.id;
    const showResult = useShow({
        resource: "governance/approvals",
        id: approvalId,
        queryOptions: {
            enabled: Boolean(approvalId),
        },
    });
    const { query: { data, isLoading, isError, refetch } } = showResult as any;

    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleDecision = async (decision: "approved" | "rejected") => {
        const comment = (document.getElementById("approval-comment") as HTMLTextAreaElement)?.value || `Manually ${decision}`;
        setIsSubmitting(true);
        try {
            if (!approval) return;
            const authHeaders = await getAuthHeaders();
            const response: any = await safeFetchJson(`/api/v1/governance/approvals/${approval.id}/decide`, {
                method: "POST",
                headers: authHeaders,
                body: JSON.stringify({
                    approve: decision === "approved",
                    reason: comment,
                    decided_by: "admin_human"
                })
            });

            if (response.status || response.decided_at) {
                notification.success({
                    message: `Approval ${decision === "approved" ? "Granted" : "Rejected"}`,
                    description: `The request has been ${decision} and sealed in lineage ${response.lineage_id?.substring(0,8) || ''}.`,
                    placement: "topRight"
                });
                refetch();
            } else {
                notification.error({
                    message: "Action Failed",
                    description: "System could not process the decision. Check backend logs.",
                });
            }
        } catch (err: any) {
            notification.error({
                message: "Network Error",
                description: (err as any).message || "Failed to connect to the Mission Control API.",
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    const approval = data?.data;

    if (isLoading) return <Card loading />;

    if (isError || !approval) return (
        <Alert
            message="Error"
            description="Approval request not found or failed to load. The record may have been archived."
            type="error"
            showIcon
            action={
                <Button size="small" type="primary" onClick={() => window.history.back()}>
                    Return to List
                </Button>
            }
        />
    );

    const getStatusTag = (status: string) => {
        const s = status.toUpperCase();
        switch (s) {
            case "PENDING": return <Tag icon={<SyncOutlined spin />} color="processing">PENDING</Tag>;
            case "APPROVED": return <Tag icon={<CheckCircleOutlined />} color="success">APPROVED</Tag>;
            case "REJECTED": return <Tag icon={<ExclamationCircleOutlined />} color="error">REJECTED</Tag>;
            default: return <Tag color="default">{s}</Tag>;
        }
    };

    return (
        <div style={{ padding: "24px" }}>
            <Button 
                icon={<ArrowLeftOutlined />} 
                onClick={() => window.history.back()} 
                style={{ marginBottom: "16px", background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "#aaa" }}
                className="hover-effect"
            >
                Back to Quorum Center
            </Button>
            
            {/* PREMIUM HEADER BAND */}
            <Card variant="borderless" style={{ background: "linear-gradient(90deg, rgba(10,12,18,0.8) 0%, rgba(20,25,35,0.4) 100%)", borderRadius: "12px", border: "1px solid rgba(102, 252, 241, 0.15)", marginBottom: "20px" }}>
                <Row gutter={16} align="middle">
                    <Col span={8}>
                        <div style={{ paddingLeft: "10px" }}>
                            <Text type="secondary" style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>Decision Gate</Text>
                            <Title level={3} style={{ color: "#fff", margin: 0, fontWeight: 900 }}>{approval.request_type}</Title>
                            <Space style={{ marginTop: "4px" }}>
                                {getStatusTag(approval.status)}
                                <Text type="secondary" style={{ fontSize: "11px", fontFamily: "monospace" }}>#{approval.id?.toString().substring(0,8)}</Text>
                            </Space>
                        </div>
                    </Col>
                    <Col span={4}>
                        <Statistic 
                            title={<span style={{ color: "#45a29e", fontSize: "10px" }}>RISK LEVEL</span>}
                            value={approval.request_type === 'AUTONOMY' ? 'HIGH' : 'MEDIUM'}
                            valueStyle={{ color: approval.request_type === 'AUTONOMY' ? '#ff4d4f' : '#66fcf1', fontSize: "18px", fontWeight: "bold" }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic 
                            title={<span style={{ color: "#45a29e", fontSize: "10px" }}>SOURCE PROJECT</span>}
                            value={approval.project_id?.toString().substring(0,8) || 'N/A'}
                            valueStyle={{ color: "#fff", fontSize: "18px", fontFamily: "monospace" }}
                        />
                    </Col>
                    <Col span={8} style={{ textAlign: "right" }}>
                        <Space>
                            <Button icon={<BranchesOutlined />} onClick={() => window.open('/governance/lineage', '_blank')} style={{ background: "rgba(102, 252, 241, 0.1)", color: "#66fcf1", border: "1px solid rgba(102, 252, 241, 0.3)" }}>Lineage Space</Button>
                            {approval?.project_id && (
                                <Button icon={<NodeIndexOutlined />} onClick={() => window.open(`/workflows/${approval.project_id}`, '_blank')} style={{ background: "rgba(255, 255, 255, 0.05)", color: "#c5c6c7", border: "1px solid rgba(255, 255, 255, 0.1)" }}>Workflow Detail</Button>
                            )}
                        </Space>
                    </Col>
                </Row>
            </Card>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "20px" }}>
                <Card variant="borderless" className="glass-card" style={{ background: "rgba(11, 12, 16, 0.6)", backdropFilter: "blur(20px)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px" }}>
                    <Title level={5} style={{ color: "#66fcf1", display: "flex", alignItems: "center", gap: "8px" }}>
                        <SafetyOutlined /> Rationale & Evidence
                    </Title>
                    <Paragraph style={{ color: "#c5c6c7", background: "rgba(0,0,0,0.2)", padding: "20px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.05)", fontSize: "15px", lineHeight: "1.6" }}>
                        {approval.reason || "No detailed rationale provided for this gate intervention."}
                    </Paragraph>
                    
                    {approval.payload && (
                        <div style={{ marginTop: "24px" }}>
                            <Title level={5} style={{ color: "#45a29e", fontSize: "13px" }}>Technical Context (JSON)</Title>
                            <pre style={{ background: "rgba(0,0,0,0.4)", padding: "16px", borderRadius: "8px", overflowX: "auto", border: "1px solid rgba(69, 162, 158, 0.1)", color: "#45a29e", fontSize: "11px", fontFamily: "monospace" }}>
                                {typeof approval.payload === 'string' ? approval.payload : JSON.stringify(approval.payload, null, 2)}
                            </pre>
                        </div>
                    )}

                    {approval.status?.toLowerCase() === "pending" && (
                        <>
                            <Divider style={{ borderColor: "rgba(255,255,255,0.05)" }} />
                            <div style={{ marginTop: "24px", padding: "20px", background: "rgba(102, 252, 241, 0.03)", borderRadius: "12px", border: "1px dashed rgba(102, 252, 241, 0.2)" }}>
                                <Title level={5} style={{ color: "#66fcf1" }}><DeploymentUnitOutlined /> Operator Intervention</Title>
                                <Space direction="vertical" style={{ width: "100%" }}>
                                    <Input.TextArea 
                                        placeholder="Enter mandatory audit notes describing the basis for this decision..." 
                                        rows={4} 
                                        style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", borderRadius: "8px" }}
                                        id="approval-comment"
                                    />
                                    <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
                                        <Button 
                                            type="primary" 
                                            icon={<CheckCircleOutlined />} 
                                            style={{ background: "#66fcf1", color: "#060a12", fontWeight: "bold", border: "none", height: "40px", padding: "0 24px" }}
                                            onClick={() => handleDecision("approved")}
                                            loading={isSubmitting}
                                        >
                                            APPROVE & SEAL
                                        </Button>
                                        <Button 
                                            danger 
                                            icon={<StopOutlined />} 
                                            style={{ height: "40px", padding: "0 24px" }}
                                            onClick={() => handleDecision("rejected")}
                                            loading={isSubmitting}
                                        >
                                            REJECT
                                        </Button>
                                    </div>
                                </Space>
                            </div>
                        </>
                    )}
                </Card>

                {/* HISTORY TIMELINE */}
                <Card variant="borderless" className="glass-card" style={{ background: "rgba(11, 12, 16, 0.4)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px" }}>
                    <Title level={5} style={{ color: "#fff", marginBottom: "24px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <HistoryOutlined /> Audit Timeline
                    </Title>
                    <Timeline
                        mode="left"
                        items={[
                            {
                                label: <Text style={{ color: "#45a29e", fontSize: "11px" }}>{new Date(approval.created_at).toLocaleTimeString()}</Text>,
                                children: (
                                    <div style={{ marginBottom: "10px" }}>
                                        <Text strong style={{ color: "#fff" }}>Request Initialized</Text>
                                        <br /><Text type="secondary" style={{ fontSize: "11px" }}>Triggered by Autonomous Agent</Text>
                                    </div>
                                ),
                                color: "#45a29e"
                            },
                            approval.decided_at && {
                                label: <Text style={{ color: approval.status === 'APPROVED' ? '#66fcf1' : '#ff4d4f', fontSize: "11px" }}>{new Date(approval.decided_at).toLocaleTimeString()}</Text>,
                                children: (
                                    <div>
                                        <Text strong style={{ color: "#fff" }}>Decision: {approval.status}</Text>
                                        <br /><Text type="secondary" style={{ fontSize: "11px" }}>By {approval.decided_by}</Text>
                                        {approval.comment && (
                                            <div style={{ marginTop: "6px", fontStyle: "italic", color: "#888", fontSize: "12px", borderLeft: "2px solid rgba(255,255,255,0.1)", paddingLeft: "8px" }}>
                                                "{approval.comment}"
                                            </div>
                                        )}
                                    </div>
                                ),
                                color: approval.status === 'APPROVED' ? '#66fcf1' : '#ff4d4f'
                            },
                            approval.status !== 'PENDING' && {
                                children: (
                                    <div>
                                        <Text strong style={{ color: "#aaa", fontSize: "12px" }}>Lineage Chain Sealed</Text>
                                    </div>
                                ),
                                color: "gray"
                            }
                        ].filter(Boolean) as any}
                    />
                </Card>
            </div>
        </div>
    );
}

