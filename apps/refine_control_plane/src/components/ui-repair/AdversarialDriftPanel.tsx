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
  metric_name: string;
  baseline_value: number;
  observed_value: number;
  drift_score: number;
  is_anomalous: boolean;
  created_at: string;
}

const AdversarialDriftPanel: React.FC = () => {
  const [drifts, setDrifts] = useState<DriftEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDrifts = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson<DriftEvent[]>('/api/v1/ui-repair/security/red-team/drifts');
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
      title: 'Metric',
      dataIndex: 'metric_name',
      key: 'metric_name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Baseline',
      dataIndex: 'baseline_value',
      key: 'baseline_value',
      render: (val: number) => val.toFixed(2),
    },
    {
      title: 'Observed',
      dataIndex: 'observed_value',
      key: 'observed_value',
      render: (val: number, record: DriftEvent) => (
        <Text type={record.is_anomalous ? 'danger' : 'success'}>{val.toFixed(2)}</Text>
      ),
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
      dataIndex: 'is_anomalous',
      key: 'is_anomalous',
      render: (anom: boolean) => anom ? 
        <Tag color="error" icon={<AlertTriangle size={12} />}>ANOMALY</Tag> : 
        <Tag color="success">STABLE</Tag>,
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
            color: d.is_anomalous ? 'red' : 'green',
            children: (
              <div>
                <Text type="secondary" className="text-xs">{new Date(d.created_at).toLocaleTimeString()}</Text>
                <br />
                <Text>{d.metric_name} drift: {(d.drift_score * 100).toFixed(0)}%</Text>
              </div>
            )
          }))}
        />
      </Card>
    </div>
  );
};

export default AdversarialDriftPanel;
