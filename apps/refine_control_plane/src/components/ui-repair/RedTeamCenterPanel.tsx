'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, Typography, Row, Col, Button, Tabs, 
  Spin, Alert, Divider, Tag, Space, Statistic
} from 'antd';
import { 
  Shield, PlayCircle, Activity, Bug, BarChart3, 
  Settings, AlertCircle, CheckCircle2, RefreshCw
} from 'lucide-react';
import RedTeamScenarioPanel from './RedTeamScenarioPanel';
import GuardrailValidationPanel from './GuardrailValidationPanel';
import AdversarialDriftPanel from './AdversarialDriftPanel';
import RedTeamFindingsPanel from './RedTeamFindingsPanel';
import RedTeamReportPanel from './RedTeamReportPanel';

const { Title, Text } = Typography;

interface RedTeamOverview {
  total_scenarios: number;
  active_operations: number;
  success_rate: number;
  avg_detection_latency: number;
  critical_drifts: number;
  last_run_at: string | null;
}

const RedTeamCenterPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState('scenarios');
  const [overview, setOverview] = useState<RedTeamOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ui-repair/security/red-team/overview');
      if (!response.ok) throw new Error('Failed to fetch Red Team overview');
      const data = await response.json();
      setOverview(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const triggerFullSuite = async () => {
    setLoading(true);
    try {
      await fetch('/api/v1/ui-repair/security/red-team/run-suite', { method: 'POST' });
      await fetchOverview();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const tabItems = [
    {
      key: 'scenarios',
      label: <Space><Shield size={16} />Scenarios</Space>,
      children: <RedTeamScenarioPanel />
    },
    {
      key: 'operations',
      label: <Space><PlayCircle size={16} />Operations</Space>,
      children: <GuardrailValidationPanel />
    },
    {
      key: 'drift',
      label: <Space><Activity size={16} />Adversarial Drift</Space>,
      children: <AdversarialDriftPanel />
    },
    {
      key: 'findings',
      label: <Space><Bug size={16} />Findings</Space>,
      children: <RedTeamFindingsPanel />
    },
    {
      key: 'reports',
      label: <Space><BarChart3 size={16} />Reports</Space>,
      children: <RedTeamReportPanel />
    }
  ];

  if (loading && !overview) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" tip="Loading Red Team Center..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={2} className="flex items-center gap-2 !mb-1">
            <Shield className="text-rose-500" /> Red Team Center
          </Title>
          <Text type="secondary">Autonomous Adversarial Testing & Guardrail Validation</Text>
        </div>
        <Space>
          <Button icon={<RefreshCw size={16} />} onClick={fetchOverview}>Refresh</Button>
          <Button 
            type="primary" 
            danger
            icon={<PlayCircle size={16} />} 
            onClick={triggerFullSuite}
            loading={loading}
          >
            Run Full Red Team Suite
          </Button>
        </Space>
      </div>

      {error && <Alert message={error} type="error" showIcon closable className="mb-6" />}

      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/50 border border-slate-800">
            <Statistic 
              title={<Text type="secondary">Total Scenarios</Text>} 
              value={overview?.total_scenarios} 
              valueStyle={{ color: '#fff', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/50 border border-slate-800">
            <Statistic 
              title={<Text type="secondary">Guardrail Pass Rate</Text>} 
              value={overview?.success_rate} 
              suffix="%"
              valueStyle={{ color: '#10b981', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/50 border border-slate-800">
            <Statistic 
              title={<Text type="secondary">Avg Detection Latency</Text>} 
              value={overview?.avg_detection_latency} 
              suffix="ms"
              valueStyle={{ color: '#3b82f6', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/50 border border-slate-800">
            <Statistic 
              title={<Text type="secondary">Critical Drifts</Text>} 
              value={overview?.critical_drifts} 
              valueStyle={{ color: '#f43f5e', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/50 border border-slate-800">
            <Statistic 
              title={<Text type="secondary">Active Operations</Text>} 
              value={overview?.active_operations} 
              valueStyle={{ color: '#8b5cf6', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
      </Row>

      <Card className="bg-slate-900/50 border-slate-800">
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab} 
          items={tabItems}
          className="custom-tabs"
        />
      </Card>
    </div>
  );
};

export default RedTeamCenterPanel;
