"use client";

import React, { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Table, Tag, Space, Button, Card, Typography, Modal, Form, Input, Select, Badge } from 'antd';
import { TeamOutlined, PlusOutlined, EditOutlined, SafetyOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const OperationsTeamsPanel: React.FC = () => {
  const t = useTranslations('repair_lab.ga_operations');
  const [teams, setTeams] = useState([
    {
      id: '1',
      team_key: 'PLATFORM_OPS',
      team_name: 'Platform Operations',
      status: 'ACTIVE',
      projects: ['CORE_UI', 'AUTH_SERVICE'],
      technical_owner: 'John Doe',
      business_owner: 'Sarah Smith'
    },
    {
      id: '2',
      team_key: 'CHECKOUT_TEAM',
      team_name: 'Checkout Experience',
      status: 'ACTIVE',
      projects: ['CHECKOUT_FLOW', 'PAYMENT_WIDGET'],
      technical_owner: 'Alice Wong',
      business_owner: 'Bob Miller'
    }
  ]);

  const columns = [
    {
      title: t('teams.table.name'),
      dataIndex: 'team_name',
      key: 'team_name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: t('teams.table.key'),
      dataIndex: 'team_key',
      key: 'team_key',
      render: (key: string) => <Tag color="blue">{key}</Tag>,
    },
    {
      title: t('teams.table.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={status === 'ACTIVE' ? 'success' : 'default'} text={status} />
      ),
    },
    {
      title: t('teams.table.projects'),
      dataIndex: 'projects',
      key: 'projects',
      render: (projects: string[]) => (
        <Space wrap>
          {projects.map(p => <Tag key={p}>{p}</Tag>)}
        </Space>
      ),
    },
    {
      title: t('ownership.technical'),
      dataIndex: 'technical_owner',
      key: 'technical_owner',
    },
    {
      title: 'Action',
      key: 'action',
      render: () => (
        <Space size="middle">
          <Button icon={<EditOutlined />} size="small">Edit</Button>
          <Button icon={<SafetyOutlined />} size="small">Policies</Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={4}>{t('tabs.teams')}</Title>
          <Text type="secondary">Manage organizational ownership and on-call policies.</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />}>
          {t('teams.actions.new_team')}
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={teams} 
        rowKey="id" 
        pagination={false}
        className="border rounded-lg"
      />
    </div>
  );
};

export default OperationsTeamsPanel;
