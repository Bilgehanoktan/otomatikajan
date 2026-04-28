"use client";

import React from "react";
import { Card, Button, Row, Col, Typography, Space, App, Alert, Tooltip } from "antd";
import {
  SyncOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  SafetyOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
} from "@ant-design/icons";
import { useApiUrl, useCustomMutation } from "@refinedev/core";

const { Title, Text } = Typography;

export default function FleetOperationsPage() {
  const apiUrl = useApiUrl();
  const { notification } = App.useApp();
  const { mutate, isLoading: isPending } = useCustomMutation() as any;

  const handleAction = (
    action: string,
    endpoint: string,
    method: "post" | "patch" = "post",
  ) => {
    mutate(
      {
        url: `${apiUrl}/fleet${endpoint}`,
        method,
        values: {},
      },
      {
        onSuccess: () => {
          notification.success({
            message: "İşlem Başarılı",
            description: `${action} başarıyla tetiklendi.`,
          });
        },
        onError: (error: { message?: string }) => {
          notification.error({
            message: "İşlem Başarısız",
            description: `Hata: ${error.message || "Bilinmeyen hata (endpoint mevcut olmayabilir)"}`,
          });
        },
      },
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>Filo Operasyonları</Title>
      <Text type="secondary">Manuel müdahale ve sistem genelinde orkestrasyon kontrolleri.</Text>

      <Alert
        message="Dikkat: Bu sayfadaki işlemler tüm filoyu etkileyen otonom süreçleri tetikler."
        type="warning"
        showIcon
        style={{ marginTop: 24 }}
      />

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="Sistem Genelinde Kontroller">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Button
                block
                type="primary"
                icon={<SyncOutlined spin={isPending} />}
                onClick={() => handleAction("Yeniden dengeleme", "/rebalance")}
                disabled={isPending}
              >
                Filo yükünü yeniden dengeler (Rebalance)
              </Button>

              <Tooltip title="Bu özellik mevcut backend sürümünde henüz aktif değildir.">
                <Button block icon={<ReloadOutlined />} disabled>
                  Küme kurtarma (pasif)
                </Button>
              </Tooltip>
            </Space>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Acil Durum Kontrolleri">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Tooltip title="Tüm projeleri duraklatma özelliği backend'e eklenmelidir. Şu an için projeler üzerinden tekil duraklatma yapılabilir.">
                <Button block danger icon={<PauseCircleOutlined />} disabled>
                  Tümünü duraklat (pasif)
                </Button>
              </Tooltip>

              <Tooltip title="Tüm projeleri devam ettirme özelliği backend'e eklenmelidir.">
                <Button block icon={<PlayCircleOutlined />} disabled>
                  Tümünü devam ettir (pasif)
                </Button>
              </Tooltip>

              <Tooltip title="Ajan sağlığı taraması arka planda otonom çalışır. Manuel tetikleme henüz desteklenmemektedir.">
                <Button block icon={<SafetyOutlined />} disabled>
                  Toplu karantina taraması (pasif)
                </Button>
              </Tooltip>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card
        style={{ marginTop: 24 }}
        title={
          <span>
            <InfoCircleOutlined /> Operasyonel Notlar
          </span>
        }
      >
        <ul style={{ paddingLeft: 20 }}>
          <li>
            <Text type="secondary">
              <b>Rebalance:</b> FleetScheduler üzerinden aktif yük dağılımını optimize eder.
            </Text>
          </li>
          <li>
            <Text type="secondary">
              <b>Tekil işlemler:</b> Ajan karantinası veya proje duraklatma işlemleri için ilgili detay sayfalarını kullanın.
            </Text>
          </li>
          <li>
            <Text type="secondary">
              <b>Audit trail:</b> Bu sayfada yapılan tüm işlemler governance loglarına kaydedilir.
            </Text>
          </li>
        </ul>
      </Card>
    </div>
  );
}
