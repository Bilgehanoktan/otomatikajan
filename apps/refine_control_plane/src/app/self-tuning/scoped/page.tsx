
"use client";

import React from "react";
import { 
  useTable, 
} from "@refinedev/antd";
import { Table, Card, Typography, Tag, Space, Button, Alert } from "antd";
import SettingOutlined from "@ant-design/icons/lib/icons/SettingOutlined";
import GlobalOutlined from "@ant-design/icons/lib/icons/GlobalOutlined";
import ApartmentOutlined from "@ant-design/icons/lib/icons/ApartmentOutlined";

const { Title, Text } = Typography;

export default function ScopedPoliciesPage() {
  // Mock data for Phase 30 WOW factor (In real usage, this would be a custom fetcher)
  const departments = [
    { 
      scope: "FINANCE", 
      overrides: { "budget_buffer": "15%", "approval_quorum": 3 },
      status: "Active",
      last_updated: "2024-04-15"
    },
    { 
      scope: "SECURITY", 
      overrides: { "max_retry_attempts": 2, "threat_level": "Strict" },
      status: "Active",
      last_updated: "2024-04-10"
    },
    { 
      scope: "RESEARCH", 
      overrides: { "data_isolation": "Loose" },
      status: "Draft",
      last_updated: "2024-04-16"
    }
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>
        <ApartmentOutlined /> Kapsamlı Politikalar (Scoped Policies)
      </Title>
      <Paragraph>
        Küresel anayasa (Global Constitution) üzerine giydirilen departman veya bölge bazlı kural setleri.
      </Paragraph>

      <Alert 
        message="Hiyerarşik Yönetişim Aktif" 
        description="Yerel ayarlar global kuralları ezer (override), ancak global güvenlik sınırlarını aşamaz."
        type="info"
        showIcon
        style={{ marginBottom: "24px" }}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        <Card title="Küresel Temel (Global Base)" icon={<GlobalOutlined />}>
           <Text type="secondary">Tüm birimler için geçerli varsayılan kurallar.</Text>
           <div style={{ marginTop: "16px" }}>
             <Tag color="cyan">Retainment: 90 Regular / 3y Cold</Tag>
             <Tag color="cyan">Quorum: Standard (2)</Tag>
             <Tag color="cyan">Failover: Auto</Tag>
           </div>
           <Button type="link" style={{ marginTop: "12px", padding: 0 }}>Global Anayasayı Görüntüle</Button>
        </Card>

        <Card title="Overlay Katmanları" icon={<SettingOutlined />}>
           <Table 
             dataSource={departments}
             pagination={false}
             size="small"
             columns={[
               { title: "Kapsam", dataIndex: "scope", render: (v) => <Tag color="geekblue">{v}</Tag> },
               { title: "Değişiklik Sayısı", dataIndex: "overrides", render: (v) => Object.keys(v).length },
               { title: "Durum", dataIndex: "status", render: (v) => <Tag color={v === "Active" ? "success" : "warning"}>{v}</Tag> },
               { title: "İşlem", render: () => <Button size="small">Düzenle</Button> }
             ]}
           />
        </Card>
      </div>

      <Title level={4} style={{ marginTop: "32px" }}>Aktif Overlay Detayları</Title>
      {departments.map((dept) => (
        <Card size="small" style={{ marginBottom: "16px" }} key={dept.scope}>
          <Space direction="vertical" style={{ width: "100%" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
               <Title level={5}>{dept.scope} OVERLAY</Title>
               <Text type="secondary">Görünüm: YAML</Text>
            </div>
            <Card size="small" style={{ backgroundColor: "#1e1e1e", color: "#d4d4d4" }}>
               <pre style={{ marginBottom: 0 }}>{JSON.stringify(dept.overrides, null, 2)}</pre>
            </Card>
          </Space>
        </Card>
      ))}
    </div>
  );
}
