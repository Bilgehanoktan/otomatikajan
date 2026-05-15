'use client';

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Tabs, message, Space, Progress, List, Typography } from 'antd';
import { 
  GlobalOutlined, 
  RocketOutlined, 
  SafetyCertificateOutlined, 
  BarChartOutlined, 
  CheckCircleOutlined, 
  BookOutlined,
  ProjectOutlined
} from '@ant-design/icons';
import { useTranslations } from 'next-intl';
import ProjectProfilePanel from './ProjectProfilePanel';
import RolloutWavePanel from './RolloutWavePanel';
import ProjectHealthMatrixPanel from './ProjectHealthMatrixPanel';
import SLASLOTrackerPanel from './SLASLOTrackerPanel';
import GAReadinessPanel from './GAReadinessPanel';
import EnterpriseRunbookPanel from './EnterpriseRunbookPanel';

const { Title, Text } = Typography;

const EnterpriseRolloutPanel: React.FC = () => {
  const t = useTranslations('repair_lab.enterprise_rollout');
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview();
  }, []);

  const fetchOverview = async () => {
    try {
      const res = await fetch('/api/v1/ui-repair/enterprise/overview');
      const data = await res.json();
      setOverview(data);
    } catch (err) {
      message.error('Failed to fetch enterprise overview');
    } finally {
      setLoading(false);
    }
  };

  const items = [
    {
      key: 'projects',
      label: (
        <span>
          <ProjectOutlined />
          {t('tabs.projects')}
        </span>
      ),
      children: <ProjectProfilePanel />,
    },
    {
      key: 'waves',
      label: (
        <span>
          <RocketOutlined />
          {t('tabs.waves')}
        </span>
      ),
      children: <RolloutWavePanel />,
    },
    {
      key: 'health',
      label: (
        <span>
          <GlobalOutlined />
          {t('tabs.health_matrix')}
        </span>
      ),
      children: <ProjectHealthMatrixPanel />,
    },
    {
      key: 'sla_slo',
      label: (
        <span>
          <BarChartOutlined />
          {t('tabs.sla_slo')}
        </span>
      ),
      children: <SLASLOTrackerPanel />,
    },
    {
      key: 'readiness',
      label: (
        <span>
          <CheckCircleOutlined />
          {t('tabs.ga_readiness')}
        </span>
      ),
      children: <GAReadinessPanel />,
    },
    {
      key: 'runbook',
      label: (
        <span>
          <BookOutlined />
          {t('tabs.runbook')}
        </span>
      ),
      children: <EnterpriseRunbookPanel />,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title={t('stats.total_projects')} 
              value={overview?.total_projects || 0} 
              prefix={<ProjectOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title={t('stats.active_projects')} 
              value={overview?.active_projects || 0} 
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title={t('stats.global_health')} 
              value={overview?.global_health_score || 0} 
              suffix="%" 
              prefix={<GlobalOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title={t('stats.ga_status')} 
              value={overview?.ga_readiness_status || 'PENDING'} 
              valueStyle={{ fontSize: '18px', fontWeight: 'bold' }}
              prefix={<SafetyCertificateOutlined />} 
            />
          </Card>
        </Col>
      </Row>

      <Card bordered={false} className="glass-card">
        <Tabs defaultActiveKey="projects" items={items} />
      </Card>
    </div>
  );
};

export default EnterpriseRolloutPanel;
