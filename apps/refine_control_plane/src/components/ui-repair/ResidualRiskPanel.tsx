import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Typography, Space, Button, Modal, Form, Input, Select, Divider } from 'antd';
import { WarningOutlined, SafetyOutlined, MessageOutlined, ExceptionOutlined } from '@ant-design/icons';
import { safeFetchJson } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

export const ResidualRiskPanel: React.FC = () => {
    const [risks, setRisks] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchRisks();
    }, []);

    const fetchRisks = async () => {
        setLoading(true);
        try {
            const data = await safeFetchJson<any[]>('/api/v1/ui-repair/final/residual-risks');
            setRisks(data);
        } catch (error) {
            console.error('Failed to fetch residual risks:', error);
        } finally {
            setLoading(false);
        }
    };

    const columns = [
        {
            title: 'Module',
            dataIndex: 'module',
            key: 'module',
            render: (text: string) => <Tag color="blue">{text}</Tag>
        },
        {
            title: 'Severity',
            dataIndex: 'severity',
            key: 'severity',
            render: (sev: string) => (
                <Tag color={sev === 'HIGH' ? 'red' : (sev === 'MEDIUM' ? 'orange' : 'green')}>
                    {sev}
                </Tag>
            )
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            width: '30%'
        },
        {
            title: 'Mitigation Strategy',
            dataIndex: 'mitigation_strategy',
            key: 'mitigation_strategy'
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string, record: any) => (
                <Space>
                    <Tag color={record.is_accepted ? "green" : "cyan"}>
                        {record.is_accepted ? "ACCEPTED" : status}
                    </Tag>
                    {record.is_accepted && <Text type="secondary" style={{fontSize: '10px'}}>by {record.accepted_by}</Text>}
                </Space>
            )
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: any) => (
                <Button 
                    size="small" 
                    type="primary" 
                    ghost 
                    disabled={record.is_accepted}
                    onClick={() => handleSignOff(record.risk_id)}
                >
                    {record.is_accepted ? 'Signed Off' : 'Sign Off'}
                </Button>
            )
        }
    ];

    const handleSignOff = async (riskId: string) => {
        try {
            await safeFetchJson(`/api/v1/ui-repair/final/residual-risks/${riskId}/sign-off`, {
                method: 'POST',
                body: JSON.stringify({ operator: 'Egemen YAZ' })
            });
            fetchRisks();
        } catch (error) {
            console.error('Sign-off failed:', error);
        }
    };

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
                <div>
                    <Title level={4} style={{ margin: 0 }}>Residual Risk Registry</Title>
                    <Text type="secondary">Known limitations and edge cases accepted for this release cycle.</Text>
                </div>
                <Button icon={<ExceptionOutlined />}>Propose New Risk Acceptance</Button>
            </div>

            <Table 
                dataSource={risks} 
                columns={columns} 
                pagination={false} 
                loading={loading}
                rowKey="risk_id"
            />

            <Card style={{ marginTop: '24px', background: '#fffbe6' }}>
                <Space align="start">
                    <WarningOutlined style={{ color: '#faad14', fontSize: '20px' }} />
                    <div>
                        <Text strong>Governance Requirement:</Text>
                        <Paragraph style={{ margin: 0 }}>
                            All residual risks must be MITIGATED or ACCEPTED by an authorized operator. 
                            Release Lock is only possible if no UNMAPPED risks exist.
                        </Paragraph>
                    </div>
                </Space>
            </Card>
        </div>
    );
};
