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
  Progress,
  Button,
  Alert
} from "antd";
import { 
  RadarChartOutlined, 
  HomeOutlined, 
  ArrowLeftOutlined, 
  LinkOutlined,
  HistoryOutlined,
  DeploymentUnitOutlined
} from "@ant-design/icons";
import { useGovernorObservability } from "@/hooks/useGovernorObservability";
import { DriftRecord } from "@/components/governor/DriftTable";
import dayjs from "dayjs";

const { Title, Text, Paragraph } = Typography;

export default function DriftDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const { useDrifts } = useGovernorObservability();
  const { data, isLoading } = useDrifts();

  // Find the specific drift from the list
  const drift = (data?.data as unknown as DriftRecord[])?.find((d) => d.id === id);

  if (isLoading) return <Card loading />;
  if (!drift) return <Alert message="Drift record not found" type="error" />;

  return (
    <div style={{ padding: "24px" }}>
      <Breadcrumb style={{ marginBottom: "16px" }}>
        <Breadcrumb.Item href="/"><HomeOutlined /></Breadcrumb.Item>
        <Breadcrumb.Item href="/governor/observability">Governance</Breadcrumb.Item>
        <Breadcrumb.Item href="/governor/drifts">Drift Monitor</Breadcrumb.Item>
        <Breadcrumb.Item>Drift Analysis</Breadcrumb.Item>
      </Breadcrumb>

      <div style={{ marginBottom: "24px" }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.back()}>Back</Button>
      </div>

      <Row gutter={24}>
        <Col span={16}>
          <Card bordered={false} style={{ boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <Space direction="vertical" size={0}>
                <Title level={3} style={{ margin: 0 }}>{drift.drift_type}</Title>
                <Text type="secondary">Detected pattern deviation in {drift.domain || "META"} domain</Text>
              </Space>
              <Tag color="cyan" style={{ padding: "4px 12px" }}>ANALYZED</Tag>
            </div>

            <Divider />

            <div style={{ padding: "24px", background: "#f0f5ff", borderRadius: "8px", marginBottom: "32px" }}>
              <Row gutter={16} align="middle">
                <Col span={8}>
                  <Progress 
                    type="circle" 
                    percent={Math.min(100, drift.drift_score * 100)} 
                    strokeColor={drift.drift_score > 0.3 ? "#ff4d4f" : "#1890ff"}
                    width={120}
                  />
                </Col>
                <Col span={16}>
                  <Title level={4} style={{ margin: 0 }}>Drift Score: {(drift.drift_score * 100).toFixed(1)}%</Title>
                  <Paragraph style={{ marginTop: "8px" }}>
                    {drift.summary}
                  </Paragraph>
                </Col>
              </Row>
            </div>

            <Title level={5}><HistoryOutlined /> Analysis Windows</Title>
            <Row gutter={16} style={{ marginBottom: "32px" }}>
              <Col span={12}>
                <Card size="small" title="Baseline Window">
                  <Text strong style={{ fontSize: "18px" }}>{drift.baseline_window_days} Days</Text>
                  <Text type="secondary" style={{ display: "block" }}>Historical behavior profile</Text>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="Comparison Window">
                  <Text strong style={{ fontSize: "18px" }}>{drift.current_window_days} Days</Text>
                  <Text type="secondary" style={{ display: "block" }}>Anomalous period analyzed</Text>
                </Card>
              </Col>
            </Row>

            <Title level={5}><DeploymentUnitOutlined /> Evidence & Correlation</Title>
            <Card size="small" bodyStyle={{ padding: 0 }}>
              <pre style={{ fontSize: "11px", padding: "16px", background: "#fafafa", margin: 0, maxHeight: "300px", overflow: "auto" }}>
                {JSON.stringify(drift.evidence_payload || {}, null, 2)}
              </pre>
            </Card>
          </Card>
        </Col>

        <Col span={8}>
          <Space direction="vertical" style={{ width: "100%" }} size={24}>
            <Card title="Quick Insights" size="small">
              <Paragraph style={{ fontSize: "13px" }}>
                This drift indicates a significant shift in how the system handles <b>{drift.drift_type}</b>. 
                Recommended action: Review recent <b>Policy Evolutions</b> or <b>Deployment changes</b>.
              </Paragraph>
              <Divider style={{ margin: "12px 0" }} />
              <Space direction="vertical" style={{ width: "100%" }}>
                <Button block icon={<LinkOutlined />}>View Related Lineage</Button>
                <Button block icon={<LinkOutlined />}>Open Related Alerts</Button>
              </Space>
            </Card>

            <Card size="small" title="Metadata">
              <Space direction="vertical" style={{ width: "100%" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Text type="secondary">Detected</Text>
                  <Text>{dayjs(drift.created_at).format("YYYY-MM-DD HH:mm")}</Text>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Text type="secondary">Confidence</Text>
                  <Tag color="green">HIGH</Tag>
                </div>
              </Space>
            </Card>
          </Space>
        </Col>
      </Row>
    </div>
  );
}
