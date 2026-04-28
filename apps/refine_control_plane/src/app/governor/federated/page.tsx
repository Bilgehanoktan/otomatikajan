"use client";

import React from "react";
import { List, Tag, Table, Space, Card, Typography, Statistic, Row, Col } from "antd";
import { useList, HttpError } from "@refinedev/core";
import { 
  SafetyCertificateOutlined, 
  WarningOutlined, 
  GlobalOutlined, 
  ThunderboltOutlined,
  ProjectOutlined
} from "@ant-design/icons";

const { Title, Text } = Typography;

export default function FederatedGovernorPage() {
  const { query } = useList<any, HttpError>({
    resource: "governor/meta/decisions",
  }) as any;
  const { data, isLoading } = query;

  const decisions = data?.data || [];

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "CRITICAL": return "volcano";
      case "HIGH": return "orange";
      case "MEDIUM": return "blue";
      default: return "green";
    }
  };

  const getDomainIcon = (domain: string) => {
    switch (domain) {
      case "POLICY": return <GlobalOutlined />;
      case "INCIDENT": return <WarningOutlined />;
      case "REPAIR": return <ThunderboltOutlined />;
      case "WORKFLOW": return <ProjectOutlined />;
      default: return <SafetyCertificateOutlined />;
    }
  };

  const columns = [
    {
      title: "Proje",
      dataIndex: "project_id",
      key: "project",
      render: (val: string) => <Text code>{val.slice(0, 8)}...</Text>,
    },
    {
      title: "Hakim Alan (Domain)",
      dataIndex: "winning_domain",
      key: "domain",
      render: (val: string) => (
        <Space>
          {getDomainIcon(val)}
          <Text strong>{val}</Text>
        </Space>
      ),
    },
    {
      title: "Karar",
      dataIndex: "final_decision",
      key: "decision",
      render: (val: string) => <Tag color="cyan">{val}</Tag>,
    },
    {
      title: "Risk Sınıfı",
      dataIndex: "final_risk_class",
      key: "risk",
      render: (val: string) => (
        <Tag color={getRiskColor(val)}>{val}</Tag>
      ),
    },
    {
      title: "Kısıtlar",
      dataIndex: "applied_constraints",
      key: "constraints",
      render: (val: string[]) => val?.map(c => <Tag key={c}>{c}</Tag>),
    },
    {
      title: "Tarih",
      dataIndex: "created_at",
      key: "date",
      render: (val: string) => new Date(val).toLocaleString(),
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>🛡️ Federated Governance View</Title>
      <Text type="secondary">
        Alan uzmanı governor'ların ortaklaşa verdiği meta-kararların merkezi izleme ekranı.
      </Text>

      <Row gutter={16} style={{ marginTop: "24px", marginBottom: "24px" }}>
        <Col span={6}>
          <Card bordered={false} className="resilience-card">
            <Statistic
              title="Aktif Domain Sayısı"
              value={5}
              prefix={<GlobalOutlined />}
              valueStyle={{ color: "#66fcf1" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="resilience-card">
            <Statistic
              title="Meta Karar Sayısı"
              value={decisions.length}
              prefix={<SafetyCertificateOutlined />}
              valueStyle={{ color: "#45a29e" }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="Son Meta Kararlar" bordered={false} className="resilience-card">
        <Table
          dataSource={decisions}
          columns={columns}
          loading={isLoading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
}
