"use client";

import { useCustom } from "@refinedev/core";
import { 
  Breadcrumb, 
  Card, 
  Col, 
  Row, 
  Table, 
  Tag, 
  Typography, 
  Button, 
  Space, 
  Statistic, 
  Badge,
  Tooltip,
  Divider,
  List
} from "antd";
import { 
  HomeOutlined, 
  SafetyCertificateOutlined, 
  VerifiedOutlined, 
  LockOutlined,
  ExportOutlined,
  EyeOutlined,
  HistoryOutlined,
  DatabaseOutlined
} from "@ant-design/icons";
import Link from "next/link";

const { Title, Text } = Typography;

export default function ProofFabricDashboard() {
  const eventsQuery = useCustom({
    url: "governance/inbox/governor/proof/events",
    method: "get",
  });
  const { data: eventsData, isLoading: eventsLoading } = eventsQuery as any;

  const snapshotsQuery = useCustom({
    url: "governance/inbox/governor/proof/snapshots",
    method: "get",
  });
  const { data: snapshotsData, isLoading: snapshotsLoading } = snapshotsQuery as any;

  const events = eventsData?.data || [];
  const snapshots = snapshotsData?.data || [];

  const breadcrumbItems = [
    { title: <Link href="/"><HomeOutlined /></Link> },
    { title: <Link href="/governor/observability">Governance</Link> },
    { title: "Proof Fabric" }
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Breadcrumb 
        items={breadcrumbItems}
        style={{ marginBottom: "16px" }} 
      />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <SafetyCertificateOutlined style={{ marginRight: 12, color: "#1890ff" }} />
            Proof Fabric (Değişmezlik Katmanı)
          </Title>
          <Text type="secondary">Zaman damgalı ve mühürlü karar kanıtları kriptografik olarak doğrulanabilir.</Text>
        </div>
        <Space>
          <Button icon={<HistoryOutlined />}>Denetim Günlüğü</Button>
          <Button type="primary" icon={<VerifiedOutlined />}>Toplu Doğrulama</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card variant="borderless">
            <Statistic title="Toplam Kanıt" value={4282} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card variant="borderless">
            <Statistic title="Mühürlü Snapshot" value={142} prefix={<LockOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card variant="borderless">
            <Statistic title="Bütünlük Skoru" value={100} suffix="%" prefix={<VerifiedOutlined />} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card variant="borderless">
            <Statistic title="Bekleyen Mühür" value={14} prefix={<Badge status="processing" />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: "24px" }}>
        <Col span={16}>
          <Card 
            title={<span><HistoryOutlined /> Son Kanıt Olayları</span>} 
            variant="borderless"
            extra={<Button type="link">Tümünü Gör</Button>}
          >
            <Table
              dataSource={events}
              loading={eventsLoading}
              rowKey="id"
              pagination={{ pageSize: 5 }}
              size="small"
            >
              <Table.Column 
                title="Tip" 
                dataIndex="event_type" 
                render={(val) => <Tag color="blue">{val}</Tag>} 
              />
              <Table.Column 
                title="Bileşen" 
                dataIndex="component" 
              />
              <Table.Column 
                title="Bütünlük Özeti" 
                dataIndex="integrity_hash" 
                render={(val) => <Text code style={{ fontSize: "10px" }}>{val?.substring(0, 12)}...</Text>} 
              />
              <Table.Column 
                title="Durum" 
                dataIndex="status" 
                render={(val) => <Badge status={val === "VERIFIED" ? "success" : "processing"} text={val} />} 
              />
              <Table.Column 
                title="Tarih" 
                dataIndex="timestamp" 
                render={(val) => new Date(val).toLocaleString()} 
              />
            </Table>
          </Card>
        </Col>
        <Col span={8}>
          <Card 
            title={<span><LockOutlined /> Kriptografik Snapshotlar</span>} 
            variant="borderless"
          >
            <List
              loading={snapshotsLoading}
              dataSource={snapshots}
              renderItem={(item: any) => (
                <List.Item
                  actions={[
                    <Tooltip title="Doğrula" key="v"><Button type="text" icon={<VerifiedOutlined />} /></Tooltip>,
                    <Tooltip title="Dışa Aktar" key="e"><Button type="text" icon={<ExportOutlined />} /></Tooltip>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Badge status={item.is_sealed ? "success" : "warning"} />}
                    title={<Text strong>Snapshot #{item.id?.substring(0, 8)}</Text>}
                    description={`Blok: ${item.block_height} | Kanıt: ${item.evidence_count}`}
                  />
                </List.Item>
              )}
            />
            <Divider />
            <Button block type="dashed" icon={<DatabaseOutlined />}>Yeni Snapshot Mühürle</Button>
          </Card>
        </Col>
      </Row>

      <Card title="Bütünlük Doğrulama Ağı (Verifier Network)" variant="borderless" style={{ marginTop: "24px" }}>
         <Row gutter={24}>
            <Col span={8}>
               <div style={{ textAlign: "center" }}>
                  <Text type="secondary" style={{ marginBottom: 16, display: "block" }}>Internal Verifier</Text>
                  <VerifiedOutlined style={{ fontSize: 48, color: "#52c41a" }} />
                  <div style={{ marginTop: 8 }}><Tag color="success">ACTIVE</Tag></div>
               </div>
            </Col>
            <Col span={8}>
               <div style={{ textAlign: "center" }}>
                  <Text type="secondary" style={{ marginBottom: 16, display: "block" }}>Prime Quorum Seal</Text>
                  <LockOutlined style={{ fontSize: 48, color: "#1890ff" }} />
                  <div style={{ marginTop: 8 }}><Tag color="processing">READY</Tag></div>
               </div>
            </Col>
            <Col span={8}>
               <div style={{ textAlign: "center" }}>
                  <Text type="secondary" style={{ marginBottom: 16, display: "block" }}>External Audit Bridge</Text>
                  <ExportOutlined style={{ fontSize: 48, color: "#faad14" }} />
                  <div style={{ marginTop: 8 }}><Tag color="warning">PENDING</Tag></div>
               </div>
            </Col>
         </Row>
      </Card>
    </div>
  );
}
