import React from "react";
import { Table, Tag, Button, Space, Tooltip, Typography } from "antd";
import { 
  BellOutlined, 
  CheckCircleOutlined, 
  EyeOutlined, 
  UserOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  StopOutlined
} from "@ant-design/icons";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

const { Text } = Typography;

export interface AlertRecord {
  id: string;
  alert_type: string;
  severity: string;
  status: string;
  domain?: string;
  title: string;
  metric_value?: number;
  threshold_value?: number;
  opened_at: string;
  owner_id?: string;
}

interface Props {
  alerts: AlertRecord[];
  loading?: boolean;
  onAck?: (id: string) => void;
  onInspect?: (id: string) => void;
}

export const AlertTable: React.FC<Props> = ({ alerts, loading, onAck, onInspect }) => {
  const getSeverityTag = (severity: string) => {
    const map: Record<string, { color: string; icon: any }> = {
      CRITICAL: { color: "red", icon: <StopOutlined /> },
      HIGH: { color: "orange", icon: <WarningOutlined /> },
      WARNING: { color: "gold", icon: <WarningOutlined /> },
      INFO: { color: "blue", icon: <InfoCircleOutlined /> },
    };
    const config = map[severity] || { color: "default", icon: <InfoCircleOutlined /> };
    return <Tag color={config.color} icon={config.icon}>{severity}</Tag>;
  };

  const getStatusTag = (status: string) => {
    const map: Record<string, string> = {
      OPEN: "error",
      ACKNOWLEDGED: "processing",
      RESOLVED: "success",
      SUPPRESSED: "default",
    };
    return <Tag color={map[status] || "default"}>{status}</Tag>;
  };

  const columns = [
    {
      title: "Severity",
      dataIndex: "severity",
      key: "severity",
      width: 120,
      render: (val: string) => getSeverityTag(val),
      sorter: (a: AlertRecord, b: AlertRecord) => a.severity.localeCompare(b.severity),
    },
    {
      title: "Alert Title",
      dataIndex: "title",
      key: "title",
      render: (val: string, record: AlertRecord) => (
        <Space direction="vertical" size={0}>
          <Text strong>{val}</Text>
          <Text type="secondary" style={{ fontSize: "12px" }}>{record.alert_type}</Text>
        </Space>
      ),
    },
    {
      title: "Domain",
      dataIndex: "domain",
      key: "domain",
      width: 100,
      render: (val?: string) => val ? <Tag>{val}</Tag> : "-",
    },
    {
      title: "Metric",
      key: "metric",
      width: 150,
      render: (_: any, record: AlertRecord) => (
        <Text>
          {record.metric_value?.toFixed(2)} 
          {record.threshold_value && (
            <Text type="secondary" style={{ marginLeft: "4px" }}>
              / {record.threshold_value.toFixed(2)}
            </Text>
          )}
        </Text>
      ),
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (val: string) => getStatusTag(val),
    },
    {
      title: "Opened",
      dataIndex: "opened_at",
      key: "opened_at",
      width: 150,
      render: (val: string) => dayjs(val).fromNow(),
      sorter: (a: AlertRecord, b: AlertRecord) => dayjs(a.opened_at).unix() - dayjs(b.opened_at).unix(),
    },
    {
      title: "Owner",
      dataIndex: "owner_id",
      key: "owner_id",
      width: 120,
      render: (val?: string) => val ? <Tag icon={<UserOutlined />}>{val}</Tag> : "-",
    },
    {
      title: "Actions",
      key: "actions",
      fixed: "right" as const,
      width: 150,
      render: (_: any, record: AlertRecord) => (
        <Space>
          {record.status === "OPEN" && (
            <Tooltip title="Acknowledge">
              <Button 
                size="small" 
                icon={<CheckCircleOutlined />} 
                onClick={() => onAck?.(record.id)}
              />
            </Tooltip>
          )}
          <Button 
            size="small" 
            type="primary" 
            icon={<EyeOutlined />} 
            onClick={() => onInspect?.(record.id)}
          >
            Inspect
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Table 
      dataSource={alerts} 
      columns={columns} 
      loading={loading} 
      rowKey="id" 
      size="small"
      pagination={{ pageSize: 10 }}
      scroll={{ x: 1000 }}
    />
  );
};
