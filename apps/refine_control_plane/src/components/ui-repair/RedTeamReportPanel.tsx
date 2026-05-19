'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, Typography, Button, Space, message, Card, List, Tag, Empty 
} from 'antd';
import { FileText, Download, Eye, Send, FileBarChart } from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

const { Text, Title, Paragraph } = Typography;

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
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson<Report[]>('/api/v1/ui-repair/security/red-team/reports');
      setReports(data);
    } catch (err) {
      message.error('Failed to fetch reports');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setLoading(true);
    try {
      await safeFetchJson('/api/v1/ui-repair/security/red-team/reports/generate', { method: 'POST' });
      message.success('Executive report generated');
      await fetchReports();
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
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-1 space-y-4">
        <div className="flex justify-between items-center">
          <Text strong>Audit Reports</Text>
          <Button type="primary" size="small" icon={<FileBarChart size={14} />} onClick={generateReport}>
            New Report
          </Button>
        </div>
        
        <List
          loading={loading}
          dataSource={reports}
          renderItem={(item) => (
            <List.Item 
              className={`cursor-pointer hover:bg-slate-800/30 p-3 rounded transition-colors ${selectedReport?.id === item.id ? 'bg-slate-800/50 border border-emerald-500/30' : ''}`}
              onClick={() => setSelectedReport(item)}
            >
              <List.Item.Meta
                avatar={<FileText size={24} className="text-slate-400" />}
                title={item.report_name}
                description={new Date(item.generated_at).toLocaleDateString()}
              />
            </List.Item>
          )}
        />
      </div>

      <div className="lg:col-span-2">
        {selectedReport ? (
          <Card 
            title={selectedReport.report_name}
            extra={
              <Space>
                <Button icon={<Download size={16} />}>Export PDF</Button>
                <Button type="primary" icon={<Send size={16} />}>Distribute</Button>
              </Space>
            }
            className="bg-slate-900/50 border-slate-800 h-full"
          >
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Card size="small" className="bg-slate-800/50 border-slate-700">
                <Statistic title="Passed" value={selectedReport.passed_scenarios} valueStyle={{ color: '#52c41a' }} />
              </Card>
              <Card size="small" className="bg-slate-800/50 border-slate-700">
                <Statistic title="Failed" value={selectedReport.failed_scenarios} valueStyle={{ color: '#f5222d' }} />
              </Card>
              <Card size="small" className="bg-slate-800/50 border-slate-700">
                <Statistic title="Critical" value={selectedReport.critical_findings} valueStyle={{ color: '#f5222d' }} />
              </Card>
              <Card size="small" className="bg-slate-800/50 border-slate-700">
                <Statistic title="Accuracy" value={((selectedReport.passed_scenarios / selectedReport.total_scenarios) * 100).toFixed(1)} suffix="%" />
              </Card>
            </div>

            <Divider orientation="left">Executive Summary</Divider>
            <Paragraph className="text-slate-300 whitespace-pre-wrap leading-relaxed">
              {selectedReport.executive_summary}
            </Paragraph>
          </Card>
        ) : (
          <div className="flex items-center justify-center h-full bg-slate-900/30 rounded border border-dashed border-slate-800">
            <Empty description="Select a report to view details" />
          </div>
        )}
      </div>
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
