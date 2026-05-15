'use client';

import React, { useState, useEffect } from 'react';
import { Table, Tag, Progress, message, Tooltip } from 'antd';
import { useTranslations } from 'next-intl';

const ProjectHealthMatrixPanel: React.FC = () => {
  const t = useTranslations('repair_lab.enterprise_rollout.health_matrix');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth();
  }, []);

  const fetchHealth = async () => {
    setLoading(true);
    // In real implementation, this would fetch UIProjectHealthSnapshot or projects with health
    try {
      const res = await fetch('/api/v1/ui-repair/projects');
      const projects = await res.json();
      
      const snapshots = projects.map((p: any) => ({
        ...p,
        health_score: 95 + Math.random() * 5, // Mock score
        open_cases: Math.floor(Math.random() * 5),
        sla_status: 'COMPLIANT',
        slo_status: 'HEALTHY'
      }));
      setData(snapshots);
    } catch (err) {
      message.error('Failed to fetch health matrix');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: t('table.project'), dataIndex: 'project_name', key: 'name' },
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
      key: 'coverage',
      render: () => <Progress type="circle" percent={100} width={30} />
    }
  ];

  return (
    <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
  );
};

export default ProjectHealthMatrixPanel;
