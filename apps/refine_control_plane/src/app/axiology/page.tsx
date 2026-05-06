"use client";

import React from "react";
import { List, useTable } from "@refinedev/antd";
import Link from "next/link";
import {
  Table,
  Tag,
  Space,
  Card,
  Statistic,
  Row,
  Col,
  Typography,
  Tooltip,
  Progress,
} from "antd";
import {
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  Info,
  Activity,
  Fingerprint,
  Eye,
  Scale,
} from "lucide-react";

const { Text, Title } = Typography;

type AxiologyRecord = {
  id: string;
  decision?: "approve" | "flag" | "reject" | string;
  context?: string;
  justification?: string;
  corrective_action?: string;
  created_at?: string;
  scores?: {
    Safety?: number;
    ResourceIntegrity?: number;
    OperationalRisk?: number;
  };
};

export default function AxiologyListPage() {
  const { tableProps } = useTable<AxiologyRecord>({
    resource: "governance/axiology",
    syncWithLocation: true,
  });

  return (
    <div className="p-8 space-y-8 animate-in fade-in duration-700">
      <div className="flex justify-between items-end">
        <div className="flex items-center gap-4">
          <div className="p-3 premium-gradient rounded-2xl shadow-[0_0_20px_rgba(102,252,241,0.2)]">
            <Scale className="text-black" size={24} />
          </div>
          <div>
            <Title level={4} className="!m-0 !text-white tracking-tighter uppercase">
              Bilissel Denetim
            </Title>
            <Text className="text-[10px] text-[#45a29e] font-black uppercase tracking-[0.2em]">
              Axiology Engine Denetim Loglari
            </Text>
          </div>
        </div>

        <div className="px-6 py-3 glass rounded-2xl border border-white/5 flex items-center gap-4">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_#48bb78]" />
          <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">
            Motor Durumu: Aktif
          </span>
        </div>
      </div>

      <Row gutter={[24, 24]}>
        <Col span={6}>
          <Card className="glass-card !bg-[#0e1320]/40 border-none">
            <Statistic
              title={<span className="label-tech text-gray-400">Hizalanma Puani</span>}
              value={98.4}
              precision={1}
              suffix="%"
              valueStyle={{ color: "#66fcf1", fontWeight: 900, fontSize: "28px" }}
              prefix={<ShieldCheck className="inline-block mr-2 text-[var(--primary)]" size={24} />}
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card className="glass-card !bg-[#0e1320]/40 border-none">
            <Statistic
              title={<span className="label-tech text-gray-400">Riskli Engellemeler</span>}
              value={12}
              valueStyle={{ color: "#f56565", fontWeight: 900, fontSize: "28px" }}
              prefix={<ShieldAlert className="inline-block mr-2 text-red-500" size={24} />}
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card className="glass-card !bg-[#0e1320]/40 border-none">
            <Statistic
              title={<span className="label-tech text-gray-400">Denetlenen Plan</span>}
              value={842}
              valueStyle={{ color: "#e2e8f0", fontWeight: 900, fontSize: "28px" }}
              prefix={<Activity className="inline-block mr-2 text-gray-400" size={24} />}
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card className="glass-card !bg-[#0e1320]/40 border-none">
            <Statistic
              title={<span className="label-tech text-gray-400">Otonom Duzeltmeler</span>}
              value={45}
              valueStyle={{ color: "#45a29e", fontWeight: 900, fontSize: "28px" }}
              prefix={<Fingerprint className="inline-block mr-2 text-[#45a29e]" size={24} />}
            />
          </Card>
        </Col>
      </Row>

      <List
        title=""
        breadcrumb={false}
        headerButtons={() => null}
        wrapperProps={{ className: "glass-panel rounded-3xl overflow-hidden border-white/5" }}
      >
        <Table
          {...tableProps}
          rowKey="id"
          className="custom-table"
          pagination={{ ...tableProps.pagination, showSizeChanger: true }}
        >
          <Table.Column<AxiologyRecord>
            dataIndex="decision"
            title={<span className="label-tech">Karar</span>}
            width={120}
            render={(value: AxiologyRecord["decision"]) => {
              let color = "default";
              let icon = <Info size={14} className="mr-1" />;

              if (value === "approve") {
                color = "success";
                icon = <ShieldCheck size={14} className="mr-1" />;
              } else if (value === "flag") {
                color = "warning";
                icon = <AlertCircle size={14} className="mr-1" />;
              } else if (value === "reject") {
                color = "error";
                icon = <ShieldAlert size={14} className="mr-1" />;
              }

              return (
                <Tag color={color} className="!rounded-full !px-3 font-black uppercase text-[9px] flex items-center w-fit border-none shadow-sm">
                  {icon} {value || "unknown"}
                </Tag>
              );
            }}
          />

          <Table.Column<AxiologyRecord>
            dataIndex="context"
            title={<span className="label-tech">Baglam</span>}
            width={150}
            render={(value: string) => (
              <Text className="font-mono text-[10px] text-[var(--primary)] uppercase tracking-wider">
                {value || "-"}
              </Text>
            )}
          />

          <Table.Column<AxiologyRecord>
            dataIndex="justification"
            title={<span className="label-tech">Gerekce ve Analiz</span>}
            render={(value: string) => (
              <div className="max-w-md">
                <Text className="text-gray-300 text-xs block leading-relaxed">
                  {value || "Kayitli gerekce yok."}
                </Text>
              </div>
            )}
          />

          <Table.Column<AxiologyRecord>
            dataIndex="scores"
            title={<span className="label-tech">Puanlar</span>}
            width={220}
            render={(value: AxiologyRecord["scores"]) => {
              const scores = value || {};
              const safety = Math.round((scores.Safety || 0) * 100);
              const resources = Math.round((scores.ResourceIntegrity || 0) * 100);
              const risk = Math.round((scores.OperationalRisk || 0) * 100);

              return (
                <Space direction="vertical" size={6} className="w-full">
                  <div>
                    <Text className="text-[10px] text-gray-500 font-bold">Safety: {safety}%</Text>
                    <Progress percent={safety} size="small" strokeColor="#48bb78" trailColor="rgba(255,255,255,0.05)" showInfo={false} />
                  </div>
                  <div>
                    <Text className="text-[10px] text-gray-500 font-bold">Resources: {resources}%</Text>
                    <Progress percent={resources} size="small" strokeColor="#66fcf1" trailColor="rgba(255,255,255,0.05)" showInfo={false} />
                  </div>
                  <div>
                    <Text className="text-[10px] text-gray-500 font-bold">Risk: {risk}%</Text>
                    <Progress percent={risk} size="small" strokeColor="#f56565" trailColor="rgba(255,255,255,0.05)" showInfo={false} />
                  </div>
                </Space>
              );
            }}
          />

          <Table.Column<AxiologyRecord>
            dataIndex="created_at"
            title={<span className="label-tech">Zaman</span>}
            width={140}
            render={(value: string) => (
              <Text className="text-gray-500 text-[10px] font-mono">
                {value ? new Date(value).toLocaleString("tr-TR") : "-"}
              </Text>
            )}
          />

          <Table.Column<AxiologyRecord>
            title={<span className="label-tech">Aksiyon</span>}
            width={120}
            render={(_, record) => (
              <Space>
                <Tooltip title={record.corrective_action || "Ek aksiyon gerekmiyor"}>
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                      record.corrective_action
                        ? "bg-[var(--primary)]/10 text-[var(--primary)] cursor-pointer hover:bg-[var(--primary)]/20"
                        : "bg-white/5 text-gray-700"
                    }`}
                  >
                    <Activity size={16} />
                  </div>
                </Tooltip>

                <Link href={`/axiology/${record.id}`}>
                  <button className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-gray-400 hover:text-[var(--primary)] hover:bg-[var(--primary)]/10 transition-all border border-white/5">
                    <Eye size={16} />
                  </button>
                </Link>
              </Space>
            )}
          />
        </Table>
      </List>
    </div>
  );
}
