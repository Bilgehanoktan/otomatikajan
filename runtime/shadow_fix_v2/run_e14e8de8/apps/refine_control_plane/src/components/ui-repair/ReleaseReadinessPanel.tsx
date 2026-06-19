import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Progress, List, Typography, Space, Divider, Alert, Badge, Spin, Row, Col, Statistic, Tooltip } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, WarningOutlined, InfoCircleOutlined, RocketOutlined } from '@ant-design/icons';
import { safeFetchJson } from '@/lib/api';

const { Title, Text } = Typography;

export const ReleaseReadinessPanel: React.FC = () => {
    const [checks, setChecks] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchChecks();
    }, []);

    const fetchChecks = async () => {
        setLoading(true);
        try {
            const data = await safeFetchJson('/api/v1/ui-repair/final/readiness/check', { method: 'POST' });
            setChecks(data);
        } catch (error) {
            console.error('Failed to fetch readiness checks:', error);
        } finally {
            setLoading(false);
        }
    };

    const columns = [
        {
            title: 'Category',
            dataIndex: 'category',
            key: 'category',
            render: (text: string) => <Text strong>{text}</Text>
        },
        {
            title: 'Score',
            dataIndex: 'score',
            key: 'score',
            render: (score: number) => (
                <Space direction="vertical" style={{ width: '100%' }}>
                    <Progress 
                        percent={score} 
                        size="small" 
                        strokeColor={score >= 90 ? '#52c41a' : (score >= 70 ? '#faad14' : '#f5222d')} 
                    />
                </Space>
            )
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                const getStatusColor = (s: string) => {
                    switch (s) {
                        case 'PASSED':
                        case 'SEALED':
                        case 'RELEASE_CANDIDATE':
                            return 'success';
                        case 'WARNING':
                        case 'STALE':
                            return 'warning';
                        case 'FAILED':
                        case 'BLOCKED':
                            return 'error';
                        case 'NO_DATA':
                            return 'default';
                        case 'SIMULATED':
                            return 'processing';
                        default:
                            return 'default';
                    }
                };
                return (
                    <Tag color={getStatusColor(status)}>
                        {status}
                    </Tag>
                );
            }
        },
        {
            title: 'Blockers',
            dataIndex: 'blockers',
            key: 'blockers',
            render: (blockers: string[]) => (
                blockers && blockers.length > 0 ? (
                    <Tooltip title={blockers.join(', ')}>
                        <Tag color="red">{blockers.length} Blockers</Tag>
                    </Tooltip>
                ) : <Text type="secondary">None</Text>
            )
        },
        {
            title: 'Warnings',
            dataIndex: 'warnings',
            key: 'warnings',
            render: (warnings: string[]) => (
                warnings && warnings.length > 0 ? (
                    <Tooltip title={warnings.join(', ')}>
                        <Tag color="orange">{warnings.length} Warnings</Tag>
                    </Tooltip>
                ) : <Text type="secondary">None</Text>
            )
        },
        {
            title: 'Recommendation',
            dataIndex: 'recommendation',
            key: 'recommendation',
            render: (text: string) => <Text type="secondary" style={{ fontSize: '12px' }}>{text}</Text>
        }
    ];

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                    <Title level={4} style={{ margin: 0 }}>Production Readiness Evaluation</Title>
                    <Text type="secondary">Automated checks against the Sovereign AGI Release Gate policy.</Text>
                </div>
                <Button type="primary" icon={<RocketOutlined />} onClick={fetchChecks} loading={loading}>
                    Re-Evaluate All Categories
                </Button>
            </div>

            <Table 
                dataSource={checks} 
                columns={columns} 
                loading={loading}
                pagination={false}
                rowKey="id"
                className="readiness-table"
            />

            <div style={{ marginTop: '24px' }}>
                <Alert
                    message="Release Candidate Eligibility"
                    description="All categories must have a score >= 90 and zero blockers to qualify for a Production Release Candidate (RC) lock."
                    type="warning"
                    showIcon
                />
            </div>

            <style>{`
                .readiness-table .ant-table-thead > tr > th {
                    background: transparent;
                }
            `}</style>
        </div>
    );
};
