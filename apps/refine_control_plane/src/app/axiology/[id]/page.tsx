"use client";

import { useShow } from "@refinedev/core";
import { Show } from "@refinedev/antd";
import { Typography, Tag, Space, Card, Progress, Row, Col, Divider, Empty, Skeleton } from "antd";
import { 
  ShieldCheck, 
  ShieldAlert, 
  AlertCircle, 
  Code, 
  FileText, 
  Zap, 
  Compass, 
  ArrowLeft,
  Info
} from "lucide-react";
import Link from "next/link";

const { Title, Text, Paragraph } = Typography;

export default function AxiologyShowPage() {
  const { query } = useShow({
    resource: "axiology",
  });
  const { data, isLoading } = query;
  const record = data?.data;

  if (isLoading) {
    return (
      <div className="p-8 space-y-8 animate-pulse">
        <Skeleton active paragraph={{ rows: 12 }} />
      </div>
    );
  }

  const decision = record?.decision || "unknown";
  let decisionColor = "default";
  let decisionIcon = <Info size={24} />;
  
  if (decision === "approve") {
    decisionColor = "success";
    decisionIcon = <ShieldCheck size={24} />;
  } else if (decision === "flag") {
    decisionColor = "warning";
    decisionIcon = <AlertCircle size={24} />;
  } else if (decision === "reject") {
    decisionColor = "error";
    decisionIcon = <ShieldAlert size={24} />;
  }

  const scores = record?.scores || {};

  return (
    <Show
      breadcrumb={false}
      headerButtons={({ listButtonProps }) => (
        <Link href="/axiology">
           <button className="flex items-center gap-2 px-4 py-2 rounded-xl glass border border-white/10 text-gray-400 hover:text-[var(--primary)] hover:border-[var(--primary)]/30 transition-all text-xs font-black uppercase tracking-widest">
            <ArrowLeft size={14} /> Geri Dön
           </button>
        </Link>
      )}
      headerProps={{
        title: (
          <div className="flex items-center gap-4">
            <div className="p-3 premium-gradient rounded-2xl shadow-[0_0_20px_rgba(102,252,241,0.2)]">
              <Compass className="text-black" size={24} />
            </div>
            <div>
              <Title level={4} className="!m-0 !text-white tracking-tighter">DENETİM ANALİZİ</Title>
              <Text className="text-[10px] text-[#45a29e] font-black uppercase tracking-[0.2em]">Bilişsel Karar Derinlemesine İnceleme</Text>
            </div>
          </div>
        ),
      }}
      wrapperProps={{ className: "p-8 animate-in slide-in-from-bottom-4 duration-700" }}
    >
      <div className="space-y-8 pb-12">
        <Row gutter={[24, 24]}>
          <Col span={16}>
            <Card className="glass-card !bg-[#0e1320]/40 border-none !p-6">
              <Space direction="vertical" size={24} className="w-full">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="label-tech block mb-2 text-gray-500">KARAR</span>
                    <div className="flex items-center gap-3">
                       <Tag color={decisionColor} className="!rounded-full !px-4 !py-1 font-black uppercase text-[11px] flex items-center w-fit border-none shadow-lg">
                          {decisionIcon} <span className="ml-2">{decision}</span>
                       </Tag>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="label-tech block mb-2 text-gray-500">BAĞLAM</span>
                    <Tag color="cyan" className="!rounded-full font-mono uppercase text-[10px] !px-4 border-none bg-white/5 text-[var(--primary)]">{record?.context || "N/A"}</Tag>
                  </div>
                </div>

                <Divider className="border-white/5 !m-0" />

                <div>
                  <Title level={5} className="!text-[var(--primary)] uppercase tracking-widest text-[11px] font-black mb-4 flex items-center gap-2">
                    <FileText size={16} /> ETİK GEREKÇE VE MANTIKSAL ANALİZ
                  </Title>
                  <Paragraph className="text-gray-300 text-sm leading-loose bg-white/5 p-6 rounded-2xl border border-white/5">
                    {record?.justification || "Bu karar için ayrıntılı bir gerekçe bulunamadı."}
                  </Paragraph>
                </div>

                {record?.target_preview && (
                  <div>
                    <Title level={5} className="!text-[var(--primary)] uppercase tracking-widest text-[11px] font-black mb-4 flex items-center gap-2">
                      <Code size={16} /> HEDEF İÇERİK / KOD ÖNİZLEME
                    </Title>
                    <div className="bg-black/40 p-6 rounded-2xl border border-white/5 font-mono text-xs text-[#66fcf1]/80 leading-relaxed overflow-x-auto relative group">
                      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all">
                         <Tag className="bg-white/5 border-white/10 text-gray-500">PROVENANCE VERIFIED</Tag>
                      </div>
                      <pre className="m-0 whitespace-pre-wrap">
                        {record.target_preview}
                      </pre>
                    </div>
                  </div>
                )}
              </Space>
            </Card>
          </Col>

          <Col span={8}>
            <Space direction="vertical" size={24} className="w-full">
              <Card className="glass-card !bg-[#0e1320]/40 border-none !p-6">
                <Title level={5} className="!text-white uppercase tracking-widest text-[11px] font-black mb-6 flex items-center gap-2">
                  <Zap size={16} className="text-yellow-400" /> GÜVENLİK SKORLARI
                </Title>
                
                <div className="space-y-8">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Safety</span>
                      <span className="text-[var(--primary)] font-bold">{Math.round((scores.Safety || 0) * 100)}%</span>
                    </div>
                    <Progress percent={(scores.Safety || 0) * 100} strokeColor="#66fcf1" trailColor="rgba(255,255,255,0.05)" size={12} showInfo={false} />
                  </div>

                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Resource Integrity</span>
                      <span className="text-blue-400 font-bold">{Math.round((scores.ResourceIntegrity || 0) * 100)}%</span>
                    </div>
                    <Progress percent={(scores.ResourceIntegrity || 0) * 100} strokeColor="#4299e1" trailColor="rgba(255,255,255,0.05)" size={12} showInfo={false} />
                  </div>

                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Operational Risk</span>
                      <span className="text-red-400 font-bold">{Math.round((scores.OperationalRisk || 0) * 100)}%</span>
                    </div>
                    <Progress percent={(scores.OperationalRisk || 0) * 100} strokeColor="#f56565" trailColor="rgba(255,255,255,0.05)" size={12} showInfo={false} />
                  </div>
                </div>
              </Card>

              {record?.corrective_action && (
                <Card className="glass-card !bg-[#0e1320]/60 border border-[var(--primary)]/20 !p-6 shadow-[0_0_30px_rgba(102,252,241,0.05)]">
                   <Title level={5} className="!text-[var(--primary)] uppercase tracking-widest text-[11px] font-black mb-4 flex items-center gap-2">
                    <ShieldCheck size={16} /> DÜZELTİCİ EYLEM
                  </Title>
                  <div className="p-4 rounded-xl bg-[var(--primary)]/5 border border-[var(--primary)]/10">
                     <Text className="text-[11px] text-[#45a29e] block mb-2 italic font-bold">Axiology engine tarafından önerilen strateji:</Text>
                     <Text className="text-white font-black block leading-relaxed">
                       "{record.corrective_action}"
                     </Text>
                  </div>
                </Card>
              )}
              
              <Card className="glass-card !bg-[#0b0c10]/40 border-none !p-6 opacity-60">
                <div className="flex flex-col items-center justify-center gap-3">
                   <Text className="text-[10px] font-mono text-gray-600 uppercase tracking-widest">Log ID</Text>
                   <Tag className="bg-white/5 border-white/10 text-gray-500 font-mono text-[9px] !m-0">{record?.id}</Tag>
                </div>
              </Card>
              <Card className="glass-card !bg-[#0b0c10]/40 border-none !p-6 opacity-60 grayscale">
                <Empty description={<span className="text-[10px] uppercase font-black tracking-widest text-gray-600">Bağlantılı Kanıt Yok</span>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
              </Card>
            </Space>
          </Col>
        </Row>
      </div>

      <style jsx global>{`
        .ant-card-body { padding: 0 !important; }
        .label-tech {
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.25em;
          text-transform: uppercase;
        }
        .premium-gradient {
          background: linear-gradient(135deg, #66fcf1 0%, #45a29e 100%);
        }
      `}</style>
    </Show>
  );
}
