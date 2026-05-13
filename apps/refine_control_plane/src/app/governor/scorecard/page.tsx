"use client";

import { useCustom } from "@refinedev/core";
import { Card, Col, Row, Statistic, Table, Typography, Tag, Progress, Spin, List, Divider, Space } from "antd";
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  ClockCircleOutlined, 
  SafetyCertificateOutlined,
  BarChartOutlined,
  WarningOutlined
} from "@ant-design/icons";

const { Title, Text } = Typography;

export default function GovernorScorecard() {
  const scorecardQuery = useCustom<any>({
    url: "/governance/governor/scorecard",
    method: "get",
  });
  const { data, isLoading } = scorecardQuery as any;

  const outcomesQuery = useCustom<any[]>({
    url: "/governance/governor/outcomes",
    method: "get",
    config: {
      query: {
        _start: 0,
        _end: 10
      }
    }
  });
  const { data: outcomesData, isLoading: outcomesLoading } = outcomesQuery as any;

  if (isLoading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const stats = data?.data || {
    total_decisions: 0,
    correct_decisions: 0,
    accuracy: 0,
    replay_success_rate: 0,
    avg_latency_seconds: 0
  };

  const outcomes = (outcomesData?.data as any) || [];

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>
        <BarChartOutlined style={{ marginRight: 12 }} />
        Governor Scorecard (Karar Kalite Ölçümü)
      </Title>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card variant="borderless">
            <Statistic
              title="Toplam Karar"
              value={stats.total_decisions}
              prefix={<SafetyCertificateOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card variant="borderless">
            <Statistic
              title="Karar Doğruluğu"
              value={stats.accuracy}
              precision={1}
              suffix="%"
              valueStyle={{ color: stats.accuracy > 90 ? '#3f8600' : '#cf1322' }}
              prefix={<CheckCircleOutlined />}
            />
            <Progress 
                percent={stats.accuracy} 
                showInfo={false} 
                strokeColor={stats.accuracy > 90 ? '#52c41a' : '#f5222d'}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card variant="borderless">
            <Statistic
              title="Replay Başarı Oranı"
              value={stats.replay_success_rate}
              precision={1}
              suffix="%"
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card variant="borderless">
            <Statistic
              title="Ortalama Çözüm Süresi"
              value={stats.avg_latency_seconds}
              precision={0}
              suffix=" sn"
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title="Son Karar Çıktıları (Outcomes)" variant="borderless" style={{ marginTop: 24 }}>
        <Table 
            dataSource={outcomes} 
            rowKey="id" 
            loading={outcomesLoading}
            pagination={false}
        >
          <Table.Column 
            dataIndex="decision" 
            title="Governor Kararı" 
            render={(val) => <Tag color="blue">{val}</Tag>}
          />
          <Table.Column 
            dataIndex="final_outcome" 
            title="Gerçek Sonuç" 
            render={(val) => {
                const color = val === "SUCCESS" ? "green" : (val === "FAILED" ? "red" : "orange");
                return <Tag color={color}>{val}</Tag>;
            }}
          />
          <Table.Column 
            dataIndex="quality" 
            title="Kalite" 
            render={(val) => {
                const color = val === "CORRECT" ? "success" : "error";
                return <Tag color={color}>{val}</Tag>;
            }}
          />
          <Table.Column 
            dataIndex="resolution_latency_seconds" 
            title="Gecikme (sn)" 
          />
          <Table.Column 
            dataIndex="created_at" 
            title="Tarih" 
            render={(val) => new Date(val).toLocaleString()}
          />
        </Table>
      </Card>

      <Card title="Resilience SLO Monitoring (p95 Performance)" variant="borderless" style={{ marginTop: 24 }}>
        <Row gutter={24}>
          <Col span={12}>
            <Text type="secondary">System responsiveness targets for autonomous governance loops.</Text>
            <List
              itemLayout="horizontal"
              dataSource={[
                { title: "Domain Decision (p95)", target: "300ms", current: "245ms", status: "success" },
                { title: "Meta Resolution (p95)", target: "500ms", current: "380ms", status: "success" },
                { title: "Action Execution (p95)", target: "700ms", current: "820ms", status: "warning" },
                { title: "Conflict Resolution (p95)", target: "1000ms", current: "410ms", status: "success" },
              ]}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    title={item.title}
                    description={`Target: < ${item.target}`}
                  />
                  <div>
                    <Text strong style={{ marginRight: 12 }}>{item.current}</Text>
                    {item.status === "success" ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <WarningOutlined style={{ color: '#faad14' }} />}
                  </div>
                </List.Item>
              )}
            />
          </Col>
          <Col span={12} style={{ textAlign: 'center', paddingTop: 24 }}>
            <Progress 
              type="dashboard" 
              percent={94.2} 
              strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} 
              format={percent => `${percent}% Compliance`}
            />
            <div style={{ marginTop: 12 }}>
              <Text strong>System-Wide SLO Compliance (Last 7 Days)</Text>
            </div>
          </Col>
        </Row>
      </Card>

      <Row gutter={24} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="Observability: Alert Burden (24h)" variant="borderless">
            <Row gutter={16}>
              <Col span={8}>
                <Statistic title="Opened" value={14} prefix={<WarningOutlined />} />
              </Col>
              <Col span={8}>
                <Statistic title="Resolved" value={12} valueStyle={{ color: '#3f8600' }} />
              </Col>
              <Col span={8}>
                <Statistic title="Suppressed" value={2} valueStyle={{ color: '#8c8c8c' }} />
              </Col>
            </Row>
            <Divider style={{ margin: "12px 0" }} />
            <Text type="secondary" style={{ fontSize: "12px" }}>
              Alert fatigue risk: <Tag color="green">LOW</Tag> (Resolution rate: 85.7%)
            </Text>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Behavioral Drift: Last 7 Days" variant="borderless">
            <List
              size="small"
              dataSource={[
                { type: "DECISION_DRIFT", domain: "WORKFLOW", score: "12%", status: "NORMAL" },
                { type: "RISK_DRIFT", domain: "INCIDENT", score: "24%", status: "STABLE" },
                { type: "LATENCY_DRIFT", domain: "META", score: "8%", status: "NORMAL" },
              ]}
              renderItem={item => (
                <List.Item>
                  <Text>{item.type} ({item.domain})</Text>
                  <Space>
                    <Text strong>{item.score}</Text>
                    <Tag color="green">{item.status}</Tag>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
