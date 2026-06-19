'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, Tag, Typography, Button, Space, Progress, message, Tooltip 
} from 'antd';
import { Play, RotateCcw, AlertTriangle, CheckCircle } from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

const { Text } = Typography;

interface Run {
  id: string;
  scenario_id: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  bypassed_controls: string[];
  triggered_controls: string[];
  result_summary: {
    probes_count?: number;
    probes_passed?: number;
    drift_events_count?: number;
  };
}

const GuardrailValidationPanel: React.FC = () => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson<Run[]>('/api/v1/ui-repair/security/red-team/runs');
      setRuns(data);
    } catch (err) {
      message.error('Failed to fetch runs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const rerunScenario = async (scenarioId: string) => {
    try {
      await safeFetchJson(`/api/v1/ui-repair/security/red-team/scenarios/${scenarioId}/run`, { method: 'POST' });
      message.success('Scenario rerun triggered');
      await fetchRuns();
    } catch (err) {
      message.error('Rerun failed');
    }
  };

  const runAllScenarios = async () => {
    try {
      await safeFetchJson('/api/v1/ui-repair/security/red-team/run-suite', { method: 'POST' });
      message.success('Full suite triggered');
      await fetchRuns();
    } catch (err) {
      message.error('Suite trigger failed');
    }
  };

  const columns = [
    {
      title: 'Scenario ID',
      dataIndex: 'scenario_id',
      key: 'scenario_id',
      render: (value: string) => <Text code>{value}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = 'default';
        let icon = null;
        if (status === 'PASSED') { color = 'success'; icon = <CheckCircle size={12} />; }
        if (status === 'FAILED') { color = 'error'; icon = <AlertTriangle size={12} />; }
        if (status === 'RUNNING') color = 'processing';
        return <Tag color={color} icon={icon}>{status}</Tag>;
      }
    },
    {
      title: 'Start Time',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Probes',
      dataIndex: 'result_summary',
      key: 'probes_count',
      render: (summary: Run['result_summary']) => <Text>{summary?.probes_passed ?? 0} / {summary?.probes_count ?? 0}</Text>,
    },
    {
      title: 'Drift Events',
      dataIndex: 'result_summary',
      key: 'drift_events_count',
      render: (summary: Run['result_summary']) => {
        const driftEvents = summary?.drift_events_count ?? 0;
        return (
          <Space direction="vertical" style={{ width: '100px' }}>
            <Progress 
              percent={Math.min(driftEvents * 25, 100)}
              size="small" 
              showInfo={false} 
              strokeColor={driftEvents > 0 ? '#f5222d' : '#1890ff'} 
            />
            <Text type="secondary" className="text-xs">{driftEvents}</Text>
          </Space>
        );
      },
    },
    {
      title: 'Triggered Controls',
      dataIndex: 'triggered_controls',
      key: 'triggered_controls',
      render: (controls: string[]) => <Text>{controls?.length ?? 0}</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      align: 'right' as const,
      render: (_: any, record: Run) => (
        <Space>
          <Tooltip title="Rerun">
            <Button type="text" icon={<RotateCcw size={16} />} onClick={() => rerunScenario(record.scenario_id)} />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Text strong>Recent Guardrail Validations</Text>
        <Button icon={<Play size={16} />} type="primary" size="small" onClick={runAllScenarios}>Run All Scenarios</Button>
      </div>

      <Table 
        dataSource={runs} 
        columns={columns} 
        rowKey="id" 
        size="small"
        loading={loading}
        className="custom-table"
      />
    </div>
  );
};

export default GuardrailValidationPanel;
