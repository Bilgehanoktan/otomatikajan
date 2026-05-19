import React, { useState, useEffect } from 'react';
import { 
  Row, Col, Card, Typography, Tag, Space, 
  List, Avatar, Badge, Button, Spin, Divider
} from 'antd';
import { 
  Binary, Shield, Target, Activity, 
  Layers, Lock, Database, Globe, Zap, Fingerprint
} from 'lucide-react';
import { safeFetchJson } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

const DefensivePatternPanel: React.FC = () => {
  const [patterns, setPatterns] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchPatterns = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson<any[]>('/api/v1/ui-repair/defense/patterns');
      setPatterns(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatterns();
  }, []);

  const getDomainIcon = (domain: string) => {
    const icons: any = {
      TENANT_ISOLATION: <Layers size={18} className="text-blue-400" />,
      IDENTITY: <Fingerprint size={18} className="text-purple-400" />,
      POLICY_AS_CODE: <Shield size={18} className="text-emerald-400" />,
      TOOL_GOVERNANCE: <Zap size={18} className="text-amber-400" />,
      COGNITIVE_INTEGRITY: <Activity size={18} className="text-rose-400" />,
    };
    return icons[domain] || <Shield size={18} />;
  };

  if (loading) return <div className="flex justify-center p-12"><Spin tip="Synthesizing patterns..." /></div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <Title level={4}>Synthesized Defensive Patterns</Title>
        <Text type="secondary">{patterns.length} Active Patterns</Text>
      </div>

      <Row gutter={[16, 16]}>
        {patterns.map((pattern) => (
          <Col xs={24} lg={12} key={pattern.id}>
            <Card 
              className="bg-slate-900/50 border-slate-800 hover:border-slate-700 transition-all"
              title={
                <Space>
                  {getDomainIcon(pattern.affected_domain)}
                  <Text strong className="text-slate-200">{pattern.pattern_key}</Text>
                  <Tag color="blue">{pattern.pattern_type}</Tag>
                </Space>
              }
              extra={<Badge status={pattern.status === 'ACTIVE' ? 'success' : 'processing'} text={<Text type="secondary">{pattern.status}</Text>} />}
            >
              <div className="space-y-4">
                <Paragraph className="text-slate-400 text-sm italic">
                  "{pattern.description}"
                </Paragraph>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950 p-3 rounded border border-slate-800">
                    <Text type="secondary" className="block mb-2 text-xs">Detection Strategy</Text>
                    <code className="text-xs text-blue-300">
                      {JSON.stringify(pattern.detection_rule, null, 2)}
                    </code>
                  </div>
                  <div className="bg-slate-950 p-3 rounded border border-slate-800">
                    <Text type="secondary" className="block mb-2 text-xs">Mitigation Action</Text>
                    <code className="text-xs text-emerald-300">
                      {JSON.stringify(pattern.mitigation_rule, null, 2)}
                    </code>
                  </div>
                </div>

                <Divider className="!my-2 border-slate-800" />
                
                <div className="flex justify-between items-center">
                  <Space>
                    <Text type="secondary" className="text-xs">Confidence Score:</Text>
                    <Badge count={`${(pattern.confidence * 100).toFixed(0)}%`} style={{ backgroundColor: pattern.confidence > 0.8 ? '#10b981' : '#3b82f6' }} />
                  </Space>
                  <Button size="small" type="link">View Source Finding</Button>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {patterns.length === 0 && (
        <Card className="text-center py-12 bg-slate-900/20 border-dashed border-slate-800">
          <Binary size={48} className="mx-auto mb-4 text-slate-700" />
          <Title level={5} type="secondary">No Defensive Patterns Synthesized Yet</Title>
          <Text type="secondary">Patterns will appear here once the optimization engine analyzes adversarial findings.</Text>
        </Card>
      )}
    </div>
  );
};

export default DefensivePatternPanel;
