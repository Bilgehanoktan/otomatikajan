"use client";

import React from "react";
import { 
  List, 
  DateField, 
  TagField, 
  TextField, 
  useTable, 
  ShowButton
} from "@refinedev/antd";
import { Table, Space, Card, Typography, Tag, Button, Modal, Form, Input, DatePicker, message } from "antd";
import { useCustomMutation, useList } from "@refinedev/core";
import AuditOutlined from "@ant-design/icons/lib/icons/AuditOutlined";
import SafetyCertificateOutlined from "@ant-design/icons/lib/icons/SafetyCertificateOutlined";
import HistoryOutlined from "@ant-design/icons/lib/icons/HistoryOutlined";
import PlusOutlined from "@ant-design/icons/lib/icons/PlusOutlined";

const { Title, Text } = Typography;

export default function CompliancePage() {
  const { tableProps } = useTable({
    resource: "compliance-bundles", // Adjust if needed
    syncWithLocation: true,
  });

  const { data: policyData } = useList({
    resource: "compliance/policies",
  });

  const [isBundleModalVisible, setIsBundleModalVisible] = React.useState(false);
  const { mutate } = useCustomMutation();

  const handleCreateBundle = (values: any) => {
    mutate({
      url: `/compliance/audit-bundles`,
      method: "post",
      values: {
        name: values.name,
        purpose: values.purpose,
        creator: "operator_ui"
      },
      successNotification: {
        message: "Paket Oluşturuluyor",
        description: "Denetim paketi arka planda hazırlanıyor.",
        type: "success",
      },
    });
    setIsBundleModalVisible(false);
  };

  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>
        <AuditOutlined /> Uyum ve Denetim (Compliance)
      </Title>
      <Text type="secondary">
        Kurumsal ölçekli veri saklama, kanıt mühürleme ve denetim paketleri yönetimi.
      </Text>

      <div style={{ marginTop: "24px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        <Card title="Aktif Saklama Politikaları" extra={<HistoryOutlined />}>
           <Table 
             dataSource={policyData?.data || []}
             pagination={false}
             size="small"
             rowKey="id"
             columns={[
               { title: "Kategori", dataIndex: "data_category" },
               { title: "Sıcak (Hot)", dataIndex: "hot_retention_days", render: (val) => `${val} Gün` },
               { title: "Ilık (Warm)", dataIndex: "warm_retention_days", render: (val) => `${val} Gün` },
               { title: "Kalıcı?", dataIndex: "is_permanent", render: (val) => val ? <Tag color="gold">Evet</Tag> : <Tag>Hayır</Tag> },
             ]}
           />
        </Card>

        <Card title="Kanıt Bütünlük Durumu" extra={<SafetyCertificateOutlined />}>
           <div style={{ textAlign: "center", padding: "10px" }}>
             <Title level={4} style={{ color: "#52c41a" }}>99.99% Bütünlük</Title>
             <Text>Tüm otonom kararlar kriptografik olarak mühürlenmiştir.</Text>
             <div style={{ marginTop: "16px" }}>
               <Space>
                 <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsBundleModalVisible(true)}>Yeni Denetim Paketi</Button>
                 <Button>Bütünlük Taraması</Button>
               </Space>
             </div>
           </div>
        </Card>
      </div>

      <Modal
        title="Yeni Denetim Paketi Oluştur"
        visible={isBundleModalVisible}
        onCancel={() => setIsBundleModalVisible(false)}
        footer={null}
      >
        <Form layout="vertical" onFinish={handleCreateBundle}>
          <Form.Item label="Paket Adı" name="name" rules={[{ required: true }]}>
            <Input placeholder="Örn: 2024 Q1 Güvenlik Özeti" />
          </Form.Item>
          <Form.Item label="Kullanım Amacı" name="purpose" rules={[{ required: true }]}>
            <Input placeholder="Örn: Yıllık Denetim Hazırlığı" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>Paketi Mühürle</Button>
          </Form.Item>
        </Form>
      </Modal>

      <Card style={{ marginTop: "24px" }} title="Denetim Paketleri (Audit Bundles)">
        <Table {...tableProps} rowKey="id">
          <Table.Column 
            dataIndex="bundle_name" 
            title="Paket Adı" 
          />
          <Table.Column 
            dataIndex="purpose" 
            title="Kullanım Amacı" 
          />
          <Table.Column 
            dataIndex="integrity_hash" 
            title="Bütünlük Mührü" 
            render={(val) => <Text code>{val?.substring(0, 16)}...</Text>}
          />
          <Table.Column 
            dataIndex="created_at" 
            title="Oluşturulma" 
            render={(val) => <DateField value={val} format="LLL" />}
          />
          <Table.Column 
            title="İşlemler"
            render={(_, record: any) => (
              <Space>
                <Button size="small">İndir (PDF)</Button>
                <ShowButton hideText size="small" recordItemId={record.id} />
              </Space>
            )}
          />
        </Table>
      </Card>
    </div>
  );
}
