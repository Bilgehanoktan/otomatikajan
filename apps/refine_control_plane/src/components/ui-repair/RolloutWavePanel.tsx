'use client';

import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, Space, message, Timeline, Typography, Card, Progress } from 'antd';
import { RocketOutlined, CheckCircleOutlined, SyncOutlined, PauseCircleOutlined } from '@ant-design/icons';
import { useTranslations } from 'next-intl';

const { Text } = Typography;

const RolloutWavePanel: React.FC = () => {
  const t = useTranslations('repair_lab.enterprise_rollout.waves');
  const [waves, setWaves] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWaves();
  }, []);

  const fetchWaves = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/ui-repair/rollout-waves');
      const data = await res.json();
      setWaves(data);
    } catch (err) {
      message.error('Failed to fetch rollout waves');
    } finally {
      setLoading(false);
    }
  };

  const startWave = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/ui-repair/rollout-waves/${id}/start`, { method: 'POST' });
      if (res.ok) {
        message.success('Rollout wave started');
        fetchWaves();
      }
    } catch (err) {
      message.error('Failed to start wave');
    }
  };

  const completeWave = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/ui-repair/rollout-waves/${id}/complete`, { method: 'POST' });
      if (res.ok) {
        message.success('Rollout wave completed');
        fetchWaves();
      }
    } catch (err) {
      message.error('Failed to complete wave');
    }
  };

  const columns = [
    { title: t('table.name'), dataIndex: 'wave_name', key: 'name' },
    { 
      title: t('table.status'), 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'COMPLETED' ? 'green' : status === 'RUNNING' ? 'blue' : 'default'}>
          {status}
        </Tag>
      )
    },
    { 
      title: t('table.projects'), 
      dataIndex: 'project_keys', 
      key: 'projects',
      render: (keys: string[]) => keys?.map(k => <Tag key={k}>{k}</Tag>)
    },
    { 
      title: t('table.mode'), 
      dataIndex: 'rollout_mode', 
      key: 'mode',
      render: (mode: string) => <Tag color="purple">{mode}</Tag>
    },
    {
      title: t('table.actions'),
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          {record.status === 'PLANNED' && (
            <Button size="small" type="primary" icon={<RocketOutlined />} onClick={() => startWave(record.id)}>
              {t('actions.start')}
            </Button>
          )}
          {record.status === 'RUNNING' && (
            <Button size="small" icon={<CheckCircleOutlined />} onClick={() => completeWave(record.id)}>
              {t('actions.complete')}
            </Button>
          )}
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <Timeline
          items={[
            { label: 'Wave 1', children: t('timeline.wave1'), color: 'green' },
            { label: 'Wave 2', children: t('timeline.wave2'), color: 'blue' },
            { label: 'Wave 3', children: t('timeline.wave3'), color: 'gray' },
            { label: 'Wave 4', children: t('timeline.wave4'), color: 'gray' },
          ]}
        />
      </div>

      <Table columns={columns} dataSource={waves} rowKey="id" loading={loading} />
    </div>
  );
};

export default RolloutWavePanel;
