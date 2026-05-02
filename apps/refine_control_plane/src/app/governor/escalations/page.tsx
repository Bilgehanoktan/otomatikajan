"use client";

import { useTable, useCustomMutation } from "@refinedev/core";
import { Table, Tag, Button, Space, Card, Typography, Tooltip, message, Modal, Dropdown, MenuProps } from "antd";
import { SafetyOutlined, CheckCircleOutlined, InfoCircleOutlined, StopOutlined, DownOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;

export default function GovernorEscalations() {
  const { tableQueryResult } = useTable({
    resource: "governance/inbox/governor/escalations",
    syncWithLocation: true,
  }) as any;

  const { data, isLoading } = tableQueryResult;
  const escalations = data?.data || [];
  const { mutate } = useCustomMutation();

  const handleAction = (id: string, action: "ack" | "resolve" | "cancel") => {
    let payload = {};
    if (action === "resolve") {
      payload = {
        resolution_type: "manual_override",
        resolution_notes: "Çözüldü olarak işaretlendi.",
        final_action: "resolved"
      };
    }

    mutate(
      {
        url: `/governance/inbox/governor/escalations/${id}/${action}`,
        method: "post",
        values: payload,
      },
      {
        onSuccess: () => {
          message.success(`Eskalasyon durumu güncellendi: ${action}`);
          tableQueryResult.refetch();
        },
        onError: (err) => {
          message.error(`Hata: ${err.message}`);
        }
      }
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          <SafetyOutlined style={{ marginRight: 12, color: "#f5222d" }} />
          Aktif Eskalasyonlar (PRIME & Quorum)
        </Title>
      </div>

      <Card variant="borderless" style={{ borderRadius: 8, background: "#1f2833" }}>
        <Table dataSource={escalations} rowKey="id" loading={isLoading}>
          <Table.Column 
            dataIndex="project_id" 
            title="Proje ID" 
            render={(value) => <Text type="secondary" copyable>{value}</Text>}
          />
          <Table.Column 
            dataIndex="escalation_type" 
            title="Eskalasyon Tipi" 
            render={(value) => <Tag color="volcano">{value}</Tag>}
          />
          <Table.Column 
            dataIndex="target_role" 
            title="Hedef Rol" 
            render={(value) => <Tag color="purple">{value}</Tag>}
          />
          <Table.Column 
            dataIndex="reason" 
            title="Gerekçe" 
          />
          <Table.Column 
            dataIndex="created_at" 
            title="SLA / Yaş" 
            render={(value) => {
              if (!value) return "-";
              const diffMs = new Date().getTime() - new Date(value).getTime();
              const diffHrs = diffMs / (1000 * 60 * 60);
              let text = "";
              let color = "default";
              
              if (diffHrs < 1) {
                text = `${Math.round(diffMs / 60000)} dk`;
                color = "green";
              } else if (diffHrs < 24) {
                text = `${Math.round(diffHrs)} saat`;
                color = "orange";
              } else {
                text = `${Math.round(diffHrs / 24)} gün`;
                color = "red";
              }
              return <Tag color={color}>{text}</Tag>;
            }}
          />
          <Table.Column 
            dataIndex="status" 
            title="Durum" 
            render={(value) => {
              const colors: any = { "open": "warning", "acknowledged": "processing", "resolved": "success", "cancelled": "default" };
              return <Tag color={colors[value] || "default"}>{value}</Tag>;
            }}
          />
          <Table.Column
            title="Aksiyonlar"
            render={(_, record: any) => {
              const items: MenuProps['items'] = [
                {
                  key: 'ack',
                  label: 'Kabul Et (Ack)',
                  icon: <InfoCircleOutlined />,
                  onClick: () => handleAction(record.id, "ack"),
                  disabled: record.status !== "open"
                },
                {
                  key: 'resolve',
                  label: 'Çöz (Resolve)',
                  icon: <CheckCircleOutlined />,
                  onClick: () => handleAction(record.id, "resolve"),
                  disabled: !["open", "acknowledged"].includes(record.status)
                },
                {
                  key: 'cancel',
                  label: 'İptal Et (Cancel)',
                  icon: <StopOutlined />,
                  onClick: () => handleAction(record.id, "cancel"),
                  disabled: !["open", "acknowledged"].includes(record.status),
                  danger: true
                }
              ];

              return (
                <Dropdown menu={{ items }} trigger={['click']}>
                  <Button type="primary">
                    İşlem Yap <DownOutlined />
                  </Button>
                </Dropdown>
              );
            }}
          />
        </Table>
      </Card>
    </div>
  );
}
