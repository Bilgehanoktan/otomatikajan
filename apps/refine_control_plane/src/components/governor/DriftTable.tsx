import React from "react";
import { Table, Tag, Progress, Space, Button, Typography } from "antd";
import { RadarChartOutlined, EyeOutlined, HistoryOutlined } from "@ant-design/icons";
import dayjs from "dayjs";

const { Text } = Typography;

export interface DriftRecord {
  id: string;
  drift_type: string;
  domain?: string;
  drift_score: number;
  baseline_window_days: number;
  current_window_days: number;
  summary: string;
  evidence_payload?: Record<string, unknown>;
  created_at: string;
}

interface Props {
  drifts: DriftRecord[];
  loading?: boolean;
  onInspect?: (id: string) => void;
}

export const DriftTable: React.FC<Props> = ({ drifts, loading, onInspect }) => {
  const getDriftScoreColor = (score: number) => {
    if (score > 0.5) return "#ff4d4f"; // Red
    if (score > 0.2) return "#faad14"; // Orange/Yellow
    return "#52c41a"; // Green
  };

  const columns = [
    {
      title: "Drift Type",
      dataIndex: "drift_type",
      key: "drift_type",
      render: (val: string) => (
        <Space>
          <RadarChartOutlined style={{ color: "#1890ff" }} />
          <Text strong>{val}</Text>
        </Space>
      ),
    },
    {
      title: "Domain",
      dataIndex: "domain",
      key: "domain",
      render: (val?: string) => val ? <Tag color="blue">{val}</Tag> : <Tag>META</Tag>,
    },
    {
      title: "Drift Score",
      dataIndex: "drift_score",
      key: "drift_score",
      width: 200,
      render: (val: number) => (
        <Space direction="vertical" style={{ width: "100%" }} size={0}>
          <Progress 
            percent={Math.min(100, val * 100)} 
            size="small" 
            strokeColor={getDriftScoreColor(val)}
            format={(p) => `${p?.toFixed(1)}%`}
          />
        </Space>
      ),
    },
    {
      title: "Baseline / Current",
      key: "window",
      render: (_: unknown, record: DriftRecord) => (
        <Space split={<Text type="secondary">/</Text>}>
          <Tag icon={<HistoryOutlined />}>{record.baseline_window_days}d</Tag>
          <Tag color="cyan">{record.current_window_days}d</Tag>
        </Space>
      ),
    },
    {
      title: "Summary",
      dataIndex: "summary",
      key: "summary",
      ellipsis: true,
      render: (val: string) => <Text type="secondary" style={{ fontSize: "12px" }}>{val}</Text>,
    },
    {
      title: "Detected",
      dataIndex: "created_at",
      key: "created_at",
      render: (val: string) => dayjs(val).format("YYYY-MM-DD HH:mm"),
    },
    {
      title: "Actions",
      key: "actions",
      width: 100,
      render: (_: unknown, record: DriftRecord) => (
        <Button 
          size="small" 
          icon={<EyeOutlined />} 
          onClick={() => onInspect?.(record.id)}
        >
          Inspect
        </Button>
      ),
    },
  ];

  return (
    <Table 
      dataSource={drifts} 
      columns={columns} 
      loading={loading} 
      rowKey="id" 
      size="small"
      pagination={{ pageSize: 5 }}
    />
  );
};
