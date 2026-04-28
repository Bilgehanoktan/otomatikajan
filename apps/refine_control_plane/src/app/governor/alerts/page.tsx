"use client";

import React, { useState } from "react";
import { Card, Typography, Space, Select, Tag, Button, Breadcrumb } from "antd";
import { BellOutlined, FilterOutlined, HomeOutlined } from "@ant-design/icons";
import { useGovernorObservability } from "@/hooks/useGovernorObservability";
import { AlertTable, AlertRecord } from "@/components/governor/AlertTable";
import { useRouter } from "next/navigation";

const { Title, Text } = Typography;

export default function AlertCenter() {
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState("OPEN");
  const { useAlerts, ackAlert } = useGovernorObservability();

  const { query } = useAlerts({
    status: statusFilter
  }) as any;
  const { data, isLoading, refetch } = query;

  const alerts = (data?.data as unknown as AlertRecord[]) || [];

  return (
    <div style={{ padding: "24px" }}>
      <Breadcrumb style={{ marginBottom: "16px" }}>
        <Breadcrumb.Item href="/"><HomeOutlined /></Breadcrumb.Item>
        <Breadcrumb.Item href="/governor/observability">Governance</Breadcrumb.Item>
        <Breadcrumb.Item>Alert Center</Breadcrumb.Item>
      </Breadcrumb>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <Title level={2} style={{ margin: 0 }}><BellOutlined /> Alert Center</Title>
          <Text type="secondary">Review and manage system-generated governance alerts.</Text>
        </div>
        
        <Space size="middle">
          <div style={{ display: "flex", flexDirection: "column" }}>
            <Text type="secondary" style={{ fontSize: "12px", marginBottom: "4px" }}>STATUS FILTER</Text>
            <Select 
              value={statusFilter} 
              style={{ width: 150 }} 
              onChange={(v) => setStatusFilter(v)}
            >
              <Select.Option value="OPEN">Open</Select.Option>
              <Select.Option value="ACKNOWLEDGED">Acknowledged</Select.Option>
              <Select.Option value="RESOLVED">Resolved</Select.Option>
              <Select.Option value="SUPPRESSED">Suppressed</Select.Option>
            </Select>
          </div>
          <Button icon={<FilterOutlined />}>More Filters</Button>
        </Space>
      </div>

      <Card size="small">
        <div style={{ marginBottom: "12px" }}>
          <Space>
            <Tag color="error">{alerts.length} Records Found</Tag>
            {statusFilter === "OPEN" && <Tag color="warning">Action Required</Tag>}
          </Space>
        </div>
        
        <AlertTable 
          alerts={alerts} 
          loading={isLoading}
          onAck={(id) => {
            ackAlert(id, "OPERATOR");
            refetch();
          }}
          onInspect={(id) => router.push(`/governor/alerts/${id}`)}
        />
      </Card>
    </div>
  );
}
