"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  Card, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Space, 
  Breadcrumb, 
  Divider, 
  Statistic,
  Alert,
  Button
} from "antd";
import { 
  BellOutlined, 
  HomeOutlined, 
  ArrowLeftOutlined, 
  HistoryOutlined,
  BlockOutlined,
  LinkOutlined
} from "@ant-design/icons";
import { useGovernorObservability } from "@/hooks/useGovernorObservability";
import { AlertActionPanel } from "@/components/governor/AlertActionPanel";
import dayjs from "dayjs";

const { Title, Text, Paragraph } = Typography;

export default function AlertDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const { useAlert, ackAlert, resolveAlert, suppressAlert } = useGovernorObservability();
  const { query } = useAlert(id as string) as any;
  const { data, isLoading, refetch } = query;

  const alert = data?.data as any;

  if (isLoading) return <Card loading />;
  if (!alert) return <Alert message="Alert not found" type="error" />;

  const getSeverityColor = (severity: string) => {
    if (severity === "CRITICAL") return "#cf1322";
    if (severity === "HIGH") return "#d48806";
    if (severity === "WARNING") return "#d4b106";
    return "#096dd9";
  };

  return (
    <div style={{ padding: "24px" }}>
      <Breadcrumb style={{ marginBottom: "16px" }}>
        <Breadcrumb.Item href="/"><HomeOutlined /></Breadcrumb.Item>
        <Breadcrumb.Item href="/governor/observability">Governance</Breadcrumb.Item>
        <Breadcrumb.Item href="/governor/alerts">Alert Center</Breadcrumb.Item>
        <Breadcrumb.Item>{alert.title}</Breadcrumb.Item>
      </Breadcrumb>

      <div style={{ marginBottom: "24px" }}>
        <Space size="middle" style={{ width: "100%", justifyContent: "space-between" }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => router.back()}>Back</Button>
          <Space>
            <Tag color="blue">{alert.alert_type}</Tag>
            <Tag color="default">{alert.domain || "META"}</Tag>
          </Space>
        </Space>
      </div>

      <Row gutter={24}>
        <Col span={16}>
          <Card 
            bordered={false}
            style={{ borderTop: `6px solid ${getSeverityColor(alert.severity)}`, boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <Title level={3} style={{ margin: 0 }}>{alert.title}</Title>
                <Text type="secondary" style={{ fontSize: "12px" }}>ID: {alert.id}</Text>
              </div>
              <Tag color={getSeverityColor(alert.severity)} style={{ padding: "4px 12px", fontSize: "14px" }}>{alert.severity}</Tag>
            </div>

            <Divider />

            <Paragraph style={{ fontSize: "16px" }}>
              {alert.summary}
            </Paragraph>

            <Row gutter={16} style={{ marginTop: "32px" }}>
              <Col span={12}>
                <Statistic 
                  title="Recorded Metric" 
                  value={alert.metric_value} 
                  precision={2}
                  valueStyle={{ color: "#262626" }}
                />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="Safety Threshold" 
                  value={alert.threshold_value} 
                  precision={2}
                  valueStyle={{ color: "#8c8c8c" }}
                />
              </Col>
            </Row>

            <div style={{ marginTop: "32px", padding: "16px", background: "#f9f9f9", borderRadius: "8px" }}>
              <Title level={5}><BlockOutlined /> Evidence Payload</Title>
              <pre style={{ fontSize: "11px", overflow: "auto", maxHeight: "300px" }}>
                {JSON.stringify(alert.evidence_payload || {}, null, 2)}
              </pre>
            </div>
          </Card>
        </Col>

        <Col span={8}>
          <Space direction="vertical" style={{ width: "100%" }} size={24}>
            <AlertActionPanel 
              alertId={alert.id}
              status={alert.status}
              onAck={() => { ackAlert(alert.id, "OPERATOR"); refetch(); }}
              onResolve={(msg) => { resolveAlert(alert.id, msg); refetch(); }}
              onSuppress={(msg) => { suppressAlert(alert.id, msg); refetch(); }}
            />

            <Card size="small" title="Context">
              <Space direction="vertical" style={{ width: "100%" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Text type="secondary">Opened At</Text>
                  <Text>{dayjs(alert.opened_at).format("YYYY-MM-DD HH:mm")}</Text>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Text type="secondary">Lineage</Text>
                  <Button type="link" size="small" icon={<LinkOutlined />}>View Decision Trail</Button>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Text type="secondary">History</Text>
                  <Button type="link" size="small" icon={<HistoryOutlined />}>Scan Similar</Button>
                </div>
              </Space>
            </Card>
          </Space>
        </Col>
      </Row>
    </div>
  );
}
