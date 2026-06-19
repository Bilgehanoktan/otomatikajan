import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  Progress,
  Row,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
} from "antd";
import {
  CloudServerOutlined,
  ClusterOutlined,
  FileSearchOutlined,
  GlobalOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
  SyncOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { safeFetchJson } from "@/lib/api";

const { Title, Text } = Typography;

export const FederationCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [overview, setOverview] = useState<any | null>(null);
  const [tenants, setTenants] = useState<any[]>([]);
  const [clusters, setClusters] = useState<any[]>([]);
  const [drifts, setDrifts] = useState<any[]>([]);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchOverview = async () => {
    const data = await safeFetchJson("/api/v1/ui-repair/federation/overview");
    setOverview(data);
  };

  const fetchTabData = async (tab: string) => {
    setLoading(true);
    try {
      if (tab === "tenants") {
        setTenants(await safeFetchJson("/api/v1/ui-repair/federation/tenants"));
      } else if (tab === "clusters") {
        setClusters(await safeFetchJson("/api/v1/ui-repair/federation/clusters"));
      } else if (tab === "drift") {
        setDrifts(await safeFetchJson("/api/v1/ui-repair/federation/policy-drift"));
      } else if (tab === "evidence") {
        setEvidence(await safeFetchJson("/api/v1/ui-repair/federation/evidence"));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  useEffect(() => {
    if (activeTab !== "overview" && activeTab !== "policies") {
      fetchTabData(activeTab);
    }
  }, [activeTab]);

  const federationStats = useMemo(() => ({
    totalTenants: overview?.total_tenants ?? 0,
    activeClusters: overview?.active_clusters ?? 0,
    globalHealth: overview?.global_health ?? 0,
    driftCount: overview?.drift_count ?? 0,
    isolationViolations: overview?.isolation_violations ?? 0,
    syncStatus: overview?.sync_status ?? "NO_DATA",
  }), [overview]);

  return (
    <div style={{ padding: "24px" }}>
      <Row gutter={[16, 16]} style={{ marginBottom: "24px" }}>
        <Col span={24}>
          <Card style={{ borderRadius: "12px", background: "linear-gradient(135deg, #001529 0%, #003a8c 100%)", color: "#fff" }}>
            <Row align="middle" gutter={24}>
              <Col>
                <GlobalOutlined style={{ fontSize: "48px", color: "#1890ff" }} />
              </Col>
              <Col flex="auto">
                <Title level={2} style={{ color: "#fff", margin: 0 }}>Federation Center</Title>
                <Text style={{ color: "rgba(255,255,255,0.8)" }}>
                  Cross-Cluster Governance - Multi-Tenant Isolation - Policy Federation
                </Text>
              </Col>
              <Col>
                <Space size="large">
                  <Statistic
                    title={<span style={{ color: "#fff" }}>Global Health</span>}
                    value={federationStats.globalHealth}
                    suffix="%"
                    valueStyle={{ color: "#52c41a" }}
                  />
                  <Statistic
                    title={<span style={{ color: "#fff" }}>Active Tenants</span>}
                    value={federationStats.totalTenants}
                    valueStyle={{ color: "#fff" }}
                  />
                </Space>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            type="card"
            items={[
              {
                key: "overview",
                label: (<span><ClusterOutlined />Overview</span>),
                children: <FederationOverview stats={federationStats} overview={overview} />,
              },
              {
                key: "tenants",
                label: (<span><LockOutlined />Tenants</span>),
                children: <TenantRegistryPanel data={tenants} loading={loading} />,
              },
              {
                key: "clusters",
                label: (<span><CloudServerOutlined />Clusters</span>),
                children: <ClusterRegistryPanel data={clusters} loading={loading} />,
              },
              {
                key: "policies",
                label: (<span><SafetyCertificateOutlined />Federated Policies</span>),
                children: <FederatedPolicyPanel syncStatus={federationStats.syncStatus} />,
              },
              {
                key: "drift",
                label: (<span><WarningOutlined />Policy Drift</span>),
                children: <PolicyDriftPanel data={drifts} loading={loading} />,
              },
              {
                key: "evidence",
                label: (<span><FileSearchOutlined />Cross-Cluster Evidence</span>),
                children: <FederatedEvidencePanel data={evidence} loading={loading} />,
              },
            ]}
          />
        </Col>
      </Row>
    </div>
  );
};

const FederationOverview: React.FC<{ stats: any; overview: any | null }> = ({ stats, overview }) => {
  return (
    <Row gutter={[16, 16]}>
      <Col span={8}>
        <Card title="Ecosystem Health" hoverable>
          <div style={{ textAlign: "center", padding: "20px" }}>
            <Progress
              type="dashboard"
              percent={stats.globalHealth}
              strokeColor={{ "0%": "#108ee9", "100%": "#87d068" }}
            />
            <div style={{ marginTop: "10px" }}>
              <Tag color={stats.globalHealth >= 90 ? "green" : stats.globalHealth >= 75 ? "orange" : "red"}>
                {stats.globalHealth >= 90 ? "STABLE" : stats.globalHealth >= 75 ? "DEGRADED" : "AT RISK"}
              </Tag>
              <Tag color="blue">{stats.activeClusters} Clusters Registered</Tag>
            </div>
          </div>
        </Card>
      </Col>
      <Col span={8}>
        <Card title="Governance Status" hoverable>
          <Statistic
            title="Active Policy Drifts"
            value={stats.driftCount}
            prefix={<WarningOutlined />}
            valueStyle={{ color: stats.driftCount > 0 ? "#faad14" : "#52c41a" }}
          />
          <div style={{ marginTop: "20px" }}>
            <Alert
              message={`Evidence Sync: ${stats.syncStatus}`}
              type={stats.syncStatus === "OPTIMAL" ? "success" : stats.syncStatus === "NO_DATA" ? "info" : "warning"}
              showIcon
              description="Federation-wide policy and evidence flow is reflected from live backend telemetry."
            />
          </div>
        </Card>
      </Col>
      <Col span={8}>
        <Card title="Isolation Integrity" hoverable>
          <Statistic
            title="Isolation Violations"
            value={stats.isolationViolations}
            prefix={<LockOutlined />}
            valueStyle={{ color: stats.isolationViolations > 0 ? "#ff4d4f" : "#52c41a" }}
          />
          <div style={{ marginTop: "20px" }}>
            <Text type="secondary">
              Evidence Records: {overview?.evidence_records ?? 0} - Healthy: {overview?.healthy_clusters ?? 0} / Degraded: {overview?.degraded_clusters ?? 0}
            </Text>
            <Progress percent={Math.max(0, 100 - (stats.isolationViolations * 10))} status={stats.isolationViolations > 0 ? "exception" : "active"} />
          </div>
        </Card>
      </Col>
    </Row>
  );
};

const TenantRegistryPanel: React.FC<{ data: any[]; loading: boolean }> = ({ data, loading }) => {
  return (
    <Card title="Tenant Registry">
      <Table
        dataSource={data}
        loading={loading}
        rowKey="id"
        columns={[
          { title: "Tenant Key", dataIndex: "tenant_key", key: "tenant_key" },
          { title: "Name", dataIndex: "tenant_name", key: "tenant_name" },
          {
            title: "Status",
            dataIndex: "status",
            key: "status",
            render: (status: string) => <Tag color={status === "ACTIVE" ? "green" : "red"}>{status}</Tag>,
          },
          { title: "Governance", dataIndex: "governance_level", key: "governance_level" },
          { title: "Created At", dataIndex: "created_at", key: "created_at" },
        ]}
      />
    </Card>
  );
};

const ClusterRegistryPanel: React.FC<{ data: any[]; loading: boolean }> = ({ data, loading }) => {
  return (
    <Card title="Cluster Registry">
      <Table
        dataSource={data}
        loading={loading}
        rowKey="id"
        columns={[
          { title: "Cluster Key", dataIndex: "cluster_key", key: "cluster_key" },
          { title: "Name", dataIndex: "cluster_name", key: "cluster_name" },
          { title: "Region", dataIndex: "region", key: "region" },
          { title: "Environment", dataIndex: "environment", key: "environment" },
          {
            title: "Status",
            dataIndex: "status",
            key: "status",
            render: (status: string) => (
              <Tag color={status === "HEALTHY" ? "green" : status === "DEGRADED" ? "orange" : "red"}>
                {status}
              </Tag>
            ),
          },
        ]}
      />
    </Card>
  );
};

const FederatedPolicyPanel: React.FC<{ syncStatus: string }> = ({ syncStatus }) => {
  return (
    <Card title="Federated Policy Hierarchy">
      <Alert
        message="Federation Rule: Most Restrictive Wins"
        description="Global policies set the baseline. Tenant and project policies can only make restrictions more stringent, never more relaxed."
        type="info"
        showIcon
        style={{ marginBottom: "20px" }}
      />
      <Alert
        message={`Synchronization Status: ${syncStatus}`}
        type={syncStatus === "OPTIMAL" ? "success" : syncStatus === "NO_DATA" ? "info" : "warning"}
        showIcon
        style={{ marginBottom: "20px" }}
      />
      <Table
        dataSource={[]}
        columns={[
          { title: "Policy Key", dataIndex: "key" },
          { title: "Global Setting", dataIndex: "global" },
          { title: "Tenant Overrides", dataIndex: "tenant" },
          { title: "Effective Decision", dataIndex: "effective" },
        ]}
        locale={{ emptyText: "No federated policy matrix has been materialized yet." }}
      />
    </Card>
  );
};

const PolicyDriftPanel: React.FC<{ data: any[]; loading: boolean }> = ({ data, loading }) => {
  return (
    <Card title="Policy Drift Detection" extra={<Button icon={<SyncOutlined />}>Scan Now</Button>}>
      <Table
        dataSource={data}
        loading={loading}
        rowKey="id"
        columns={[
          { title: "Tenant", dataIndex: "tenant_key" },
          { title: "Policy", dataIndex: "policy_key" },
          {
            title: "Drift Level",
            dataIndex: "drift_level",
            render: (level: string) => <Tag color={level === "CRITICAL" ? "red" : "orange"}>{level}</Tag>,
          },
          { title: "Drift Type", dataIndex: "drift_type" },
          { title: "Detected At", dataIndex: "created_at" },
        ]}
        locale={{ emptyText: "No policy drifts detected. All clusters are in compliance." }}
      />
    </Card>
  );
};

const FederatedEvidencePanel: React.FC<{ data: any[]; loading: boolean }> = ({ data, loading }) => {
  return (
    <Card title="Cross-Cluster Evidence Ledger">
      <div style={{ marginBottom: "20px" }}>
        <Text type="secondary">
          All autonomous actions across the federation are anchored to the central ledger via cryptographically verifiable hashes.
        </Text>
      </div>
      <Table
        dataSource={data}
        loading={loading}
        rowKey="id"
        columns={[
          { title: "Timestamp", dataIndex: "created_at" },
          { title: "Cluster", dataIndex: "cluster_key" },
          { title: "Tenant", dataIndex: "tenant_key" },
          { title: "Type", dataIndex: "evidence_type" },
          { title: "Hash", dataIndex: "evidence_hash", render: (hash: string) => <code>{hash}</code> },
        ]}
        locale={{ emptyText: "Waiting for evidence synchronization..." }}
      />
    </Card>
  );
};
