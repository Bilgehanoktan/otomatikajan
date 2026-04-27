"use client";

import React from "react";
import { Card, Button, Row, Col, Typography, Space, App, Alert, Tooltip } from "antd";
import { 
  SyncOutlined, 
  PauseCircleOutlined, 
  PlayCircleOutlined, 
  SafetyOutlined,
  ReloadOutlined,
  InfoCircleOutlined
} from "@ant-design/icons";
import { useCustomMutation } from "@refinedev/core";

const { Title, Text } = Typography;

export default function FleetOperationsPage() {
  const { notification } = App.useApp();
  const { mutate, isPending } = useCustomMutation();

  const handleAction = (action: string, endpoint: string, method: "post" | "patch" = "post") => {
    mutate({
      url: `http://127.0.0.1:8000/api/v1/fleet${endpoint}`,
      method,
      values: {},
    }, {
      onSuccess: () => {
        notification.success({
          message: "İşlem Başarılı",
          description: `${action} başarıyla tetiklendi.`,
        });
      },
      onError: (error: any) => {
        notification.error({
          message: "İşlem Başarısız",
          description: `Hata: ${error.message || "Bilinmeyen hata (Endpoint mevcut olmayabilir)"}`,
        });
      }
    });
  };

  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>Filo Operasyonları</Title>
      <Text type="secondary">Manuel müdahale ve sistem genelinde orkestrasyon kontrolleri.</Text>

      <Alert 
        message="Dikkat: Bu sayfadaki işlemler tüm filoyu etkileyen otonom süreçleri tetikler." 
        type="warning" 
        showIcon 
        style={{ marginTop: '24px' }}
      />

      <Row gutter={[16, 16]} style={{ marginTop: "24px" }}>
        <Col span={12}>
          <Card title="Sistem Genelinde Kontroller">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                block 
                type="primary"
                icon={<SyncOutlined spin={isPending} />} 
                onClick={() => handleAction("Yeniden Dengeleme", "/rebalance")}
                disabled={isPending}
              >
                Filo Yükünü Yeniden Dengeler (Rebalance)
              </Button>
              
              <Tooltip title="Bu özellik mevcut backend versiyonunda henüz aktif değildir.">
                <Button 
                  block 
                  icon={<ReloadOutlined />} 
                  disabled
                >
                  Cluster Kurtarma (Pasif)
                </Button>
              </Tooltip>
            </Space>
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Acil Durum Kontrolleri">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Tooltip title="Tüm projeleri duraklatma özelliği backend'e eklenmelidir. Şu an için projeler üzerinden tekil duraklatma yapılabilir.">
                <Button 
                  block 
                  danger 
                  icon={<PauseCircleOutlined />} 
                  disabled
                >
                  Tümünü Duraklat (Pasif)
                </Button>
              </Tooltip>

              <Tooltip title="Tüm projeleri devam ettirme özelliği backend'e eklenmelidir.">
                <Button 
                  block 
                  icon={<PlayCircleOutlined />} 
                  disabled
                >
                  Tümünü Devam Ettir (Pasif)
                </Button>
              </Tooltip>

              <Tooltip title="Ajan sağlığı taraması otonom olarak arka planda çalışmaktadır, manuel tetikleme henüz desteklenmemektedir.">
                <Button 
                  block 
                  icon={<SafetyOutlined />} 
                  disabled
                >
                  Toplu Karantina Taraması (Pasif)
                </Button>
              </Tooltip>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: '24px' }} title={<span><InfoCircleOutlined /> Operasyonel Notlar</span>}>
        <ul style={{ paddingLeft: '20px' }}>
          <li><Text type="secondary"><b>Rebalance:</b> FleetScheduler üzerinden aktif yük dağılımını optimize eder.</Text></li>
          <li><Text type="secondary"><b>Tekil İşlemler:</b> Ajan karantinası veya proje duraklatma işlemleri için ilgili detay sayfalarını kullanın.</Text></li>
          <li><Text type="secondary"><b>Audit Trail:</b> Bu sayfada yapılan tüm işlemler Governance loglarına kaydedilir.</Text></li>
        </ul>
      </Card>
    </div>
  );
}
