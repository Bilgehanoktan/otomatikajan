"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Card, Table, Typography, Space, Tag, Button, Empty, Descriptions, Divider } from "antd";
import { AuditOutlined, CloudDownloadOutlined, LockOutlined, FileSearchOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;

export const FinalAuditPackPanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const [pack, setPack] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const fetchPack = async () => {
        setLoading(true);
        try {
            // In real app, fetch list and take latest
            // For now, mock or fetch latest
        } catch (error) {
            console.error("Failed to fetch audit pack", error);
        } finally {
            setLoading(false);
        }
    };

    const generatePack = async () => {
        setLoading(true);
        try {
            const res = await fetch("/api/v1/ui-repair/final-audit-pack/generate?name=Sovereign_Control_Plane_Release&version=1.0.0", { method: "POST" });
            const data = await res.json();
            setPack(data);
        } catch (error) {
            console.error("Pack generation failed", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Space direction="vertical" style={{ width: "100%" }} size="large">
            <Card 
                title={<Space><AuditOutlined /> {t("final_audit_pack")}</Space>}
                extra={<Button type="primary" icon={<LockOutlined />} onClick={generatePack} loading={loading}>{t("seal_audit_pack")}</Button>}
            >
                {pack ? (
                    <div>
                        <Descriptions title="Audit Package Details" bordered column={2}>
                            <Descriptions.Item label="Pack Name">{pack.name}</Descriptions.Item>
                            <Descriptions.Item label="Version">{pack.version}</Descriptions.Item>
                            <Descriptions.Item label="Status"><Tag color="blue">{pack.is_sealed ? "SEALED" : "DRAFT"}</Tag></Descriptions.Item>
                            <Descriptions.Item label="Created At">{new Date(pack.created_at).toLocaleString()}</Descriptions.Item>
                            <Descriptions.Item label="Integrity Hash" span={2}>
                                <Text code>{pack.evidence_bundle_hash}</Text>
                            </Descriptions.Item>
                        </Descriptions>
                        
                        <Divider />
                        
                        <Title level={5}>Content Manifest</Title>
                        <ul style={{ paddingLeft: "20px" }}>
                            {Object.entries(pack.content_manifest_json).map(([key, val]: [string, any]) => (
                                <li key={key}><Text strong>{key.replace("_", " ")}:</Text> {val}</li>
                            ))}
                        </ul>

                        <div style={{ marginTop: "24px" }}>
                            <Button icon={<CloudDownloadOutlined />}>Download Full Bundle</Button>
                            <Button icon={<FileSearchOutlined />} style={{ marginLeft: "12px" }}>View Summary Report</Button>
                        </div>
                    </div>
                ) : (
                    <Empty description="No audit pack generated yet." />
                )}
            </Card>
        </Space>
    );
};
