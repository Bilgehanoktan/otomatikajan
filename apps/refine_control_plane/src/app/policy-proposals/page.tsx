"use client";

import React from "react";
import { 
  List, 
  DateField, 
  useTable, 
  TagField,
  EditButton,
  useDrawerForm
} from "@refinedev/antd";
import { Table, Space, Card, Typography, Tag, Button, Progress, Tooltip, Drawer, Descriptions, message } from "antd";
import { useCustomMutation } from "@refinedev/core";
import FileProtectOutlined from "@ant-design/icons/lib/icons/FileProtectOutlined";
import BranchesOutlined from "@ant-design/icons/lib/icons/BranchesOutlined";
import CheckCircleOutlined from "@ant-design/icons/lib/icons/CheckCircleOutlined";
import EyeOutlined from "@ant-design/icons/lib/icons/EyeOutlined";

const { Title, Text, Paragraph } = Typography;

export default function PolicyProposalsPage() {
  const { tableProps } = useTable({
    resource: "governance/proposals",
    syncWithLocation: true,
  });

  const [detailVisible, setDetailVisible] = React.useState(false);
  const [selectedRecord, setSelectedRecord] = React.useState<any>(null);

  const { mutate } = useCustomMutation();

  const handleApprove = (id: string) => {
    mutate({
      url: `/governance/proposals/${id}/approve`,
      method: "post",
      values: {},
      successNotification: {
        message: "Onay Kaydedildi",
        description: "Politika teklifi için onayınız işlendi.",
        type: "success",
      },
    });
  };

  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>
        <FileProtectOutlined /> Anayasa Teklifleri (Policy Proposals)
      </Title>
      <Text type="secondary">
        Sistem kurallarını ve yönetişim eşiklerini güncelleyen anayasal değişiklik teklifleri.
      </Text>

      <div style={{ marginTop: "24px", marginBottom: "24px" }}>
        <Button type="primary" size="large" icon={<FileProtectOutlined />}>
          Yeni Anayasa Teklifi Oluştur
        </Button>
      </div>

      <Card title="Teklif Havuzu">
        <Table {...tableProps} rowKey="id">
          <Table.Column 
            dataIndex="title" 
            title="Başlık" 
          />
          <Table.Column 
            dataIndex="scope" 
            title="Kapsam" 
            render={(val) => <Tag color="blue">{val}</Tag>}
          />
          <Table.Column 
            dataIndex="status" 
            title="Durum" 
            render={(val) => {
              let color = "default";
              if (val === "COMMITTED") color = "success";
              if (val === "APPROVED") color = "processing";
              if (val === "PROPOSED") color = "warning";
              return <Tag color={color}>{val}</Tag>;
            }}
          />
          <Table.Column 
            title="Onay Durumu (Quorum)"
            render={() => (
              <div style={{ width: 120 }}>
                <Tooltip title="2/3 Onay Toplandı">
                  <Progress percent={66} size="small" strokeColor="#52c41a" />
                </Tooltip>
              </div>
            )}
          />
          <Table.Column 
            dataIndex="git_commit_sha" 
            title="Git İzlemi" 
            render={(val) => val ? <Text code><BranchesOutlined /> {val.substring(0, 7)}</Text> : <Text type="secondary">Henüz mühürlenmedi</Text>}
          />
          <Table.Column 
            dataIndex="created_at" 
            title="Tarih" 
            render={(val) => <DateField value={val} format="LLL" />}
          />
          <Table.Column 
            title="İşlemler"
            render={(_, record: any) => (
              <Space>
                <Button 
                  size="small" 
                  icon={<EyeOutlined />}
                  onClick={() => {
                    setSelectedRecord(record);
                    setDetailVisible(true);
                  }}
                >Detay</Button>
                <Button 
                  size="small" 
                  icon={<CheckCircleOutlined />} 
                  type="primary"
                  disabled={record.status !== "PROPOSED"}
                  onClick={() => handleApprove(record.id)}
                >Onayla</Button>
              </Space>
            )}
          />
        </Table>
      </Card>

      <Drawer
        title="Anayasa Teklifi Detayı"
        width={640}
        onClose={() => setDetailVisible(false)}
        visible={detailVisible}
      >
        {selectedRecord && (
          <Space direction="vertical" size="large" style={{ width: "100%" }}>
            <Descriptions title="Teklif Bilgileri" bordered column={1}>
              <Descriptions.Item label="Başlık">{selectedRecord.title}</Descriptions.Item>
              <Descriptions.Item label="Kapsam">{selectedRecord.scope}</Descriptions.Item>
              <Descriptions.Item label="Durum">
                <Tag color={selectedRecord.status === "COMMITTED" ? "success" : "warning"}>{selectedRecord.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Yazar">{selectedRecord.author_id}</Descriptions.Item>
              <Descriptions.Item label="Tarih">{new Date(selectedRecord.created_at).toLocaleString()}</Descriptions.Item>
            </Descriptions>

            <div>
              <Title level={5}>Açıklama</Title>
              <Paragraph>{selectedRecord.description}</Paragraph>
            </div>

            <div>
              <Title level={5}>Değişiklik Özeti (IaP)</Title>
              <Card size="small" style={{ backgroundColor: "#f5f5f5" }}>
                <pre>{JSON.stringify(selectedRecord.proposed_changes || { "msg": "Değişiklik detayı yükleniyor..." }, null, 2)}</pre>
              </Card>
            </div>

            {selectedRecord.status === "COMMITTED" && (
              <Card size="small" title="Git Origin Tracking">
                <Text type="secondary">Commit SHA:</Text>
                <Text code copyable>{selectedRecord.git_commit_sha || "5f8a2c3..."}</Text>
                <br />
                <Text type="secondary">Branch:</Text>
                <Tag icon={<BranchesOutlined />}>main</Tag>
              </Card>
            )}
            
            <Button 
               type="primary" 
               block 
               icon={<CheckCircleOutlined />}
               disabled={selectedRecord.status !== "PROPOSED"}
               onClick={() => handleApprove(selectedRecord.id)}
            >
              Kurumsal Sign-off Ver
            </Button>
          </Space>
        )}
      </Drawer>
    </div>
  );
}
