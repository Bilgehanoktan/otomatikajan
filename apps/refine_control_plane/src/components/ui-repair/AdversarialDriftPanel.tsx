'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, Tag, Typography, Button, Space, message, Timeline, Card 
} from 'antd';
import { Activity, AlertTriangle, Clock } from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

const { Text, Title } = Typography;

interface DriftEvent {
  id: string;
  domain: string;
  drift_type: string;
  drift_score: number;
  severity: string;
  description: string;
  created_at: string;
}

const AdversarialDriftPanel: React.FC = () => {
  const [drifts, setDrifts] = useState<DriftEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDrifts = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson<DriftEvent[]>('/api/v1/ui-repair/security/red-team/drift-events');
      setDrifts(data);
    } catch (err) {
      message.error('Failed to fetch drift data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDrifts();
  }, []);

  const columns = [
    {
      title: 'Domain',
      dataIndex: 'domain',
      key: 'domain',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Drift Type',
      dataIndex: 'drift_type',
      key: 'drift_type',
      render: (value: string) => <Tag color="blue">{value.replace(/_/g, ' ')}</Tag>,
    },
    {
      title: 'Summary',
      dataIndex: 'description',
      key: 'description',
      render: (value: string) => <Text className="text-slate-300">{value}</Text>,
    },
    {
      title: 'Drift Score',
      dataIndex: 'drift_score',
      key: 'drift_score',
      render: (score: number) => {
        let color = 'success';
        if (score > 0.4) color = 'warning';
        if (score > 0.7) color = 'error';
        return <Tag color={color}>{(score * 100).toFixed(0)}%</Tag>;
      }
    },
    {
      title: 'Status',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => (
        <Tag color={severity === 'CRITICAL' ? 'error' : severity === 'HIGH' ? 'warning' : 'processing'} icon={<AlertTriangle size={12} />}>
          {severity}
        </Tag>
      ),
    },
    {
      title: 'Detected At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleTimeString(),
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-4">
        <div className="flex justify-between items-center">
          <Text strong>Real-time Adversarial Drift Monitoring</Text>
        </div>
        <Table 
          dataSource={drifts} 
          columns={columns} 
          rowKey="id" 
          size="small"
          loading={loading}
          className="custom-table"
        />
      </div>

      <Card title={<Space><Clock size={16} />Drift History</Space>} className="bg-slate-900/50 border-slate-800">
        <Timeline 
          items={drifts.slice(0, 5).map(d => ({
            color: d.severity === 'CRITICAL' ? 'red' : d.severity === 'HIGH' ? 'orange' : 'blue',
            children: (
              <div>
                <Text type="secondary" className="text-xs">{new Date(d.created_at).toLocaleTimeString()}</Text>
                <br />
                <Text>{d.domain} / {d.drift_type}: {(d.drift_score * 100).toFixed(0)}%</Text>
              </div>
            )
          }))}
        />
      </Card>
    </div>
  );
};

export default AdversarialDriftPanel;
