"use client";

import React from "react";
import { useCustom, useApiUrl } from "@refinedev/core";
import { Card, Row, Col, Typography, Progress, Table, Tag, Space, Tooltip, Empty, Spin } from "antd";
import {
  History,
  BrainCircuit,
  ZapOff,
  CheckCircle2,
  XCircle,
  Activity,
  FileWarning,
  TrendingUp,
  Brain
} from "lucide-react";

const { Title, Text } = Typography;

export default function RepairMemoryPage() {
  const apiUrl = useApiUrl();

  // Fetch Heatmaps
  const heatmapQuery = useCustom<any[]>({
    url: `${apiUrl}/repair-lab/memory/heatmaps`,
    method: "get",
  });
  const { data: heatmapData, isLoading: heatmapLoading } = heatmapQuery.query;

  // Fetch Learning Insights
  const insightQuery = useCustom<any>({
    url: `${apiUrl}/repair-lab/learning/insights`,
    method: "get",
  });
  const { data: insightData, isLoading: insightLoading } = insightQuery.query;

  const heatmaps = heatmapData?.data || [];
  const strategies = insightData?.data?.strategies || [];
  const negatives = insightData?.data?.penalized_patterns || [];

  const isLoading = heatmapLoading || insightLoading;

  return (
    <div className="p-8 space-y-10 animate-in fade-in duration-1000">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-black tracking-tighter text-white mb-2">
            OTONOM <span className="text-[var(--primary)]">HAFIZA</span>
          </h1>
          <p className="text-[#45a29e] font-bold uppercase tracking-[0.3em] text-[10px]">
            Repair Memory & Strategy Learning Engine
          </p>
        </div>
        <div className="flex gap-4">
           <div className="px-6 py-3 glass rounded-2xl border border-white/5 flex items-center gap-4">
              <Brain className="text-[var(--primary)]" size={20} />
              <div className="text-right">
                <div className="text-xs font-black text-white">{strategies.length} Strateji</div>
                <div className="text-[8px] text-gray-500 uppercase font-black">Aktif Hafıza</div>
              </div>
           </div>
        </div>
      </div>

      {isLoading ? (
        <div className="h-64 flex items-center justify-center">
          <Spin size="large" />
        </div>
      ) : (
        <>
          {/* 1. Heatmap Grid */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 px-4">
               <Activity className="text-[var(--primary)]" size={18} />
               <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest">Alt Sistem Başarı Yoğunluk Haritası</h3>
            </div>
            <Row gutter={[16, 16]}>
              {heatmaps.map((ss: any) => (
                <Col span={6} key={ss.subsystem}>
                  <Card className="glass-card !bg-[#0e1320]/40 border-none !p-6 hover:translate-y-[-4px] transition-all cursor-default group">
                    <div className="flex justify-between items-start mb-6">
                      <div className="p-3 bg-white/5 rounded-xl group-hover:bg-[var(--primary)]/10 transition-colors">
                        <History size={20} className="text-gray-400 group-hover:text-[var(--primary)]" />
                      </div>
                      <div className="text-right">
                        <Text className="text-[10px] text-gray-500 font-black uppercase block tracking-tighter">Başarı Oranı</Text>
                        <Text className="text-lg font-black text-white">%{Math.round(ss.rate * 100)}</Text>
                      </div>
                    </div>
                    <Title level={5} className="!text-white tracking-tight !m-0 !mb-4 uppercase text-xs">{ss.subsystem}</Title>
                    <Progress
                      percent={ss.rate * 100}
                      strokeColor={ss.rate > 0.7 ? "#66fcf1" : ss.rate > 0.4 ? "#f6ad55" : "#f56565"}
                      trailColor="rgba(255,255,255,0.05)"
                      size={8}
                      showInfo={false}
                    />
                    <div className="flex justify-between mt-4 text-[9px] font-bold uppercase tracking-tighter">
                       <span className="text-green-500 flex items-center gap-1"><CheckCircle2 size={10} /> {ss.success} Ok</span>
                       <span className="text-red-500 flex items-center gap-1"><XCircle size={10} /> {ss.failure} Fail</span>
                    </div>
                  </Card>
                </Col>
              ))}
              {heatmaps.length === 0 && (
                 <Col span={24}>
                   <Card className="glass-card !bg-[#0e1320]/20 border-dashed border-white/5 !p-12 flex flex-col items-center justify-center">
                     <Empty
                       image={Empty.PRESENTED_IMAGE_SIMPLE}
                       description={
                        <div className="text-center">
                          <Text className="text-[11px] font-black uppercase tracking-widest text-gray-500 block mb-2">Bilişsel Kuluçka Evresi</Text>
                          <Text className="text-[10px] text-gray-600">Sistem henüz otonom tamir tecrübesi biriktiriyor. Veriler toplandıkça harita canlanacaktır.</Text>
                        </div>
                       }
                     />
                   </Card>
                 </Col>
              )}
            </Row>
          </div>

          <Row gutter={[24, 24]}>
            {/* 2. Strategy Trust Score */}
            <Col span={14}>
              <Card className="glass-panel !bg-[#0b0c10]/40 border-white/5 !p-8 h-full">
                <div className="flex items-center gap-3 mb-8">
                  <BrainCircuit className="text-[var(--primary)]" size={24} />
                  <Title level={4} className="!text-white !m-0 tracking-tighter uppercase text-sm">Strateji Güven ve Verimlilik Matrisi</Title>
                </div>
                <Table
                  dataSource={strategies}
                  pagination={false}
                  className="custom-table"
                  rowKey="name"
                >
                  <Table.Column
                    title={<span className="label-tech">STRATEJİ</span>}
                    dataIndex="name"
                    render={(val) => <Text className="font-black text-[var(--primary)] uppercase text-[10px] tracking-widest">{val}</Text>}
                  />
                  <Table.Column
                    title={<span className="label-tech">GÜVEN PUANI</span>}
                    dataIndex="trust_score"
                    render={(val) => (
                      <div className="flex items-center gap-3">
                        <Progress percent={val * 100} size="small" strokeColor="#66fcf1" showInfo={false} className="w-24" />
                        <Text className="text-white font-mono text-[10px]">{Math.round(val * 100)}%</Text>
                      </div>
                    )}
                  />
                  <Table.Column
                    title={<span className="label-tech">BAŞARI / ROLLBACK</span>}
                    render={(_, r: any) => (
                      <Space size={12}>
                        <Tag color="success" className="!rounded-full border-none font-bold text-[9px] px-3">+{r.success}</Tag>
                        <Tag color="error" className="!rounded-full border-none font-bold text-[9px] px-3">-{r.rollbacks}</Tag>
                      </Space>
                    )}
                  />
                  <Table.Column
                    title={<span className="label-tech">DURUM</span>}
                    dataIndex="state"
                    render={(val) => (
                      <Tag className={`!rounded-full font-black uppercase text-[8px] border-none px-3 ${val === 'PROMOTED' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>
                        {val}
                      </Tag>
                    )}
                  />
                </Table>
              </Card>
            </Col>

            {/* 3. Negative Patterns */}
            <Col span={10}>
              <Card className="glass-panel !bg-[#0b0c10]/40 border-white/5 !p-8 h-full">
                <div className="flex items-center gap-3 mb-8">
                  <ZapOff className="text-red-500" size={24} />
                  <Title level={4} className="!text-white !m-0 tracking-tighter uppercase text-sm">Cezalandırılan Negatif Kalıplar</Title>
                </div>
                <div className="space-y-4">
                  {negatives.map((n: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-red-500/30 transition-all group">
                       <div className="flex justify-between items-start mb-3">
                          <Tag color="error" className="!rounded-full border-none font-black text-[8px] uppercase">{n.strategy}</Tag>
                          <div className="text-right">
                             <Text className="text-[10px] text-red-400 font-bold block leading-none">-{Math.round(n.penalty * 100)} Puan</Text>
                             <Text className="text-[8px] text-gray-600 uppercase font-black">Ceza Ağırlığı</Text>
                          </div>
                       </div>
                       <Text className="text-gray-300 text-[11px] block italic mb-2">"{n.reason}"</Text>
                       <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1 text-[9px] text-gray-500 font-bold">
                             <TrendingUp size={10} /> {n.occurrences} Tekrar
                          </div>
                          <div className="flex items-center gap-1 text-[9px] text-gray-500 font-bold">
                             <FileWarning size={10} /> Etki: {n.blast_radius || 'Sınırlı'}
                          </div>
                       </div>
                    </div>
                  ))}
                  {negatives.length === 0 && (
                    <Empty description={<span className="text-[10px] font-black uppercase text-gray-600 tracking-widest">Kısıtlanan kalıp yok</span>} />
                  )}
                </div>
              </Card>
            </Col>
          </Row>
        </>
      )}

      <style jsx global>{`
        .custom-table .ant-table { background: transparent !important; color: #888 !important; }
        .custom-table .ant-table-thead > tr > th {
          background: rgba(255,255,255,0.02) !important;
          border-bottom: 1px solid rgba(255,255,255,0.05) !important;
          color: #555 !important;
          padding: 12px 16px !important;
        }
        .custom-table .ant-table-tbody > tr > td {
          border-bottom: 1px solid rgba(255,255,255,0.03) !important;
          padding: 16px !important;
        }
        .custom-table .ant-table-tbody > tr:hover > td { background: rgba(102, 252, 241, 0.02) !important; }
        .label-tech { font-size: 9px; font-weight: 900; letter-spacing: 0.25em; text-transform: uppercase; color: #555; }
      `}</style>
    </div>
  );
}


