"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Card, Button, Space, Typography, Tag, Select, InputNumber, Alert, Modal, Input } from "antd";
import { RocketOutlined, PauseCircleOutlined, PlayCircleOutlined, StopOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { safeFetchJson } from "@/lib/api";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

export const PilotModePanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [isStartModalVisible, setIsStartModalVisible] = useState(false);
    const [startForm, setStartForm] = useState({ name: "Q2_UI_Repair_Pilot", mode: "GOVERNED_REPAIR", duration: 7 });

    const fetchStatus = async () => {
        try {
            const data = await safeFetchJson("/api/v1/ui-repair/pilot/status");
            setStatus(data);
        } catch (e) {
            console.error("Failed to fetch pilot status", e);
        }
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    const handleStart = async () => {
        setLoading(true);
        try {
            await safeFetchJson(`/api/v1/ui-repair/pilot/start?name=${startForm.name}&mode=${startForm.mode}&duration=${startForm.duration}`, { method: "POST" });
            await fetchStatus();
            setIsStartModalVisible(false);
        } finally {
            setLoading(false);
        }
    };

    const handlePause = async () => {
        if (!status) return;
        setLoading(true);
        try {
            await safeFetchJson(`/api/v1/ui-repair/pilot/pause?rollout_id=${status.id}&rationale=Manual_Operator_Pause`, { method: "POST" });
            await fetchStatus();
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (s: string) => {
        switch (s) {
            case "RUNNING": return "green";
            case "PAUSED": return "orange";
            case "COMPLETED": return "blue";
            default: return "default";
        }
    };

    return (
        <Card title={<Space><RocketOutlined /> {t("pilot_rollout")}</Space>} extra={
            status?.status === "RUNNING" ? (
                <Button icon={<PauseCircleOutlined />} onClick={handlePause} loading={loading}>Pause Pilot</Button>
            ) : status?.status === "PAUSED" ? (
                <Button type="primary" icon={<PlayCircleOutlined />} loading={loading}>Resume Pilot</Button>
            ) : (
                <Button type="primary" icon={<RocketOutlined />} onClick={() => setIsStartModalVisible(true)}>Start Pilot</Button>
            )
        }>
            {status ? (
                <Space direction="vertical" style={{ width: "100%" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <Space direction="vertical" size={0}>
                            <Title level={4}>{status.name}</Title>
                            <Space>
                                <Tag color={getStatusColor(status.status)}>{status.status}</Tag>
                                <Tag color="blue">{status.mode}</Tag>
                            </Space>
                        </Space>
                        <div style={{ textAlign: "right" }}>
                            <Text type="secondary">Started: {new Date(status.started_at).toLocaleString()}</Text>
                            <br />
                            <Text strong>Duration: {status.duration_days} Days</Text>
                        </div>
                    </div>
                    
                    <Alert 
                        message="Governed Repair Active" 
                        description="System is monitoring and proposing patches. Apply operations require operator rationale." 
                        type="info" 
                        showIcon 
                        icon={<SafetyCertificateOutlined />}
                    />
                </Space>
            ) : (
                <div style={{ textAlign: "center", padding: "20px" }}>
                    <Paragraph type="secondary">No active pilot rollout. Start a pilot to begin live shadow monitoring.</Paragraph>
                </div>
            )}

            <Modal 
                title="Configure Pilot Rollout" 
                open={isStartModalVisible} 
                onOk={handleStart} 
                onCancel={() => setIsStartModalVisible(false)}
                confirmLoading={loading}
            >
                <Space direction="vertical" style={{ width: "100%" }} size="middle">
                    <div>
                        <Text strong>Pilot Name</Text>
                        <Input value={startForm.name} onChange={e => setStartForm({...startForm, name: e.target.value})} />
                    </div>
                    <div>
                        <Text strong>Pilot Mode</Text>
                        <Select 
                            style={{ width: "100%" }} 
                            value={startForm.mode} 
                            onChange={v => setStartForm({...startForm, mode: v})}
                            options={[
                                { label: "Shadow Only", value: "SHADOW_ONLY" },
                                { label: "Assisted Repair", value: "ASSISTED_REPAIR" },
                                { label: "Governed Repair", value: "GOVERNED_REPAIR" },
                                { label: "Limited Production", value: "LIMITED_PRODUCTION" },
                            ]}
                        />
                    </div>
                    <div>
                        <Text strong>Duration (Days)</Text>
                        <br />
                        <InputNumber min={1} max={30} value={startForm.duration} onChange={v => setStartForm({...startForm, duration: v || 7})} />
                    </div>
                </Space>
            </Modal>
        </Card>
    );
};
