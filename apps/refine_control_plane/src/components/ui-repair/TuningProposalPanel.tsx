import React, { useState, useEffect } from 'react';
import { 
  Table, Tag, Button, Space, Modal, Typography, 
  Descriptions, Badge, Timeline, Card, message, Tooltip, Row, Col
} from 'antd';
import { safeFetchJson } from '@/lib/api';
import { 
  Eye, CheckCircle, XCircle, PlayCircle, Shield, 
  Zap, Activity, Clock, Filter, AlertTriangle, Settings
} from 'lucide-react';

const { Text, Title, Paragraph } = Typography;

const TuningProposalPanel: React.FC = () => {
  const [proposals, setProposals] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState<any>(null);
  const [modalVisible, setModalVisible] = useState(false);

  const fetchProposals = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson('/api/v1/ui-repair/defense/proposals');
      setProposals(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProposals();
  }, []);

  const promoteProposal = async (id: string) => {
    try {
      await safeFetchJson(`/api/v1/ui-repair/defense/proposals/${id}/promote`, { method: 'POST' });
      message.success('Proposal promoted to next verification stage.');
      fetchProposals();
    } catch (err) {
      message.error('Failed to promote proposal.');
    }
  };

  const approveProposal = async (id: string) => {
    try {
      await safeFetchJson(`/api/v1/ui-repair/defense/proposals/${id}/approve`, { method: 'POST' });
      message.success('Proposal approved by operator.');
      fetchProposals();
    } catch (err) {
      message.error('Failed to approve proposal.');
    }
  };

  const applyProposal = async (id: string) => {
    try {
      await safeFetchJson(`/api/v1/ui-repair/defense/proposals/${id}/apply`, { method: 'POST' });
      message.success('Optimization applied to live guardrails.');
      fetchProposals();
    } catch (err) {
      message.error('Failed to apply proposal.');
    }
  };

  const columns = [
    {
      title: 'Key',
      dataIndex: 'proposal_key',
      key: 'key',
      render: (text: string) => <Text strong className="text-blue-400">{text}</Text>
    },
    {
      title: 'Guardrail',
      dataIndex: 'affected_guardrail',
      key: 'guardrail',
    },
    {
      title: 'Risk Level',
      dataIndex: 'risk_level',
      key: 'risk',
      render: (level: string) => {
        const colors: any = { CRITICAL: 'red', HIGH: 'orange', MEDIUM: 'blue', LOW: 'green' };
        return <Tag color={colors[level] || 'default'}>{level}</Tag>;
      }
    },
    {
      title: 'Security Gain',
      dataIndex: 'expected_security_gain',
      key: 'gain',
      render: (val: number) => <Text className="text-emerald-400">+{ (val * 100).toFixed(1) }%</Text>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: any = {
          DRAFT: 'default',
          REGRESSION_PASSED: 'blue',
          CANARY_RUNNING: 'processing',
          CANARY_PASSED: 'cyan',
          GOVERNANCE_REQUESTED: 'purple',
          APPROVED: 'green',
          APPLIED: 'emerald',
          REJECTED: 'red'
        };
        return <Tag color={colors[status] || 'default'}>{status.replace(/_/g, ' ')}</Tag>;
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          <Tooltip title="View Details">
            <Button size="small" icon={<Eye size={14} />} onClick={() => { setSelectedProposal(record); setModalVisible(true); }} />
          </Tooltip>
          {['DRAFT', 'REGRESSION_PASSED', 'CANARY_PASSED'].includes(record.status) && (
            <Tooltip title="Promote Stage">
              <Button size="small" type="primary" ghost icon={<Zap size={14} />} onClick={() => promoteProposal(record.id)} />
            </Tooltip>
          )}
          {record.status === 'GOVERNANCE_REQUESTED' && (
            <Tooltip title="Operator Approval">
              <Button size="small" className="border-purple-500 text-purple-500 hover:text-purple-400" icon={<CheckCircle size={14} />} onClick={() => approveProposal(record.id)} />
            </Tooltip>
          )}
          {record.status === 'APPROVED' && (
            <Tooltip title="Apply to Live">
              <Button size="small" type="primary" className="bg-emerald-600 border-emerald-600" icon={<PlayCircle size={14} />} onClick={() => applyProposal(record.id)} />
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Title level={4}>Active Optimization Proposals</Title>
        <Space>
          <Button icon={<Filter size={16} />}>Filter</Button>
          <Button icon={<Clock size={16} />}>History</Button>
        </Space>
      </div>

      <Table 
        dataSource={proposals} 
        columns={columns} 
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 8 }}
        className="custom-table"
      />

      <Modal
        title={<Space><Settings className="text-blue-400" /> {selectedProposal?.proposal_key} Details</Space>}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>Close</Button>,
          selectedProposal?.status === 'APPROVED' && (
            <Button key="apply" type="primary" className="bg-emerald-600" onClick={() => applyProposal(selectedProposal.id)}>Apply Optimization</Button>
          )
        ]}
        width={800}
      >
        {selectedProposal && (
          <div className="space-y-6">
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="Source">{selectedProposal.source_type}</Descriptions.Item>
              <Descriptions.Item label="Domain">{selectedProposal.affected_guardrail}</Descriptions.Item>
              <Descriptions.Item label="Policy Key">{selectedProposal.affected_policy_key}</Descriptions.Item>
              <Descriptions.Item label="Risk Level">
                <Tag color={selectedProposal.risk_level === 'CRITICAL' ? 'red' : 'orange'}>{selectedProposal.risk_level}</Tag>
              </Descriptions.Item>
            </Descriptions>

            <div>
              <Text strong>Reasoning:</Text>
              <Paragraph className="mt-2 text-slate-400">{selectedProposal.reason}</Paragraph>
            </div>

            <Row gutter={16}>
              <Col span={12}>
                <Card title="Current Config" size="small" className="bg-slate-800 border-slate-700">
                  <pre className="text-xs text-slate-300">{JSON.stringify(selectedProposal.current_config, null, 2)}</pre>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Proposed Config" size="small" className="bg-slate-900 border-emerald-900/50">
                  <pre className="text-xs text-emerald-300">{JSON.stringify(selectedProposal.proposed_config, null, 2)}</pre>
                </Card>
              </Col>
            </Row>

            <div>
              <Text strong>Verification Pipeline:</Text>
              <Timeline 
                className="mt-4"
                items={[
                  {
                    color: 'green',
                    children: 'Proposal Generated (Findings Analyzed)',
                  },
                  {
                    color: selectedProposal.status !== 'DRAFT' ? 'green' : 'gray',
                    children: 'Policy Regression Verification',
                  },
                  {
                    color: ['CANARY_RUNNING', 'CANARY_PASSED', 'GOVERNANCE_REQUESTED', 'APPROVED', 'APPLIED'].includes(selectedProposal.status) ? 'green' : 'gray',
                    children: 'Shadow Canary Deployment',
                  },
                  {
                    color: ['GOVERNANCE_REQUESTED', 'APPROVED', 'APPLIED'].includes(selectedProposal.status) ? 'green' : 'gray',
                    children: 'Governance Approval Gate',
                  },
                  {
                    color: selectedProposal.status === 'APPLIED' ? 'green' : 'gray',
                    children: 'Applied to Production',
                  },
                ]}
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default TuningProposalPanel;
