"use client";

import React, { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Table, Tag, Button, Typography, Space, Alert, Progress } from 'antd';
import { DeploymentUnitOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const CompatibilityChecksPanel: React.FC = () => {
  const t = useTranslations('repair_lab.ga_operations');
  const [checks, setChecks] = useState([
    {
      id: '1',
      project_key: 'CORE_UI',
      version: 'v1.12.5',
      status: 'PASSED',
      breaking: 0,
      deprecated: 2,
      last_check: '2026-05-15 03:00'
    },
    {
      id: '2',
      project_key: 'LEGACY_CRM',
      version: 'v0.9.0',
      status: 'FAILED',
      breaking: 3,
      deprecated: 5,
      last_check: '2026-05-15 02:30'
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
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'PASSED' ? 'success' : (status === 'WARNING' ? 'warning' : 'error');
        const icon = status === 'PASSED' ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />;
        return <Tag color={color} icon={icon}>{t(`compatibility.status.${status.toLowerCase()}`)}</Tag>;
      },
    },
    {
      title: t('compatibility.breaking'),
      dataIndex: 'breaking',
      key: 'breaking',
      render: (val: number) => <Text type={val > 0 ? 'danger' : 'success'}>{val}</Text>,
    },
    {
      title: t('compatibility.deprecated'),
      dataIndex: 'deprecated',
      key: 'deprecated',
      render: (val: number) => <Text type={val > 0 ? 'warning' : 'success'}>{val}</Text>,
    },
    {
      title: 'Last Check',
      dataIndex: 'last_check',
      key: 'last_check',
    },
    {
      title: 'Action',
      key: 'action',
      render: () => (
        <Button size="small">Run Check</Button>
      ),
    },
  ];

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={4}>{t('tabs.compatibility')}</Title>
          <Text type="secondary">Validate project configurations against system-wide standards.</Text>
        </div>
        <Button type="primary" icon={<DeploymentUnitOutlined />}>
          Batch Check
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={checks} 
        rowKey="id" 
        pagination={false}
        className="border rounded-lg"
      />
      
      {checks.some(c => c.status === 'FAILED') && (
        <Alert
          message="Compatibility Issues Detected"
          description="Legacy CRM project has breaking changes that require manual migration before auto-repair can continue."
          type="error"
          showIcon
          className="mt-4"
        />
      )}
    </div>
  );
};

export default CompatibilityChecksPanel;
