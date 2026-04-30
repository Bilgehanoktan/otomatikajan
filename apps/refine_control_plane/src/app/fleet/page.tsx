"use client";

import React from "react";
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Tag,
  Progress,
  Typography,
  Space,
  Button,
  Spin,
} from "antd";
import {
  ClusterOutlined,
  UserOutlined,
  RocketOutlined,
  SafetyCertificateOutlined,
  DollarOutlined,
} from "@ant-design/icons";
import { useApiUrl, useCustom } from "@refinedev/core";

const { Title, Text } = Typography;

interface FleetEvent {
  id: string;
  event_type: string;
  payload_summary: string | null;
  created_at: string;
}

interface FleetMetrics {
  active_agents: number;
  queued_projects: number;
  busy_ratio: number;
  budget_burn: number;
  quarantined_agents: number;
}

interface FleetCluster {
  id: string;
  name: string;
  status: string;
  current_load: number;
  agent_count: number;
  budget_usage_pct: number;
}

const eventTypeLabels: Record<string, string> = {
  AGENT_ASSIGNED: "Ajan Atandı",
  AGENT_RELEASED: "Ajan Serbest Bırakıldı",
  AGENT_QUARANTINED: "Ajan Karantinaya Alındı",
  BUDGET_BLOCK: "Bütçe Blokajı",
  CLUSTER_FROZEN: "Küme Donduruldu",
  FLEET_REBALANCED: "Filo Yeniden Dengelendi",
};

export default function FleetDashboard() {
  const apiUrl = useApiUrl();

  const metricsQuery = useCustom<FleetMetrics>({
    url: `${apiUrl}/fleet/metrics`,
    method: "get",
  }) as any;
  const clustersQuery = useCustom<FleetCluster[]>({
    url: `${apiUrl}/fleet/clusters`,
    method: "get",
  }) as any;
  const eventsQuery = useCustom<FleetEvent[]>({
    url: `${apiUrl}/fleet/events`,
    method: "get",
  }) as any;

  const metrics: FleetMetrics = metricsQuery.data?.data || {
    active_agents: 0,
    queued_projects: 0,
    busy_ratio: 0,
    budget_burn: 0,
    quarantined_agents: 0,
  };
  const clusters: FleetCluster[] = clustersQuery.data?.data || [];
  const events: FleetEvent[] = eventsQuery.data?.data || [];

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return Number.isNaN(date.getTime()) ? "---" : date.toLocaleTimeString("tr-TR");
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>Filo Merkezi: Çoklu Ajan Orkestrasyonu</Title>
      <Text type="secondary">
        Otonom ajan dağıtımı ve proje orkestrasyonu için canlı kontrol düzlemi.
      </Text>

      <Spin spinning={metricsQuery.isLoading}>
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col span={4}>
            <Card variant="borderless" className="premium-card">
              <Statistic
                title="Aktif Ajanlar"
                value={metrics.active_agents}
                prefix={<UserOutlined />}
                valueStyle={{ color: "#1890ff" }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card variant="borderless" className="premium-card">
              <Statistic
                title="Kuyruktaki Projeler"
                value={metrics.queued_projects}
                prefix={<RocketOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card variant="borderless" className="premium-card">
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
            <Card variant="borderless" className="premium-card">
              <Statistic
                title="Bütçe Tüketimi"
                value={metrics.budget_burn}
                prefix={<DollarOutlined />}
                suffix="USD"
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card variant="borderless" className="premium-card">
              <Statistic
                title="Karantinadakiler"
                value={metrics.quarantined_agents}
                prefix={<SafetyCertificateOutlined />}
                valueStyle={{
                  color: metrics.quarantined_agents > 0 ? "#cf1322" : "#3f8600",
                }}
              />
            </Card>
          </Col>
        </Row>
      </Spin>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={16}>
          <Card
            title="Küme Durumu"
            extra={<Button icon={<ClusterOutlined />}>Kümeleri Yönet</Button>}
            loading={clustersQuery.isLoading}
          >
            <Table
              dataSource={clusters}
              pagination={false}
              rowKey="id"
              columns={[
                { title: "Küme Adı", dataIndex: "name", key: "name" },
                {
                  title: "Durum",
                  dataIndex: "status",
                  key: "status",
                  render: (status: string) => (
                    <Tag color={status === "ACTIVE" ? "green" : "volcano"}>{status}</Tag>
                  ),
                },
                {
                  title: "Yük",
                  dataIndex: "current_load",
                  key: "current_load",
                  render: (load: number) => (
                    <Progress percent={Math.max(0, Math.min(100, load ?? 0))} size="small" />
                  ),
                },
                { title: "Ajan Sayısı", dataIndex: "agent_count", key: "agent_count" },
                {
                  title: "Bütçe Kullanımı",
                  dataIndex: "budget_usage_pct",
                  key: "budget_usage_pct",
                  render: (pct: number) => `${(pct ?? 0).toFixed(1)}%`,
                },
              ]}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card
            title={
              <Space>
                <RocketOutlined style={{ color: "#1890ff" }} />
                <span>Son Filo Olayları</span>
              </Space>
            }
            extra={<Tag color="blue">CANLI</Tag>}
          >
            <div style={{ maxHeight: 450, overflowY: "auto", paddingRight: 8 }}>
              <Spin spinning={eventsQuery.isLoading}>
                <Space direction="vertical" style={{ width: "100%" }} size="middle">
                  {events.map((event) => {
                    let tagColor = "default";
                    let icon = <RocketOutlined />;

                    switch (event.event_type) {
                      case "AGENT_ASSIGNED":
                        tagColor = "green";
                        icon = <UserOutlined />;
                        break;
                      case "BUDGET_BLOCK":
                        tagColor = "orange";
                        icon = <DollarOutlined />;
                        break;
                      case "AGENT_QUARANTINED":
                        tagColor = "red";
                        icon = <SafetyCertificateOutlined />;
                        break;
                      case "CLUSTER_FROZEN":
                        tagColor = "cyan";
                        icon = <ClusterOutlined />;
                        break;
                      case "AGENT_RELEASED":
                        tagColor = "blue";
                        break;
                      case "FLEET_REBALANCED":
                        tagColor = "purple";
                        break;
                    }

                    const borderColor =
                      tagColor === "green"
                        ? "#52c41a"
                        : tagColor === "orange"
                          ? "#faad14"
                          : tagColor === "red"
                            ? "#ff4d4f"
                            : tagColor === "cyan"
                              ? "#13c2c2"
                              : "#1890ff";

                    return (
                      <div
                        key={event.id}
                        className="event-item"
                        style={{
                          padding: 12,
                          borderRadius: 8,
                          background: "#f9f9f9",
                          borderLeft: `4px solid ${borderColor}`,
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            marginBottom: 4,
                          }}
                        >
                          <Tag icon={icon} color={tagColor} style={{ fontWeight: "bold" }}>
                            {eventTypeLabels[event.event_type] || event.event_type}
                          </Tag>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {formatTime(event.created_at)}
                          </Text>
                        </div>
                        <Text style={{ fontSize: 13, display: "block", marginTop: 4 }}>
                          {event.payload_summary || "Özet bulunamadı."}
                        </Text>
                      </div>
                    );
                  })}
                  {events.length === 0 && (
                    <div style={{ textAlign: "center", padding: "40px 0" }}>
                      <Text type="secondary" italic>
                        Henüz olay kaydedilmedi.
                      </Text>
                    </div>
                  )}
                </Space>
              </Spin>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
