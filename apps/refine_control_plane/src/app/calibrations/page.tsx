"use client";

import React from "react";
import { useTable, useImport } from "@refinedev/antd";
import { Table, Tag, Button, Space, Card, Typography, Tooltip, message, Popconfirm, Progress } from "antd";
import { 
  ExperimentOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  UndoOutlined, 
  ThunderboltOutlined,
  InfoCircleOutlined
} from "@ant-design/icons";
import { useCustomMutation, useCustom } from "@refinedev/core";
import dayjs from "dayjs";

const { Title, Text, Paragraph } = Typography;

export default function GovernorCalibrations() {
  const { tableProps, tableQueryResult } = useTable({
    resource: "governance/inbox/governor/calibrations",
    syncWithLocation: true,
    pagination: {
      pageSize: 20,
    },
    sorters: {
      initial: [{ field: "created_at", order: "desc" }],
    },
  }) as any;

  const { mutate } = useCustomMutation();

  const handleAction = (id: string, action: string) => {
    mutate({
      url: `/governance/inbox/governor/calibrations/${id}/${action}`,
      method: "post",
      values: { reason: "Operatör işlemi: " + action },
    }, {
      onSuccess: () => {
        message.success(`Kalibrasyon ${action} işlemi başarılı.`);
        tableQueryResult.refetch();
      },
      onError: (err: any) => {
        message.error(`Hata: ${err.message}`);
      }
    });
  };

  const triggerProposals = () => {
    mutate({
      url: "/governance/inbox/governor/calibrations/propose",
      method: "post",
      values: {},
    }, {
      onSuccess: (data: any) => {
        message.success(`${data.data.proposals_count} yeni kalibrasyon önerisi oluşturuldu.`);
        tableQueryResult.refetch();
      }
    });
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case "PROPOSED": return <Tag color="blue">ÖNERİ</Tag>;
      case "APPLIED": return <Tag color="green">UYGULANDI</Tag>;
      case "REJECTED": return <Tag color="red">REDDEDİLDİ</Tag>;
      case "ROLLED_BACK": return <Tag color="orange">GERİ ALINDI</Tag>;
      default: return <Tag>{status}</Tag>;
    }
  };

  const renderValueChange = (oldVal: number, newVal: number) => {
    const diff = newVal - oldVal;
    const color = diff > 0 ? "#52c41a" : "#ff4d4f";
    return (
      <Space>
        <Text delete>{oldVal.toFixed(3)}</Text>
        <Text strong style={{ color }}>{newVal.toFixed(3)}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          ({diff > 0 ? "+" : ""}{diff.toFixed(3)})
        </Text>
      </Space>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          <ExperimentOutlined style={{ marginRight: 12, color: "#a855f7" }} />
          Adaptive Threshold Governance
        </Title>
        <Button 
          type="primary" 
          icon={<ThunderboltOutlined />} 
          onClick={triggerProposals}
          style={{ background: "#a855f7", borderColor: "#a855f7" }}
        >
          Yeni Kalibrasyon Tara
        </Button>
      </div>

      <Card variant="borderless" style={{ borderRadius: 8, background: "#1f2833", marginBottom: 24 }}>
        <Paragraph style={{ color: "#ffffffa6" }}>
          Governor, geçmiş karar performansını (accuracy, latency, operator agreement) analiz ederek kendi eşik değerlerini (threshold) optimize eder. 
          Önerilen değişiklikler <b>PROPOSED</b> olarak düşer ve operatör onayıyla <b>APPLIED</b> durumuna geçer.
        </Paragraph>
      </Card>

      <Card variant="borderless" style={{ borderRadius: 8, background: "#1f2833" }}>
        <Table 
          {...tableProps} 
          rowKey="id"
        >
          <Table.Column 
            dataIndex="parameter_name" 
            title="Parametre" 
            render={(value) => <Text strong style={{ color: "#66fcf1" }}>{value}</Text>}
          />
          <Table.Column 
            title="Değişim (Old → New)" 
            render={(_, record: any) => renderValueChange(record.old_value, record.proposed_value)}
          />
          <Table.Column 
            dataIndex="confidence_score" 
            title="Güven Puanı" 
            render={(value) => (
              <Tooltip title={`Örneklem büyüklüğü bazlı güven.`}>
                <Progress percent={Math.round(value * 100)} size="small" strokeColor="#a855f7" />
              </Tooltip>
            )}
          />
          <Table.Column 
            dataIndex="status" 
            title="Durum" 
            render={(value) => getStatusTag(value)}
          />
          <Table.Column 
            dataIndex="change_reason" 
            title="Gerekçe" 
            render={(value) => (
              <Tooltip title={value}>
                <Text ellipsis style={{ maxWidth: 200 }}>{value}</Text>
              </Tooltip>
            )}
          />
          <Table.Column 
            dataIndex="created_at" 
            title="Oluşturulma" 
            render={(value) => <Text type="secondary" style={{ fontSize: 12 }}>{dayjs(value).fromNow()}</Text>}
          />
          <Table.Column
            title="Aksiyonlar"
            render={(_, record: any) => (
              <Space>
                {record.status === "PROPOSED" && (
                  <>
                    <Popconfirm title="Bu kalibrasyonu onaylıyor musunuz?" onConfirm={() => handleAction(record.id, "approve")}>
                      <Button type="primary" size="small" icon={<CheckCircleOutlined />}>Onayla</Button>
                    </Popconfirm>
                    <Popconfirm title="Bu kalibrasyonu reddetmek istediğinize emin misiniz?" onConfirm={() => handleAction(record.id, "reject")}>
                      <Button size="small" icon={<CloseCircleOutlined />} danger>Reddet</Button>
                    </Popconfirm>
                  </>
                )}
                {record.status === "APPLIED" && (
                  <Popconfirm title="Değişikliği geri almak istiyor musunuz?" onConfirm={() => handleAction(record.id, "rollback")}>
                    <Button size="small" icon={<UndoOutlined />}>Geri Al</Button>
                  </Popconfirm>
                )}
              </Space>
            )}
          />
        </Table>
      </Card>
    </div>
  );
}
