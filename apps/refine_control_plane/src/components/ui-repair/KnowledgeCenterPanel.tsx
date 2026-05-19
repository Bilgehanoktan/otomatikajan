import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Typography, Space, Button, message, List, Avatar, Badge, Spin } from 'antd';
import { 
    BookOutlined, 
    NodeIndexOutlined, 
    BulbOutlined, 
    HistoryOutlined, 
    SearchOutlined, 
    SafetyCertificateOutlined,
    ShareAltOutlined,
    RadarChartOutlined
} from '@ant-design/icons';
import { safeFetchJson } from '@/lib/api';

const { Title, Text } = Typography;

export const KnowledgeCenterPanel: React.FC = () => {
    const [overview, setOverview] = useState<any>(null);
    const [nodes, setNodes] = useState<any[]>([]);
    const [predictions, setPredictions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchKnowledgeData = async () => {
        setLoading(true);
        try {
            const [overviewData, nodesData, predictionsData] = await Promise.all([
                safeFetchJson<any>('/api/v1/ui-repair/knowledge/overview'),
                safeFetchJson<any[]>('/api/v1/ui-repair/knowledge/nodes'),
                safeFetchJson<any[]>('/api/v1/ui-repair/knowledge/predictions')
            ]);
            setOverview(overviewData);
            setNodes(nodesData);
            setPredictions(predictionsData);
        } catch (error) {
            console.error("Failed to fetch knowledge data", error);
            message.error("Knowledge Center sync failure");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchKnowledgeData();
    }, []);

    const nodeColumns = [
        {
            title: 'Node Key',
            dataIndex: 'node_key',
            key: 'node_key',
            render: (text: string) => <Text strong className="font-mono">{text}</Text>
        },
        {
            title: 'Type',
            dataIndex: 'node_type',
            key: 'node_type',
            render: (type: string) => <Tag color="blue">{type}</Tag>
        },
        {
            title: 'Confidence',
            dataIndex: 'confidence',
            key: 'confidence',
            render: (score: number) => (
                <Badge 
                    status={score > 0.8 ? 'success' : 'warning'} 
                    text={`${(score * 100).toFixed(0)}%`} 
                />
            )
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => new Date(date).toLocaleDateString()
        }
    ];

    return (
        <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '80vh' }}>
            <Row gutter={[24, 24]}>
                <Col span={24}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <Title level={2}><BookOutlined /> Knowledge Graph & Causal Memory</Title>
                            <Text type="secondary">Autonomous learning engine capturing system lineage and predicting risks based on historical patterns.</Text>
                        </div>
                        <Button type="primary" icon={<RadarChartOutlined />} onClick={fetchKnowledgeData}>
                            Rebuild Graph
                        </Button>
                    </div>
                </Col>

                {/* Metrics */}
                <Col span={6}>
                    <Card bordered={false} className="glass-card">
                        <Statistic 
                            title="Total Knowledge Nodes" 
                            value={overview?.total_nodes || 0} 
                            prefix={<ShareAltOutlined />} 
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card bordered={false} className="glass-card">
                        <Statistic 
                            title="Inferred Causal Edges" 
                            value={overview?.total_edges || 0} 
                            prefix={<NodeIndexOutlined />} 
                            valueStyle={{ color: '#722ed1' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card bordered={false} className="glass-card">
                        <Statistic 
                            title="Active Risk Predictions" 
                            value={predictions.length} 
                            prefix={<BulbOutlined />} 
                            valueStyle={{ color: '#faad14' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card bordered={false} className="glass-card">
                        <Statistic 
                            title="Last Graph Rebuild" 
                            value={overview?.last_rebuild_at ? new Date(overview.last_rebuild_at).toLocaleTimeString() : 'N/A'} 
                            prefix={<HistoryOutlined />} 
                        />
                    </Card>
                </Col>

                {/* Graph Entities */}
                <Col span={16}>
                    <Card title={<Space><NodeIndexOutlined /> System Entity Nodes</Space>} bordered={false} className="glass-card">
                        <Table 
                            dataSource={nodes} 
                            columns={nodeColumns} 
                            loading={loading} 
                            rowKey="id"
                            pagination={{ pageSize: 6 }}
                        />
                    </Card>
                </Col>

                {/* Risk Predictions */}
                <Col span={8}>
                    <Card title={<Space><BulbOutlined /> Predictive Risk Analysis</Space>} bordered={false} className="glass-card">
                        <List
                            loading={loading}
                            itemLayout="horizontal"
                            dataSource={predictions}
                            renderItem={item => (
                                <List.Item>
                                    <List.Item.Meta
                                        avatar={<Avatar icon={<SafetyCertificateOutlined />} style={{ backgroundColor: item.severity === 'CRITICAL' ? '#f5222d' : '#faad14' }} />}
                                        title={<Text strong>{item.risk_type}</Text>}
                                        description={
                                            <div>
                                                <Text type="secondary" style={{ fontSize: '12px' }}>{item.target_key}</Text>
                                                <br />
                                                <Tag color={item.severity === 'CRITICAL' ? 'red' : 'orange'}>{item.severity}</Tag>
                                                <Text type="secondary">Prob: {(item.probability * 100).toFixed(0)}%</Text>
                                            </div>
                                        }
                                    />
                                </List.Item>
                            )}
                        />
                    </Card>
                </Col>
            </Row>

            <style jsx global>{`
                .glass-card {
                    background: rgba(255, 255, 255, 0.75);
                    backdrop-filter: blur(10px);
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
            `}</style>
        </div>
    );
};
