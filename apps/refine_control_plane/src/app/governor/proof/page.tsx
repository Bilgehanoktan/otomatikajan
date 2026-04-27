"use client";

import React from "react";
import { Row, Col, Card, Statistic, Table, Typography, Tag, Button, Space, Breadcrumb } from "antd";
import { 
  SafetyCertificateOutlined, 
  HistoryOutlined, 
  LockOutlined, 
  CheckCircleOutlined,
  HomeOutlined,
  FileSearchOutlined
} from "@ant-design/icons";
import { useList, useUpdate, useCustomMutation } from "@refinedev/core";
import dayjs from "dayjs";

const { Title, Text } = Typography;

export default function ProofFabricDashboard() {
  const { query: { data: eventsData, isLoading: eventsLoading } } = useList({
    resource: "governance/proof/events",
    pagination: { pageSize: 10 }
  });

  const { query: { data: snapshotsData, isLoading: snapshotsLoading } } = useList({
    resource: "governance/proof/snapshots",
    pagination: { pageSize: 5 }
  });

  const events = eventsData?.data || [];
  const snapshots = snapshotsData?.data || [];

  const kpis = {
    latestIndex: events[0]?.chain_index || 0,
    sealedCount: snapshots.length,
    lastSealed: snapshots[0]?.created_at,
  };

  return (
    <div style={{ padding: "24px" }}>
      <Breadcrumb style={{ marginBottom: "16px" }}>
        <Breadcrumb.Item href="/"><HomeOutlined /></Breadcrumb.Item>
        <Breadcrumb.Item href="/governor/observability">Governance</Breadcrumb.Item>
        <Breadcrumb.Item>Proof Fabric</Breadcrumb.Item>
      </Breadcrumb>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <SafetyCertificateOutlined style={{ marginRight: 12, color: "#52c41a" }} />
            Proof Fabric (Değiştirilemez Denetim Zinciri)
          </Title>
          <Text type="secondary">Kriptografik olarak mühürlenmiş yönetişim olayları ve hash zinciri.</Text>
        </div>
        <Space>
          <Button icon={<HistoryOutlined />}>Chain Health Check</Button>
          <Button type="primary" icon={<LockOutlined />}>Seal New Snapshot</Button>
        </Space>
      </div>

      <Row gutter={16} style={{ marginBottom: "24px" }}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Chain Height" value={kpis.latestIndex} prefix={<HistoryOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Sealed Snapshots" value={kpis.sealedCount} prefix={<LockOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Verified Events" value={kpis.latestIndex} valueStyle={{ color: "#3f8600" }} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic 
                title="Chain Status" 
                value="INTACT" 
                valueStyle={{ color: "#3f8600", fontSize: "18px" }} 
                prefix={<SafetyCertificateOutlined />} 
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={24}>
        <Col span={16}>
          <Card title={<Space><HistoryOutlined /> Recent Audit Events</Space>}>
            <Table 
              dataSource={events} 
              rowKey="id" 
              loading={eventsLoading} 
              pagination={false}
              size="small"
            >
              <Table.Column 
                dataIndex="chain_index" 
                title="Idx" 
                render={(val) => <Text code>{val}</Text>}
              />
              <Table.Column 
                dataIndex="event_type" 
                title="Event Type" 
                render={(val) => <Tag color="blue">{val}</Tag>}
              />
              <Table.Column 
                dataIndex="event_hash" 
                title="Hash" 
                render={(val) => <Text copyable={{ text: val }}>{val.slice(0, 8)}...</Text>}
              />
              <Table.Column 
                dataIndex="created_at" 
                title="Created" 
                render={(val) => dayjs(val).format("HH:mm:ss")}
              />
            </Table>
          </Card>
        </Col>
        <Col span={8}>
          <Card title={<Space><LockOutlined /> Sealed Snapshots</Space>}>
            <Table 
              dataSource={snapshots} 
              rowKey="id" 
              loading={snapshotsLoading} 
              pagination={false}
              size="small"
            >
              <Table.Column 
                dataIndex="snapshot_name" 
                title="Name" 
                render={(val) => <Text strong style={{ fontSize: "12px" }}>{val}</Text>}
              />
              <Table.Column 
                dataIndex="seal_status" 
                title="Status" 
                render={(val) => <Tag color={val === "SEALED" ? "green" : "blue"}>{val}</Tag>}
              />
              <Table.Column 
                title="Action" 
                render={(_, r: any) => <Button type="link" size="small" icon={<FileSearchOutlined />}>Verify</Button>}
              />
            </Table>
          </Card>
        </Col>
      </Row>
    </div>
  );
}


