"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Card, Typography, Space, Button, Empty, Descriptions, Divider, List, Tag } from "antd";
import { ContactsOutlined, FileTextOutlined, RocketOutlined, AlertOutlined } from "@ant-design/icons";
// Using local icon names for now to avoid potential missing imports

const { Title, Text, Paragraph } = Typography;

export const HandoverPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const [report, setReport] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const generateHandover = async () => {
        setLoading(true);
        try {
            const res = await fetch("/api/v1/ui-repair/handover/generate?title=Production_Handover_Alpha", { method: "POST" });
            const data = await res.json();
            setReport(data);
        } catch (error) {
            console.error("Handover generation failed", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Space direction="vertical" style={{ width: "100%" }} size="large">
            <Card 
                title={<Space><FileTextOutlined /> {t("operator_handover")}</Space>}
                extra={<Button type="primary" onClick={generateHandover} loading={loading}>{t("generate_handover")}</Button>}
            >
                {report ? (
                    <div>
                        <Title level={4}>{report.title}</Title>
                        <Text type="secondary">Generated for Operational Handover on {new Date(report.created_at).toLocaleString()}</Text>
                        
                        <Divider />
                        
                        <Space direction="vertical" style={{ width: "100%" }} size="middle">
                            <section>
                                <Title level={5}><RocketOutlined /> Architecture Summary</Title>
                                <Paragraph>{report.architecture_summary}</Paragraph>
                            </section>

                            <section>
                                <Title level={5}><ContactsOutlined /> Operational Guide</Title>
                                <Paragraph style={{ whiteSpace: "pre-wrap" }}>{report.operational_guide}</Paragraph>
                            </section>

                            <section>
                                <Title level={5}><AlertOutlined style={{ color: "#faad14" }} /> Emergency Protocols</Title>
                                <Paragraph style={{ color: "#fa541c", whiteSpace: "pre-wrap" }}>{report.emergency_protocols}</Paragraph>
                            </section>
                            
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
                                <div>
                                    <Title level={5}>Residual Risks</Title>
                                    <List 
                                        size="small"
                                        dataSource={report.residual_risks_json}
                                        renderItem={(item: string) => <List.Item><Tag color="orange">RISK</Tag> {item}</List.Item>}
                                    />
                                </div>
                                <div>
                                    <Title level={5}>System Limitations</Title>
                                    <List 
                                        size="small"
                                        dataSource={report.limitations_json}
                                        renderItem={(item: string) => <List.Item><Tag>LIMIT</Tag> {item}</List.Item>}
                                    />
                                </div>
                            </div>
                        </Space>

                        <div style={{ marginTop: "24px" }}>
                            <Button icon={<FileTextOutlined />}>View Full Document</Button>
                        </div>
                    </div>
                ) : (
                    <Empty description="No handover report generated." />
                )}
            </Card>
        </Space>
    );
};
