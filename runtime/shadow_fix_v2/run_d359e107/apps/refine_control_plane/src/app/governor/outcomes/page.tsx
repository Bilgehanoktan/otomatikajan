"use client";

import React from "react";
import { useTable } from "@refinedev/antd";
import { Card, Table, Tag, Typography, Space } from "antd";
import { BarChartOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;

export default function GovernorOutcomesPage() {
  const { tableProps } = useTable({
    resource: "governance/governor/outcomes",
    syncWithLocation: true,
    pagination: {
      pageSize: 20,
    },
    sorters: {
      initial: [{ field: "created_at", order: "desc" }],
    },
  }) as any;

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size={20} style={{ width: "100%" }}>
        <div>
          <Title level={2} style={{ marginBottom: 0 }}>
            <BarChartOutlined style={{ marginRight: 12, color: "#66fcf1" }} />
            Governor Outcomes
          </Title>
          <Text type="secondary">
            Son governor kararlarının gerçek sonuçları ve kalite dağılımı.
          </Text>
        </div>

        <Card variant="borderless" style={{ borderRadius: 12, background: "#1f2833" }}>
          <Table {...tableProps} rowKey="id" pagination={{ ...tableProps.pagination, showSizeChanger: true }}>
            <Table.Column dataIndex="decision" title="Karar" render={(value) => <Tag color="blue">{value}</Tag>} />
            <Table.Column
              dataIndex="final_outcome"
              title="Sonuç"
              render={(value: string) => {
                const color =
                  value === "SUCCESS" || value === "IMPROVEMENT"
                    ? "green"
                    : value === "FAILURE" || value === "REGRESSION"
                      ? "red"
                      : "orange";
                return <Tag color={color}>{value}</Tag>;
              }}
            />
            <Table.Column
              dataIndex="quality"
              title="Kalite"
              render={(value: string) => {
                const color = value === "OPTIMAL" ? "success" : value === "SUBOPTIMAL" ? "warning" : "error";
                return <Tag color={color}>{value}</Tag>;
              }}
            />
            <Table.Column dataIndex="resolution_latency_seconds" title="Gecikme (sn)" />
            <Table.Column
              dataIndex="created_at"
              title="Tarih"
              render={(value: string) => new Date(value).toLocaleString("tr-TR")}
            />
          </Table>
        </Card>
      </Space>
    </div>
  );
}
