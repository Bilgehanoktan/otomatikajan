"use client";

import React, { useState, useEffect } from "react";
import { Table, Typography, Progress } from "antd";
import { 
  Rocket, 
  Target,
  BarChart3,
  Zap,
  ShieldCheck,
  Cpu
} from "lucide-react";
import { useTable } from "@refinedev/antd";
import { useTranslations } from "next-intl";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";

const { Text } = Typography;

export default function StrategyMemoryPage() {
  const t = useTranslations("learning.strategyMemory");
  const [isClient, setIsClient] = useState(false);
  const { tableProps } = useTable({
    resource: "learning/strategy-memory",
    sorters: {
      initial: [{ field: "trust_score", order: "desc" }]
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
        subtitle="Historical Performance Matrix & Behavioral Heuristics" 
        icon={<Cpu size={32} />}
        badge="HEURISTIC-CORE v4"
      />

      <div className="glass-panel rounded-[2.5rem] border-white/10 bg-[#0b0f19]/60 p-10 shadow-2xl backdrop-blur-md relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
           <BarChart3 size={300} />
        </div>

        <Table 
          {...tableProps} 
          rowKey="id" 
          className="custom-table-v2"
          pagination={{ pageSize: 10 }}
        >
          <Table.Column
            dataIndex="strategy_name"
            title={t("strategy").toUpperCase()}
            render={(value) => (
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-500/10 rounded-xl border border-purple-500/20 text-purple-400">
                  <Rocket size={16} />
                </div>
                <span className="text-white font-black uppercase tracking-tight italic">{value}</span>
              </div>
            )}
          />
          <Table.Column
            dataIndex="trust_score"
            title={t("trustScore").toUpperCase()}
            render={(value) => (
              <div className="flex flex-col gap-1">
                <div className="flex justify-between text-[10px] font-black text-gray-500 uppercase tracking-widest">
                  <span>Index</span>
                  <span>{(value * 100).toFixed(0)}%</span>
                </div>
                <div className="w-32 h-1 bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.5)] transition-all duration-1000" 
                    style={{ width: `${value * 100}%` }}
                  />
                </div>
              </div>
            )}
          />
          <Table.Column
            dataIndex="avg_latency"
            title={t("latency").toUpperCase()}
            render={(value) => (
              <div className="flex items-center gap-2">
                <Zap size={12} className="text-yellow-500/50" />
                <span className="text-[11px] font-black text-white italic">{value}ms</span>
              </div>
            )}
          />
        </Table>
      </div>
    </div>
  );
}
