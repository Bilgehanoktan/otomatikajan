"use client";

import React from "react";
import { List, useTable, TagField, DateField } from "@refinedev/antd";
import { Table, Tag, Space, Button, Typography, Card, Statistic, Row, Col } from "antd";
import { 
  BugOutlined, 
  HistoryOutlined, 
  SafetyCertificateOutlined,
  ThunderboltOutlined 
} from "@ant-design/icons";
import Link from "next/link";
import { useTranslations } from "next-intl";

const { Text, Title } = Typography;

export default function FingerprintList() {
  const t = useTranslations();
  const { tableProps } = useTable({
    resource: "learning/fingerprints",
    sorters: {
      initial: [
        {
          field: "recurrence_count",
          order: "desc",
        },
      ]
    },
  });

  return (
    <div className="p-6">
      <Row gutter={[16, 16]} className="mb-6">
        <Col span={6}>
          <Card className="bg-[#1a1c22] border-[#30363d]">
            <Statistic
              title={<span className="text-gray-400">{t("fingerprints.total")}</span>}
              value={tableProps.dataSource?.length || 0}
              prefix={<BugOutlined className="text-[#66fcf1]" />}
              valueStyle={{ color: "#66fcf1" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="bg-[#1a1c22] border-[#30363d]">
            <Statistic
              title={<span className="text-gray-400">{t("fingerprints.critical")}</span>}
              value={tableProps.dataSource?.filter((i: any) => i.severity === "critical").length || 0}
              prefix={<ThunderboltOutlined className="text-red-400" />}
              valueStyle={{ color: "#f87171" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="bg-[#1a1c22] border-[#30363d]">
            <Statistic
              title={<span className="text-gray-400">{t("fingerprints.lessons")}</span>}
              value={tableProps.dataSource?.reduce((acc: number, cur: any) => acc + (cur.recurrence_count || 0), 0)}
              prefix={<HistoryOutlined className="text-blue-400" />}
              valueStyle={{ color: "#60a5fa" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="bg-[#1a1c22] border-[#30363d]">
            <Statistic
              title={<span className="text-gray-400">{t("fingerprints.safetyScore")}</span>}
              value="94.2"
              suffix="%"
              prefix={<SafetyCertificateOutlined className="text-green-400" />}
              valueStyle={{ color: "#4ade80" }}
            />
          </Card>
        </Col>
      </Row>

      <List
        breadcrumb={
          <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-2">
            {t("dashboard.missionControl")} / {t("resources.learning")} / {t("fingerprints.title")}
          </div>
        }
        title={
          <div className="flex items-center gap-2">
            <BugOutlined className="text-[#66fcf1]" />
            <span className="text-[#66fcf1] font-bold">{t("fingerprints.title")}</span>
          </div>
        }
      >
        <Table {...tableProps} rowKey="id" className="custom-table">
          <Table.Column
            dataIndex="id"
            title="ID"
            render={(value) => <Text copyable className="text-gray-400 font-mono text-xs">{value.substring(0, 8)}</Text>}
          />
          <Table.Column
            dataIndex="error_family"
            title={t("fingerprints.family")}
            render={(value) => (
              <Tag color="magenta" className="border-none bg-magenta-900/30 text-magenta-400 uppercase font-bold text-[10px]">
                {value}
              </Tag>
            )}
          />
          <Table.Column
            dataIndex="normalized_message"
            title={t("fingerprints.signal")}
            render={(value) => (
              <Text className="text-gray-300 block max-w-[400px]" ellipsis={{ tooltip: value }}>
                {value}
              </Text>
            )}
          />
          <Table.Column
            dataIndex="severity"
            title={t("fingerprints.severity")}
            render={(value) => {
              const colors: any = { critical: "red", warning: "orange", info: "blue" };
              return <Tag color={colors[value] || "blue"}>{value?.toUpperCase()}</Tag>;
            }}
          />
          <Table.Column
            dataIndex="recurrence_count"
            title={t("fingerprints.recurrence")}
            sorter
            render={(value) => (
              <div className="flex items-center gap-2">
                <div className="h-2 w-16 bg-gray-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[#66fcf1]" 
                    style={{ width: `${Math.min(100, (value / 50) * 100)}%` }} 
                  />
                </div>
                <Text className="text-[#66fcf1] font-bold">{value}</Text>
              </div>
            )}
          />
          <Table.Column
            dataIndex="last_seen_at"
            title={t("fingerprints.lastSeen")}
            render={(value) => <DateField value={value} format="LLL" className="text-gray-400 text-xs" />}
          />
          <Table.Column
            title={t("fingerprints.actions")}
            dataIndex="id"
            render={(id) => (
              <Space>
                <Link href={`/learning/fingerprints/${id}`}>
                  <Button size="small" type="primary" ghost icon={<HistoryOutlined />}>
                    {t("fingerprints.analyze")}
                  </Button>
                </Link>
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
