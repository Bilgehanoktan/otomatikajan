"use client";

import React, { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Tabs, Card, Typography, Row, Col, Statistic, Space, Tag } from 'antd';
import { 
  TeamOutlined, 
  SafetyCertificateOutlined, 
  HistoryOutlined, 
  DeploymentUnitOutlined, 
  DatabaseOutlined, 
  WarningOutlined,
  ForkOutlined
} from '@ant-design/icons';
import OperationsTeamsPanel from '@/app/ui-repair/OperationsTeamsPanel';
import MaintenancePoliciesPanel from '@/app/ui-repair/MaintenancePoliciesPanel';
import ReleaseRecordsPanel from '@/app/ui-repair/ReleaseRecordsPanel';
import CompatibilityChecksPanel from '@/app/ui-repair/CompatibilityChecksPanel';
import EvidenceRetentionPanel from '@/app/ui-repair/EvidenceRetentionPanel';
import SLOBreachesPanel from '@/app/ui-repair/SLOBreachesPanel';
import EscalationMatrixPanel from '@/app/ui-repair/EscalationMatrixPanel';

const { Title, Text } = Typography;

const GAOperationsDashboard: React.FC = () => {
  const t = useTranslations('repair_lab.ga_operations');
  const [activeTab, setActiveTab] = useState('teams');

  const items = [
    {
      key: 'teams',
      label: (
        <span>
          <TeamOutlined />
          {t('tabs.teams')}
        </span>
      ),
      children: <OperationsTeamsPanel />,
    },
    {
      key: 'maintenance',
      label: (
        <span>
          <SafetyCertificateOutlined />
          {t('tabs.maintenance')}
        </span>
      ),
      children: <MaintenancePoliciesPanel />,
    },
    {
      key: 'releases',
      label: (
        <span>
          <HistoryOutlined />
          {t('tabs.releases')}
        </span>
      ),
      children: <ReleaseRecordsPanel />,
    },
    {
      key: 'compatibility',
      label: (
        <span>
          <DeploymentUnitOutlined />
          {t('tabs.compatibility')}
        </span>
      ),
      children: <CompatibilityChecksPanel />,
    },
    {
      key: 'evidence',
      label: (
        <span>
          <DatabaseOutlined />
          {t('tabs.evidence')}
        </span>
      ),
      children: <EvidenceRetentionPanel />,
    },
    {
      key: 'slo',
      label: (
        <span>
          <WarningOutlined />
          {t('tabs.slo')}
        </span>
      ),
      children: <SLOBreachesPanel />,
    },
    {
      key: 'escalation',
      label: (
        <span>
          <ForkOutlined />
          {t('tabs.escalation')}
        </span>
      ),
      children: <EscalationMatrixPanel />,
    },
  ];

  return (
    <div className="ga-operations-dashboard">
      <Row gutter={[16, 16]} className="mb-6">
        <Col span={6}>
          <Card bordered={false} className="stat-card">
            <Statistic
              title={t('stats.owner_coverage')}
              value={98}
              suffix="%"
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="stat-card">
            <Statistic
              title={t('stats.active_windows')}
              value={3}
              prefix={<SafetyCertificateOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="stat-card">
            <Statistic
              title={t('stats.open_breaches')}
              value={0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="stat-card">
            <Statistic
              title={t('stats.recent_releases')}
              value={12}
              prefix={<HistoryOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card bordered={false} className="ga-ops-tabs-card shadow-lg rounded-xl">
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab} 
          items={items}
          type="line"
          size="large"
        />
      </Card>
    </div>
  );
};

export default GAOperationsDashboard;
