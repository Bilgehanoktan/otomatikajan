"use client";

import React from "react";
import { useShow } from "@refinedev/core";
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
    Empty
} from "antd";

// Use direct imports for Ant Design Icons to avoid build resolution issues
import PlayCircleOutlined from "@ant-design/icons/lib/icons/PlayCircleOutlined";
import CheckCircleOutlined from "@ant-design/icons/lib/icons/CheckCircleOutlined";
import SyncOutlined from "@ant-design/icons/lib/icons/SyncOutlined";
import ExclamationCircleOutlined from "@ant-design/icons/lib/icons/ExclamationCircleOutlined";
import ClockCircleOutlined from "@ant-design/icons/lib/icons/ClockCircleOutlined";
import ArrowLeftOutlined from "@ant-design/icons/lib/icons/ArrowLeftOutlined";
import RocketOutlined from "@ant-design/icons/lib/icons/RocketOutlined";

const { Title, Text, Paragraph } = Typography;

export default function WorkflowDetailClient() {
    const { query: { data, isLoading, isError } } = useShow({
        resource: "workflows",
    });

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
        />
    );

    const getStatusTag = (status: string) => {
        switch (status) {
            case "RUNNING": return <Tag icon={<SyncOutlined spin />} color="processing">RUNNING</Tag>;
            case "COMPLETED": return <Tag icon={<CheckCircleOutlined />} color="success">COMPLETED</Tag>;
            case "FAILED": return <Tag icon={<ExclamationCircleOutlined />} color="error">FAILED</Tag>;
            default: return <Tag>{status}</Tag>;
        }
    };

    return (
        <div style={{ padding: "24px" }}>
            <Button 
                icon={<ArrowLeftOutlined />} 
                onClick={() => window.history.back()} 
                style={{ marginBottom: "16px" }}
                className="hover-effect"
            >
                Back to Workflows
            </Button>
            
            <Card bordered={false} className="glass-card" style={{ background: "rgba(11, 12, 16, 0.6)", backdropFilter: "blur(20px)", border: "1px solid rgba(102, 252, 241, 0.1)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                        <Title level={4} style={{ color: "#66fcf1", margin: 0 }}>
                            <RocketOutlined /> {workflow.workflow_type}
                        </Title>
                        <Text type="secondary" style={{ fontSize: "12px" }}>ID: {workflow.id}</Text>
                    </div>
                    {getStatusTag(workflow.status)}
                </div>

                <Divider style={{ borderColor: "rgba(255,255,255,0.05)" }} />

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
                    <div>
                        <Title level={5} style={{ color: "#45a29e" }}>Description</Title>
                        <Paragraph style={{ color: "#c5c6c7" }}>
                            {workflow.description || "No description provided."}
                        </Paragraph>
                        
                        <Title level={5} style={{ color: "#45a29e" }}>Timeline</Title>
                        <Space direction="vertical">
                            <Text style={{ color: "#c5c6c7" }}><ClockCircleOutlined /> Started: {workflow.started_at ? new Date(workflow.started_at).toLocaleString() : "N/A"}</Text>
                            {workflow.completed_at && (
                                <Text style={{ color: "#c5c6c7" }}><CheckCircleOutlined /> Completed: {new Date(workflow.completed_at).toLocaleString()}</Text>
                            )}
                        </Space>
                    </div>

                    <div>
                        <Title level={5} style={{ color: "#45a29e" }}>Execution Progress</Title>
                        <Steps
                            direction="vertical"
                            size="small"
                            current={workflow.current_step_index || 0}
                            items={(workflow.steps || []).map((step: any, index: number) => ({
                                title: <span style={{ color: index <= (workflow.current_step_index || 0) ? "#fff" : "#666" }}>{step.name}</span>,
                                description: <span style={{ color: "#45a29e" }}>{step.status}</span>,
                                status: index < (workflow.current_step_index || 0) ? "finish" : 
                                       index === (workflow.current_step_index || 0) ? "process" : "wait"
                            }))}
                        />
                    </div>
                </div>

                <Divider style={{ borderColor: "rgba(255,255,255,0.05)" }} />

                <Title level={5} style={{ color: "#45a29e" }}>Artifacts & Results</Title>
                {workflow.artifacts && Object.keys(workflow.artifacts).length > 0 ? (
                    <List
                        size="small"
                        dataSource={Object.entries(workflow.artifacts)}
                        renderItem={([key, value]: [string, any]) => (
                            <List.Item style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                                <Text strong style={{ color: "#66fcf1" }}>{key}:</Text> <Text code style={{ background: "rgba(31, 40, 51, 0.5)", color: "#c5c6c7", border: "none" }}>{JSON.stringify(value)}</Text>
                            </List.Item>
                        )}
                    />
                ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span style={{ color: "#45a29e" }}>No artifacts generated yet.</span>} />
                )}
            </Card>
        </div>
    );
}
