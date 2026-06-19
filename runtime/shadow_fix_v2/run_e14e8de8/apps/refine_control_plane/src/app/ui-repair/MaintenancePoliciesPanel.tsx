"use client";

import React, { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Table, Tag, Switch, Button, Typography, Space, Tooltip, Badge } from 'antd';
import { SafetyCertificateOutlined, ClockCircleOutlined, PlusOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const MaintenancePoliciesPanel: React.FC = () => {
  const t = useTranslations('repair_lab.ga_operations');
  const [policies, setPolicies] = useState([
    {
      id: '1',
      project_key: 'CORE_UI',
      policy_name: 'Strict Weekend Maintenance',
      window: 'Sat-Sun 02:00 - 05:00',
      auto_repair: true,
      auto_apply: false,
      approval_required: true
    },
    {
      id: '2',
      project_key: 'AUTH_SERVICE',
      policy_name: 'Nightly Pilot Window',
      window: 'Daily 01:00 - 03:00',
      auto_repair: true,
      auto_apply: true,
      approval_required: false
    }
  ]);

  const columns = [
    {
      title: 'Project',
      dataIndex: 'project_key',
      key: 'project_key',
      render: (key: string) => <Tag color="purple">{key}</Tag>,
    },
    {
      title: t('maintenance.table.policy'),
      dataIndex: 'policy_name',
      key: 'policy_name',
    },
    {
      title: t('maintenance.table.window'),
      dataIndex: 'window',
      key: 'window',
      render: (window: string) => (
        <span><ClockCircleOutlined className="mr-2" />{window}</span>
      ),
    },
    {
      title: t('maintenance.table.auto_repair'),
      dataIndex: 'auto_repair',
      key: 'auto_repair',
      render: (val: boolean) => <Switch checked={val} size="small" />,
    },
    {
      title: t('maintenance.table.auto_apply'),
      dataIndex: 'auto_apply',
      key: 'auto_apply',
      render: (val: boolean) => <Switch checked={val} size="small" />,
    },
    {
      title: 'Approval',
      dataIndex: 'approval_required',
      key: 'approval_required',
      render: (val: boolean) => (
        <Badge status={val ? 'warning' : 'success'} text={val ? 'Required' : 'Automated'} />
      ),
    },
  ];

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={4}>{t('tabs.maintenance')}</Title>
          <Text type="secondary">Define windows where autonomous repair and deployments are authorized.</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />}>
          New Policy
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={policies} 
        rowKey="id" 
        pagination={false}
        className="border rounded-lg"
      />
    </div>
  );
};

export default MaintenancePoliciesPanel;
