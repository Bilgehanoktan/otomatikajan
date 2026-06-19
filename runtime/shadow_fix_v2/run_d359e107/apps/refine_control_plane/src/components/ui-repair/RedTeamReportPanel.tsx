'use client';

import React, { useState, useEffect } from 'react';
import { 
  Typography, Button, Space, message, Card, Empty 
} from 'antd';
import { FileText, Download, Send, FileBarChart } from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

const { Text, Paragraph } = Typography;

interface Report {
  id: string;
  report_name: string;
  total_scenarios: number;
  passed_scenarios: number;
  failed_scenarios: number;
  critical_findings: number;
  generated_at: string;
  executive_summary: string;
}

const RedTeamReportPanel: React.FC = () => {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson<Report | null>('/api/v1/ui-repair/security/red-team/report/latest');
      setReport(data);
    } catch (err) {
      message.error('Failed to fetch reports');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setLoading(true);
    try {
      const nextReport = await safeFetchJson<Report>('/api/v1/ui-repair/security/red-team/report/generate', { method: 'POST' });
      setReport(nextReport);
      message.success('Executive report generated');
    } catch (err) {
      message.error('Generation failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Text strong>Audit Reports</Text>
        <Button type="primary" size="small" icon={<FileBarChart size={14} />} onClick={generateReport} loading={loading}>
          New Report
        </Button>
      </div>

      {report ? (
        <Card 
          title={report.report_name}
          extra={
            <Space>
              <Button icon={<Download size={16} />}>Export PDF</Button>
              <Button type="primary" icon={<Send size={16} />}>Distribute</Button>
            </Space>
          }
          className="bg-slate-900/50 border-slate-800"
        >
          <div className="mb-4 flex items-center gap-2 text-xs text-slate-500">
            <FileText size={16} />
            <span>{new Date(report.generated_at).toLocaleString()}</span>
          </div>

          <div className="grid grid-cols-4 gap-4 mb-6">
            <Card size="small" className="bg-slate-800/50 border-slate-700">
              <Statistic title="Passed" value={report.passed_scenarios} valueStyle={{ color: '#52c41a' }} />
            </Card>
            <Card size="small" className="bg-slate-800/50 border-slate-700">
              <Statistic title="Failed" value={report.failed_scenarios} valueStyle={{ color: '#f5222d' }} />
            </Card>
            <Card size="small" className="bg-slate-800/50 border-slate-700">
              <Statistic title="Critical" value={report.critical_findings} valueStyle={{ color: '#f5222d' }} />
            </Card>
            <Card size="small" className="bg-slate-800/50 border-slate-700">
              <Statistic title="Accuracy" value={((report.passed_scenarios / Math.max(report.total_scenarios, 1)) * 100).toFixed(1)} suffix="%" />
            </Card>
          </div>

          <Divider orientation="left">Executive Summary</Divider>
          <Paragraph className="text-slate-300 whitespace-pre-wrap leading-relaxed">
            {report.executive_summary}
          </Paragraph>
        </Card>
      ) : (
        <div className="flex items-center justify-center h-full bg-slate-900/30 rounded border border-dashed border-slate-800 py-16">
          <Empty description="No report generated yet" />
        </div>
      )}
    </div>
  );
};

// Internal Statistic helper for cleaner code
const Statistic: React.FC<{title: string, value: any, valueStyle?: React.CSSProperties, suffix?: string}> = ({title, value, valueStyle, suffix}) => (
  <div>
    <Text type="secondary" className="text-xs">{title}</Text>
    <div style={{ fontSize: '18px', fontWeight: 'bold', ...valueStyle }}>
      {value}{suffix}
    </div>
  </div>
);

const Divider: React.FC<{orientation?: "left" | "right" | "center", children: React.ReactNode}> = ({orientation, children}) => (
  <div className="flex items-center my-4">
    {orientation === "left" && <div className="pr-4"><Text strong>{children}</Text></div>}
    <div className="flex-grow border-t border-slate-800"></div>
    {orientation === "center" && <div className="px-4"><Text strong>{children}</Text></div>}
    {orientation === "right" && <div className="pl-4"><Text strong>{children}</Text></div>}
  </div>
);

export default RedTeamReportPanel;
