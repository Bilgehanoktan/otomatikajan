"use client";

import React from "react";
import { Card, Typography, Space, Breadcrumb, Alert } from "antd";
import { RadarChartOutlined, HomeOutlined, HistoryOutlined } from "@ant-design/icons";
import { useGovernorObservability } from "@/hooks/useGovernorObservability";
import { DriftTable, DriftRecord } from "@/components/governor/DriftTable";
import { useRouter } from "next/navigation";

const { Title, Text } = Typography;

export default function DriftMonitor() {
  const router = useRouter();
  const { useDrifts } = useGovernorObservability();
  const { query } = useDrifts() as any;
  const { data, isLoading } = query;

  const drifts = (data?.data as unknown as DriftRecord[]) || [];

  return (
    <div style={{ padding: "24px" }}>
      <Breadcrumb style={{ marginBottom: "16px" }}>
        <Breadcrumb.Item href="/"><HomeOutlined /></Breadcrumb.Item>
        <Breadcrumb.Item href="/governor/observability">Governance</Breadcrumb.Item>
        <Breadcrumb.Item>Drift Monitor</Breadcrumb.Item>
      </Breadcrumb>

      <div style={{ marginBottom: "24px" }}>
        <Title level={2} style={{ margin: 0 }}><RadarChartOutlined /> Behavioral Drift Monitor</Title>
        <Text type="secondary">Detect long-term shifts in governance behavior and decision patterns.</Text>
      </div>

      <Alert 
        message="System Analysis Active"
        description="Comparing last 24h performance against 14d baseline. Drift scores above 30% trigger high-severity alerts."
        type="info"
        showIcon
        icon={<HistoryOutlined />}
        style={{ marginBottom: "24px" }}
      />

      <Card size="small">
        <DriftTable 
          drifts={drifts} 
          loading={isLoading}
          onInspect={(id) => router.push(`/governor/drifts/${id}`)}
        />
      </Card>
    </div>
  );
}
