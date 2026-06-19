'use client';

import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, Space, Modal, Form, Input, Select, Switch, message } from 'antd';
import { PlusOutlined, EditOutlined, PauseCircleOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useTranslations } from 'next-intl';
import { safeFetchJson } from '@/lib/api';

const ProjectProfilePanel: React.FC = () => {
  const t = useTranslations('repair_lab.enterprise_rollout.projects');
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = await safeFetchJson('/api/v1/ui-repair/projects');
      setProjects(data);
    } catch (err) {
      message.error('Failed to fetch projects');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      await safeFetchJson('/api/v1/ui-repair/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      message.success('Project created successfully');
      setIsModalVisible(false);
      form.resetFields();
      fetchProjects();
    } catch (err) {
      message.error('Failed to create project');
    }
  };

  const toggleStatus = async (key: string, currentStatus: string) => {
    const action = currentStatus === 'ACTIVE' ? 'pause' : 'activate';
    try {
      await safeFetchJson(`/api/v1/ui-repair/projects/${key}/${action}`, { method: 'POST' });
      message.success(`Project ${action}d`);
      fetchProjects();
    } catch (err) {
      message.error(`Failed to ${action} project`);
    }
  };

  const columns = [
    { title: t('table.name'), dataIndex: 'project_name', key: 'name' },
    { title: t('table.key'), dataIndex: 'project_key', key: 'key' },
    { title: t('table.env'), dataIndex: 'environment', key: 'env' },
    { 
      title: t('table.status'), 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'ACTIVE' ? 'green' : status === 'PILOT' ? 'blue' : 'orange'}>
          {status}
        </Tag>
      )
    },
    {
      title: t('table.auto_repair'),
      dataIndex: 'auto_repair_enabled',
      key: 'auto_repair',
      render: (enabled: boolean) => (enabled ? <Tag color="cyan">ON</Tag> : <Tag color="default">OFF</Tag>)
    },
    {
      title: t('table.actions'),
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          <Button 
            size="small" 
            icon={record.status === 'ACTIVE' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => toggleStatus(record.project_key, record.status)}
          >
            {record.status === 'ACTIVE' ? t('actions.pause') : t('actions.activate')}
          </Button>
          <Button size="small" icon={<EditOutlined />}>{t('actions.edit')}</Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
          {t('actions.new_project')}
        </Button>
      </div>

      <Table columns={columns} dataSource={projects} rowKey="id" loading={loading} />

      <Modal
        title={t('modal.title')}
        open={isModalVisible}
        forceRender={true}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="project_name" label={t('modal.name')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="project_key" label={t('modal.key')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="environment" label={t('modal.env')} initialValue="PRODUCTION">
            <Select>
              <Select.Option value="PRODUCTION">Production</Select.Option>
              <Select.Option value="STAGING">Staging</Select.Option>
              <Select.Option value="DEVELOPMENT">Development</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="owner" label={t('modal.owner')}>
            <Input />
          </Form.Item>
          <Form.Item name="auto_repair_enabled" label={t('modal.auto_repair')} valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProjectProfilePanel;
