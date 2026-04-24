"use client";

import React from "react";
import { List, useTable } from "@refinedev/antd";
import { Table, Tag, Typography, Card, Statistic, Row, Col, Space, Tooltip } from "antd";
import { 
  SafetyOutlined, 
  WarningOutlined, 
  GlobalOutlined,
  BlockOutlined,
  HistoryOutlined
} from "@ant-design/icons";

const { Text, Title } = Typography;

export default function NegativePatternsList() {
  const { tableProps } = useTable({
    resource: "learning/negative-patterns",
    initialSorter: [
      {
        field: "penalty_weight",
        order: "desc",
      },
    ],
  });

  return (
    <div className="p-6">
      <Row gutter={[16, 16]} className="mb-6">
        <Col span={12}>
          <Card className="bg-[#1a1c22] border-[#30363d]">
            <Statistic
              title={<span className="text-gray-400">Kayıtlı Negatif Kalıp</span>}
              value={tableProps.dataSource?.length || 0}
              prefix={<BlockOutlined className="text-red-400" />}
              valueStyle={{ color: "#f87171" }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card className="bg-[#1a1c22] border-[#30363d]">
            <Statistic
              title={<span className="text-gray-400">Önlenen Tekrarlı Hata</span>}
              value={tableProps.dataSource?.reduce((acc: number, cur: any) => acc + (cur.occurrence_count || 0), 0)}
              prefix={<SafetyOutlined className="text-[#66fcf1]" />}
              valueStyle={{ color: "#66fcf1" }}
            />
          </Card>
        </Col>
      </Row>

      <List
        title={
          <div className="flex items-center gap-2">
            <WarningOutlined className="text-red-500" />
            <span className="text-red-500 font-bold">Negatif Kalıplar — Kara Liste & Cezalandırma</span>
          </div>
        }
      >
        <Table {...tableProps} rowKey="id" className="custom-table">
          <Table.Column
            dataIndex="strategy_name"
            title="Strateji"
            render={(value) => <Text className="text-red-400 font-bold">{value}</Text>}
          />
          <Table.Column
            dataIndex="component"
            title="Bileşen"
            render={(value) => <Tag color="blue">{value}</Tag>}
          />
          <Table.Column
            dataIndex="failure_reason"
            title="Hata Sebebi"
            render={(value) => (
              <Text className="text-gray-400 text-xs" ellipsis={{ tooltip: value }}>
                {value}
              </Text>
            )}
          />
          <Table.Column
            dataIndex="penalty_weight"
            title="Ceza Ağırlığı"
            sorter
            render={(value) => (
              <div className="flex items-center gap-2">
                <Text className="text-red-500 font-mono font-bold">x{value?.toFixed(2)}</Text>
                <div className="h-1 w-20 bg-gray-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-red-600" 
                    style={{ width: `${Math.min(100, (value / 5) * 100)}%` }} 
                  />
                </div>
              </div>
            )}
          />
          <Table.Column
            dataIndex="occurrence_count"
            title="Tekrar"
            render={(value) => <Text className="text-gray-300">{value}</Text>}
          />
          <Table.Column
            dataIndex="blast_radius"
            title="Etki Çapı"
            render={(value) => (
              <Tag color={value === 'high' ? 'red' : 'orange'}>{value?.toUpperCase()}</Tag>
            )}
          />
          <Table.Column
            dataIndex="last_seen_at"
            title="Son Tespit"
            render={(value) => <Text className="text-gray-500 text-[10px]">{new Date(value).toLocaleString()}</Text>}
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
