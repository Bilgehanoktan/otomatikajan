'use client';

import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Table, Tag, Button, Space, Tooltip, message 
} from 'antd';
import { Play, Eye, RefreshCw, Wand2 } from 'lucide-react';

const { Text } = Typography;

interface Scenario {
  id: string;
  scenario_key: string;
  scenario_name: string;
  scenario_type: string;
  target_domain: string;
  risk_level: string;
  safety_mode: string;
  enabled: boolean;
}

const RedTeamScenarioPanel: React.FC = () => {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchScenarios = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/ui-repair/security/red-team/scenarios');
      const data = await res.json();
      setScenarios(data);
    } catch (err) {
      message.error('Failed to fetch scenarios');
    } finally {
      setLoading(false);
    }
  };

  const generateScenarios = async () => {
    setLoading(true);
    try {
      await fetch('/api/v1/ui-repair/security/red-team/scenarios/generate', { method: 'POST' });
      message.success('Generated scenarios from attack paths');
      await fetchScenarios();
    } catch (err) {
      message.error('Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const runScenario = async (id: string) => {
    try {
      await fetch(`/api/v1/ui-repair/security/red-team/scenarios/${id}/run`, { method: 'POST' });
      message.success('Scenario operation triggered');
    } catch (err) {
      message.error('Trigger failed');
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, []);

  const columns = [
    {
      title: 'Key',
      dataIndex: 'scenario_key',
      key: 'scenario_key',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: 'Name',
      dataIndex: 'scenario_name',
      key: 'scenario_name',
    },
    {
      title: 'Type',
      dataIndex: 'scenario_type',
      key: 'scenario_type',
      render: (type: string) => <Tag>{type.replace(/_/g, ' ')}</Tag>,
    },
    {
      title: 'Domain',
      dataIndex: 'target_domain',
      key: 'target_domain',
    },
    {
      title: 'Risk',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (risk: string) => {
        let color = 'default';
        if (risk === 'CRITICAL') color = 'error';
        if (risk === 'HIGH') color = 'warning';
        if (risk === 'MEDIUM') color = 'processing';
        return <Tag color={color}>{risk}</Tag>;
      }
    },
    {
      title: 'Safety',
      dataIndex: 'safety_mode',
      key: 'safety_mode',
      render: (mode: string) => <Text type="secondary" size="small">{mode}</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      align: 'right' as const,
      render: (_: any, record: Scenario) => (
        <Space>
          <Tooltip title="Run Scenario">
            <Button 
              type="text" 
              icon={<Play size={16} className="text-emerald-500" />} 
              onClick={() => runScenario(record.id)} 
            />
          </Tooltip>
          <Tooltip title="View Details">
            <Button type="text" icon={<Eye size={16} />} />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Text strong>Configured Adversarial Scenarios</Text>
        <Space>
          <Button icon={<Wand2 size={16} />} onClick={generateScenarios} loading={loading}>
            Generate from Paths
          </Button>
          <Button icon={<RefreshCw size={16} />} onClick={fetchScenarios} />
        </Space>
      </div>

      <Table 
        dataSource={scenarios} 
        columns={columns} 
        rowKey="id" 
        size="small"
        loading={loading}
        pagination={{ pageSize: 10 }}
        className="custom-table"
      />
    </div>
  );
};

export default RedTeamScenarioPanel;
