"use client";

import React, { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Table, Tag, Button, Typography, Space, Progress, Switch, Card, Row, Col, Statistic } from 'antd';
import { DatabaseOutlined, SaveOutlined, DeleteOutlined, LockOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const EvidenceRetentionPanel: React.FC = () => {
  const t = useTranslations('repair_lab.ga_operations');
  const [policies, setPolicies] = useState([
    {
      id: '1',
      type: 'Monitoring Evidence',
      retention: 90,
      archive: 30,
      delete: 90,
      legal_hold: false,
      size: '1.2 TB'
    },
    {
      id: '2',
      type: 'Repair Governance Proofs',
      retention: 365,
      archive: 90,
      delete: 365,
      legal_hold: true,
      size: '450 GB'
    }
  ]);

  const columns = [
    {
      title: 'Evidence Type',
      dataIndex: 'type',
      key: 'type',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: t('evidence.archive'),
      dataIndex: 'archive',
      key: 'archive',
      render: (days: number) => `${days} days`,
    },
    {
      title: t('evidence.delete'),
      dataIndex: 'delete',
      key: 'delete',
      render: (days: number) => `${days} days`,
    },
    {
      title: 'Storage Size',
      dataIndex: 'size',
      key: 'size',
    },
    {
      title: t('evidence.legal_hold'),
      dataIndex: 'legal_hold',
      key: 'legal_hold',
      render: (hold: boolean) => (
        <Switch 
          checked={hold} 
          size="small" 
          checkedChildren={<LockOutlined />} 
          unCheckedChildren={<LockOutlined />}
        />
      ),
    },
    {
      title: 'Action',
      key: 'action',
      render: () => (
        <Button size="small">Configure</Button>
      ),
    },
  ];

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={4}>{t('tabs.evidence')}</Title>
          <Text type="secondary">Manage data lifecycle for autonomous repair evidence and audit trails.</Text>
        </div>
        <Button type="primary" icon={<SaveOutlined />}>
          Save Policies
        </Button>
      </div>

      <Row gutter={16} className="mb-6">
        <Col span={8}>
          <Card size="small">
            <Statistic title="Total Evidence Data" value="4.8" suffix="TB" prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic title="Archived Proofs" value={15400} prefix={<SaveOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic title="Daily Data Growth" value={45} suffix="GB" />
          </Card>
        </Col>
      </Row>

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

export default EvidenceRetentionPanel;
