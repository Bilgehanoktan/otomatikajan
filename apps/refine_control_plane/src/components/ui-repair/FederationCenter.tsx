import React, { useState } from "react";
import { 
    Card, 
    Row, 
    Col, 
    Typography, 
    Tabs, 
    Table, 
    Tag, 
    Button, 
    Space, 
    Statistic, 
    Alert,
    Progress,
    Tooltip
} from "antd";
import { 
    GlobalOutlined, 
    CloudServerOutlined, 
    SafetyCertificateOutlined, 
    WarningOutlined, 
    ClusterOutlined,
    SyncOutlined,
    LockOutlined,
    FileSearchOutlined
} from "@ant-design/icons";
import { useList } from "@refinedev/core";

const { Title, Text } = Typography;
const { TabPane } = Tabs;

export const FederationCenter: React.FC = () => {
    const [activeTab, setActiveTab] = useState("overview");

    // Mock data for aggregation (In real app, fetch from /api/v1/ui-repair/federation/cluster-health)
    const federationStats = {
        totalTenants: 12,
        activeClusters: 8,
        globalHealth: 94.5,
        driftCount: 3,
        isolationViolations: 0,
        syncStatus: "OPTIMAL"
    };

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
                                    Cross-Cluster Governance • Multi-Tenant Isolation • Policy Federation
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
                                children: <FederationOverview stats={federationStats} />
                            },
                            {
                                key: "tenants",
                                label: (<span><LockOutlined />Tenants</span>),
                                children: <TenantRegistryPanel />
                            },
                            {
                                key: "clusters",
                                label: (<span><CloudServerOutlined />Clusters</span>),
                                children: <ClusterRegistryPanel />
                            },
                            {
                                key: "policies",
                                label: (<span><SafetyCertificateOutlined />Federated Policies</span>),
                                children: <FederatedPolicyPanel />
                            },
                            {
                                key: "drift",
                                label: (<span><WarningOutlined />Policy Drift</span>),
                                children: <PolicyDriftPanel />
                            },
                            {
                                key: "evidence",
                                label: (<span><FileSearchOutlined />Cross-Cluster Evidence</span>),
                                children: <FederatedEvidencePanel />
                            }
                        ]}
                    />
                </Col>
            </Row>
        </div>
    );
};

const FederationOverview: React.FC<{ stats: any }> = ({ stats }) => {
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
                            <Tag color="green">STABLE</Tag>
                            <Tag color="blue">{stats.activeClusters} Clusters Online</Tag>
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
                            message="Hierarchy Enforcement Active" 
                            type="success" 
                            showIcon 
                            description="Most restrictive policy wins rule is being applied globally." 
                        />
                    </div>
                </Card>
            </Col>
            <Col span={8}>
                <Card title="Isolation Integrity" hoverable>
                    <Statistic 
                        title="Isolation Violations (24h)" 
                        value={stats.isolationViolations} 
                        prefix={<LockOutlined />} 
                        valueStyle={{ color: stats.isolationViolations > 0 ? "#ff4d4f" : "#52c41a" }} 
                    />
                    <div style={{ marginTop: "20px" }}>
                        <Text type="secondary">All tenant boundaries are currently secure.</Text>
                        <Progress percent={100} status="active" strokeColor="#52c41a" />
                    </div>
                </Card>
            </Col>
        </Row>
    );
};

const TenantRegistryPanel: React.FC = () => {
    const { data, isLoading } = useList({ resource: "ui-repair/federation/tenants" });
    
    const columns = [
        { title: "Tenant Key", dataIndex: "tenant_key", key: "tenant_key" },
        { title: "Name", dataIndex: "tenant_name", key: "tenant_name" },
        { 
            title: "Status", 
            dataIndex: "status", 
            key: "status",
            render: (status: string) => <Tag color={status === "ACTIVE" ? "green" : "red"}>{status}</Tag>
        },
        { title: "Governance", dataIndex: "governance_level", key: "governance_level" },
        { title: "Created At", dataIndex: "created_at", key: "created_at" },
        { 
            title: "Actions", 
            key: "actions",
            render: () => <Button type="link">Manage Projects</Button>
        }
    ];

    return (
        <Card title="Tenant Registry" extra={<Button type="primary">Add Tenant</Button>}>
            <Table dataSource={data?.data} columns={columns} loading={isLoading} rowKey="id" />
        </Card>
    );
};

const ClusterRegistryPanel: React.FC = () => {
    const { data, isLoading } = useList({ resource: "ui-repair/federation/clusters" });
    
    const columns = [
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
            )
        }
    ];

    return (
        <Card title="Cluster Registry" extra={<Button type="primary" icon={<CloudServerOutlined />}>Register Cluster</Button>}>
            <Table dataSource={data?.data} columns={columns} loading={isLoading} rowKey="id" />
        </Card>
    );
};

const FederatedPolicyPanel: React.FC = () => {
    return (
        <Card title="Federated Policy Hierarchy">
            <Alert 
                message="Federation Rule: Most Restrictive Wins" 
                description="Global policies set the baseline. Tenant and Project policies can only make restrictions more stringent, never more relaxed."
                type="info"
                showIcon
                style={{ marginBottom: "20px" }}
            />
            <Table 
                dataSource={[]} 
                columns={[
                    { title: "Policy Key", dataIndex: "key" },
                    { title: "Global Setting", dataIndex: "global" },
                    { title: "Tenant Overrides", dataIndex: "tenant" },
                    { title: "Effective Decision", dataIndex: "effective" }
                ]}
                locale={{ emptyText: "No federated policies defined." }}
            />
        </Card>
    );
};

const PolicyDriftPanel: React.FC = () => {
    const { data, isLoading } = useList({ resource: "ui-repair/federation/policy-drift" });
    
    return (
        <Card title="Policy Drift Detection" extra={<Button icon={<SyncOutlined />}>Scan Now</Button>}>
            <Table 
                dataSource={data?.data} 
                loading={isLoading}
                columns={[
                    { title: "Tenant", dataIndex: "tenant_key" },
                    { title: "Policy", dataIndex: "policy_key" },
                    { 
                        title: "Drift Level", 
                        dataIndex: "drift_level",
                        render: (level: string) => <Tag color={level === "CRITICAL" ? "red" : "orange"}>{level}</Tag>
                    },
                    { title: "Drift Type", dataIndex: "drift_type" },
                    { title: "Detected At", dataIndex: "created_at" }
                ]}
                locale={{ emptyText: "No policy drifts detected. All clusters are in compliance." }}
            />
        </Card>
    );
};

const FederatedEvidencePanel: React.FC = () => {
    return (
        <Card title="Cross-Cluster Evidence Ledger">
            <div style={{ marginBottom: "20px" }}>
                <Text type="secondary">
                    All autonomous actions across the federation are anchored to the central ledger via cryptographically verifiable hashes.
                </Text>
            </div>
            <Table 
                dataSource={[]} 
                columns={[
                    { title: "Timestamp", dataIndex: "time" },
                    { title: "Cluster", dataIndex: "cluster" },
                    { title: "Tenant", dataIndex: "tenant" },
                    { title: "Type", dataIndex: "type" },
                    { title: "Hash", dataIndex: "hash", render: (h: string) => <code>{h}</code> }
                ]}
                locale={{ emptyText: "Waiting for evidence synchronization..." }}
            />
        </Card>
    );
};
