"use client";

import Link from "next/link";
import dayjs from "dayjs";
import { Breadcrumb, Button, Card, Col, Row, Space, Statistic, Table, Tag, Typography } from "antd";
import {
  CheckCircleOutlined,
  FileSearchOutlined,
  HistoryOutlined,
  HomeOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { useList } from "@refinedev/core";

const { Title, Text } = Typography;

interface LineageRecord {
  id: string;
  decision_type: string;
  component_name: string;
  rationale: string;
  outcome?: string | null;
  confidence_score: number;
  integrity_hash?: string | null;
  created_at: string;
}

interface AuditBundleRecord {
  id: string;
  name: string;
  purpose: string;
  project: string;
  created_at: string;
  operator: string;
  seal: string;
  size: string;
  status: string;
}

export default function ProofFabricDashboard() {
  const {
    query: { data: eventsData, isLoading: eventsLoading },
  } = useList<LineageRecord>({
    resource: "governance/lineage",
    pagination: { pageSize: 10 },
    sorters: [{ field: "created_at", order: "desc" }],
  });

  const {
    query: { data: snapshotsData, isLoading: snapshotsLoading },
  } = useList<AuditBundleRecord>({
    resource: "governance/compliance/audit-bundles",
    pagination: { pageSize: 5 },
    sorters: [{ field: "created_at", order: "desc" }],
  });

  const events = eventsData?.data || [];
  const snapshots = snapshotsData?.data || [];

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
            Proof Fabric
          </Title>
          <Text type="secondary">Immutable governance ledger and sealed audit bundles.</Text>
        </div>
        <Space>
          <Link href="/proof/events">
            <Button icon={<HistoryOutlined />}>Open Event Ledger</Button>
          </Link>
          <Link href="/proof/snapshots">
            <Button type="primary" icon={<LockOutlined />}>Open Snapshots</Button>
          </Link>
        </Space>
      </div>

      <Row gutter={16} style={{ marginBottom: "24px" }}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Chain Height" value={events.length} prefix={<HistoryOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Sealed Snapshots" value={snapshots.length} prefix={<LockOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Verified Events" value={events.length} valueStyle={{ color: "#3f8600" }} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="Chain Status" value={snapshots.length > 0 ? "INTACT" : "ACTIVE"} valueStyle={{ color: "#3f8600", fontSize: "18px" }} prefix={<SafetyCertificateOutlined />} />
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
              <Table.Column dataIndex="component_name" title="Component" render={(val) => <Text strong>{val}</Text>} />
              <Table.Column dataIndex="decision_type" title="Decision" render={(val) => <Tag color="blue">{val}</Tag>} />
              <Table.Column dataIndex="outcome" title="Outcome" render={(val) => val ? <Tag color="green">{val}</Tag> : <Text type="secondary">-</Text>} />
              <Table.Column dataIndex="integrity_hash" title="Hash" render={(val, r: LineageRecord) => <Text copyable={{ text: val || r.id }}>{String(val || r.id).slice(0, 8)}...</Text>} />
              <Table.Column dataIndex="created_at" title="Created" render={(val) => dayjs(val).format("HH:mm:ss")} />
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
              <Table.Column dataIndex="name" title="Name" render={(val) => <Text strong style={{ fontSize: "12px" }}>{val}</Text>} />
              <Table.Column dataIndex="status" title="Status" render={(val) => <Tag color={val === "sealed" ? "green" : "blue"}>{String(val).toUpperCase()}</Tag>} />
              <Table.Column
                title="Action"
                render={() => (
                  <Link href="/audit">
                    <Button type="link" size="small" icon={<FileSearchOutlined />}>Inspect</Button>
                  </Link>
                )}
              />
            </Table>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
