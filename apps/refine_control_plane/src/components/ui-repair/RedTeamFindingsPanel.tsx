'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, Tag, Typography, Button, Space, message, Badge 
} from 'antd';
import { ShieldAlert, ExternalLink, Hammer, CheckCircle } from 'lucide-react';

const { Text } = Typography;

interface Finding {
  id: string;
  finding_name: string;
  severity: string;
  affected_domain: string;
  is_remediated: boolean;
  remediation_id: string | null;
  created_at: string;
}

const RedTeamFindingsPanel: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchFindings = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/ui-repair/security/red-team/findings');
      const data = await res.json();
      setFindings(data);
    } catch (err) {
      message.error('Failed to fetch findings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, []);

  const triggerRemediation = async (id: string) => {
    try {
      await fetch(`/api/v1/ui-repair/security/red-team/findings/${id}/remediate`, { method: 'POST' });
      message.success('Remediation workflow triggered');
      await fetchFindings();
    } catch (err) {
      message.error('Remediation failed');
    }
  };

  const columns = [
    {
      title: 'Finding',
      dataIndex: 'finding_name',
      key: 'finding_name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (sev: string) => {
        let color = 'default';
        if (sev === 'CRITICAL') color = 'error';
        if (sev === 'HIGH') color = 'warning';
        return <Tag color={color}>{sev}</Tag>;
      }
    },
    {
      title: 'Domain',
      dataIndex: 'affected_domain',
      key: 'affected_domain',
      render: (domain: string) => <Tag color="blue">{domain}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'is_remediated',
      key: 'is_remediated',
      render: (rem: boolean) => rem ? 
        <Badge status="success" text="Remediated" /> : 
        <Badge status="warning" text="Pending" />,
    },
    {
      title: 'Detected',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      align: 'right' as const,
      render: (_: any, record: Finding) => (
        <Space>
          {!record.is_remediated && (
            <Button 
              type="primary" 
              size="small" 
              icon={<Hammer size={14} />} 
              onClick={() => triggerRemediation(record.id)}
            >
              Fix
            </Button>
          )}
          <Button type="text" icon={<ExternalLink size={16} />} />
        </Space>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Text strong>Vulnerabilities & Policy Bypasses</Text>
      </div>
      <Table 
        dataSource={findings} 
        columns={columns} 
        rowKey="id" 
        size="small"
        loading={loading}
        className="custom-table"
      />
    </div>
  );
};

export default RedTeamFindingsPanel;
