"use client";

import React, { useState, useEffect } from "react";
import { Card, Steps, Typography, Space, Badge, List, Tag } from "antd";
import { EyeOutlined, SearchOutlined, BuildOutlined, CheckCircleOutlined, LockOutlined } from "@ant-design/icons";

const { Text } = Typography;

export const ShadowModeStatusPanel: React.FC = () => {
    const [currentStep, setCurrentStep] = useState(0);

    // Simulated live progress for demo
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentStep(prev => (prev + 1) % 5);
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    const steps = [
        { title: "Observing", icon: <EyeOutlined />, description: "Live monitoring active" },
        { title: "Diagnosing", icon: <SearchOutlined />, description: "Analyzing route health" },
        { title: "Proposing", icon: <BuildOutlined />, description: "Generating shadow patch" },
        { title: "Reviewing", icon: <CheckCircleOutlined />, description: "PR-Agent & Verifier" },
        { title: "Gated", icon: <LockOutlined />, description: "Awaiting Operator" },
    ];

    return (
        <Card title="Live Shadow Pipeline" size="small">
            <Steps
                direction="vertical"
                size="small"
                current={currentStep}
                items={steps}
                style={{ padding: "12px 0" }}
            />
            
            <div style={{ marginTop: "16px", borderTop: "1px solid #f0f0f0", paddingTop: "12px" }}>
                <Text strong>Active Observables:</Text>
                <List
                    size="small"
                    dataSource={["/dashboard", "/profile", "/settings"]}
                    renderItem={item => (
                        <List.Item style={{ padding: "4px 0" }}>
                            <Space size="small">
                                <Badge status="processing" />
                                <Text code>{item}</Text>
                                <Tag color="cyan" style={{ fontSize: "10px" }}>SCANNING</Tag>
                            </Space>
                        </List.Item>
                    )}
                />
            </div>
        </Card>
    );
};
