"use client";

import React, { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Table, Tag, Space, Button, Card, Typography, Badge, Steps, Row, Col } from 'antd';
import { ForkOutlined, PhoneOutlined, MailOutlined, MessageOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const EscalationMatrixPanel: React.FC = () => {
  const t = useTranslations('repair_lab.ga_operations');
  
  const [matrix] = useState([
    {
      id: '1',
      level: 1,
      role: 'On-Call Engineer',
      method: 'Slack / PagerDuty',
      responseTime: '15m',
      status: 'ACTIVE'
    },
    {
      id: '2',
      level: 2,
      role: 'Team Lead',
      method: 'Phone / SMS',
      responseTime: '30m',
      status: 'ACTIVE'
    },
    {
      id: '3',
      level: 3,
      role: 'Platform Architect',
      method: 'Direct Call',
      responseTime: '1h',
      status: 'STANDBY'
    },
    {
      id: '4',
      level: 4,
      role: 'VP Engineering / CTO',
      method: 'Crisis Bridge',
      responseTime: '4h',
      status: 'STANDBY'
    }
  ]);

  const columns = [
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      render: (level: number) => <Tag color={level > 2 ? 'red' : 'orange'}>L{level}</Tag>,
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Communication Method',
      dataIndex: 'method',
      key: 'method',
      render: (method: string) => (
        <Space>
          {method.includes('Slack') && <MessageOutlined />}
          {method.includes('Phone') && <PhoneOutlined />}
          {method.includes('Mail') && <MailOutlined />}
          {method}
        </Space>
      ),
    },
    {
      title: 'Target Response',
      dataIndex: 'responseTime',
      key: 'responseTime',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={status === 'ACTIVE' ? 'processing' : 'default'} text={status} />
      ),
    },
  ];

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={4}>{t('tabs.escalation')}</Title>
          <Text type="secondary">Enterprise-grade escalation hierarchy for critical SLO breaches and autonomous repair failures.</Text>
        </div>
        <Button icon={<ForkOutlined />}>
          Update Matrix
        </Button>
      </div>

      <Row gutter={16}>
        <Col span={16}>
          <Table 
            columns={columns} 
            dataSource={matrix} 
            rowKey="id" 
            pagination={false}
            className="border rounded-lg"
          />
        </Col>
        <Col span={8}>
          <Card title="Incident Flow" size="small" className="h-full border rounded-lg">
            <Steps
              direction="vertical"
              size="small"
              current={0}
              items={[
                { title: 'Detection', description: 'SLO breach detected by SLOService' },
                { title: 'Auto-Healing', description: 'System attempts L1/L2 autonomous repair' },
                { title: 'Escalation', description: 'Failure to repair triggers L1 human on-call' },
                { title: 'Governance', description: 'Major changes require VP/CTO approval' },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default EscalationMatrixPanel;
