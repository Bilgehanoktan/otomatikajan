"use client";

import React from "react";
import { List, Tag, Table, Space, Card, Typography, Button, message } from "antd";
import { useList, useUpdate, HttpError } from "@refinedev/core";
import { 
  NodeIndexOutlined, 
  SwapOutlined,
  CheckCircleOutlined
} from "@ant-design/icons";

const { Title, Text } = Typography;

export default function ConflictsPage() {
  const { query } = useList<any, HttpError>({
    resource: "governance/inbox/governor/meta/conflicts",
    filters: [
      {
        field: "status",
        operator: "eq",
        value: "open",
      },
    ],
  }) as any;
  const { data, isLoading, refetch } = query;

  const { mutate: resolveConflict } = useUpdate();

  const handleResolve = (id: string) => {
    resolveConflict({
      resource: "governance/inbox/governor/meta/conflicts",
      id,
      values: {},
      successNotification: {
        message: "Çakışma Çözüldü",
        description: "Karar çakışması manuel olarak çözüldü işaretlendi.",
        type: "success"
      },
    }, {
      onSuccess: () => refetch()
    });
  };

  const conflicts = data?.data || [];

  const columns = [
    {
      title: "Proje",
      dataIndex: "project_id",
      key: "project",
      render: (val: string) => <Text code>{val.slice(0, 8)}...</Text>,
    },
    {
      title: "Alan A",
      dataIndex: "domain_a",
      key: "domain_a",
      render: (val: string, record: any) => (
        <Space direction="vertical" size={0}>
          <Tag color="blue">{val}</Tag>
          <Text type="secondary" style={{ fontSize: "12px" }}>{record.decision_a}</Text>
        </Space>
      ),
    },
    {
      title: "",
      key: "vs",
      render: () => <SwapOutlined style={{ color: "#66fcf1" }} />,
    },
    {
      title: "Alan B",
      dataIndex: "domain_b",
      key: "domain_b",
      render: (val: string, record: any) => (
        <Space direction="vertical" size={0}>
          <Tag color="purple">{val}</Tag>
          <Text type="secondary" style={{ fontSize: "12px" }}>{record.decision_b}</Text>
        </Space>
      ),
    },
    {
      title: "Çakışma Tipi",
      dataIndex: "conflict_type",
      key: "type",
      render: (val: string) => <Tag color="volcano">{val}</Tag>,
    },
    {
      title: "Özet",
      dataIndex: "conflict_summary",
      key: "summary",
    },
    {
      title: "Aksiyon",
      key: "action",
      render: (_: any, record: any) => (
        <Button 
          type="primary" 
          ghost 
          icon={<CheckCircleOutlined />} 
          onClick={() => handleResolve(record.id)}
        >
          Çözüldü İşaretle
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>🧬 Domain Conflict Management</Title>
      <Text type="secondary">
        Farklı governor alanları arasındaki karar uyumsuzluklarını ve risk ayrışmalarını yönetin.
      </Text>

      <Card 
        title={
          <Space>
            <NodeIndexOutlined />
            <span>Aktif Çakışmalar</span>
          </Space>
        } 
        style={{ marginTop: "24px" }}
        variant="borderless" 
        className="resilience-card"
      >
        <Table
          dataSource={conflicts}
          columns={columns}
          loading={isLoading}
          rowKey="id"
        />
      </Card>
    </div>
  );
}
