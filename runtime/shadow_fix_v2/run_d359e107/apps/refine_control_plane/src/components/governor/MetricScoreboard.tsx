import React from "react";
import { Card, Row, Col, Statistic, Tag, Typography } from "antd";
import { ArrowUpOutlined, ArrowDownOutlined, DashboardOutlined } from "@ant-design/icons";

const { Text } = Typography;

interface MetricItem {
  metric_key: string;
  value: number;
  baseline_value?: number;
  delta_value?: number;
  domain?: string;
}

interface Props {
  metrics: MetricItem[];
  loading?: boolean;
}

export const MetricScoreboard: React.FC<Props> = ({ metrics, loading }) => {
  const getTrendColor = (key: string, delta: number) => {
    if (delta === 0) return "gray";
    
    // Bazı metriklerde artış iyidir (accuracy), bazılarında kötüdür (latency, conflict)
    const positiveIsGood = ["decision_accuracy", "replay_success_rate"].includes(key);
    
    if (delta > 0) return positiveIsGood ? "green" : "red";
    return positiveIsGood ? "red" : "green";
  };

  const formatMetricName = (key: string) => {
    return key.replace(/_/g, " ").toUpperCase();
  };

  const formatValue = (key: string, val: number) => {
    if (key.includes("rate") || key.includes("accuracy")) {
      return `${(val * 100).toFixed(1)}%`;
    }
    if (key.includes("latency")) {
      return `${val.toFixed(0)}ms`;
    }
    return val.toFixed(2);
  };

  return (
    <div style={{ padding: "16px 0" }}>
      <Row gutter={[16, 16]}>
        {metrics.map((m) => {
          const color = m.delta_value ? getTrendColor(m.metric_key, m.delta_value) : "blue";
          const Icon = m.delta_value && m.delta_value > 0 ? ArrowUpOutlined : ArrowDownOutlined;

          return (
            <Col key={m.metric_key} xs={24} sm={12} md={8} lg={6}>
              <Card 
                size="small" 
                hoverable
                style={{ borderRadius: "8px", borderLeft: `4px solid ${color}` }}
              >
                <Statistic
                  title={
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <Text strong style={{ fontSize: "12px", color: "#8c8c8c" }}>{formatMetricName(m.metric_key)}</Text>
                      {m.domain && <Tag>{m.domain}</Tag>}
                    </div>
                  }
                  value={formatValue(m.metric_key, m.value)}
                  valueStyle={{ color: "#262626", fontWeight: "bold" }}
                  prefix={<DashboardOutlined style={{ fontSize: "16px", color: "#bfbfbf" }} />}
                  suffix={
                    m.delta_value ? (
                      <span style={{ fontSize: "14px", color }}>
                        <Icon /> {Math.abs(m.delta_value * (m.metric_key.includes("rate") ? 100 : 1)).toFixed(1)}
                      </span>
                    ) : null
                  }
                />
              </Card>
            </Col>
          );
        })}
      </Row>
    </div>
  );
};
