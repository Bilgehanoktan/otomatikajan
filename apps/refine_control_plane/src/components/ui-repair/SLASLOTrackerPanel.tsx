'use client';

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Progress, message, List, Typography } from 'antd';
import { useTranslations } from 'next-intl';
import { safeFetchJson } from '@/lib/api';

const { Title, Text } = Typography;

const SLASLOTrackerPanel: React.FC = () => {
  const t = useTranslations('repair_lab.enterprise_rollout.sla_slo');
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson('/api/v1/ui-repair/enterprise/sla-slo');
      setMetrics(data);
    } catch (err) {
      message.error('Failed to fetch SLA/SLO metrics');
    } finally {
      setLoading(false);
    }
  };

  const sloList = [
    { name: t('slo.uptime'), value: metrics?.monitoring_uptime, target: 99.0 },
    { name: t('slo.coverage'), value: metrics?.critical_route_coverage, target: 100.0 },
    { name: t('slo.compliance'), value: metrics?.rollback_snapshot_compliance, target: 100.0 },
    { name: t('slo.notifications'), value: metrics?.notification_success_rate, target: 95.0 },
  ];

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card bordered={false} size="small">
            <Statistic title={t('stats.mt_detect')} value={metrics?.mean_time_to_detect_s} suffix="s" />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} size="small">
            <Statistic title={t('stats.mt_diagnose')} value={metrics?.mean_time_to_diagnose_s} suffix="s" />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} size="small">
            <Statistic title={t('stats.mt_pr')} value={metrics?.mean_time_to_pr_s} suffix="s" />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} size="small">
            <Statistic title={t('stats.fp_rate')} value={metrics?.false_positive_rate * 100} precision={2} suffix="%" />
          </Card>
        </Col>
      </Row>

      <Title level={4}>{t('slo_compliance')}</Title>
      <List
        grid={{ gutter: 16, column: 2 }}
        dataSource={sloList}
        renderItem={item => (
          <List.Item>
            <Card title={item.name} size="small">
              <Row align="middle">
                <Col span={18}>
                  <Progress 
                    percent={item.value} 
                    status={item.value >= item.target ? 'success' : 'exception'}
                    strokeColor={item.value >= item.target ? '#52c41a' : '#f5222d'}
                  />
                </Col>
                <Col span={6} style={{ textAlign: 'right' }}>
                  <Text type="secondary">Target: {item.target}%</Text>
                </Col>
              </Row>
            </Card>
          </List.Item>
        )}
      />
    </div>
  );
};

export default SLASLOTrackerPanel;
