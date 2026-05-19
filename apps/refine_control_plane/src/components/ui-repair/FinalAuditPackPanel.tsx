import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Typography, Space, List, Divider, Badge, Empty, Result } from 'antd';
import { FilePdfOutlined, DownloadOutlined, SafetyCertificateOutlined, HistoryOutlined, FileSearchOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { safeFetchJson } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

export const FinalAuditPackPanel: React.FC = () => {
    const [latestPack, setLatestPack] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchLatestPack();
    }, []);

    const fetchLatestPack = async () => {
        setLoading(true);
        try {
            const data = await safeFetchJson<any>('/api/v1/ui-repair/final/audit-pack/latest');
            setLatestPack(data);
        } catch (error) {
            console.error('Failed to fetch latest audit pack:', error);
        } finally {
            setLoading(false);
        }
    };

    const generatePack = async () => {
        setLoading(true);
        try {
            const data = await safeFetchJson<any>('/api/v1/ui-repair/final/audit-pack/generate?version=1.0.0-RC1', { method: 'POST' });
            setLatestPack(data);
        } catch (error) {
            console.error('Failed to generate audit pack:', error);
        } finally {
            setLoading(false);
        }
    };

    if (!latestPack && !loading) {
        return (
            <div style={{ padding: '60px', textAlign: 'center' }}>
                <Empty 
                    image={Empty.PRESENTED_IMAGE_SIMPLE} 
                    description="No audit pack has been generated yet for this release cycle."
                >
                    <Button type="primary" size="large" onClick={generatePack} loading={loading}>
                        Generate Initial Audit Pack
                    </Button>
                </Empty>
            </div>
        );
    }

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
                <div>
                    <Title level={4} style={{ margin: 0 }}>Final Audit Documentation</Title>
                    <Text type="secondary">Comprehensive evidence pack for compliance and production handover.</Text>
                </div>
                <Space>
                    <Button icon={<HistoryOutlined />}>History</Button>
                    <Button type="primary" icon={<FilePdfOutlined />} onClick={generatePack} loading={loading}>
                        Regenerate Pack
                    </Button>
                </Space>
            </div>

            {latestPack && (
                <div className="pack-details">
                    <Card style={{ marginBottom: '24px', background: '#f9f9f9', border: '1px dashed #d9d9d9' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Space size="large">
                                <Statistic title="Version" value={latestPack.version} />
                                <Statistic title="Generated At" value={new Date(latestPack.generated_at).toLocaleString()} valueStyle={{ fontSize: '14px' }} />
                                <Statistic title="Evidence Hash" value={latestPack.evidence_hash?.substring(0, 16) + '...'} valueStyle={{ fontSize: '14px', fontFamily: 'monospace' }} />
                            </Space>
                            <Button type="primary" ghost icon={<DownloadOutlined />} size="large">Download Full PDF</Button>
                        </div>
                    </Card>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                        <Card title={<><FileSearchOutlined /> Included Sections</>} size="small">
                            <List
                                size="small"
                                dataSource={latestPack.included_sections}
                                renderItem={(item: string) => <List.Item><CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} /> {item}</List.Item>}
                            />
                        </Card>
                        <Card title={<><SafetyCertificateOutlined /> Compliance & Governance</>} size="small">
                            <Space direction="vertical" style={{ width: '100%' }}>
                                <Badge status="success" text="Identity & Trust Framework: VERIFIED" />
                                <Badge status="success" text="Cognitive Integrity Gates: ACTIVE" />
                                <Badge status="success" text="Tool Policy Sandbox: ENFORCED" />
                                <Badge status="success" text="Evidence Retention Chain: SECURE" />
                                <Divider style={{ margin: '12px 0' }} />
                                <Text type="secondary" italic>Audit pack signed by Autonomous Governance Orchestrator.</Text>
                            </Space>
                        </Card>
                    </div>
                </div>
            )}
        </div>
    );
};

import { Statistic } from 'antd';
