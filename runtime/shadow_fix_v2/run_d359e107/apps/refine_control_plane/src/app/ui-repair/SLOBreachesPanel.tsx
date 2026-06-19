"use client";

import React, { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Table, Tag, Button, Typography, Space, Badge, Modal, Timeline, Card } from 'antd';
import { WarningOutlined, CheckCircleOutlined, InfoCircleOutlined, RocketOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const SLOBreachesPanel: React.FC = () => {
  const t = useTranslations('repair_lab.ga_operations');
  const [breaches, setBreaches] = useState([
    {
      id: '1',
      project_key: 'CORE_UI',
      slo_name: 'Repair Latency < 30m',
      severity: 'CRITICAL',
      observed: '45m',
      target: '30m',
      started_at: '2026-05-15 01:00',
      status: 'OPEN'
    },
    {
      id: '2',
      project_key: 'AUTH_SERVICE',
      slo_name: 'Success Rate > 95%',
      severity: 'WARNING',
      observed: '92%',
      target: '95%',
      started_at: '2026-05-15 00:30',
      status: 'ACKNOWLEDGED'
    }
  ]);

  const columns = [
    {
      title: 'Project',
      dataIndex: 'project_key',
      key: 'project_key',
      render: (key: string) => <Tag color="blue">{key}</Tag>,
    },
    {
      title: 'SLO Name',
      dataIndex: 'slo_name',
      key: 'slo_name',
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (sev: string) => (
        <Tag color={sev === 'CRITICAL' ? 'error' : 'warning'}>{sev}</Tag>
      ),
    },
    {
      title: 'Observed / Target',
      key: 'values',
      render: (record: any) => (
        <Space>
          <Text type="danger">{record.observed}</Text> / <Text type="secondary">{record.target}</Text>
        </Space>
      ),
    },
    {
      title: 'Started At',
      dataIndex: 'started_at',
      key: 'started_at',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={status === 'OPEN' ? 'error' : 'processing'} text={t(`slo.status.${status.toLowerCase()}`)} />
      ),
    },
    {
      title: 'Action',
      key: 'action',
      render: () => (
        <Space>
          <Button size="small" type="primary" ghost icon={<RocketOutlined />}>Remediate</Button>
          <Button size="small" icon={<InfoCircleOutlined />}>Log</Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={4}>{t('tabs.slo')}</Title>
          <Text type="secondary">Monitor and remediate SLO violations across all projects.</Text>
        </div>
      </div>

      <Table 
        columns={columns} 
        dataSource={breaches} 
        rowKey="id" 
        pagination={false}
        className="border rounded-lg"
      />
      
      <div className="mt-8">
        <Title level={5}>Remediation Timeline</Title>
        <Card size="small" className="mt-4">
          <Timeline
            items={[
              {
                color: 'red',
                children: 'SLO Breach Detected: Repair Latency > 30m on CORE_UI (01:00)',
              },
              {
                color: 'blue',
                children: 'Auto-scaling applied to repair workers (01:15)',
              },
              {
                children: 'On-call engineer notified (01:20)',
              },
              {
                color: 'gray',
                children: 'Pending resolution (01:30)',
              },
            ]}
          />
        </Card>
      </div>
    </div>
  );
};

export default SLOBreachesPanel;
