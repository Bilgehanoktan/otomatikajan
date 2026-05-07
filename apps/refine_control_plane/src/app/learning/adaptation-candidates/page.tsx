"use client";

import React, { useState, useEffect } from "react";
import { App, Table, Tag, Typography, Button, Modal, Alert } from "antd";
import { 
  FlaskConical, 
  ShieldCheck,
  Zap,
  CheckCircle,
  Rocket
} from "lucide-react";
import { useTable } from "@refinedev/antd";
import { useCustomMutation } from "@refinedev/core";
import { useTranslations } from "next-intl";
import { ResourceHeader } from "@/components/dashboard/ResourceHeader";

const { Text } = Typography;

export default function AdaptationCandidatesPage() {
  const t = useTranslations("learning.adaptation");
  const [isClient, setIsClient] = useState(false);
  const { tableProps } = useTable({
    resource: "learning/adaptation-candidates",
    syncWithLocation: false,
  });

  const { mutate, mutation } = useCustomMutation();
  const { message } = App.useApp();

  useEffect(() => {
    setIsClient(true);
  }, []);

  const handleApply = (id: string) => {
    mutate(
      {
        url: `/api/v1/learning/adaptation-candidates/${id}/apply`,
        method: "post",
        values: {},
      },
      {
        onSuccess: () => {
          message.success(t("applySuccess"));
        },
        onError: () => {
          message.error(t("applyError"));
        },
      }
    );
  };

  if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;

  return (
    <div className="min-h-screen p-8 bg-[#060a12] text-gray-300 animate-in fade-in duration-1000 overflow-x-hidden">
      
      <ResourceHeader 
        title={t("title")} 
        subtitle={t("subtitle")} 
        icon={<FlaskConical size={32} />}
        badge="Evolution-Tier 2"
      />

      <div className="glass-panel rounded-[2.5rem] border-white/10 bg-[#0b0f19]/60 p-10 shadow-2xl backdrop-blur-md relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-10 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
           <Zap size={300} />
        </div>

        <Table 
          {...tableProps} 
          rowKey="id" 
          className="custom-table-v2"
          pagination={false}
        >
          <Table.Column
            dataIndex="strategy_name"
            title="STRATEGY"
            render={(value) => (
              <div className="flex items-center gap-4">
                <div className="p-3 bg-[var(--primary)]/10 rounded-xl border border-[var(--primary)]/20 text-[var(--primary)]">
                  <Rocket size={16} />
                </div>
                <span className="text-white font-black uppercase tracking-tight italic">{value}</span>
              </div>
            )}
          />
          <Table.Column
            dataIndex="trust_score"
            title="CONFIDENCE"
            render={(value) => (
              <div className="flex flex-col gap-1">
                <div className="flex justify-between text-[10px] font-black text-gray-500 uppercase tracking-widest">
                  <span>Signal</span>
                  <span>{(value * 100).toFixed(0)}%</span>
                </div>
                <div className="w-32 h-1 bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[var(--primary)] shadow-[0_0_8px_rgba(102,252,241,0.5)] transition-all duration-1000" 
                    style={{ width: `${value * 100}%` }}
                  />
                </div>
              </div>
            )}
          />
          <Table.Column
            title="ACTION"
            render={(_, record: any) => (
              <button
                onClick={() => handleApply(record.id)}
                disabled={mutation.isPending}
                className="flex items-center gap-2 rounded-xl bg-white/5 border border-white/10 px-6 py-2 text-[10px] font-black uppercase tracking-widest text-white transition-all hover:bg-[var(--primary)] hover:text-[#060a12] active:scale-95 disabled:opacity-50"
              >
                <CheckCircle size={14} />
                {t("apply")}
              </button>
            )}
          />
        </Table>
      </div>
    </div>
  );
}
