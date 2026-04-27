"use client";

import React from "react";
import { 
  Row, Col, Card, Statistic, Table, Tag, 
  Progress, Typography, Space, Button, Spin 
} from "antd";
import { 
  ClusterOutlined, 
  UserOutlined, 
  RocketOutlined, 
  SafetyCertificateOutlined,
  DollarOutlined
} from "@ant-design/icons";
import { useCustom } from "@refinedev/core";

const { Title, Text } = Typography;

interface FleetEvent {
  id: string;
  event_type: string;
  details: string;
  created_at: string;
}

export default function FleetDashboard() {
  const { data: metricsData, isLoading: metricsLoading } = useCustom({
    url: "http://127.0.0.1:8000/api/v1/fleet/metrics",
    method: "get",
  });

  const { data: clustersData, isLoading: clustersLoading } = useCustom({
    url: "http://127.0.0.1:8000/api/v1/fleet/clusters",
    method: "get",
  });

  const { data: eventsData, isLoading: eventsLoading } = useCustom({
    url: "http://127.0.0.1:8000/api/v1/fleet/events",
    method: "get",
  });

  const metrics = (metricsData?.data as any) || {
    active_agents: 0,
    queued_projects: 0,
    busy_ratio: 0,
    budget_burn: 0,
    quarantined_agents: 0
  };

  const clusters = (clustersData?.data as any) || [];
  const events = (eventsData?.data as unknown as FleetEvent[]) || [];

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString();
    } catch {
      return "---";
    }
  };

  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>Filo Merkezi: Çoklu Ajan Orkestrası</Title>
      <Text type="secondary">Otonom ajan dağıtımı ve proje orkestrasyon kontrol düzlemi.</Text>

      <Spin spinning={metricsLoading}>
        <Row gutter={[16, 16]} style={{ marginTop: "24px" }}>
          <Col span={4}>
            <Card bordered={false} className="premium-card">
              <Statistic 
                title="Aktif Ajanlar" 
                value={metrics.active_agents} 
                prefix={<UserOutlined />} 
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card bordered={false} className="premium-card">
              <Statistic 
                title="Kuyruktaki Projeler" 
                value={metrics.queued_projects} 
                prefix={<RocketOutlined />} 
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card bordered={false} className="premium-card">
              <Statistic 
                title="Doluluk Oranı" 
                value={metrics.busy_ratio} 
                suffix="%" 
                precision={1}
              />
              <Progress percent={metrics.busy_ratio} size="small" showInfo={false} />
            </Card>
          </Col>
          <Col span={4}>
            <Card bordered={false} className="premium-card">
              <Statistic 
                title="Bütçe Tüketimi" 
                value={metrics.budget_burn} 
                prefix={<DollarOutlined />} 
                suffix="USD"
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card bordered={false} className="premium-card">
              <Statistic 
                title="Karantinadakiler" 
                value={metrics.quarantined_agents} 
                prefix={<SafetyCertificateOutlined />} 
                valueStyle={{ color: metrics.quarantined_agents > 0 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
        </Row>
      </Spin>

      <Row gutter={[16, 16]} style={{ marginTop: "24px" }}>
        <Col span={16}>
          <Card title="Küme Durumu" extra={<Button icon={<ClusterOutlined />}>Kümeleri Yönet</Button>} loading={clustersLoading}>
            <Table 
              dataSource={clusters} 
              pagination={false}
              rowKey="id"
              columns={[
                { title: 'Küme Adı', dataIndex: 'name', key: 'name' },
                { 
                  title: 'Durum', 
                  dataIndex: 'status', 
                  key: 'status',
                  render: (status: string) => (
                    <Tag color={status === 'ACTIVE' ? 'green' : 'volcano'}>{status}</Tag>
                  )
                },
                { 
                  title: 'Yük', 
                  dataIndex: 'current_load', 
                  key: 'current_load',
                  render: (load: number) => <Progress percent={load} size="small" />
                },
                { title: 'Ajan Sayısı', dataIndex: 'agent_count', key: 'agent_count' },
                { 
                  title: 'Bütçe Kullanımı', 
                  dataIndex: 'budget_usage_pct', 
                  key: 'budget_usage_pct',
                  render: (pct: number) => `${pct.toFixed(1)}%`
                }
              ]}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Son Filo Olayları">
            <Space direction="vertical" style={{ width: '100%' }}>
              {events.map((e) => (
                <div key={e.id} className="event-item" style={{ marginBottom: '12px', paddingBottom: '8px', borderBottom: '1px solid #f0f0f0' }}>
                  <Text strong>[{e.event_type}]</Text> <Text>{e.details}</Text>
                  <div style={{ fontSize: '10px', color: '#999' }}>{formatTime(e.created_at)}</div>
                </div>
              ))}
              {events.length === 0 && <Text type="secondary" italic>Henüz olay kaydedilmedi.</Text>}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
