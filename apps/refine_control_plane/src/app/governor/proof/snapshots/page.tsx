"use client";

import Link from "next/link";
import dayjs from "dayjs";
import { Breadcrumb, Button, Card, Space, Table, Tag, Typography } from "antd";
import {
  FileSearchOutlined,
  HomeOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { useList } from "@refinedev/core";

const { Title, Text } = Typography;

interface ProofSnapshotRecord {
  id: string;
  snapshot_name: string;
  merkle_root: string;
  snapshot_hash: string;
  event_count: number;
  seal_status: string;
  created_at: string;
}

export default function ProofSnapshotsPage() {
  const {
    query: { data, isLoading },
  } = useList<ProofSnapshotRecord>({
    resource: "governance/governor/proof/snapshots",
    pagination: { pageSize: 50 },
    sorters: [{ field: "created_at", order: "desc" }],
  });

  const snapshots = data?.data ?? [];

  return (
    <div style={{ padding: "24px" }}>
      <Breadcrumb
        style={{ marginBottom: "16px" }}
        items={[
          { title: <Link href="/"><HomeOutlined /></Link> },
          { title: <Link href="/governor/proof">Proof Fabric</Link> },
          { title: "Snapshots" },
        ]}
      />

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
        }}
      >
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <LockOutlined style={{ marginRight: 12, color: "#52c41a" }} />
            Proof Snapshots
          </Title>
          <Text type="secondary">
            Sealed Merkle snapshots of the immutable governance chain.
          </Text>
        </div>
        <Space>
          <Link href="/governor/proof">
            <Button icon={<SafetyCertificateOutlined />}>Back to Proof Fabric</Button>
          </Link>
          <Link href="/proof/events">
            <Button type="primary" icon={<FileSearchOutlined />}>
              Open Event Ledger
            </Button>
          </Link>
        </Space>
      </div>

      <Card>
        <Table<ProofSnapshotRecord>
          dataSource={snapshots}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20 }}
          size="middle"
          scroll={{ x: 960 }}
        >
          <Table.Column<ProofSnapshotRecord>
            title="Snapshot"
            dataIndex="snapshot_name"
            render={(value: string) => <Text strong>{value}</Text>}
          />
          <Table.Column<ProofSnapshotRecord>
            title="Status"
            dataIndex="seal_status"
            width={140}
            render={(value: string) => (
              <Tag color={value === "sealed" ? "green" : "blue"}>
                {value.toUpperCase()}
              </Tag>
            )}
          />
          <Table.Column<ProofSnapshotRecord>
            title="Events"
            dataIndex="event_count"
            width={120}
          />
          <Table.Column<ProofSnapshotRecord>
            title="Merkle Root"
            dataIndex="merkle_root"
            width={220}
            ellipsis
            render={(value: string) => (
              <Text copyable={{ text: value }}>{value.slice(0, 18)}...</Text>
            )}
          />
          <Table.Column<ProofSnapshotRecord>
            title="Snapshot Hash"
            dataIndex="snapshot_hash"
            ellipsis
            render={(value: string) => (
              <Text copyable={{ text: value }}>{value.slice(0, 18)}...</Text>
            )}
          />
          <Table.Column<ProofSnapshotRecord>
            title="Created"
            dataIndex="created_at"
            width={180}
            render={(value: string) => dayjs(value).format("YYYY-MM-DD HH:mm:ss")}
          />
          <Table.Column<ProofSnapshotRecord>
            title="Action"
            width={120}
            render={() => (
              <Link href="/audit">
                <Button type="link" size="small" icon={<FileSearchOutlined />}>
                  Inspect
                </Button>
              </Link>
            )}
          />
        </Table>
      </Card>
    </div>
  );
}
