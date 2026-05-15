'use client';

import React, { useState, useEffect } from 'react';
import { Card, Button, Typography, message, Skeleton, Result, Tag, Space, Divider } from 'antd';
import { BookOutlined, SyncOutlined, DownloadOutlined, FileTextOutlined } from '@ant-design/icons';
import { useTranslations } from 'next-intl';
import ReactMarkdown from 'react-markdown';

const { Title, Text, Paragraph } = Typography;

const EnterpriseRunbookPanel: React.FC = () => {
  const t = useTranslations('repair_lab.enterprise_rollout.runbook');
  const [runbook, setRunbook] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLatest();
  }, []);

  const fetchLatest = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/ui-repair/enterprise/runbook/latest');
      const data = await res.json();
      setRunbook(data);
    } catch (err) {
      message.error('Failed to fetch runbook');
    } finally {
      setLoading(false);
    }
  };

  const generateRunbook = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/ui-repair/enterprise/runbook/generate?title=Egemen YAZ Enterprise Runbook&version=1.0.0', { method: 'POST' });
      const data = await res.json();
      setRunbook(data);
      message.success('Runbook generated');
    } catch (err) {
      message.error('Failed to generate runbook');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
        <Button icon={<SyncOutlined />} onClick={generateRunbook} loading={loading}>
          {t('actions.regenerate')}
        </Button>
        <Button type="primary" icon={<DownloadOutlined />} disabled={!runbook}>
          {t('actions.download_pdf')}
        </Button>
      </div>

      {!runbook ? (
        <Result
          icon={<BookOutlined />}
          title={t('no_runbook')}
          subTitle={t('no_runbook_sub')}
          extra={<Button type="primary" onClick={generateRunbook}>{t('actions.generate')}</Button>}
        />
      ) : (
        <Card bordered={false} className="runbook-viewer">
          <div style={{ marginBottom: '24px' }}>
            <Title level={2}>{runbook.title}</Title>
            <Space split={<Divider type="vertical" />}>
              <Text type="secondary">Version: {runbook.version}</Text>
              <Text type="secondary">Generated: {new Date(runbook.generated_at).toLocaleString()}</Text>
              <Tag color="blue">{runbook.scope}</Tag>
              <Tooltip title={runbook.evidence_hash}>
                <Tag icon={<FileTextOutlined />}>Verified Hash</Tag>
              </Tooltip>
            </Space>
          </div>
          <Divider />
          <div className="markdown-content">
            <ReactMarkdown>{runbook.content}</ReactMarkdown>
          </div>
        </Card>
      )}
    </div>
  );
};

export default EnterpriseRunbookPanel;
