"use client";

import React from "react";
import { Row, Col, Card, Statistic, Typography, Button, Space, Divider, Alert } from "antd";
import { 
  ReloadOutlined, 
  BellOutlined, 
  RadarChartOutlined, 
  DashboardOutlined,
  SafetyCertificateOutlined,
  ExclamationCircleOutlined
} from "@ant-design/icons";
import { useGovernorObservability } from "@/hooks/useGovernorObservability";
import { MetricScoreboard } from "@/components/governor/MetricScoreboard";
import { AlertTable, AlertRecord } from "@/components/governor/AlertTable";
import { DriftTable, DriftRecord } from "@/components/governor/DriftTable";
import { useRouter } from "next/navigation";

const { Title, Text } = Typography;

export default function ObservabilityDashboard() {
  const router = useRouter();
  const { useAlerts, useDrifts, useMetrics, ackAlert, runScan } = useGovernorObservability();
  
  const { query: alertsQuery } = useAlerts({
    status: "OPEN"
  }) as any;
  const { data: alertsData, isLoading: alertsLoading, refetch: refetchAlerts } = alertsQuery;

  const { query: driftsQuery } = useDrifts(5) as any;
  const { data: driftsData, isLoading: driftsLoading, refetch: refetchDrifts } = driftsQuery;

  const { query: metricsQuery } = useMetrics() as any;
  const { data: metricsData, isLoading: metricsLoading, refetch: refetchMetrics } = metricsQuery;

  const alerts = (alertsData?.data as unknown as AlertRecord[]) || [];
  const drifts = (driftsData?.data as unknown as DriftRecord[]) || [];
  const metrics = (metricsData?.data as any) || [];

  const handleRefresh = async () => {
    await Promise.all([refetchAlerts(), refetchDrifts(), refetchMetrics()]);
  };

  const handleRunScan = async () => {
    await runScan();
    handleRefresh();
  };

  const kpis = {
    openAlerts: alerts.length,
    criticalAlerts: alerts.filter((a: any) => a.severity === "CRITICAL").length,
    activeDrifts: drifts.filter((d: any) => d.drift_score > 0.3).length,
    accuracy: metrics.find((m: any) => m.metric_key === "decision_accuracy")?.value || 0,
  };

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>Governance Observability</Title>
          <Text type="secondary">System decision quality, behavioral drifts, and active alerts.</Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>Refresh</Button>
          <Button type="primary" icon={<DashboardOutlined />} onClick={handleRunScan}>Trigger Scan</Button>
        </Space>
      </div>

      {/* KPI Strip */}
      <Row gutter={16} style={{ marginBottom: "24px" }}>
        <Col span={6}>
          <Card size="small" style={{ borderTop: "4px solid #ff4d4f" }}>
            <Statistic 
              title="Open Alerts" 
              value={kpis.openAlerts} 
              prefix={<BellOutlined />} 
              valueStyle={{ color: kpis.openAlerts > 0 ? "#cf1322" : "#3f8600" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ borderTop: "4px solid #faad14" }}>
            <Statistic 
              title="Active Drifts" 
              value={kpis.activeDrifts} 
              prefix={<RadarChartOutlined />} 
              valueStyle={{ color: kpis.activeDrifts > 0 ? "#d48806" : "#3f8600" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ borderTop: "4px solid #1890ff" }}>
            <Statistic 
              title="Avg Accuracy" 
              value={kpis.accuracy * 100} 
              precision={1}
              suffix="%"
              prefix={<SafetyCertificateOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ borderTop: "4px solid #52c41a" }}>
            <Statistic 
              title="System Health" 
              value="DEGRADED" 
              valueStyle={{ color: "#faad14", fontSize: "18px" }}
              prefix={<ExclamationCircleOutlined />} 
            />
          </Card>
        </Col>
      </Row>

      <MetricScoreboard metrics={metrics} loading={metricsLoading} />

      <Divider />

      <Row gutter={24}>
        <Col span={24} style={{ marginBottom: "24px" }}>
          <Card 
            title={<Space><BellOutlined /> Recent Open Alerts</Space>} 
            extra={<Button type="link" onClick={() => router.push("/governor/alerts")}>View All</Button>}
          >
            <AlertTable 
              alerts={alerts.slice(0, 5)} 
              loading={alertsLoading} 
              onAck={(id) => ackAlert(id, "OPERATOR")}
              onInspect={(id) => router.push(`/governor/alerts/${id}`)}
            />
          </Card>
        </Col>
        
        <Col span={24}>
          <Card 
            title={<Space><RadarChartOutlined /> Active Behavioral Drifts</Space>}
            extra={<Button type="link" onClick={() => router.push("/governor/drifts")}>View All</Button>}
          >
            <DriftTable 
              drifts={drifts} 
              loading={driftsLoading} 
              onInspect={(id) => router.push(`/governor/drifts/${id}`)}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
