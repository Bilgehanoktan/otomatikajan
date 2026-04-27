"use client";

import { useShow, useCustomMutation } from "@refinedev/core";
import { Card, Typography, Descriptions, Tag, Button, Space, Divider, message, Popconfirm, Row, Col, Alert, Input } from "antd";
import { ArrowLeftOutlined, SafetyOutlined, CheckCircleOutlined, SyncOutlined, StopOutlined, InboxOutlined, RollbackOutlined } from "@ant-design/icons";
import { useNavigation } from "@refinedev/core";
import { useState } from "react";

const { Title, Text } = Typography;
const { TextArea } = Input;

export default function GovernorCaseDetail() {
  const { query } = useShow({
    resource: "governor/cases",
  });
  const { data, isLoading } = query;
  const record = data?.data;
  const { list } = useNavigation();
  const { mutate } = useCustomMutation();
  const [actionLoading, setActionLoading] = useState(false);
  const [justification, setJustification] = useState("");

  if (isLoading) return <div>Yükleniyor...</div>;
  if (!record) return <div>Kayıt bulunamadı.</div>;

  const handleOverride = (action: string) => {
    if (justification.trim().length < 20) {
      message.error("Lütfen en az 20 karakterlik bir gerekçe girin.");
      return;
    }
    setActionLoading(true);
    mutate(
      {
        url: `/governance/governor/cases/${record.id}/override`,
        method: "post",
        values: { action, reason: justification },
      },
      {
        onSuccess: () => {
          message.success(`Aksiyon uygulandı: ${action}`);
          list("governor/cases");
        },
        onError: (err) => {
          message.error(`Hata: ${err.message}`);
        },
        onSettled: () => setActionLoading(false),
      }
    );
  };

  const handleRestore = () => {
    setActionLoading(true);
    mutate(
      {
        url: `/governance/governor/cases/${record.id}/restore`,
        method: "post",
        values: {},
      },
      {
        onSuccess: (res) => {
          message.success(`Case geri yüklendi.`);
          list("governor/cases");
        },
        onError: (err) => {
          message.error(`Hata: ${err.message}`);
        },
        onSettled: () => setActionLoading(false),
      }
    );
  };

  const handleExecute = () => {
    setActionLoading(true);
    mutate(
      {
        url: `/governance/governor/cases/${record.id}/execute`,
        method: "post",
        values: {},
      },
      {
        onSuccess: () => {
          message.success(`Governor otomatik kararı uygulandı.`);
          list("governor/cases");
        },
        onError: (err) => {
          message.error(`Hata: ${err.message}`);
        },
        onSettled: () => setActionLoading(false),
      }
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => list("governor/cases")}>Geri</Button>
        <Title level={3} style={{ margin: 0 }}>Case Incelemesi: {record.project_title}</Title>
      </Space>

      {(record.risk_class === "CRITICAL" || record.risk_class === "HIGH" || record.has_safety_lock) && (
        <Alert
          message="🚨 HARD GUARDRAIL AKTİF"
          description="Bu işlem güvenlik kilitlerine, kimlik politikalarına veya yüksek risk profiline takılmıştır. Manuel override (zorla onay) sistemi atlatır ve tüm sorumluluk operatöre geçer."
          type="error"
          showIcon
          style={{ marginBottom: 24, fontWeight: "bold" }}
        />
      )}

      <Row gutter={[24, 24]}>
        <Col span={16}>
          <Card title="Bağlam ve Teşhis" bordered={false} style={{ background: "#1f2833", borderRadius: 8 }}>
            <Descriptions column={2} bordered size="small" labelStyle={{ background: "#0b0c10", color: "#66fcf1" }}>
              <Descriptions.Item label="Risk Sınıfı"><Tag color={record.risk_class === "CRITICAL" ? "red" : "blue"}>{record.risk_class}</Tag></Descriptions.Item>
              <Descriptions.Item label="Risk Skoru">{record.risk_score}</Descriptions.Item>
              <Descriptions.Item label="Bekleme Nedeni">{record.pending_reason}</Descriptions.Item>
              <Descriptions.Item label="Mevcut Durum">{record.project_status}</Descriptions.Item>
              <Descriptions.Item label="Açık Olay Var Mı?">{record.has_open_incident ? "Evet" : "Hayır"}</Descriptions.Item>
              <Descriptions.Item label="Parmak İzi Eşleşmesi">{record.has_active_fingerprint ? "Evet" : "Hayır"}</Descriptions.Item>
              <Descriptions.Item label="Güvenlik Kilidi">{record.has_safety_lock ? "Aktif" : "Yok"}</Descriptions.Item>
              <Descriptions.Item label="Bayatlık (Saat)">{(record.stale_seconds / 3600).toFixed(1)}</Descriptions.Item>
            </Descriptions>

            <Divider orientation="left" style={{ color: "#c5c6c7" }}>Governor Kararı ve Gerekçesi</Divider>
            <div style={{ padding: 16, background: "#0b0c10", borderRadius: 8 }}>
              <Space direction="vertical" style={{ width: "100%" }}>
                <Text strong style={{ color: "#66fcf1" }}>Önerilen Aksiyon: <Tag color="warning">{record.recommended_decision}</Tag></Text>
                <div>
                  {record.decision_reason_codes?.map((code: string, i: number) => (
                    <div key={i}><Text type="secondary">- {code}</Text></div>
                  ))}
                </div>
              </Space>
            </div>
            <Divider orientation="left" style={{ color: "#c5c6c7" }}>Lineage (Soyağacı) Bağlantısı</Divider>
            <Space direction="vertical" style={{ width: "100%", padding: "0 16px" }}>
              <Text type="secondary">
                Bu governor kararı, override işlemi ve workflow'un nihai sonucu aynı lineage zincirinde birleştirilir.
              </Text>
              <Button type="link" onClick={() => list("governance-lineage")} style={{ padding: 0 }}>
                Bu Kararın Soyağacını Görüntüle ➜
              </Button>
            </Space>
          </Card>
        </Col>

        <Col span={8}>
          <Card title="Operatör Aksiyonları" bordered={false} style={{ background: "#1f2833", borderRadius: 8 }}>
            <Space direction="vertical" style={{ width: "100%" }} size="large">
              
              {!["HIGH", "CRITICAL"].includes(record.risk_class) && (
                <Button 
                  type="primary" 
                  block 
                  size="large"
                  icon={<SafetyOutlined />}
                  onClick={handleExecute}
                  loading={actionLoading}
                >
                  Otomatik Kararı Uygula
                </Button>
              )}

              <Divider style={{ margin: "12px 0", color: "#c5c6c7" }}>Manuel Müdahale (Override)</Divider>
              
              <div style={{ marginBottom: 16 }}>
                <Text style={{ color: "#c5c6c7", display: "block", marginBottom: 8 }}>Override Gerekçesi (Zorunlu):</Text>
                <TextArea 
                  rows={3} 
                  placeholder="En az 20 karakterlik karar gerekçesi girin..." 
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  style={{ background: "#0b0c10", color: "#66fcf1", borderColor: "#45a29e" }}
                />
              </div>

              <Popconfirm title="Emin misiniz?" onConfirm={() => handleOverride("approve")}>
                <Button block icon={<CheckCircleOutlined />} style={{ color: "#52c41a", borderColor: "#52c41a" }} loading={actionLoading} disabled={justification.length < 20}>Zorla Onayla (Force Approve)</Button>
              </Popconfirm>
              
              <Popconfirm title="Emin misiniz?" onConfirm={() => handleOverride("replay")}>
                <Button block icon={<SyncOutlined />} style={{ color: "#1890ff", borderColor: "#1890ff" }} loading={actionLoading} disabled={justification.length < 20}>Yeniden Dene (Replay)</Button>
              </Popconfirm>
              
              <Popconfirm title="Emin misiniz?" onConfirm={() => handleOverride("archive")}>
                <Button block icon={<InboxOutlined />} style={{ color: "#faad14", borderColor: "#faad14" }} loading={actionLoading} disabled={justification.length < 20}>Arşivle (Archive)</Button>
              </Popconfirm>
              
              <Popconfirm title="Emin misiniz?" onConfirm={() => handleOverride("cancel")}>
                <Button block danger icon={<StopOutlined />} loading={actionLoading} disabled={justification.length < 20}>İptal Et (Cancel)</Button>
              </Popconfirm>

              {record.project_status === "CANCELLED" && record.recommended_decision === "ARCHIVE_STALE" && (
                <>
                  <Divider style={{ margin: "12px 0", color: "#c5c6c7" }}>Geri Alma (Rollback)</Divider>
                  <Popconfirm title="24 Saatlik pencere içinde arşivi geri almak üzeresiniz. Emin misiniz?" onConfirm={handleRestore}>
                    <Button block icon={<RollbackOutlined />} style={{ color: "#e0e0e0", borderColor: "#e0e0e0" }} loading={actionLoading}>Arşivden Çıkar (Restore)</Button>
                  </Popconfirm>
                </>
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
