"use client";

import React from "react";
import { Table, Tag, Button, Typography, Card, Space, Input, Spin } from "antd";
import { UserOutlined, SearchOutlined, SafetyOutlined } from "@ant-design/icons";
import { useCustom } from "@refinedev/core";

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
  const { data, isLoading, refetch } = useCustom({
    url: "http://127.0.0.1:8000/api/v1/fleet/agents",
    method: "get",
  });

  const agents: Agent[] = (data?.data as any) || [];

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      IDLE: 'green',
      ASSIGNED: 'blue',
      BUSY: 'orange',
      PAUSED: 'cyan',
      QUARANTINED: 'red',
      OFFLINE: 'default'
    };
    return colors[status] || 'default';
  };

  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>Ajan Kayıt Defteri</Title>
      
      <Card bordered={false} style={{ marginBottom: '24px' }}>
        <Space>
          <Input prefix={<SearchOutlined />} placeholder="Ajan ara..." style={{ width: 300 }} />
          <Button type="primary" onClick={() => refetch?.()}>Yenile</Button>
          <Button>Yeni Ajan Ekle</Button>
        </Space>
      </Card>

      <Spin spinning={isLoading}>
        <Table 
          dataSource={agents} 
          rowKey="id"
          columns={[
            { 
              title: 'Ajan Adı', 
              dataIndex: 'name', 
              key: 'name', 
              render: (text: string) => <Space><UserOutlined />{text}</Space> 
            },
            { 
              title: 'Rol', 
              dataIndex: 'role', 
              key: 'role', 
              render: (role: string) => <Tag color="blue">{role}</Tag> 
            },
            { 
              title: 'Durum', 
              dataIndex: 'status', 
              key: 'status',
              render: (status: string) => <Tag color={getStatusColor(status)}>{status}</Tag>
            },
            { 
              title: 'Güven Skoru', 
              dataIndex: 'trust_score', 
              key: 'trust_score', 
              render: (score: number) => <Text strong>{score.toFixed(2)}</Text> 
            },
            { title: 'Güncel Yük', dataIndex: 'current_load', key: 'current_load' },
            { 
              title: 'İşlemler', 
              key: 'actions',
              render: (_, record: Agent) => (
                <Space>
                  <Button size="small">Detaylar</Button>
                  {record.status !== 'QUARANTINED' && (
                    <Button size="small" danger icon={<SafetyOutlined />}>Karantinaya Al</Button>
                  )}
                </Space>
              )
            }
          ]}
        />
      </Spin>
    </div>
  );
}
