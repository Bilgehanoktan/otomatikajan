'use client';

import React, { useState, useEffect } from 'react';
import { Table, Tag, Progress, message, Tooltip } from 'antd';
import { useTranslations } from 'next-intl';
import { safeFetchJson } from '@/lib/api';

const ProjectHealthMatrixPanel: React.FC = () => {
  const t = useTranslations('repair_lab.enterprise_rollout.health_matrix');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth();
  }, []);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const snapshots = await safeFetchJson('/api/v1/ui-repair/projects/health-matrix');
      setData(snapshots);
    } catch (err) {
      message.error('Failed to fetch health matrix');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: t('table.project'),
      dataIndex: 'project_name',
      key: 'name',
      render: (_: string, row: any) => (
        <div>
          <div className="font-medium text-slate-100">{row.project_name}</div>
          <div className="text-[11px] text-slate-500">{row.project_key}</div>
        </div>
      )
    },
    { 
      title: t('table.health_score'), 
      dataIndex: 'health_score', 
      key: 'score',
      render: (score: number) => (
        <Progress 
          percent={Math.round(score)} 
          size="small" 
          strokeColor={score > 90 ? '#52c41a' : score > 70 ? '#faad14' : '#f5222d'} 
        />
      )
    },
    { title: t('table.open_cases'), dataIndex: 'open_cases', key: 'cases' },
    { 
      title: t('table.sla_status'), 
      dataIndex: 'sla_status', 
      key: 'sla',
      render: (status: string) => <Tag color="green">{status}</Tag>
    },
    { 
      title: t('table.slo_status'), 
      dataIndex: 'slo_status', 
      key: 'slo',
      render: (status: string) => <Tag color="cyan">{status}</Tag>
    },
    {
      title: t('table.route_coverage'),
      dataIndex: 'route_coverage_percent',
      key: 'coverage',
      render: (value: number) => <Progress type="circle" percent={Math.round(value ?? 0)} width={30} />
    }
  ];

  return (
    <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
  );
};

export default ProjectHealthMatrixPanel;
