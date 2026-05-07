"use client";

import React from "react";
import { Row, Col, Card, Statistic, Typography, Button, Space, Divider } from "antd";
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
import { useTranslations } from "next-intl";

const { Title, Text } = Typography;

export default function ObservabilityDashboard() {
  const router = useRouter();
  const t = useTranslations("observability");
  const { useAlerts, useDrifts, useMetrics, ackAlert, runScan } = useGovernorObservability();
  
  const { query: alertsQuery } = useAlerts([
    { field: "status", operator: "eq", value: "OPEN" }
  ]);
  const { data: alertsData, isLoading: alertsLoading, refetch: refetchAlerts } = alertsQuery;

  const { query: driftsQuery } = useDrifts(5);
  const { data: driftsData, isLoading: driftsLoading, refetch: refetchDrifts } = driftsQuery;

  const { query: metricsQuery } = useMetrics();
  const { data: metricsData, isLoading: metricsLoading, refetch: refetchMetrics } = metricsQuery;

  const alerts = (alertsData?.data as AlertRecord[]) || [];
  const drifts = (driftsData?.data as DriftRecord[]) || [];
  const metrics = (metricsData?.data as Array<{ metric_key: string; value: number }>) || [];

  const handleRefresh = async () => {
    await Promise.all([refetchAlerts(), refetchDrifts(), refetchMetrics()]);
  };

  const handleRunScan = async () => {
    await runScan();
    handleRefresh();
  };

  const kpis = {
    openAlerts: alerts.length,
    criticalAlerts: alerts.filter((a) => a.severity === "CRITICAL").length,
    activeDrifts: drifts.filter((d) => d.drift_score > 0.3).length,
    accuracy: metrics.find((m) => m.metric_key === "decision_accuracy")?.value || 0,
  };

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>{t("title")}</Title>
          <Text type="secondary">{t("subtitle")}</Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>{t("actions.refresh")}</Button>
          <Button type="primary" icon={<DashboardOutlined />} onClick={handleRunScan}>{t("actions.triggerScan")}</Button>
        </Space>
      </div>

      {/* KPI Strip */}
      <Row gutter={16} style={{ marginBottom: "24px" }}>
        <Col span={6}>
          <Card variant="borderless" style={{ borderTop: "4px solid #ff4d4f" }}>
            <Statistic 
              title={t("kpis.openAlerts")} 
              value={kpis.openAlerts} 
              prefix={<BellOutlined />} 
              valueStyle={{ color: kpis.openAlerts > 0 ? "#cf1322" : "#3f8600" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card variant="borderless" style={{ borderTop: "4px solid #faad14" }}>
            <Statistic 
              title={t("kpis.activeDrifts")} 
              value={kpis.activeDrifts} 
              prefix={<RadarChartOutlined />} 
              valueStyle={{ color: kpis.activeDrifts > 0 ? "#d48806" : "#3f8600" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card variant="borderless" style={{ borderTop: "4px solid #1890ff" }}>
            <Statistic 
              title={t("kpis.avgAccuracy")} 
              value={kpis.accuracy * 100} 
              precision={1}
              suffix="%"
              prefix={<SafetyCertificateOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card variant="borderless" style={{ borderTop: "4px solid #faad14" }}>
            <Statistic 
              title={t("kpis.systemHealth")} 
              value={t("kpis.degraded")} 
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
            title={<Space><BellOutlined /> {t("alerts.recentTitle")}</Space>} 
            variant="borderless"
            extra={<Button type="link" onClick={() => router.push("/governor/alerts")}>{t("alerts.viewAll")}</Button>}
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
            title={<Space><RadarChartOutlined /> {t("drifts.recentTitle")}</Space>}
            variant="borderless"
            extra={<Button type="link" onClick={() => router.push("/governor/drifts")}>{t("drifts.viewAll")}</Button>}
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
