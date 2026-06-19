"use client";

import Link from "next/link";
import { useTranslations, useFormatter } from "next-intl";
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
  const t = useTranslations("audit");
  const format = useFormatter();
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
      <Breadcrumb 
        style={{ marginBottom: "16px" }}
        items={[
          { title: <Link href="/"><HomeOutlined /></Link> },
          { title: <Link href="/governor/proof">{t("breadcrumb.proofFabric")}</Link> },
          { title: t("breadcrumb.eventLedger") }
        ]}
      />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <HistoryOutlined style={{ marginRight: 12, color: "#1677ff" }} />
            {t("title")}
          </Title>
          <Text type="secondary">{t("subtitle")}</Text>
        </div>
        <Space>
          <Link href="/governor/proof">
            <Button icon={<SafetyCertificateOutlined />}>{t("buttons.backToProof")}</Button>
          </Link>
          <Link href="/proof/snapshots">
            <Button type="primary" icon={<FileSearchOutlined />}>{t("buttons.openSnapshots")}</Button>
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
            title={t("table.component")}
            dataIndex="component_name"
            width={180}
            render={(value: string) => <Text strong>{value}</Text>}
          />
          <Table.Column<LineageRecord>
            title={t("table.decision")}
            dataIndex="decision_type"
            width={180}
            render={(value: string) => <Tag color="blue">{value}</Tag>}
          />
          <Table.Column<LineageRecord>
            title={t("table.outcome")}
            dataIndex="outcome"
            width={160}
            render={(value?: string | null) => value ? <Tag color="green">{value}</Tag> : <Text type="secondary">-</Text>}
          />
          <Table.Column<LineageRecord>
            title={t("table.confidence")}
            dataIndex="confidence_score"
            width={120}
            render={(value: number) => format.number((value || 0), { style: "percent" })}
          />
          <Table.Column<LineageRecord>
            title={t("table.integrityHash")}
            dataIndex="integrity_hash"
            ellipsis
            render={(value: string | null | undefined, record) => <Text copyable={{ text: value || record.id }}>{(value || record.id).slice(0, 12)}...</Text>}
          />
          <Table.Column<LineageRecord>
            title={t("table.created")}
            dataIndex="created_at"
            width={180}
            render={(value: string) => format.dateTime(new Date(value), {
              year: "numeric",
              month: "2-digit",
              day: "2-digit",
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit"
            })}
          />
        </Table>
      </Card>
    </div>
  );
}
