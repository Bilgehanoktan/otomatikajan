"use client";

import React from "react";
import { useShow, useNavigation } from "@refinedev/core";
import { 
  Typography, 
  Card, 
  Tag, 
  Descriptions, 
  Table, 
  Row, 
  Col, 
  Statistic, 
  Button, 
  List, 
  Timeline,
  Divider,
  Progress
} from "antd";
import { 
  ArrowLeftOutlined, 
  BugOutlined, 
  HistoryOutlined, 
  RocketOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  AuditOutlined
} from "@ant-design/icons";
import { DateField } from "@refinedev/antd";

const { Title, Text, Paragraph } = Typography;

export default function FingerprintDetail() {
  const { queryResult } = useShow();
  const { list } = useNavigation();
  const { data, isLoading } = queryResult;

  const record = data?.data as any;
  const fp = record?.fingerprint;
  const recentRecords = record?.recent_records || [];
  const strategies = record?.strategies || [];

  if (isLoading) return <div className="p-10 text-[#66fcf1]">Yükleniyor...</div>;

  return (
    <div className="p-6">
      <Button 
        icon={<ArrowLeftOutlined />} 
        onClick={() => list("learning/fingerprints")}
        className="mb-6 bg-transparent text-gray-400 border-gray-700 hover:text-[#66fcf1]"
      >
        Listeye Dön
      </Button>

      <Row gutter={[24, 24]}>
        {/* Left Column: Core Info */}
        <Col span={16}>
          <Card 
            className="bg-[#1a1c22] border-[#30363d] mb-6"
            title={
              <div className="flex items-center gap-2">
                <BugOutlined className="text-[#66fcf1]" />
                <span className="text-[#66fcf1] font-bold">Hata Analizi: {fp?.error_family}</span>
              </div>
            }
          >
            <Descriptions column={2} bordered className="custom-descriptions">
              <Descriptions.Item label="Servis" span={1}>{fp?.service}</Descriptions.Item>
              <Descriptions.Item label="Bileşen" span={1}>{fp?.component}</Descriptions.Item>
              <Descriptions.Item label="İstisna Tipi" span={2}>
                <Tag color="magenta">{fp?.exception_type}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Normalize Mesaj" span={2}>
                <Paragraph className="text-gray-300 font-mono text-xs bg-black/30 p-2 rounded border border-white/5">
                  {fp?.normalized_message}
                </Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="Risk Alanı" span={1}>{fp?.risk_domain}</Descriptions.Item>
              <Descriptions.Item label="Önem Derecesi" span={1}>
                <Tag color={fp?.severity === 'critical' ? 'red' : 'orange'}>{fp?.severity?.toUpperCase()}</Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card 
            className="bg-[#1a1c22] border-[#30363d]"
            title={<div className="text-[#66fcf1]"><HistoryOutlined /> Çözüm Geçmişi (Son 10)</div>}
          >
            <Table 
              dataSource={recentRecords} 
              pagination={false} 
              rowKey="id" 
              className="custom-table"
              size="small"
            >
              <Table.Column 
                dataIndex="created_at" 
                title="Tarih" 
                render={(value) => <DateField value={value} format="DD/MM HH:mm" />} 
              />
              <Table.Column 
                dataIndex="strategy_used" 
                title="Kullanılan Strateji" 
                render={(value) => <Text className="text-[#66fcf1] font-bold">{value}</Text>} 
              />
              <Table.Column 
                dataIndex="final_outcome" 
                title="Sonuç" 
                render={(value) => (
                  <Tag color={value === 'SUCCESS' ? 'green' : 'red'}>{value}</Tag>
                )} 
              />
              <Table.Column 
                dataIndex="verification_score" 
                title="Doğrulama" 
                render={(value) => <Text className="text-gray-400 font-mono">{(value * 100).toFixed(0)}%</Text>} 
              />
              <Table.Column 
                dataIndex="integrity_hash" 
                title="Kanıt" 
                render={(value) => <Text className="text-gray-500 text-[10px] font-mono">{value?.substring(0, 8)}</Text>} 
              />
            </Table>
          </Card>
        </Col>

        {/* Right Column: Statistics & Strategies */}
        <Col span={8}>
          <Card className="bg-[#1a1c22] border-[#30363d] mb-6">
            <Statistic 
              title={<span className="text-gray-400">Tekrarlanma Sayısı</span>}
              value={fp?.recurrence_count} 
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#66fcf1' }}
            />
            <Divider className="border-gray-800 my-4" />
            <Text className="text-gray-500 text-[10px] block mb-2 uppercase tracking-widest">Sinyal Gücü</Text>
            <Progress 
              percent={Math.min(100, (fp?.recurrence_count / 20) * 100)} 
              status={fp?.recurrence_count > 15 ? "exception" : "active"}
              strokeColor="#66fcf1"
              trailColor="#0b0c10"
              showInfo={false}
            />
            <Text className="text-gray-500 text-[10px] block mt-1">Eşik: 20 Sinyal / Adaptasyon Kararı</Text>
          </Card>

          <Card 
            className="bg-[#1a1c22] border-[#30363d]"
            title={<div className="text-[#66fcf1]"><RocketOutlined /> Strateji Verimliliği</div>}
          >
            <List
              dataSource={strategies}
              renderItem={(s: any) => (
                <div className="mb-4 border-b border-gray-800 pb-2 last:border-0">
                  <div className="flex justify-between items-center mb-1">
                    <Text className="text-[#c5c6c7] font-bold">{s.strategy_name}</Text>
                    <Tag color={s.state === 'promoted' ? 'gold' : 'blue'}>{s.state?.toUpperCase()}</Tag>
                  </div>
                  <div className="flex justify-between text-[10px] mb-2">
                    <Text className="text-green-500">Başarı: {s.success_count}</Text>
                    <Text className="text-red-500">Hata: {s.failure_count}</Text>
                    <Text className="text-orange-500">Geri Alma: {s.rollback_count}</Text>
                  </div>
                  <Progress 
                    percent={Math.round(s.trust_score * 100)} 
                    size="small" 
                    strokeColor={s.trust_score > 0.8 ? '#4ade80' : '#f87171'}
                    trailColor="#0b0c10"
                  />
                </div>
              )}
            />
          </Card>

          <Card 
            className="bg-[#1a1c22] border-[#30363d] mt-6"
            title={<div className="text-[#66fcf1]"><AuditOutlined /> Otonom Öneri</div>}
          >
            {fp?.recurrence_count > 10 ? (
              <div className="bg-blue-900/20 p-3 rounded border border-blue-500/30">
                <Text className="text-blue-400 text-xs flex items-center gap-2">
                  <ExclamationCircleOutlined /> Yüksek tekrarlanma sinyali tespit edildi.
                </Text>
                <Paragraph className="text-gray-400 text-[10px] mt-2">
                  Bu hata tipi için {strategies[0]?.strategy_name} stratejisi %{(strategies[0]?.trust_score * 100).toFixed(1)} güven vermektedir. 
                  Otonomi seviyesinin artırılması önerilir.
                </Paragraph>
                <Button size="small" type="primary" block ghost className="mt-2 text-[10px] h-6">
                  Politika Teklifi Oluştur
                </Button>
              </div>
            ) : (
              <Text className="text-gray-500 italic text-[10px]">
                Yeterli veri birikmedi. (Eşik: 10)
              </Text>
            )}
          </Card>
        </Col>
      </Row>

      <style jsx global>{`
        .custom-descriptions .ant-descriptions-item-label {
          background: #23272e !important;
          color: #66fcf1 !important;
          border-color: #30363d !important;
          font-weight: bold;
          font-size: 11px;
        }
        .custom-descriptions .ant-descriptions-item-content {
          background: #1a1c22 !important;
          color: #c5c6c7 !important;
          border-color: #30363d !important;
          font-size: 11px;
        }
        .custom-table .ant-table {
          background: transparent !important;
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
      `}</style>
    </div>
  );
}
