"use client";

import React from "react";
import { Table, Tag, Button, Typography, Card, Space, Input, Spin } from "antd";
import { UserOutlined, SearchOutlined, SafetyOutlined } from "@ant-design/icons";
import { useApiUrl, useCustom } from "@refinedev/core";

const { Title, Text } = Typography;

interface Agent {
  id: string;
  name: string;
  role: string;
  status: string;
  trust_score: number;
  current_load: number;
}

export default function AgentRegistryPage() {
  const apiUrl = useApiUrl();
  const agentsQuery = useCustom<Agent[]>({
    url: `${apiUrl}/fleet/ops/agents`,
    method: "get",
  });

  const { query } = agentsQuery;
  const { data, isLoading, refetch } = query;
  const agents: Agent[] = data?.data || [];

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      IDLE: "green",
      ASSIGNED: "blue",
      BUSY: "orange",
      PAUSED: "cyan",
      QUARANTINED: "red",
      OFFLINE: "default",
    };
    return colors[status] || "default";
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>Ajan Kayıt Defteri</Title>

      <Card variant="borderless" style={{ marginBottom: 24 }}>
        <Space>
          <Input prefix={<SearchOutlined />} placeholder="Ajan ara..." style={{ width: 300 }} />
          <Button type="primary" onClick={() => refetch()}>
            Yenile
          </Button>
          <Button>Yeni Ajan Ekle</Button>
        </Space>
      </Card>

      <Spin spinning={isLoading}>
        <Table
          dataSource={agents}
          rowKey="id"
          columns={[
            {
              title: "Ajan Adı",
              dataIndex: "name",
              key: "name",
              render: (text: string) => (
                <Space>
                  <UserOutlined />
                  {text}
                </Space>
              ),
            },
            {
              title: "Rol",
              dataIndex: "role",
              key: "role",
              render: (role: string) => <Tag color="blue">{role}</Tag>,
            },
            {
              title: "Durum",
              dataIndex: "status",
              key: "status",
              render: (status: string) => <Tag color={getStatusColor(status)}>{status}</Tag>,
            },
            {
              title: "Güven Skoru",
              dataIndex: "trust_score",
              key: "trust_score",
              render: (score: number) => <Text strong>{(score ?? 0).toFixed(2)}</Text>,
            },
            { title: "Güncel Yük", dataIndex: "current_load", key: "current_load" },
            {
              title: "İşlemler",
              key: "actions",
              render: (_: unknown, record: Agent) => (
                <Space>
                  <Button size="small">Detaylar</Button>
                  {record.status !== "QUARANTINED" && (
                    <Button size="small" danger icon={<SafetyOutlined />}>
                      Karantinaya Al
                    </Button>
                  )}
                </Space>
              ),
            },
          ]}
        />
      </Spin>
    </div>
  );
}
