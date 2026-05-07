"use client";

import React, { useState, useEffect } from "react";
import { Table, Tag, Typography } from "antd";
import { 
  AlertTriangle, 
  ShieldAlert,
  Ghost,
  Target,
  Skull
} from "lucide-react";
import { useTable } from "@refinedev/antd";
import { useTranslations } from "next-intl";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";

const { Text } = Typography;

export default function NegativePatternsPage() {
  const t = useTranslations("learning.negativePatterns");
  const [isClient, setIsClient] = useState(false);
  const { tableProps } = useTable({
    resource: "learning/negative-patterns",
    sorters: {
      initial: [{ field: "occurrence_count", order: "desc" }]
    },
  });

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title={t("title")} 
        subtitle="Blacklist Registry & Failure Pattern Recognition" 
        icon={<ShieldAlert size={32} />}
        badge="SECURITY-MESH ACTIVE"
      />

      <div className="glass-panel rounded-[2.5rem] border-white/10 bg-[#0b0f19]/60 p-10 shadow-2xl backdrop-blur-md relative overflow-hidden group border-red-500/10 shadow-red-500/5">
        <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none text-red-500">
           <Skull size={300} />
        </div>

        <Table 
          {...tableProps} 
          rowKey="id" 
          className="custom-table-v2"
          pagination={{ pageSize: 10 }}
        >
          <Table.Column
            dataIndex="pattern_name"
            title={t("strategy").toUpperCase()}
            render={(value) => (
              <div className="flex items-center gap-4">
                <div className="p-3 bg-red-500/10 rounded-xl border border-red-500/20 text-red-400">
                  <Ghost size={16} />
                </div>
                <span className="text-white font-black uppercase tracking-tight italic">{value}</span>
              </div>
            )}
          />
          <Table.Column
            dataIndex="occurrence_count"
            title={t("occurrence").toUpperCase()}
            render={(value) => (
              <div className="flex items-center gap-2">
                <AlertTriangle size={14} className="text-red-500" />
                <span className="text-sm font-black text-white italic">{value}x</span>
              </div>
            )}
          />
          <Table.Column
            dataIndex="penalty_weight"
            title={t("penaltyWeight").toUpperCase()}
            render={(value) => (
              <Tag color="red" className="font-mono bg-red-950/40 border-red-900/50 text-red-400">
                {(value * 100).toFixed(1)}% PENALTY
              </Tag>
            )}
          />
        </Table>
      </div>
    </div>
  );
}
