'use client';

import React, { useState, useEffect } from 'react';
import { Card, Button, List, Tag, Typography, Progress, message, Space, Result } from 'antd';
import { CheckCircleOutlined, WarningOutlined, CloseCircleOutlined, SyncOutlined } from '@ant-design/icons';
import { useTranslations } from 'next-intl';
import { safeFetchJson } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

const GAReadinessPanel: React.FC = () => {
  const t = useTranslations('repair_lab.enterprise_rollout.ga_readiness');
  const [assessment, setAssessment] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLatest();
  }, []);

  const fetchLatest = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson('/api/v1/ui-repair/enterprise/ga-readiness/latest');
      setAssessment(data);
    } catch (err) {
      message.error('Failed to fetch GA readiness assessment');
    } finally {
      setLoading(false);
    }
  };

  const triggerCheck = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson('/api/v1/ui-repair/enterprise/ga-readiness/check?assessor=Admin', { method: 'POST' });
      setAssessment(data);
      message.success('Assessment completed');
    } catch (err) {
      message.error('Assessment failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'GA_READY': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'GA_WITH_WARNINGS': return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'NO_GO': return <CloseCircleOutlined style={{ color: '#f5222d' }} />;
      default: return <SyncOutlined spin />;
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'flex-end' }}>
        <Button icon={<SyncOutlined />} onClick={triggerCheck} loading={loading}>
          {t('actions.reassess')}
        </Button>
      </div>

      {!assessment ? (
        <Result
          status="info"
          title={t('no_assessment')}
          subTitle={t('no_assessment_sub')}
          extra={<Button type="primary" onClick={triggerCheck}>{t('actions.start_assessment')}</Button>}
        />
      ) : (
        <div>
          <Card bordered={false} style={{ marginBottom: '24px' }}>
            <div style={{ textAlign: 'center' }}>
              <Title level={2}>{getStatusIcon(assessment.recommendation)} {assessment.recommendation}</Title>
              <Progress 
                type="dashboard" 
                percent={assessment.readiness_score} 
                strokeColor={assessment.readiness_score > 80 ? '#52c41a' : '#faad14'} 
              />
              <Paragraph style={{ marginTop: '16px' }}>
                {t('projects_ready')}: {assessment.passed_projects} / {assessment.project_count}
              </Paragraph>
            </div>
          </Card>

          <Space direction="vertical" style={{ width: '100%' }}>
            <Card title={t('blockers')} size="small" headStyle={{ color: '#f5222d' }}>
              <List
                dataSource={assessment.blockers}
                renderItem={(item: string) => <List.Item><CloseCircleOutlined style={{ color: '#f5222d', marginRight: '8px' }} /> {item}</List.Item>}
              />
            </Card>
            <Card title={t('warnings')} size="small" headStyle={{ color: '#faad14' }}>
              <List
                dataSource={assessment.warnings}
                renderItem={(item: string) => <List.Item><WarningOutlined style={{ color: '#faad14', marginRight: '8px' }} /> {item}</List.Item>}
              />
            </Card>
          </Space>
        </div>
      )}
    </div>
  );
};

export default GAReadinessPanel;
