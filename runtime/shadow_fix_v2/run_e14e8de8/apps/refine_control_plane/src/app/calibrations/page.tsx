"use client";

import React from "react";
import { useTable } from "@refinedev/antd";
import { Table, Tag, Button, Space, Card, Typography, Tooltip, message, Popconfirm, Progress } from "antd";
import { 
  ExperimentOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  UndoOutlined, 
  ThunderboltOutlined
} from "@ant-design/icons";
import { useCustomMutation } from "@refinedev/core";
import { useTranslations } from "next-intl";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import "dayjs/locale/tr";

dayjs.extend(relativeTime);
dayjs.locale("tr");

const { Title, Text, Paragraph } = Typography;

export default function GovernorCalibrations() {
  const t = useTranslations("dashboard.calibrations");
  
  const { tableProps, tableQuery } = useTable({
    resource: "governance/governor/calibrations",
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
      url: `/governance/governor/calibrations/${id}/${action}`,
      method: "post",
      values: { reason: "Operatör işlemi: " + action },
    }, {
      onSuccess: () => {
        message.success(t(`success${action.charAt(0).toUpperCase() + action.slice(1)}`));
        tableQuery.refetch();
      },
      onError: (err: any) => {
        message.error(`Hata: ${(err as any).message}`);
      }
    });
  };

  const triggerProposals = () => {
    mutate({
      url: "/governance/governor/calibrations/propose",
      method: "post",
      values: {},
    }, {
      onSuccess: (data: any) => {
        message.success(t("successPropose", { count: data.data.proposals_count }));
        tableQuery.refetch();
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

  const renderValueChange = (parameter: string, oldVal: number, newVal: number) => {
    const diff = newVal - oldVal;
    
    // Higher is better for accuracy/confidence, lower is better for latency/timeouts
    const isLowerBetter = parameter.toLowerCase().includes("latency") || 
                          parameter.toLowerCase().includes("timeout") || 
                          parameter.toLowerCase().includes("error");
    
    const isImproved = isLowerBetter ? diff < 0 : diff > 0;
    const color = isImproved ? "#52c41a" : "#ff4d4f";
    
    return (
      <Space>
        <Text delete style={{ opacity: 0.6 }}>{oldVal.toFixed(3)}</Text>
        <Text strong style={{ color }}>{newVal.toFixed(3)}</Text>
        <Text type="secondary" style={{ fontSize: 11 }}>
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
          {t("title")}
        </Title>
        <Button 
          type="primary" 
          icon={<ThunderboltOutlined />} 
          onClick={triggerProposals}
          style={{ background: "#a855f7", borderColor: "#a855f7", borderRadius: 6 }}
        >
          {t("scanButton")}
        </Button>
      </div>

      <Card variant="borderless" style={{ borderRadius: 12, background: "rgba(31, 40, 51, 0.6)", backdropFilter: "blur(10px)", border: "1px solid rgba(255,255,255,0.05)", marginBottom: 24 }}>
        <Paragraph style={{ color: "#ffffffd9", margin: 0 }}>
          {t("description")}
        </Paragraph>
      </Card>

      <Card variant="borderless" style={{ borderRadius: 12, background: "#1f2833", border: "1px solid rgba(255,255,255,0.05)", overflow: "hidden" }}>
        <Table 
          {...tableProps} 
          rowKey="id"
          pagination={{ ...tableProps.pagination, showSizeChanger: true }}
        >
          <Table.Column 
            dataIndex="parameter_name" 
            title={t("parameter")} 
            render={(value) => <Text strong style={{ color: "#66fcf1", fontSize: 13 }}>{value}</Text>}
          />
          <Table.Column 
            title={t("change")} 
            render={(_, record: any) => renderValueChange(record.parameter_name, record.old_value, record.proposed_value)}
          />
          <Table.Column 
            dataIndex="confidence_score" 
            title={t("confidence")} 
            render={(value) => (
              <Tooltip title={`Örneklem büyüklüğü bazlı güven.`}>
                <div style={{ width: 100 }}>
                  <Progress percent={Math.round(value * 100)} size="small" strokeColor="#a855f7" trailColor="rgba(255,255,255,0.05)" />
                </div>
              </Tooltip>
            )}
          />
          <Table.Column 
            dataIndex="status" 
            title={t("status")} 
            render={(value) => getStatusTag(value)}
          />
          <Table.Column 
            dataIndex="change_reason" 
            title={t("reason")} 
            render={(value) => (
              <Tooltip title={value}>
                <Text ellipsis style={{ maxWidth: 220, fontSize: 12 }}>{value}</Text>
              </Tooltip>
            )}
          />
          <Table.Column 
            dataIndex="created_at" 
            title={t("created")} 
            render={(value) => <Text type="secondary" style={{ fontSize: 11 }}>{dayjs(value).fromNow()}</Text>}
          />
          <Table.Column
            title={t("actions")}
            render={(_, record: any) => (
              <Space>
                {record.status === "PROPOSED" && (
                  <>
                    <Popconfirm title={t("confirmApprove")} onConfirm={() => handleAction(record.id, "approve")}>
                      <Button type="primary" size="small" icon={<CheckCircleOutlined />} style={{ borderRadius: 4 }}>{t("approve")}</Button>
                    </Popconfirm>
                    <Popconfirm title={t("confirmReject")} onConfirm={() => handleAction(record.id, "reject")}>
                      <Button size="small" icon={<CloseCircleOutlined />} danger style={{ borderRadius: 4 }}>{t("reject")}</Button>
                    </Popconfirm>
                  </>
                )}
                {record.status === "APPLIED" && (
                  <Popconfirm title={t("confirmRollback")} onConfirm={() => handleAction(record.id, "rollback")}>
                    <Button size="small" icon={<UndoOutlined />} style={{ borderRadius: 4 }}>{t("rollback")}</Button>
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
