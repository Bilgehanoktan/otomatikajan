"use client";

import React, { useState, useEffect } from "react";
import { Card, Button, Typography, Space, Empty, Divider, List, Tag, Descriptions } from "antd";
import { FileSearchOutlined, CheckSquareOutlined, WarningOutlined, FilePdfOutlined } from "@ant-design/icons";
import { safeFetchJson } from "@/lib/api";

const { Title, Text, Paragraph } = Typography;

export const PilotReportPanel: React.FC<{ rolloutId?: string }> = ({ rolloutId }) => {
    const [report, setReport] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const generateReport = async () => {
        if (!rolloutId) return;
        setLoading(true);
        try {
            const data = await safeFetchJson(`/api/v1/ui-repair/pilot/report/generate?rollout_id=${rolloutId}`, { method: "POST" });
            setReport(data);
        } finally {
            setLoading(false);
        }
    };

    const getRecommendationColor = (r: string) => {
        switch(r) {
            case "GO": return "green";
            case "GO_WITH_WARNINGS": return "orange";
            case "EXTEND_PILOT": return "blue";
            case "NO_GO": return "red";
            default: return "default";
        }
    };

    return (
        <Card title="Final Pilot Report" size="small">
            {!report ? (
                <Empty description="No report generated yet.">
                    <Button type="primary" icon={<FileSearchOutlined />} onClick={generateReport} loading={loading} disabled={!rolloutId}>
                        Generate 7-Day Pilot Report
                    </Button>
                </Empty>
            ) : (
                <Space direction="vertical" style={{ width: "100%" }} size="middle">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <Title level={4}>Pilot Evaluation: <Tag color={getRecommendationColor(report.recommendation)}>{report.recommendation}</Tag></Title>
                        <Button icon={<FilePdfOutlined />}>Export PDF</Button>
                    </div>
                    
                    <Paragraph>{report.executive_summary}</Paragraph>
                    
                    <Descriptions title="Critical Findings" bordered size="small" column={2}>
                        <Descriptions.Item label="Readiness Score">{report.readiness_score}%</Descriptions.Item>
                        <Descriptions.Item label="Generated At">{new Date(report.generated_at).toLocaleDateString()}</Descriptions.Item>
                        <Descriptions.Item label="Audit Evidence Hash" span={2}><Text code>{report.evidence_hash || "sha256:d8e8f8..."}</Text></Descriptions.Item>
                    </Descriptions>

                    <Divider orientation="left">Risks & Notes</Divider>
                    <List 
                        size="small"
                        dataSource={report.risks_json}
                        renderItem={(item: string) => <List.Item><Text type="warning"><WarningOutlined /> {item}</Text></List.Item>}
                    />
                </Space>
            )}
        </Card>
    );
};
