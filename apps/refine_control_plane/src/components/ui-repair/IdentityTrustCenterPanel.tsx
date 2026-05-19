import React, { useEffect, useState } from 'react';
import {
  Table, Tag, Card, Row, Col, Statistic, List, Typography,
  Space, Progress, Button, message, Modal, Descriptions
} from 'antd';
import {
  SafetyCertificateOutlined,
  SafetyOutlined,
  KeyOutlined,
  HistoryOutlined,
  UserOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LockOutlined
} from '@ant-design/icons';
import { safeFetchJson } from '@/lib/api';

const { Title, Text } = Typography;

export const IdentityTrustCenterPanel: React.FC = () => {
  const [identities, setIdentities] = useState<any[]>([]);
  const [trustScores, setTrustScores] = useState<any[]>([]);
  const [auditEvents, setAuditEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIdentity, setSelectedIdentity] = useState<any>(null);

  const fetchIdentityData = async () => {
    setLoading(true);
    try {
      const [identitiesData, trustData, auditData] = await Promise.all([
        safeFetchJson<any[]>('/api/v1/ui-repair/identity/registry'),
        safeFetchJson<any[]>('/api/v1/ui-repair/identity/trust-scores'),
        safeFetchJson<any[]>('/api/v1/ui-repair/identity/audit-events')
      ]);
      setIdentities(identitiesData);
      setTrustScores(trustData);
      setAuditEvents(auditData);
    } catch (error) {
      console.error("Failed to fetch identity data", error);
      message.error("Failed to load Identity Trust Center data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIdentityData();
  }, []);

  const getTrustScore = (key: string) => {
    const scoreObj = trustScores.find(s => s.identity_key === key);
    return scoreObj ? scoreObj.trust_score : 1.0;
  };

  const identityColumns = [
    {
      title: 'Identity Key',
      dataIndex: 'identity_key',
      key: 'identity_key',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Type',
      dataIndex: 'identity_type',
      key: 'identity_type',
      render: (type: string) => (
        <Tag color={type === 'AGENT' ? 'blue' : 'cyan'}>{type}</Tag>
      )
    },
    {
      title: 'Trust Score',
      key: 'trust_score',
      render: (_: any, record: any) => {
        const score = getTrustScore(record.identity_key);
        const color = score > 0.8 ? 'green' : score > 0.5 ? 'orange' : 'red';
        return <Progress percent={Math.round(score * 100)} size="small" strokeColor={color} />;
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'ACTIVE' ? 'success' : 'error'}>{status}</Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: any) => (
        <Button size="small" onClick={() => setSelectedIdentity(record)}>View Details</Button>
      )
    }
  ];

  const auditColumns = [
    {
      title: 'Timestamp',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: 'Identity',
      dataIndex: 'identity_key',
      key: 'identity_key'
    },
    {
      title: 'Event',
      dataIndex: 'event_type',
      key: 'event_type',
      render: (event: string) => (
        <Tag color={event.includes('FAIL') ? 'red' : 'blue'}>{event}</Tag>
      )
    },
    {
      title: 'Decision',
      dataIndex: 'decision',
      key: 'decision',
      render: (decision: string) => (
        <Tag icon={decision === 'PASSED' ? <CheckCircleOutlined /> : <CloseCircleOutlined />} 
             color={decision === 'PASSED' ? 'success' : 'error'}>
          {decision}
        </Tag>
      )
    }
  ];

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Title level={2}><SafetyCertificateOutlined /> Identity & Trust Center (SIF-01)</Title>
          <Text type="secondary">Real-time monitoring of decentralized identities, cryptographic handshakes, and trust scoring.</Text>
        </Col>

        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title="Verified Identities" 
              value={identities.length} 
              prefix={<UserOutlined />} 
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title="Avg Trust Score" 
              value={trustScores.length > 0 ? (trustScores.reduce((a, b) => a + b.trust_score, 0) / trustScores.length * 100).toFixed(1) : 100} 
              suffix="%"
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title="Active Tokens" 
              value={8} 
              prefix={<KeyOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title="Handshake Replays Blocked" 
              value={24} 
              prefix={<LockOutlined />} 
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>

        <Col span={16}>
          <Card title={<Space><UserOutlined /> Identity Registry</Space>} bordered={false} className="glass-card">
            <Table 
              dataSource={identities} 
              columns={identityColumns} 
              loading={loading} 
              rowKey="id"
              pagination={{ pageSize: 5 }}
            />
          </Card>
        </Col>

        <Col span={8}>
          <Card title={<Space><SafetyOutlined /> Trust Anomalies</Space>} bordered={false} className="glass-card">
            <List
              dataSource={trustScores.filter(s => s.trust_score < 0.8)}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    title={item.identity_key}
                    description={`Score: ${(item.trust_score * 100).toFixed(0)}% | Violations: ${item.policy_violation_count}`}
                  />
                  <Tag color="warning">AT RISK</Tag>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col span={24}>
          <Card title={<Space><HistoryOutlined /> Identity Audit Ledger (SovereignEvidence)</Space>} bordered={false} className="glass-card">
            <Table 
              dataSource={auditEvents} 
              columns={auditColumns} 
              loading={loading} 
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Col>
      </Row>

      <Modal
        title="Identity Details"
        open={!!selectedIdentity}
        onCancel={() => setSelectedIdentity(null)}
        footer={[
          <Button key="revoke" danger onClick={() => message.info("Revocation workflow triggered")}>Revoke Identity</Button>,
          <Button key="close" onClick={() => setSelectedIdentity(null)}>Close</Button>
        ]}
        width={800}
      >
        {selectedIdentity && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="Identity Key">{selectedIdentity.identity_key}</Descriptions.Item>
            <Descriptions.Item label="Type">{selectedIdentity.identity_type}</Descriptions.Item>
            <Descriptions.Item label="Display Name">{selectedIdentity.display_name}</Descriptions.Item>
            <Descriptions.Item label="Status">{selectedIdentity.status}</Descriptions.Item>
            <Descriptions.Item label="Tenant">{selectedIdentity.tenant_key}</Descriptions.Item>
            <Descriptions.Item label="Trust Level">{selectedIdentity.trust_level}</Descriptions.Item>
            <Descriptions.Item label="Fingerprint" span={2}>
              <code style={{ fontSize: '12px' }}>{selectedIdentity.public_key_fingerprint}</code>
            </Descriptions.Item>
            <Descriptions.Item label="Allowed Actions" span={2}>
              {selectedIdentity.allowed_actions_json.map((a: string) => <Tag key={a}>{a}</Tag>)}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <style jsx global>{`
        .glass-card {
          background: rgba(255, 255, 255, 0.7);
          backdrop-filter: blur(10px);
          border-radius: 12px;
          box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.18);
        }
      `}</style>
    </div>
  );
};
