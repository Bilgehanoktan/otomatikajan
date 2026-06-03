"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Card, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Space, 
  Breadcrumb, 
  Divider, 
  Button,
  Statistic,
  Alert,
  Result
} from "antd";
import { 
  LockOutlined, 
  HomeOutlined, 
  ArrowLeftOutlined, 
  CheckCircleOutlined,
  DownloadOutlined,
  DeploymentUnitOutlined,
  AuditOutlined
} from "@ant-design/icons";
import { useCustom, useCustomMutation } from "@refinedev/core";
import dayjs from "dayjs";

const { Title, Text, Paragraph } = Typography;

export default function SnapshotDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const { mutate: exportBundle } = useCustomMutation();
  const snapshotId = Array.isArray(id) ? id[0] : id;
  
  const snapshotQuery = useCustom<any>({
    url: `governance/governor/proof/snapshots/${snapshotId}`,
    method: "get"
  });
  const { data, isLoading } = snapshotQuery.query;

  const snapshot = data?.data as any;

  if (isLoading) return <Card loading />;
  if (!snapshot) return <Alert message="Snapshot not found" type="error" />;

  return (
    <div style={{ padding: "24px" }}>
      <Breadcrumb 
        style={{ marginBottom: "16px" }}
        items={[
          { title: <Link href="/"><HomeOutlined /></Link> },
          { title: <Link href="/governor/observability">Governance</Link> },
          { title: <Link href="/governor/proof">Proof Fabric</Link> },
          { title: snapshot.snapshot_name }
        ]}
      />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.back()}>Back</Button>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={() => exportBundle({ url: `/governance/governor/proof/export/${snapshotId}`, method: "post", values: {} })}>
            Export Audit Bundle
          </Button>
          <Button type="primary" icon={<CheckCircleOutlined />}>Verify Integrity</Button>
        </Space>
      </div>

      <Row gutter={24}>
        <Col span={16}>
          <Card variant="borderless" style={{ boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <Space direction="vertical" size={0}>
                <Title level={3} style={{ margin: 0 }}>{snapshot.snapshot_name}</Title>
                <Text type="secondary">Cryptographically sealed governance window</Text>
              </Space>
              <Tag color="green" style={{ padding: "4px 12px", fontSize: "14px" }}>{snapshot.seal_status}</Tag>
            </div>

            <Divider />

            <Row gutter={16}>
              <Col span={12}>
                <Card size="small" title="Merkle Root Hash">
                  <Text copyable code>{snapshot.merkle_root}</Text>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="Snapshot Signature">
                  <Text copyable code>{snapshot.snapshot_hash}</Text>
                </Card>
              </Col>
            </Row>

            <div style={{ marginTop: "32px" }}>
              <Title level={5}><AuditOutlined /> Governance Range</Title>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="Start Index" value={snapshot.start_chain_index} />
                </Col>
                <Col span={8}>
                  <Statistic title="End Index" value={snapshot.end_chain_index} />
                </Col>
                <Col span={8}>
                  <Statistic title="Total Events" value={snapshot.event_count} />
                </Col>
              </Row>
            </div>

            <Divider />
            
            <div style={{ textAlign: "center", padding: "32px" }}>
              <DeploymentUnitOutlined style={{ fontSize: "64px", color: "#f0f0f0" }} />
              <Paragraph style={{ color: "#8c8c8c", marginTop: "16px" }}>
                Merkle Tree structure for this snapshot is stored in the database.<br/>
                Membership proofs can be generated for any event in this range.
              </Paragraph>
            </div>
          </Card>
        </Col>

        <Col span={8}>
          <Card title="Seal Metadata" size="small">
            <Space direction="vertical" style={{ width: "100%" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <Text type="secondary">Sealed At</Text>
                <Text>{dayjs(snapshot.created_at).format("YYYY-MM-DD HH:mm")}</Text>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <Text type="secondary">Signer</Text>
                <Tag color="blue">{snapshot.sealed_by || "SYSTEM"}</Tag>
              </div>
              <Divider style={{ margin: "12px 0" }} />
              <Alert 
                type="success" 
                showIcon 
                message="Verification Active" 
                description="This snapshot is continuously verified against the underlying event chain."
              />
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
}


