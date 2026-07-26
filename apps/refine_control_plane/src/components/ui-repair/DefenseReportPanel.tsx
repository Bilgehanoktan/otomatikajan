import React, { useState, useEffect } from 'react';
import { 
  Card, Typography, Row, Col, Statistic, 
  Button, List, Divider, Space, Spin, Alert,
  Progress, Descriptions, Tag
} from 'antd';
import { 
  FileText, Download, TrendingUp, ShieldCheck, 
  Target, Zap, History, BarChart3, ChevronRight
} from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

const DefenseReportPanel: React.FC = () => {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson<any>('/api/v1/ui-repair/security/defense/report/latest');
      setReport(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson<any>('/api/v1/ui-repair/security/defense/report/generate', { method: 'POST' });
      setReport(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  if (loading && !report) return <div className="flex justify-center p-12"><Spin tip="Generating audit summary..." /></div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <Title level={4}>Executive Defense Optimization Reports</Title>
        <Space>
          <Button icon={<History size={16} />}>Archive</Button>
          <Button type="primary" icon={<BarChart3 size={16} />} onClick={generateReport}>Generate New Report</Button>
        </Space>
      </div>

      {!report ? (
        <Alert
          message="No reports generated yet"
          description="Trigger a manual generation or wait for the next scheduled optimization cycle."
          type="info"
          showIcon
        />
      ) : (
        <div className="space-y-6">
          <Card className="bg-slate-900/50 border-slate-800">
            <div className="flex justify-between items-start mb-6">
              <div>
                <Title level={3} className="!mb-0">{report.report_name}</Title>
                <Text type="secondary">Period: {new Date(report.period_start).toLocaleDateString()} - {new Date(report.period_end).toLocaleDateString()}</Text>
              </div>
              <Button icon={<Download size={16} />}>Download PDF</Button>
            </div>

            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Card size="small" className="bg-slate-800/50 border-slate-700">
                  <Statistic 
                    title="Total Proposals" 
                    value={report.total_proposals} 
                    valueStyle={{ color: '#fff' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small" className="bg-slate-800/50 border-slate-700">
                  <Statistic 
                    title="Optimization Success" 
                    value={(report.approved_proposals / (report.total_proposals || 1)) * 100} 
                    suffix="%" 
                    precision={1}
                    valueStyle={{ color: '#10b981' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small" className="bg-slate-800/50 border-slate-700">
                  <Statistic 
                    title="Security Lift" 
                    value={report.security_score_after - report.security_score_before} 
                    suffix="pts" 
                    prefix={<TrendingUp size={14} className="mr-1" />}
                    valueStyle={{ color: '#3b82f6' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small" className="bg-slate-800/50 border-slate-700">
                  <Statistic 
                    title="False Allow Delta" 
                    value={report.false_allow_delta} 
                    valueStyle={{ color: '#10b981' }}
                  />
                </Card>
              </Col>
            </Row>

            <Divider className="border-slate-800" />

            <div className="grid grid-cols-3 gap-8">
              <div className="col-span-2">
                <Title level={5} className="flex items-center gap-2">
                  <FileText size={18} className="text-blue-400" /> Executive Summary
                </Title>
                <div className="mt-4 prose prose-invert max-w-none prose-sm">
                  <div dangerouslySetInnerHTML={{ __html: report.executive_summary.replace(/\n/g, '<br/>') }} />
                </div>
              </div>
              <div>
                <Title level={5} className="flex items-center gap-2">
                  <ShieldCheck size={18} className="text-emerald-400" /> Security Posture Delta
                </Title>
                <div className="mt-4 space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <Text type="secondary" className="text-xs">Before</Text>
                      <Text strong className="text-xs">{report.security_score_before}%</Text>
                    </div>
                    <Progress percent={report.security_score_before} size="small" showInfo={false} strokeColor="#64748b" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <Text type="secondary" className="text-xs">After Optimization</Text>
                      <Text strong className="text-emerald-400 text-xs">{report.security_score_after}%</Text>
                    </div>
                    <Progress percent={report.security_score_after} size="small" showInfo={false} strokeColor="#10b981" />
                  </div>
                </div>

                <Divider className="border-slate-800" />

                <Title level={5} className="flex items-center gap-2">
                  <Target size={18} className="text-rose-400" /> Impact Analysis
                </Title>
                <List
                  size="small"
                  className="mt-2"
                  dataSource={[
                    { label: 'False Positives', val: report.false_block_delta, pos: false },
                    { label: 'False Negatives', val: report.false_allow_delta, pos: true },
                    { label: 'Detection Coverage', val: '+12%', pos: true },
                  ]}
                  renderItem={(item) => (
                    <List.Item className="!px-0 border-none">
                      <Space className="w-full justify-between">
                        <Text type="secondary" className="text-xs">{item.label}</Text>
                        <Tag color={item.pos ? 'emerald' : 'orange'} className="m-0 text-xs">
                          {item.val > 0 ? `+${item.val}` : item.val}
                        </Tag>
                      </Space>
                    </List.Item>
                  )}
                />
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default DefenseReportPanel;
