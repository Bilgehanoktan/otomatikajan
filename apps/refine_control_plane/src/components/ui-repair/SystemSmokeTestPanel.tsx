import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Typography, Space, Progress, Badge, List, Row, Col, Divider } from 'antd';
import { PlayCircleOutlined, ReloadOutlined, BugOutlined, DashboardOutlined, SafetyOutlined, DatabaseOutlined } from '@ant-design/icons';
import { safeFetchJson } from '@/lib/api';

const { Title, Text } = Typography;

export const SystemSmokeTestPanel: React.FC = () => {
    const [results, setResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const runTests = async () => {
        setLoading(true);
        try {
            const data = await safeFetchJson('/api/v1/ui-repair/final/smoke-test/run', { method: 'POST' });
            setResults(data);
        } catch (error) {
            console.error('Smoke tests failed:', error);
        } finally {
            setLoading(false);
        }
    };

    const columns = [
        {
            title: 'Module Name',
            dataIndex: 'module_name',
            key: 'module_name',
            render: (text: string) => (
                <Space>
                    {getModuleIcon(text)}
                    <Text strong>{text}</Text>
                </Space>
            )
        },
        {
            title: 'Latency',
            dataIndex: 'latency_ms',
            key: 'latency_ms',
            render: (ms: number) => <Tag color={ms < 100 ? 'green' : 'orange'}>{ms}ms</Tag>
        },
        {
            title: 'Last Run',
            dataIndex: 'last_run_at',
            key: 'last_run_at',
            render: (date: string) => new Date(date).toLocaleTimeString()
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Badge status={status === 'PASSED' ? 'success' : 'error'} text={status} />
            )
        }
    ];

    const getModuleIcon = (name: string) => {
        if (name.includes('Health')) return <DashboardOutlined />;
        if (name.includes('Security')) return <SafetyOutlined />;
        if (name.includes('Knowledge')) return <DatabaseOutlined />;
        return <BugOutlined />;
    };

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
                <div>
                    <Title level={4} style={{ margin: 0 }}>System-Wide Smoke Tests</Title>
                    <Text type="secondary">Real-time health check of critical infrastructure components.</Text>
                </div>
                <Button type="primary" icon={<PlayCircleOutlined />} onClick={runTests} loading={loading}>
                    Run All Smoke Tests
                </Button>
            </div>

            <Row gutter={[24, 24]}>
                <Col span={16}>
                    <Table 
                        dataSource={results} 
                        columns={columns} 
                        pagination={false} 
                        loading={loading}
                        rowKey="module_name"
                    />
                </Col>
                <Col span={8}>
                    <Card title="Operational Health Index" size="small">
                        <div style={{ textAlign: 'center', padding: '20px 0' }}>
                            <Progress 
                                type="dashboard" 
                                percent={results.length > 0 ? (results.filter(r => r.status === 'PASSED').length / results.length) * 100 : 0} 
                                strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                            />
                            <div style={{ marginTop: '12px' }}>
                                <Text type="secondary">Overall System Stability</Text>
                            </div>
                        </div>
                        <Divider style={{ margin: '12px 0' }} />
                        <List size="small">
                            <List.Item><Text type="secondary">Total Modules:</Text> <Text strong>{results.length}</Text></List.Item>
                            <List.Item><Text type="secondary">Failures:</Text> <Text strong type="danger">{results.filter(r => r.status !== 'PASSED').length}</Text></List.Item>
                            <List.Item><Text type="secondary">Warnings:</Text> <Text strong type="warning">0</Text></List.Item>
                        </List>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
