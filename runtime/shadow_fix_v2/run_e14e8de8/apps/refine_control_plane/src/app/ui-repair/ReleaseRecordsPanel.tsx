"use client";

import React, { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Table, Tag, Button, Typography, Space, Modal, List, Badge } from 'antd';
import { HistoryOutlined, FileTextOutlined, CheckCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const ReleaseRecordsPanel: React.FC = () => {
  const t = useTranslations('repair_lab.ga_operations');
  const [releases, setReleases] = useState([
    {
      id: '1',
      version: 'v1.12.5',
      release_type: 'PATCH',
      date: '2026-05-14 10:00',
      summary: 'UI Repair Engine Optimization',
      status: 'STABLE'
    },
    {
      id: '2',
      version: 'v1.12.0',
      release_type: 'MINOR',
      date: '2026-05-10 14:30',
      summary: 'Multi-Project Support Implementation',
      status: 'STABLE'
    }
  ]);

  const columns = [
    {
      title: t('releases.table.version'),
      dataIndex: 'version',
      key: 'version',
      render: (v: string) => <Text strong>{v}</Text>,
    },
    {
      title: t('releases.table.type'),
      dataIndex: 'release_type',
      key: 'release_type',
      render: (type: string) => (
        <Tag color={type === 'PATCH' ? 'green' : 'blue'}>{type}</Tag>
      ),
    },
    {
      title: t('releases.table.date'),
      dataIndex: 'date',
      key: 'date',
    },
    {
      title: 'Summary',
      dataIndex: 'summary',
      key: 'summary',
    },
    {
      title: t('releases.table.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status="success" text={status} />
      ),
    },
    {
      title: 'Action',
      key: 'action',
      render: () => (
        <Button icon={<FileTextOutlined />} size="small">Details</Button>
      ),
    },
  ];

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={4}>{t('tabs.releases')}</Title>
          <Text type="secondary">Audit records of system updates, policy changes, and patches.</Text>
        </div>
        <Button type="primary" icon={<HistoryOutlined />}>
          {t('releases.generate')}
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={releases} 
        rowKey="id" 
        pagination={false}
        className="border rounded-lg"
      />
    </div>
  );
};

export default ReleaseRecordsPanel;
