"use client";

import React from "react";
import { List, useTable } from "@refinedev/antd";
import { Table, Tag, Space, Typography, Card, Button, Modal, notification, Alert } from "antd";
import { 
  ExperimentOutlined, 
  SafetyCertificateOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined
} from "@ant-design/icons";
import { useCustomMutation } from "@refinedev/core";

const { Text, Title, Paragraph } = Typography;

export default function AdaptationCandidatesPage() {
  const { tableProps } = useTable({
    resource: "learning/adaptation-candidates",
  });

  const { mutate } = useCustomMutation();

  const handlePromote = (id: string, name: string) => {
    Modal.confirm({
      title: "Strateji Terfisi Onayı",
      content: (
        <div>
          <Paragraph>
            <Text className="text-[#66fcf1] font-bold">{name}</Text> stratejisi, istatistiksel başarı eşiklerini geçerek terfi adayı olmuştur.
          </Paragraph>
          <Paragraph>
            Onaylamanız durumunda, bu strateji <Text strong>Otonom Tam Yetkili</Text> moduna geçecek ve Governance katmanında öncelikli hale gelecektir.
          </Paragraph>
          <Alert
            message="Kritik İşlem"
            description="Bu işlem denetim soyağacına (Lineage) işlenecek ve geri alınması manuel müdahale gerektirecektir."
            type="warning"
            showIcon
          />
        </div>
      ),
      okText: "Terfi Ettir",
      cancelText: "İptal",
      okButtonProps: { className: "bg-[#66fcf1] text-black border-none hover:bg-[#45a29e]" },
      onOk: () => {
        mutate({
          url: `/learning/promote-strategy/${id}`,
          method: "post",
          values: {},
        }, {
          onSuccess: () => {
            notification.success({
              message: "Başarılı",
              description: `${name} stratejisi başarıyla terfi ettirildi.`,
              placement: "topRight",
            });
          },
        });
      },
    });
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2} className="!text-[#66fcf1] !mb-0 flex items-center gap-3">
          <ExperimentOutlined /> Adaptasyon Adayları
        </Title>
        <Text className="text-gray-400">
          Sistem performansı ve istatistiksel veriler ışığında otonomi seviyesi yükseltilmeye aday stratejiler.
        </Text>
      </div>

      <List
        title={
          <div className="flex items-center gap-2">
            <ThunderboltOutlined className="text-[#66fcf1]" />
            <span className="text-[#66fcf1] font-bold">Önerilen Sistem Güncellemeleri</span>
          </div>
        }
      >
        <Table {...tableProps} rowKey="id" className="custom-table">
          <Table.Column
            dataIndex="strategy_name"
            title="Strateji"
            render={(value) => <Text className="text-[#66fcf1] font-bold">{value}</Text>}
          />
          <Table.Column
            dataIndex="trust_score"
            title="Sinyal Gücü"
            render={(value) => (
              <Tag color="cyan" className="font-mono">
                {(value * 100).toFixed(1)}%
              </Tag>
            )}
          />
          <Table.Column
            title="Performans Metrikleri"
            render={(_, record: any) => (
              <div className="flex gap-4">
                <div>
                  <Text className="text-gray-500 block text-[10px]">SUCCESS RATE</Text>
                  <Text className="text-green-400 font-bold">
                    {((record.success_count / record.total_runs) * 100).toFixed(1)}%
                  </Text>
                </div>
                <div>
                  <Text className="text-gray-500 block text-[10px]">TOTAL RUNS</Text>
                  <Text className="text-[#c5c6c7] font-bold">{record.total_runs}</Text>
                </div>
              </div>
            )}
          />
          <Table.Column
            dataIndex="state"
            title="Mevcut Durum"
            render={(value) => <Tag color="blue">{value?.toUpperCase()}</Tag>}
          />
          <Table.Column
            title="İşlemler"
            dataIndex="id"
            render={(id, record: any) => (
              <Button 
                type="primary" 
                icon={<SafetyCertificateOutlined />}
                onClick={() => handlePromote(id, record.strategy_name)}
                className="bg-[#66fcf1] text-black border-none hover:bg-[#45a29e]"
              >
                Terfi Onayı
              </Button>
            )}
          />
        </Table>
      </List>

      <style jsx global>{`
        .custom-table .ant-table {
          background: #1a1c22 !important;
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
        .custom-table .ant-table-tbody > tr:hover > td {
          background: #23272e !important;
        }
        .ant-modal-content {
          background-color: #1a1c22 !important;
          border: 1px solid #30363d !important;
        }
        .ant-modal-header {
          background-color: #1a1c22 !important;
          border-bottom: 1px solid #30363d !important;
        }
        .ant-modal-title {
          color: #66fcf1 !important;
        }
        .ant-modal-close {
          color: #c5c6c7 !important;
        }
      `}</style>
    </div>
  );
}
