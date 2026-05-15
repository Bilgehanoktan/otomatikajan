import React, { useState, useEffect } from 'react';
import { 
  Table, Card, Tag, Button, Space, Typography, Modal, Form, 
  Input, Select, Switch, Alert, List, Badge, Divider, Tooltip, Tabs,
  Statistic, Row, Col, Progress, Empty
} from 'antd';
import { 
  SafetyCertificateOutlined, 
  ExclamationCircleOutlined, 
  SafetyOutlined, 
  HistoryOutlined,
  UnlockOutlined,
  CheckCircleOutlined,
  StopOutlined,
  FileTextOutlined,
  WarningOutlined,
  InteractionOutlined,
  SecurityScanOutlined,
  BarChartOutlined,
  EyeOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const GovernanceCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState('rules');
  const [policies, setPolicies] = useState<any[]>([]);
  const [evaluations, setEvaluations] = useState<any[]>([]);
  const [findings, setFindings] = useState<any[]>([]);
  const [overrides, setOverrides] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [isPolicyModalVisible, setIsPolicyModalVisible] = useState(false);
  const [isOverrideModalVisible, setIsOverrideModalVisible] = useState(false);
  const [selectedEvaluation, setSelectedEvaluation] = useState<any>(null);
  const [form] = Form.useForm();

  const fetchGovernanceData = async () => {
    setLoading(true);
    try {
      const [policiesRes, evaluationsRes, findingsRes, overridesRes] = await Promise.all([
        axios.get('/api/v1/ui-repair/governance/policies'),
        axios.get('/api/v1/ui-repair/governance/evaluations'),
        axios.get('/api/v1/ui-repair/governance/compliance-findings'),
        axios.get('/api/v1/ui-repair/governance/overrides').catch(() => ({ data: [] }))
      ]);
      setPolicies(policiesRes.data);
      setEvaluations(evaluationsRes.data);
      setFindings(findingsRes.data);
      setOverrides(overridesRes.data);
    } catch (error) {
      console.error('Failed to fetch governance data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGovernanceData();
  }, []);

  const handleCreatePolicy = async (values: any) => {
    try {
      await axios.post('/api/v1/ui-repair/governance/policies', {
        ...values,
        rule_definition_json: JSON.parse(values.rule_definition_json || '{}')
      });
      setIsPolicyModalVisible(false);
      form.resetFields();
      fetchGovernanceData();
    } catch (error) {
      console.error('Failed to create policy', error);
    }
  };

  const handleCreateOverride = async (values: any) => {
    try {
      await axios.post('/api/v1/ui-repair/governance/overrides', {
        action_type: selectedEvaluation.action_type,
        target_type: selectedEvaluation.target_type || 'UNKNOWN',
        target_id: selectedEvaluation.target_id || 'UNKNOWN',
        blocked_policy_key: selectedEvaluation.policy_key || 'UNKNOWN',
        override_reason: values.rationale,
        operator: 'CURRENT_OPERATOR', // Should come from auth context
        risk_level: 'HIGH'
      });
      setIsOverrideModalVisible(false);
      fetchGovernanceData();
    } catch (error) {
      console.error('Failed to create override', error);
    }
  };

  const policyColumns = [
    {
      title: 'Policy Key',
      dataIndex: 'policy_key',
      key: 'policy_key',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Scope',
      dataIndex: 'scope',
      key: 'scope',
      render: (scope: string) => <Tag color={scope === 'GLOBAL' ? 'blue' : 'purple'}>{scope}</Tag>
    },
    {
      title: 'Type',
      dataIndex: 'rule_type',
      key: 'rule_type',
      render: (type: string) => <Tag>{type}</Tag>
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
    },
    {
      title: 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Badge status={enabled ? 'success' : 'default'} text={enabled ? 'Active' : 'Inactive'} />
      )
    }
  ];

  const evaluationColumns = [
    {
      title: 'Time',
      dataIndex: 'evaluated_at',
      key: 'evaluated_at',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: 'Action',
      dataIndex: 'action_type',
      key: 'action_type',
      render: (text: string) => <Tag icon={<InteractionOutlined />}>{text}</Tag>
    },
    {
      title: 'Decision',
      dataIndex: 'decision',
      key: 'decision',
      render: (decision: string) => (
        <Tag color={
          decision === 'ALLOW' ? 'green' : 
          decision === 'DENY' ? 'red' : 
          decision.includes('BLOCKED') ? 'red' : 'orange'
        }>
          {decision}
        </Tag>
      )
    },
    {
      title: 'Reason',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => {
            setSelectedEvaluation(record);
            // Show details
          }} />
          {(record.decision === 'DENY' || record.decision.includes('BLOCKED')) && (
            <Button 
              size="small" 
              danger 
              icon={<UnlockOutlined />} 
              onClick={() => {
                setSelectedEvaluation(record);
                setIsOverrideModalVisible(true);
              }}
            >
              Override
            </Button>
          )}
        </Space>
      )
    }
  ];

  const findingColumns = [
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: 'Standard',
      dataIndex: 'standard',
      key: 'standard'
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (sev: string) => (
        <Tag color={sev === 'CRITICAL' ? 'red' : sev === 'HIGH' ? 'orange' : 'blue'}>{sev}</Tag>
      )
    },
    {
      title: 'Type',
      dataIndex: 'finding_type',
      key: 'finding_type'
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description'
    }
  ];

  return (
    <div className="p-6 bg-[#060a12] min-h-screen">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div className="flex justify-between items-center">
          <div>
            <Title level={2} className="!text-white !mb-0">
              <SafetyCertificateOutlined className="mr-3" /> Policy Center
            </Title>
            <Text className="text-gray-500 uppercase text-[10px] font-black tracking-widest">
              Autonomous Ecosystem Governance & Policy-as-Code
            </Text>
          </div>
          <Space>
             <Button icon={<BarChartOutlined />}>Audit Report</Button>
             <Button type="primary" icon={<SafetyOutlined />} onClick={() => setIsPolicyModalVisible(true)}>
                New Policy Proposal
             </Button>
          </Space>
        </div>

        <Row gutter={24}>
           <Col span={6}>
              <Card className="bg-white/5 border-white/10">
                 <Statistic 
                   title={<span className="text-gray-400">Policy Adherence</span>} 
                   value={98.4} 
                   precision={1}
                   suffix="%" 
                   valueStyle={{ color: '#3f8600' }}
                 />
                 <Progress percent={98.4} size="small" strokeColor="#3f8600" />
              </Card>
           </Col>
           <Col span={6}>
              <Card className="bg-white/5 border-white/10">
                 <Statistic 
                   title={<span className="text-gray-400">Blocked Actions (24h)</span>} 
                   value={evaluations.filter(v => v.decision === 'DENY').length} 
                   valueStyle={{ color: '#cf1322' }}
                 />
                 <Text className="text-[10px] text-gray-500 font-black">2 CRITICAL RISKS PREVENTED</Text>
              </Card>
           </Col>
           <Col span={6}>
              <Card className="bg-white/5 border-white/10">
                 <Statistic 
                   title={<span className="text-gray-400">Open Findings</span>} 
                   value={findings.filter(f => f.status === 'OPEN').length} 
                   valueStyle={{ color: '#faad14' }}
                 />
                 <Text className="text-[10px] text-gray-500 font-black">REMEDIATION REQUIRED</Text>
              </Card>
           </Col>
           <Col span={6}>
              <Card className="bg-white/5 border-white/10">
                 <Statistic 
                   title={<span className="text-gray-400">Active Overrides</span>} 
                   value={overrides.length} 
                 />
                 <Text className="text-[10px] text-gray-500 font-black">OPERATOR SUPERVISED</Text>
              </Card>
           </Col>
        </Row>

        <Card className="bg-white/5 border-white/10">
           <Tabs activeKey={activeTab} onChange={setActiveTab} className="!text-gray-400">
              <TabPane tab={<span><SafetyOutlined /> Policy Rules</span>} key="rules">
                 <Table 
                   columns={policyColumns} 
                   dataSource={policies} 
                   rowKey="id" 
                   loading={loading}
                   className="custom-table"
                 />
              </TabPane>
              <TabPane tab={<span><HistoryOutlined /> Evaluations</span>} key="evaluations">
                 <Table 
                   columns={evaluationColumns} 
                   dataSource={evaluations} 
                   rowKey="id" 
                   loading={loading}
                 />
              </TabPane>
              <TabPane tab={<span><SecurityScanOutlined /> Compliance Center</span>} key="compliance">
                 <Table 
                   columns={findingColumns} 
                   dataSource={findings} 
                   rowKey="id" 
                   loading={loading}
                 />
              </TabPane>
              <TabPane tab={<span><UnlockOutlined /> Override Ledger</span>} key="overrides">
                 {overrides.length > 0 ? (
                    <Table 
                      columns={[
                        { title: 'Time', dataIndex: 'created_at', render: (d) => new Date(d).toLocaleString() },
                        { title: 'Operator', dataIndex: 'operator' },
                        { title: 'Reason', dataIndex: 'override_reason' },
                        { title: 'Evidence Hash', dataIndex: 'evidence_hash', render: (h) => <Text code>{h}</Text> }
                      ]} 
                      dataSource={overrides} 
                      rowKey="id" 
                    />
                 ) : (
                    <Empty description="No manual overrides recorded." />
                 )}
              </TabPane>
           </Tabs>
        </Card>
      </Space>

      {/* New Policy Modal */}
      <Modal
        title="Create Policy Proposal"
        visible={isPolicyModalVisible}
        onCancel={() => setIsPolicyModalVisible(false)}
        onOk={() => form.submit()}
        width={800}
      >
        <Form form={form} layout="vertical" onFinish={handleCreatePolicy}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="policy_key" label="Policy Key" rules={[{ required: true }]}>
                <Input placeholder="e.g. DENY_HIGH_RISK_AUTO_APPLY" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="scope" label="Scope" initialValue="GLOBAL">
                <Select>
                  <Select.Option value="GLOBAL">Global</Select.Option>
                  <Select.Option value="PROJECT">Project</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="rule_type" label="Rule Type" initialValue="AUTO_APPLY">
            <Select>
              <Select.Option value="AUTO_APPLY">Auto Apply Control</Select.Option>
              <Select.Option value="MAINTENANCE_WINDOW">Maintenance Window</Select.Option>
              <Select.Option value="COMPLIANCE">Compliance Scanner</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="rule_definition_json" label="Rule Logic (JSON-PaC)">
            <Input.TextArea rows={6} placeholder='{"if": {"risk_level": "CRITICAL"}, "then": {"decision": "DENY"}}' />
          </Form.Item>
          <Form.Item name="description" label="Rationale / Description">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Override Modal */}
      <Modal
        title="Authorized Policy Override"
        visible={isOverrideModalVisible}
        onCancel={() => setIsOverrideModalVisible(false)}
        footer={[
          <Button key="back" onClick={() => setIsOverrideModalVisible(false)}>Cancel</Button>,
          <Button key="submit" type="primary" danger icon={<UnlockOutlined />} onClick={() => form.submit()}>
            Authorize & Execute
          </Button>
        ]}
      >
        <Form onFinish={handleCreateOverride} layout="vertical">
          <Alert
            message="Sovereign Governance Bypass"
            description="Manually overriding a policy decision requires a cryptographic signature in the evidence chain. Rationale is non-repudiable."
            type="warning"
            showIcon
            className="mb-4"
          />
          <Form.Item name="rationale" label="Justification Rationale" rules={[{ required: true }]}>
            <Input.TextArea rows={4} placeholder="Technical reason for bypass..." />
          </Form.Item>
        </Form>
      </Modal>

      <style jsx global>{`
        .custom-table .ant-table {
          background: transparent !important;
          color: white !important;
        }
        .ant-table-thead > tr > th {
          background: rgba(255,255,255,0.05) !important;
          color: rgba(255,255,255,0.4) !important;
          border-bottom: 1px solid rgba(255,255,255,0.1) !important;
          font-size: 10px;
          text-transform: uppercase;
          font-weight: 900;
          letter-spacing: 0.1em;
        }
        .ant-table-tbody > tr > td {
          border-bottom: 1px solid rgba(255,255,255,0.05) !important;
          background: transparent !important;
          color: white !important;
        }
        .ant-table-tbody > tr:hover > td {
          background: rgba(255,255,255,0.02) !important;
        }
        .ant-tabs-tab {
          color: rgba(255,255,255,0.4) !important;
          font-weight: 900;
          text-transform: uppercase;
          font-size: 11px;
          letter-spacing: 0.05em;
        }
        .ant-tabs-tab-active {
          color: #66fcf1 !important;
        }
        .ant-tabs-ink-bar {
          background: #66fcf1 !important;
        }
      `}</style>
    </div>
  );
};

export default GovernanceCenter;
