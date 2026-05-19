"use client";

import React, { useState, useEffect } from "react";
import { Card, Row, Col, Statistic, Progress, Typography, Space, Tooltip } from "antd";
import { safeFetchJson } from "@/lib/api";
import { 
    DashboardOutlined, 
    BugOutlined, 
    SafetyOutlined, 
    ClockCircleOutlined, 
    UserOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined
} from "@ant-design/icons";

const { Title, Text } = Typography;

export const PilotMetricsPanel: React.FC<{ rolloutId?: string }> = ({ rolloutId }) => {
    const [metrics, setMetrics] = useState<any>(null);

    useEffect(() => {
        if (rolloutId) {
            safeFetchJson(`/api/v1/ui-repair/pilot/metrics/${rolloutId}`)
                .then(data => setMetrics(data))
                .catch(err => console.error("Failed to fetch pilot metrics", err));
        }
    }, [rolloutId]);

    // Simulated data for demo if no rollout active
    const displayMetrics = metrics || {
        monitoring_runs: 142,
        failures_detected: 8,
        prs_created: 5,
        approved_applies: 3,
        false_positive_count: 1,
        false_negative_count: 0,
        avg_mttr_s: 420,
        avg_governance_latency_s: 1800,
        operator_actions_count: 12
    };

    return (
        <Card title="Pilot Performance Metrics" size="small">
            <Row gutter={[16, 16]}>
                <Col span={6}>
                    <Statistic title="Monitoring Runs" value={displayMetrics.monitoring_runs} prefix={<DashboardOutlined />} />
                </Col>
                <Col span={6}>
                    <Statistic title="Failures Detected" value={displayMetrics.failures_detected} prefix={<BugOutlined />} valueStyle={{ color: '#cf1322' }} />
                </Col>
                <Col span={6}>
                    <Statistic title="Shadow PRs" value={displayMetrics.prs_created} prefix={<SafetyOutlined />} />
                </Col>
                <Col span={6}>
                    <Statistic title="Approvals" value={displayMetrics.approved_applies} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#3f8600' }} />
                </Col>
            </Row>

            <div style={{ marginTop: "24px" }}>
                <Row gutter={24}>
                    <Col span={12}>
                        <Title level={5}>Safety Efficiency</Title>
                        <Space direction="vertical" style={{ width: "100%" }}>
                            <div>
                                <Text type="secondary">False Positive Rate</Text>
                                <Progress percent={Math.round((displayMetrics.false_positive_count / (displayMetrics.failures_detected || 1)) * 100)} status="active" strokeColor="#faad14" />
                            </div>
                            <div>
                                <Text type="secondary">Repair Success Rate</Text>
                                <Progress percent={Math.round((displayMetrics.approved_applies / (displayMetrics.prs_created || 1)) * 100)} status="active" />
                            </div>
                        </Space>
                    </Col>
                    <Col span={12}>
                        <Title level={5}>Operational Velocity</Title>
                        <Space direction="vertical" style={{ width: "100%" }}>
                            <Row>
                                <Col span={12}>
                                    <Statistic title="Avg Proposal MTTR" value={displayMetrics.avg_mttr_s} suffix="s" valueStyle={{ fontSize: "16px" }} prefix={<ClockCircleOutlined />} />
                                </Col>
                                <Col span={12}>
                                    <Statistic title="Avg Gov Latency" value={displayMetrics.avg_governance_latency_s / 60} precision={1} suffix="m" valueStyle={{ fontSize: "16px" }} prefix={<UserOutlined />} />
                                </Col>
                            </Row>
                        </Space>
                    </Col>
                </Row>
            </div>
        </Card>
    );
};
