import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Badge, 
  Button, 
  Progress, 
  Divider, 
  Space, 
  Typography, 
  Statistic, 
  Row, 
  Col, 
  List, 
  Empty, 
  Tag,
  Tooltip,
  Alert,
  Modal,
  Form,
  InputNumber,
  Select,
  notification
} from 'antd';
import { 
  DollarOutlined, 
  WarningOutlined, 
  RocketOutlined, 
  PieChartOutlined, 
  HistoryOutlined,
  CheckCircleOutlined,
  ArrowUpOutlined,
  BulbOutlined,
  CalendarOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';
import { useTranslations } from 'next-intl';
import { safeFetchJson } from '@/lib/api';

const { Title, Text } = Typography;

interface FinOpsOverview {
  total_cost_today: number;
  total_cost_week: number;
  total_cost_month: number;
  project_cost_distribution: any[];
  team_cost_distribution: any[];
  operation_type_distribution: any[];
  budget_usage_percent: number;
  active_anomalies_count: number;
  forecasted_next_30d_cost: number;
  potential_savings_usd: number;
}

export const FinOpsCenter: React.FC = () => {
  const t = useTranslations('repair_lab');
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<FinOpsOverview | null>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [recs, setRecs] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any | null>(null);

  const fetchFinOpsData = async () => {
    setLoading(true);
    try {
      const [overviewData, anomaliesData, recsData] = await Promise.all([
        safeFetchJson<FinOpsOverview>('/api/v1/ui-repair/finops/overview'),
        safeFetchJson<any[]>('/api/v1/ui-repair/finops/anomalies'),
        safeFetchJson<any[]>('/api/v1/ui-repair/finops/recommendations')
      ]);
      
      setOverview(overviewData);
      setAnomalies(anomaliesData);
      setRecs(recsData);
    } catch (err) {
      console.error("Failed to fetch FinOps data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinOpsData();
    const interval = setInterval(fetchFinOpsData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleResolveAnomaly = async (id: string) => {
    try {
      await safeFetchJson(`/api/v1/ui-repair/finops/anomalies/${id}/resolve`, { method: 'POST' });
      notification.success({ message: "Anomaly Resolved" });
      fetchFinOpsData();
    } catch (err) {
      notification.error({ message: "Failed to resolve anomaly" });
    }
  };

  const handleUpdateRec = async (id: string, status: string) => {
    try {
      await safeFetchJson(`/api/v1/ui-repair/finops/recommendations/${id}/status?status=${status}`, { method: 'POST' });
      notification.success({ message: `Recommendation ${status}` });
      fetchFinOpsData();
    } catch (err) {
      notification.error({ message: "Failed to update recommendation" });
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic
              title="Monthly Spend"
              value={overview?.total_cost_month || 0}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="USD"
            />
            <Progress percent={overview?.budget_usage_percent || 0} status="active" strokeColor="#1890ff" />
            <Text type="secondary" style={{ fontSize: '12px' }}>Budget Usage</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic
              title="Active Anomalies"
              value={overview?.active_anomalies_count || 0}
              valueStyle={{ color: (overview?.active_anomalies_count || 0) > 0 ? '#cf1322' : '#3f8600' }}
              prefix={<WarningOutlined />}
            />
            <Text type="secondary">Requires attention</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic
              title="30D Forecast"
              value={overview?.forecasted_next_30d_cost || 0}
              precision={2}
              prefix={<CalendarOutlined />}
              suffix="USD"
            />
            <Tag color="blue" style={{ marginTop: '8px' }}>Predictive Analytics Active</Tag>
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic
              title="Potential Savings"
              value={overview?.potential_savings_usd || 0}
              precision={2}
              valueStyle={{ color: '#3f8600' }}
              prefix={<RocketOutlined />}
              suffix="USD"
            />
            <Text type="secondary">Actionable optimizations</Text>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        <Col span={16}>
          <Card 
            title={<span><WarningOutlined /> Cost Anomalies & Spikes</span>}
            className="glass-card"
            extra={<Button size="small" icon={<HistoryOutlined />} onClick={fetchFinOpsData}>Refresh</Button>}
          >
            <Table
              dataSource={anomalies}
              loading={loading}
              pagination={{ pageSize: 5 }}
              size="small"
              columns={[
                { title: 'Type', dataIndex: 'anomaly_type', key: 'type', render: (t) => <Badge status="error" text={t} /> },
                { title: 'Deviation', dataIndex: 'deviation_percent', key: 'dev', render: (v) => <Text type="danger"><ArrowUpOutlined /> {v.toFixed(1)}%</Text> },
                { title: 'Observed', dataIndex: 'observed_cost_usd', key: 'obs', render: (v) => `$${v.toFixed(2)}` },
                { title: 'Status', dataIndex: 'status', key: 'status', render: (s) => <Tag color={s === 'OPEN' ? 'red' : 'green'}>{s}</Tag> },
                { title: 'Action', key: 'action', render: (_, r) => (
                  r.status === 'OPEN' && <Button type="link" size="small" onClick={() => handleResolveAnomaly(r.id)}>Resolve</Button>
                )}
              ]}
            />
          </Card>

          <Card 
            title={<span><BulbOutlined /> Optimization Recommendations</span>}
            className="glass-card"
            style={{ marginTop: '16px' }}
          >
            <List
              dataSource={recs.filter(r => r.status === 'PENDING')}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button key="apply" type="primary" size="small" onClick={() => handleUpdateRec(item.id, 'APPLIED')}>Apply</Button>,
                    <Button key="dismiss" size="small" onClick={() => handleUpdateRec(item.id, 'DISMISSED')}>Dismiss</Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Badge color={item.priority === 'HIGH' ? 'red' : 'orange'} dot />}
                    title={item.title}
                    description={item.description}
                  />
                  <div style={{ textAlign: 'right' }}>
                    <Text type="success">+ ${item.expected_savings_usd.toFixed(2)} savings</Text>
                    <br />
                    <Tag color="cyan">{item.recommendation_type}</Tag>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col span={8}>
          <Card title={<span><PieChartOutlined /> Cost Attribution</span>} className="glass-card">
            <Title level={5}>By Operation Type</Title>
            <List
              size="small"
              dataSource={overview?.operation_type_distribution || []}
              renderItem={(item) => (
                <List.Item>
                  <Text>{item.operation_type}</Text>
                  <Text strong>${item.total_cost.toFixed(2)}</Text>
                </List.Item>
              )}
            />
            <Divider />
            <Title level={5}>By Project</Title>
            <List
              size="small"
              dataSource={overview?.project_cost_distribution || []}
              renderItem={(item) => (
                <List.Item>
                  <Text>{item.project_key}</Text>
                  <Text strong>${item.total_cost.toFixed(2)}</Text>
                </List.Item>
              )}
            />
          </Card>

          <Card 
            title={<span><SafetyCertificateOutlined /> Budget Guardrails</span>} 
            className="glass-card" 
            style={{ marginTop: '16px' }}
          >
            <Alert
              message="Hard Limit Protection Active"
              description="System will automatically pause autonomous repairs if monthly hard limit is reached."
              type="info"
              showIcon
            />
            <Button block type="dashed" style={{ marginTop: '16px' }} icon={<DollarOutlined />}>
              Adjust Budget Policies
            </Button>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
