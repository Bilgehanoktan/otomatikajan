"use client";

import React from "react";
import { List, Table, Tag, Space, Card, Typography, Button, Modal, Form, Select, notification } from "antd";
import { useTable } from "@refinedev/antd";
import { useCustomMutation } from "@refinedev/core";
import dayjs from "dayjs";
import { 
    BugOutlined, 
    PlayCircleOutlined, 
    HistoryOutlined,
    ExperimentOutlined
} from "@ant-design/icons";

const { Title, Text } = Typography;

export default function GovernorDrillsPage() {
    const [isClient, setIsClient] = React.useState(false);
    const { tableProps, tableQuery } = useTable<any>({
        resource: "governance/governor/resilience/drills",
    });

    const { data, isLoading, refetch } = tableQuery;

    const { mutate } = useCustomMutation();

    const [isModalOpen, setIsModalOpen] = React.useState(false);
    const [form] = Form.useForm();

    React.useEffect(() => {
        setIsClient(true);
    }, []);

    const handleStartDrill = async (values: any) => {
        mutate({
            url: "/governance/governor/resilience/drills",
            method: "post",
            values,
        }, {
            onSuccess: () => {
                notification.success({ message: "Drill started successfully" });
                setIsModalOpen(false);
                form.resetFields();
                refetch();
            }
        });
    };

    const getStatusTag = (status: string) => {
        switch (status) {
            case "PASSED": return <Tag color="success">PASSED</Tag>;
            case "FAILED": return <Tag color="error">FAILED</Tag>;
            case "RUNNING": return <Tag color="processing" icon={<PlayCircleOutlined spin />}>RUNNING</Tag>;
            case "PLANNED": return <Tag color="default">PLANNED</Tag>;
            case "ABORTED": return <Tag color="warning">ABORTED</Tag>;
            default: return <Tag>{status}</Tag>;
        }
    };

    const columns = [
        {
            title: "Drill Type",
            dataIndex: "drill_type",
            key: "drill_type",
            render: (text: string) => <Tag icon={<BugOutlined />}>{text}</Tag>,
        },
        {
            title: "Target Domain",
            dataIndex: "target_domain",
            key: "target_domain",
            render: (text: string) => text ? <Text code>{text}</Text> : <Text type="secondary">ALL</Text>,
        },
        {
            title: "Status",
            dataIndex: "status",
            key: "status",
            render: (status: string) => getStatusTag(status),
        },
        {
            title: "Started",
            dataIndex: "started_at",
            key: "started_at",
            render: (date: string) => date ? dayjs(date).format("YYYY-MM-DD HH:mm:ss") : "-",
        },
        {
            title: "Duration",
            key: "duration",
            render: (_value: unknown, record: any) => {
                if (!record.started_at || !record.completed_at) return "-";
                const diff = new Date(record.completed_at).getTime() - new Date(record.started_at).getTime();
                return `${(diff / 1000).toFixed(2)}s`;
            }
        }
    ];

    if (!isClient) {
        return <div className="min-h-screen bg-[#060a12]" />;
    }

    return (
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                    <Title level={2}><ExperimentOutlined /> Chaos Engineering Lab</Title>
                    <Text type="secondary">Run controlled drills to verify system resilience and fail-safe policies.</Text>
                </div>
                <Button 
                    type="primary" 
                    icon={<PlayCircleOutlined />} 
                    onClick={() => setIsModalOpen(true)}
                    size="large"
                >
                    Start New Drill
                </Button>
            </div>

            <Card variant="borderless" title={<span><HistoryOutlined /> Drill History</span>}>
                <Table 
                    {...tableProps}
                    columns={columns} 
                    rowKey="id"
                />
            </Card>

            <Modal
                title="Execute Chaos Drill"
                open={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                onOk={() => form.submit()}
                okText="Run Scenario"
                forceRender={true}
            >
                <Form form={form} layout="vertical" onFinish={handleStartDrill}>
                    <Form.Item 
                        name="drill_type" 
                        label="Scenario Type" 
                        rules={[{ required: true }]}
                        initialValue="DOMAIN_TIMEOUT"
                    >
                        <Select options={[
                            { label: "Domain Timeout", value: "DOMAIN_TIMEOUT" },
                            { label: "Meta Timeout", value: "META_TIMEOUT" },
                            { label: "Conflict Storm", value: "CONFLICT_STORM" },
                            { label: "False Escalation Burst", value: "FALSE_ESCALATION_BURST" },
                            { label: "Replay Storm", value: "REPLAY_STORM" },
                            { label: "Policy Veto Flood", value: "POLICY_VETO_FLOOD" },
                        ]} />
                    </Form.Item>
                    <Form.Item name="target_domain" label="Target Domain (Optional)">
                        <Select allowClear options={[
                            { label: "Workflow", value: "WORKFLOW" },
                            { label: "Incident", value: "INCIDENT" },
                            { label: "Policy", value: "POLICY" },
                            { label: "Repair", value: "REPAIR" },
                            { label: "Approval", value: "APPROVAL" },
                        ]} />
                    </Form.Item>
                </Form>
            </Modal>
        </Space>
    );
}
