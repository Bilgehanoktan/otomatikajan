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
  scenario_name: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  findings_count: number;
  drift_score: number;
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

  const columns = [
    {
      title: 'Scenario',
      dataIndex: 'scenario_name',
      key: 'scenario_name',
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
      title: 'Findings',
      dataIndex: 'findings_count',
      key: 'findings_count',
      render: (count: number) => <Text type={count > 0 ? 'danger' : 'secondary'}>{count}</Text>,
    },
    {
      title: 'Drift Score',
      dataIndex: 'drift_score',
      key: 'drift_score',
      render: (score: number) => (
        <Space direction="vertical" style={{ width: '100px' }}>
          <Progress 
            percent={score * 100} 
            size="small" 
            showInfo={false} 
            strokeColor={score > 0.7 ? '#f5222d' : '#1890ff'} 
          />
          <Text type="secondary" className="text-xs">{score.toFixed(2)}</Text>
        </Space>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      align: 'right' as const,
      render: (_: any, record: Run) => (
        <Space>
          <Tooltip title="Rerun">
            <Button type="text" icon={<RotateCcw size={16} />} onClick={() => {}} />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Text strong>Recent Guardrail Validations</Text>
        <Button icon={<Play size={16} />} type="primary" size="small">Run All Scenarios</Button>
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
