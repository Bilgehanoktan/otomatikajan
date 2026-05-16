'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, Typography, Row, Col, Button, Tabs, 
  Spin, Alert, Divider, Tag, Space, Statistic,
  Table, Modal, message, List, Progress
} from 'antd';
import { 
  ShieldCheck, Zap, Activity, Cpu, BarChart3, 
  RefreshCw, PlayCircle, CheckCircle2, AlertTriangle,
  History, Settings, ShieldAlert, Binary
} from 'lucide-react';
import TuningProposalPanel from './TuningProposalPanel';
import DefensivePatternPanel from './DefensivePatternPanel';
import DefenseReportPanel from './DefenseReportPanel';

const { Title, Text } = Typography;

interface ShieldOverview {
  total_proposals: number;
  active_canaries: number;
  security_lift: number;
  patterns_synthesized: number;
  compliance_status: string;
}

const AutonomousShieldCenterPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState('proposals');
  const [overview, setOverview] = useState<ShieldOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    try {
      // In a real app, this would be an aggregate endpoint
      // Mocking overview based on component state
      setOverview({
        total_proposals: 12,
        active_canaries: 3,
        security_lift: 18.5,
        patterns_synthesized: 8,
        compliance_status: 'HEALTHY'
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const triggerTuningCycle = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/ui-repair/defense/optimization/cycle', { method: 'POST' });
      if (res.ok) {
        message.success('Autonomous tuning cycle triggered successfully.');
        fetchOverview();
      } else {
        throw new Error('Failed to trigger tuning cycle');
      }
    } catch (err: any) {
      message.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const tabItems = [
    {
      key: 'proposals',
      label: <Space><Settings size={16} />Tuning Proposals</Space>,
      children: <TuningProposalPanel />
    },
    {
      key: 'patterns',
      label: <Space><Binary size={16} />Defensive Patterns</Space>,
      children: <DefensivePatternPanel />
    },
    {
      key: 'reports',
      label: <Space><BarChart3 size={16} />Optimization Reports</Space>,
      children: <DefenseReportPanel />
    }
  ];

  if (loading && !overview) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" tip="Initializing Autonomous Shield..." />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-700">
      <div className="flex justify-between items-center mb-8 relative">
        <div className="absolute -top-10 -left-10 w-40 h-40 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="relative z-10">
          <Title level={2} className="flex items-center gap-3 !mb-1 !text-white tracking-tight">
            <div className="p-2 bg-emerald-500/10 rounded-xl border border-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
              <ShieldCheck className="text-emerald-400 w-8 h-8" />
            </div>
            Autonomous Shield
          </Title>
          <Text className="text-slate-400 font-medium">Continuous Guardrail Tuning & Defensive Pattern Synthesis</Text>
        </div>
        <Space className="relative z-10">
          <Button 
            icon={<RefreshCw size={16} />} 
            onClick={fetchOverview}
            className="bg-slate-900/80 border-slate-700 text-slate-300 hover:text-white"
          >
            Refresh
          </Button>
          <Button 
            type="primary" 
            icon={<Zap size={16} />} 
            onClick={triggerTuningCycle}
            loading={loading}
            className="bg-gradient-to-r from-emerald-600 to-teal-600 border-none hover:from-emerald-500 hover:to-teal-500 shadow-[0_0_20px_rgba(16,185,129,0.2)] font-bold px-6 h-10 rounded-lg"
          >
            Trigger Tuning Cycle
          </Button>
        </Space>
      </div>

      {error && <Alert message={error} type="error" showIcon closable className="mb-6 rounded-xl border-rose-500/20 bg-rose-500/5" />}

      <Row gutter={[20, 20]} className="mb-8">
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/40 backdrop-blur-md border border-slate-800/50 rounded-2xl hover:border-blue-500/30 transition-all duration-300 shadow-xl group">
            <Statistic 
              title={<Text className="text-slate-500 text-xs font-black uppercase tracking-widest">Tuning Proposals</Text>} 
              value={overview?.total_proposals} 
              valueStyle={{ color: '#fff', fontWeight: '900', fontSize: '2rem' }}
              prefix={<div className="p-2 bg-blue-500/10 rounded-lg mr-3 group-hover:scale-110 transition-transform"><Settings className="text-blue-400" size={20} /></div>}
            />
            <div className="mt-2 text-[10px] text-blue-400 font-bold">+2 from last cycle</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/40 backdrop-blur-md border border-slate-800/50 rounded-2xl hover:border-amber-500/30 transition-all duration-300 shadow-xl group">
            <Statistic 
              title={<Text className="text-slate-500 text-xs font-black uppercase tracking-widest">Active Canaries</Text>} 
              value={overview?.active_canaries} 
              valueStyle={{ color: '#f59e0b', fontWeight: '900', fontSize: '2rem' }}
              prefix={<div className="p-2 bg-amber-500/10 rounded-lg mr-3 group-hover:scale-110 transition-transform"><Activity className="text-amber-400" size={20} /></div>}
            />
            <div className="mt-2 text-[10px] text-amber-400 font-bold">In progress</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/40 backdrop-blur-md border border-slate-800/50 rounded-2xl hover:border-emerald-500/30 transition-all duration-300 shadow-xl group">
            <Statistic 
              title={<Text className="text-slate-500 text-xs font-black uppercase tracking-widest">Security Lift</Text>} 
              value={overview?.security_lift} 
              suffix="%"
              valueStyle={{ color: '#10b981', fontWeight: '900', fontSize: '2rem' }}
              prefix={<div className="p-2 bg-emerald-500/10 rounded-lg mr-3 group-hover:scale-110 transition-transform"><Zap className="text-emerald-400" size={20} /></div>}
            />
            <div className="mt-2 text-[10px] text-emerald-400 font-bold">Target reached</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/40 backdrop-blur-md border border-slate-800/50 rounded-2xl hover:border-purple-500/30 transition-all duration-300 shadow-xl group">
            <Statistic 
              title={<Text className="text-slate-500 text-xs font-black uppercase tracking-widest">Patterns Synthesized</Text>} 
              value={overview?.patterns_synthesized} 
              valueStyle={{ color: '#8b5cf6', fontWeight: '900', fontSize: '2rem' }}
              prefix={<div className="p-2 bg-purple-500/10 rounded-lg mr-3 group-hover:scale-110 transition-transform"><Binary className="text-purple-400" size={20} /></div>}
            />
            <div className="mt-2 text-[10px] text-purple-400 font-bold">Reusable rules</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4.8}>
          <Card bordered={false} className="bg-slate-900/40 backdrop-blur-md border border-slate-800/50 rounded-2xl hover:border-emerald-500/30 transition-all duration-300 shadow-xl group">
            <Statistic 
              title={<Text className="text-slate-500 text-xs font-black uppercase tracking-widest">System Compliance</Text>} 
              value={overview?.compliance_status} 
              valueStyle={{ color: '#10b981', fontWeight: '900', fontSize: '1.2rem', marginTop: '8px' }}
              prefix={<div className="p-2 bg-emerald-500/10 rounded-lg mr-3 group-hover:scale-110 transition-transform"><ShieldCheck className="text-emerald-400" size={20} /></div>}
            />
            <div className="mt-2 text-[10px] text-slate-500 font-bold italic">ISO/IEC 42001 Aligned</div>
          </Card>
        </Col>
      </Row>

      <Card className="bg-slate-950/40 backdrop-blur-xl border border-slate-800 shadow-2xl rounded-2xl overflow-hidden p-0">
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab} 
          items={tabItems}
          className="custom-shield-tabs"
        />
      </Card>
    </div>
  );
};

export default AutonomousShieldCenterPanel;
