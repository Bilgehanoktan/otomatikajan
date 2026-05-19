import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Progress, List, Typography, Space, Divider, Alert, Badge, Spin, Row, Col, Statistic } from 'antd';
import { RocketOutlined, AuditOutlined, SafetyOutlined, AppstoreOutlined, CheckCircleOutlined, WarningOutlined, LockOutlined, FileTextOutlined } from '@ant-design/icons';
import { ReleaseReadinessPanel } from './ReleaseReadinessPanel';
import { FinalAuditPackPanel } from './FinalAuditPackPanel';
import { SystemSmokeTestPanel } from './SystemSmokeTestPanel';
import { ResidualRiskPanel } from './ResidualRiskPanel';
import RedTeamPanel from './RedTeamPanel';
import { safeFetchJson } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

export const FinalReleaseCenterPanel: React.FC = () => {
    const [activeTab, setActiveTab] = useState('readiness');
    const [readinessSummary, setReadinessSummary] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchReadiness();
    }, []);

    const fetchReadiness = async () => {
        setLoading(true);
        try {
            const data = await safeFetchJson('/api/v1/ui-repair/final/readiness');
            setReadinessSummary(data);
        } catch (error) {
            console.error('Failed to fetch readiness:', error);
        } finally {
            setLoading(false);
        }
    };

    const tabList = [
        { key: 'readiness', tab: 'Release Readiness' },
        { key: 'audit', tab: 'Integration Audit' },
        { key: 'smoke', tab: 'Smoke Tests' },
        { key: 'pack', tab: 'Audit Pack' },
        { key: 'risks', tab: 'Residual Risks' },
        { key: 'redteam', tab: 'Red Team' },
        { key: 'lock', tab: 'Release Lock' },
    ];

    const renderContent = () => {
        switch (activeTab) {
            case 'readiness': return <ReleaseReadinessPanel />;
            case 'audit': return <AuditPanel />;
            case 'pack': return <FinalAuditPackPanel />;
            case 'smoke': return <SystemSmokeTestPanel />;
            case 'risks': return <ResidualRiskPanel />;
            case 'redteam': return <RedTeamPanel />;
            case 'lock': return <ReleaseLockPanel />;
            default: return null;
        }
    };

    return (
        <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <Title level={2} style={{ margin: 0 }}>
                        <RocketOutlined style={{ marginRight: '12px', color: '#1890ff' }} />
                        Final Release Center
                    </Title>
                    <Text type="secondary">Phase 30: Final Integration, Production Hardening & Release Lock</Text>
                </div>
                <Space>
                    <Badge status={readinessSummary?.status === 'RELEASE_CANDIDATE' ? 'success' : 'processing'} 
                           text={<Text strong>{readinessSummary?.status || 'PENDING'}</Text>} />
                    <Button type="primary" icon={<RocketOutlined />} disabled={readinessSummary?.status !== 'RELEASE_CANDIDATE'}>
                        Final Release Lock
                    </Button>
                </Space>
            </div>

            <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
                <Col span={6}>
                    <Card bordered={false} className="glass-card">
                        <Statistic 
                            title="Readiness Score" 
                            value={readinessSummary?.score || 0} 
                            precision={1}
                            suffix="/ 100"
                            valueStyle={{ color: (readinessSummary?.score || 0) > 90 ? '#3f8600' : '#cf1322' }}
                            prefix={<CheckCircleOutlined />}
                        />
                        <Progress 
                            percent={readinessSummary?.score || 0} 
                            strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                            status={(readinessSummary?.score || 0) > 90 ? 'active' : 'exception'}
                            showInfo={false}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card bordered={false} className="glass-card">
                        <Statistic 
                            title="Critical Blockers" 
                            value={readinessSummary?.blockers?.length || 0} 
                            valueStyle={{ color: (readinessSummary?.blockers?.length || 0) > 0 ? '#cf1322' : '#3f8600' }}
                            prefix={<WarningOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card bordered={false} className="glass-card">
                        <Statistic 
                            title="Audit Status" 
                            value="SEALED" 
                            valueStyle={{ color: '#1890ff' }}
                            prefix={<SafetyOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card bordered={false} className="glass-card">
                        <Statistic 
                            title="Version" 
                            value="1.0.0-RC1" 
                            prefix={<LockOutlined />}
                        />
                    </Card>
                </Col>
            </Row>

            <Card
                style={{ width: '100%', borderRadius: '12px', overflow: 'hidden' }}
                tabList={tabList}
                activeTabKey={activeTab}
                onTabChange={key => setActiveTab(key)}
                className="main-tabs-card"
            >
                {renderContent()}
            </Card>

            <style>{`
                .glass-card {
                    background: rgba(255, 255, 255, 0.8) !important;
                    backdrop-filter: blur(8px);
                    border-radius: 12px !important;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                }
                .main-tabs-card .ant-tabs-nav {
                    padding: 0 24px;
                    background: #fafafa;
                }
            `}</style>
        </div>
    );
};

const AuditPanel: React.FC = () => {
    const [audits, setAudits] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const runAudit = async () => {
        setLoading(true);
        try {
            const data = await safeFetchJson('/api/v1/ui-repair/final/integration-audit/run', { method: 'POST' });
            setAudits([data, ...audits]);
        } catch (error) {
            console.error('Audit failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
                <Title level={4}>Integration Audit Ledger</Title>
                <Button type="primary" onClick={runAudit} loading={loading}>Run Full Audit</Button>
            </div>
            <List
                itemLayout="horizontal"
                dataSource={audits}
                renderItem={audit => (
                    <Card size="small" style={{ marginBottom: '12px' }}>
                        <List.Item
                            actions={[<Button key="view-details" type="link">View Details</Button>]}
                        >
                            <List.Item.Meta
                                avatar={<Badge status={audit.status === 'PASSED' ? 'success' : 'error'} />}
                                title={<Text strong>{audit.audit_key}</Text>}
                                description={`Performed at: ${new Date(audit.created_at).toLocaleString()} | Result: ${audit.status}`}
                            />
                            <div>
                                <Tag color="blue">{audit.summary?.passed} Passed</Tag>
                                <Tag color="orange">{audit.summary?.warnings} Warnings</Tag>
                                <Tag color="red">{audit.summary?.failed} Failed</Tag>
                            </div>
                        </List.Item>
                    </Card>
                )}
            />
        </div>
    );
};

const ReleaseLockPanel: React.FC = () => {
    return (
        <div style={{ padding: '40px', textAlign: 'center' }}>
            <LockOutlined style={{ fontSize: '64px', color: '#1890ff', marginBottom: '24px' }} />
            <Title level={3}>Immutable Release Lock</Title>
            <Paragraph style={{ maxWidth: '600px', margin: '0 auto 24px' }}>
                Once all integration audits, smoke tests, and readiness checks pass, you can issue an immutable release lock. 
                This will seal the current state of the system, generate a final evidence hash, and create a release candidate.
            </Paragraph>
            <Alert 
                message="Production Release Lock required for GA deployment" 
                description="This action will finalize the version lock and prevent further feature changes for this release cycle."
                type="info"
                showIcon
                style={{ maxWidth: '600px', margin: '0 auto 24px', textAlign: 'left' }}
            />
            <Button type="primary" size="large" icon={<LockOutlined />} disabled>
                Seal Release Candidate
            </Button>
        </div>
    );
};
