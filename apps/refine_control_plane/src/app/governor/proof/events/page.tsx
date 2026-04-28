"use client";

import Link from "next/link";
import dayjs from "dayjs";
import { Breadcrumb, Button, Card, Space, Table, Tag, Typography } from "antd";
import { FileSearchOutlined, HistoryOutlined, HomeOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
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

export default function ProofEventsPage() {
  const {
    query: { data, isLoading },
  } = useList<LineageRecord>({
    resource: "governance/lineage",
    pagination: { pageSize: 50 },
    sorters: [{ field: "created_at", order: "desc" }],
  });

  const events = data?.data ?? [];

  return (
    <div style={{ padding: "24px" }}>
      <Breadcrumb style={{ marginBottom: "16px" }}>
        <Breadcrumb.Item href="/"><HomeOutlined /></Breadcrumb.Item>
        <Breadcrumb.Item href="/governor/proof">Proof Fabric</Breadcrumb.Item>
        <Breadcrumb.Item>Event Ledger</Breadcrumb.Item>
      </Breadcrumb>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <HistoryOutlined style={{ marginRight: 12, color: "#1677ff" }} />
            Proof Event Ledger
          </Title>
          <Text type="secondary">Immutable governance decisions ordered by ledger time.</Text>
        </div>
        <Space>
          <Link href="/governor/proof">
            <Button icon={<SafetyCertificateOutlined />}>Back to Proof Fabric</Button>
          </Link>
          <Link href="/proof/snapshots">
            <Button type="primary" icon={<FileSearchOutlined />}>Open Snapshots</Button>
          </Link>
        </Space>
      </div>

      <Card>
        <Table<LineageRecord>
          dataSource={events}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20 }}
          size="middle"
          scroll={{ x: 960 }}
        >
          <Table.Column<LineageRecord>
            title="Component"
            dataIndex="component_name"
            width={180}
            render={(value: string) => <Text strong>{value}</Text>}
          />
          <Table.Column<LineageRecord>
            title="Decision"
            dataIndex="decision_type"
            width={180}
            render={(value: string) => <Tag color="blue">{value}</Tag>}
          />
          <Table.Column<LineageRecord>
            title="Outcome"
            dataIndex="outcome"
            width={160}
            render={(value?: string | null) => value ? <Tag color="green">{value}</Tag> : <Text type="secondary">-</Text>}
          />
          <Table.Column<LineageRecord>
            title="Confidence"
            dataIndex="confidence_score"
            width={120}
            render={(value: number) => `${Math.round((value || 0) * 100)}%`}
          />
          <Table.Column<LineageRecord>
            title="Integrity Hash"
            dataIndex="integrity_hash"
            ellipsis
            render={(value: string | null | undefined, record) => <Text copyable={{ text: value || record.id }}>{(value || record.id).slice(0, 12)}...</Text>}
          />
          <Table.Column<LineageRecord>
            title="Created"
            dataIndex="created_at"
            width={180}
            render={(value: string) => dayjs(value).format("YYYY-MM-DD HH:mm:ss")}
          />
        </Table>
      </Card>
    </div>
  );
}
