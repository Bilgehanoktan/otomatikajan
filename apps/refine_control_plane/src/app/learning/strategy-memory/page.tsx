"use client";

import React from "react";
import { List, useTable } from "@refinedev/antd";
import { Table, Tag, Space, Typography, Card, Statistic, Row, Col, Progress, Tooltip } from "antd";
import { 
  RocketOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  DollarOutlined,
  SafetyOutlined,
  AimOutlined
} from "@ant-design/icons";

const { Text } = Typography;

export default function StrategyMemoryList() {
  const { tableProps } = useTable({
    resource: "learning/strategy-memory",
    initialSorter: [
      {
        field: "trust_score",
        order: "desc",
      },
    ],
  });

  return (
    <div className="p-6">
      <Row gutter={[16, 16]} className="mb-6">
        <Col span={8}>
          <Card className="bg-[#1a1c22] border-[#30363d]">
            <Statistic
              title={<span className="text-gray-400">Aktif Stratejiler</span>}
              value={tableProps.dataSource?.length || 0}
              prefix={<RocketOutlined className="text-[#66fcf1]" />}
              valueStyle={{ color: "#66fcf1" }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="bg-[#1a1c22] border-[#30363d]">
            <Statistic
              title={<span className="text-gray-400">Ortalama Başarı</span>}
              value={
                tableProps.dataSource?.length 
                  ? (tableProps.dataSource.reduce((acc: number, cur: any) => acc + (cur.success_count || 0), 0) / 
                     tableProps.dataSource.reduce((acc: number, cur: any) => acc + (cur.success_count + cur.failure_count || 1), 0) * 100).toFixed(1)
                  : 0
              }
              suffix="%"
              prefix={<CheckCircleOutlined className="text-green-400" />}
              valueStyle={{ color: "#4ade80" }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="bg-[#1a1c22] border-[#30363d]">
            <Statistic
              title={<span className="text-gray-400">Promosyon Bekleyen</span>}
              value={tableProps.dataSource?.filter((i: any) => i.state === "candidate").length || 0}
              prefix={<AimOutlined className="text-yellow-400" />}
              valueStyle={{ color: "#fbbf24" }}
            />
          </Card>
        </Col>
      </Row>

      <List
        title={
          <div className="flex items-center gap-2">
            <RocketOutlined className="text-[#66fcf1]" />
            <span className="text-[#66fcf1] font-bold">Strateji Belleği — Karar Optimizasyonu</span>
          </div>
        }
      >
        <Table {...tableProps} rowKey="id" className="custom-table">
          <Table.Column
            dataIndex="strategy_name"
            title="Strateji"
            render={(value) => (
              <div className="flex flex-col">
                <Text className="text-[#66fcf1] font-bold">{value}</Text>
                <Text className="text-gray-500 text-[10px]">Autonmous Recovery Unit</Text>
              </div>
            )}
          />
          <Table.Column
            dataIndex="state"
            title="Durum"
            render={(value) => {
              const states: any = {
                promoted: { color: "green", label: "PROMOTED" },
                trusted: { color: "cyan", label: "TRUSTED" },
                candidate: { color: "gold", label: "CANDIDATE" },
                observed: { color: "blue", label: "OBSERVED" },
                deprecated: { color: "red", label: "DEPRECATED" },
              };
              const s = states[value] || { color: "default", label: value?.toUpperCase() };
              return <Tag color={s.color}>{s.label}</Tag>;
            }}
          />
          <Table.Column
            dataIndex="trust_score"
            title="Güven Skoru"
            sorter
            render={(value) => (
              <Tooltip title={`Sistem Güven Endeksi: ${(value * 100).toFixed(1)}%`}>
                <Progress 
                  percent={Math.round(value * 100)} 
                  size="small" 
                  strokeColor={{
                    '0%': '#f87171',
                    '100%': '#66fcf1',
                  }}
                  trailColor="#1a1c22"
                />
              </Tooltip>
            )}
          />
          <Table.Column
            title="Performans (B/H/G)"
            render={(_, record: any) => (
              <Space split={<Text className="text-gray-700">|</Text>}>
                <Tooltip title="Başarılı">
                  <Text className="text-green-400 font-mono">{record.success_count}</Text>
                </Tooltip>
                <Tooltip title="Hatalı">
                  <Text className="text-red-400 font-mono">{record.failure_count}</Text>
                </Tooltip>
                <Tooltip title="Geri Alınan">
                  <Text className="text-orange-400 font-mono">{record.rollback_count}</Text>
                </Tooltip>
              </Space>
            )}
          />
          <Table.Column
            dataIndex="avg_repair_latency"
            title="Ort. Gecikme"
            render={(value) => <Text className="text-gray-400">{value?.toFixed(2)}s</Text>}
          />
          <Table.Column
            dataIndex="avg_cost_usd"
            title="Ort. Maliyet"
            render={(value) => (
              <Space className="text-gray-400">
                <DollarOutlined />
                <Text>{value?.toFixed(2)}</Text>
              </Space>
            )}
          />
        </Table>
      </List>

      <style jsx global>{`
        .custom-table .ant-table {
          background: #1a1c22 !important;
          color: #c5c6c7 !important;
        }
        .custom-table .ant-table-thead > tr > th {
          background: #23272e !important;
          color: #66fcf1 !important;
          border-bottom: 1px solid #30363d !important;
        }
        .custom-table .ant-table-tbody > tr > td {
          border-bottom: 1px solid #23272e !important;
        }
        .custom-table .ant-table-tbody > tr:hover > td {
          background: #23272e !important;
        }
      `}</style>
    </div>
  );
}
