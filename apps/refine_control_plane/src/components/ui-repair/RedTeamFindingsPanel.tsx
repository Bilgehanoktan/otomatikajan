'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, Tag, Typography, Button, Space, message, Badge 
} from 'antd';
import { ShieldAlert, ExternalLink, Hammer, CheckCircle } from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

const { Text } = Typography;

interface Finding {
  id: string;
  finding_type: string;
  severity: string;
  description: string;
  affected_domain: string;
  feasible: boolean;
  remediation_plan_id: string | null;
  created_at: string;
  resolved_at: string | null;
}

const RedTeamFindingsPanel: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchFindings = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson<Finding[]>('/api/v1/ui-repair/security/red-team/findings');
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
      await safeFetchJson(`/api/v1/ui-repair/security/remediation/plan/${id}`, { method: 'POST' });
      message.success('Remediation workflow triggered');
      await fetchFindings();
    } catch (err) {
      message.error('Remediation failed');
    }
  };

  const columns = [
    {
      title: 'Finding',
      dataIndex: 'finding_type',
      key: 'finding_type',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Summary',
      dataIndex: 'description',
      key: 'description',
      render: (text: string) => <Text className="text-slate-300">{text}</Text>,
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
      dataIndex: 'resolved_at',
      key: 'resolved_at',
      render: (_: string | null, record: Finding) => {
        if (record.resolved_at) {
          return <Badge status="success" text="Resolved" />;
        }
        if (record.remediation_plan_id) {
          return <Badge status="processing" text="Plan Created" />;
        }
        return <Badge status="warning" text="Pending" />;
      },
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
          {!record.resolved_at && record.feasible && (
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
