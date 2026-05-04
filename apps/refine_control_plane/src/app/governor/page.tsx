"use client";

import React, { useState } from "react";
import { useTable } from "@refinedev/antd";
import { Table, Tag, Button, Space, Card, Typography, Tooltip, message, Popconfirm, Row, Col, Statistic } from "antd";
import { SearchOutlined, SafetyOutlined, ClockCircleOutlined, ExclamationCircleOutlined, CheckCircleOutlined, InboxOutlined, SyncOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { useNavigation, useCustomMutation } from "@refinedev/core";
import { useTranslations } from "next-intl";

const { Title, Text } = Typography;

export default function GovernorInbox() {
  const t = useTranslations("dashboard");
  const { tableProps, tableQueryResult } = useTable({
    resource: "governance/inbox/governor/cases",
    syncWithLocation: true,
    pagination: {
      pageSize: 50,
    },
    sorters: {
      initial: [{ field: "updated_at", order: "desc" }],
    },
  }) as any;

  const { show } = useNavigation();
  const { mutate } = useCustomMutation();
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const handleBulkAction = (action: string) => {
    if (selectedRowKeys.length === 0) return;
    
    const promises = selectedRowKeys.map((id) => 
      new Promise((resolve, reject) => {
        mutate(
          {
            url: `/governance/inbox/governor/cases/${String(id)}/override`,
            method: "post",
            values: { action, reason: "Toplu işlem: " + action },
          },
          { onSuccess: resolve, onError: reject }
        );
      })
    );

    Promise.all(promises).then(() => {
      message.success(`${selectedRowKeys.length} case için '${action}' uygulandı.`);
      setSelectedRowKeys([]);
      tableQueryResult.refetch();
    }).catch((err) => {
      message.error("Toplu işlem sırasında hata oluştu: " + err.message);
    });
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "LOW": return "green";
      case "MEDIUM": return "orange";
      case "HIGH": return "volcano";
      case "CRITICAL": return "red";
      default: return "default";
    }
  };

  const getActionColor = (action: string) => {
    if (action.includes("APPROVE")) return "success";
    if (action.includes("REPLAY")) return "processing";
    if (action.includes("ARCHIVE")) return "default";
    if (action.includes("REQUIRES") || action.includes("OVERRIDE")) return "warning";
    return "default";
  };

  const isExecuted = (action: string) => {
    return action.includes("OVERRIDE_") || ["AUTO_APPROVE_CANDIDATE", "AUTO_REPLAY_CANDIDATE", "ARCHIVE_STALE"].includes(action);
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          <SafetyOutlined style={{ marginRight: 12, color: "#66fcf1" }} />
          Governor Inbox
        </Title>
        <Space>
          <Button 
            icon={<CheckCircleOutlined />} 
            disabled={selectedRowKeys.length === 0}
            onClick={() => handleBulkAction("approve")}
          >
            {t("governance.approveSelected", { defaultMessage: "Seçilenleri Onayla" })}
          </Button>
          <Button 
            icon={<SyncOutlined />} 
            disabled={selectedRowKeys.length === 0}
            onClick={() => handleBulkAction("replay")}
          >
            {t("governance.replaySelected", { defaultMessage: "Seçilenleri Yeniden Dene" })}
          </Button>
          <Button 
            danger 
            icon={<InboxOutlined />} 
            disabled={selectedRowKeys.length === 0}
            onClick={() => handleBulkAction("archive")}
          >
            {t("governance.archiveSelected", { defaultMessage: "Seçilenleri Arşivle" })}
          </Button>
          <Button 
            icon={<SyncOutlined />} 
            onClick={() => tableQueryResult.refetch()}
          >
            {t("governance.refresh", { defaultMessage: "Yenile" })}
          </Button>
        </Space>
      </div>

      <Row gutter={16} style={{ marginBottom: "24px" }}>
        <Col span={6}>
          <Card size="small" style={{ borderRadius: "8px", borderLeft: "4px solid #ff4d4f" }} hoverable>
            <Statistic 
              title={<Text type="secondary" style={{ fontSize: "12px" }}>{t("governance.openAlerts", { defaultMessage: "OPEN ALERTS" })}</Text>}
              value={3} 
              valueStyle={{ color: '#cf1322', fontWeight: 'bold' }}
              prefix={<ExclamationCircleOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ borderRadius: "8px", borderLeft: "4px solid #faad14" }} hoverable>
            <Statistic 
              title={<Text type="secondary" style={{ fontSize: "12px" }}>{t("governance.activeDrifts", { defaultMessage: "ACTIVE DRIFTS" })}</Text>}
              value={1} 
              valueStyle={{ color: '#d48806', fontWeight: 'bold' }}
              prefix={<SyncOutlined spin />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ borderRadius: "8px", borderLeft: "4px solid #1890ff" }} hoverable>
            <Statistic 
              title={<Text type="secondary" style={{ fontSize: "12px" }}>{t("governance.lastBreach", { defaultMessage: "LAST BREACH" })}</Text>}
              value={t("governance.none", { defaultMessage: "None" })} 
              valueStyle={{ color: '#3f8600', fontSize: '16px', fontWeight: 'bold' }}
              prefix={<CheckCircleOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ borderRadius: "8px", borderLeft: "4px solid #52c41a" }} hoverable>
            <Statistic 
              title={<Text type="secondary" style={{ fontSize: "12px" }}>{t("governance.accuracy", { defaultMessage: "ACCURACY (1h)" })}</Text>}
              value={96.4} 
              precision={1}
              suffix="%"
              valueStyle={{ color: '#3f8600', fontWeight: 'bold' }}
              prefix={<SafetyCertificateOutlined />} 
            />
          </Card>
        </Col>
      </Row>

      <Card variant="borderless" style={{ borderRadius: 8, background: "#1f2833" }}>
        <Table 
          {...tableProps} 
          rowKey="id" 
          pagination={{...tableProps.pagination, showSizeChanger: true}}
          rowSelection={rowSelection}
        >
          <Table.Column 
            dataIndex="project_title" 
            title={t("governance.projectAction", { defaultMessage: "Proje / İşlem" })} 
            render={(value, record: any) => (
              <Space direction="vertical" size={0}>
                <Text strong>{value}</Text>
                <Text type="secondary" style={{ fontSize: 12 }}>{record.project_id}</Text>
              </Space>
            )}
          />
          <Table.Column 
            dataIndex="risk_class" 
            title={t("governance.riskScore", { defaultMessage: "Risk / Skor" })} 
            render={(value, record: any) => (
              <Space direction="vertical" size={0}>
                <Tag color={getRiskColor(value)}>{value}</Tag>
                <Text type="secondary" style={{ fontSize: 12 }}>Skor: {record.risk_score}</Text>
              </Space>
            )}
          />
          <Table.Column 
            dataIndex="pending_reason" 
            title={t("governance.waitReason", { defaultMessage: "Bekleme Nedeni" })} 
            render={(value) => <Tag color="default">{value}</Tag>}
          />
          <Table.Column 
            dataIndex="recommended_decision" 
            title={t("governance.decisionSummary", { defaultMessage: "Karar Özeti" })} 
            render={(value, record: any) => (
              <Space direction="vertical" size={2}>
                <Space>
                  <Tag color={getActionColor(value)}>{value}</Tag>
                  {isExecuted(value) ? (
                    <Tag color="success">Uygulandı</Tag>
                  ) : (
                    <Tag color="processing">Öneri</Tag>
                  )}
                </Space>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: 4 }}>
                  {record.decision_reason_codes?.slice(0, 2).map((code: string, i: number) => {
                    let shortCode = code;
                    if (code.includes("Açık incident")) shortCode = "OPEN_INCIDENT";
                    else if (code.includes("saattir bekliyor")) shortCode = "STALE>24H";
                    else if (code.includes("Retry")) shortCode = "RETRY_USED";
                    else if (shortCode.length > 20) shortCode = shortCode.substring(0, 20) + "...";
                    return <Tag key={i} color="default" style={{ fontSize: 10 }}>{shortCode}</Tag>;
                  })}
                </div>
              </Space>
            )}
          />
          <Table.Column 
            title={t("governance.context", { defaultMessage: "Bağlam" })} 
            render={(_, record: any) => (
              <Space>
                {record.has_open_incident && (
                  <Tooltip title="Açık Olay Var">
                    <ExclamationCircleOutlined style={{ color: "#faad14" }} />
                  </Tooltip>
                )}
                {record.requires_prime && (
                  <Tooltip title="PRIME Onayı Gerekli">
                    <SafetyOutlined style={{ color: "#f5222d" }} />
                  </Tooltip>
                )}
                {record.stale_seconds > 86400 && (
                  <Tooltip title="Çok Eski (>24s)">
                    <ClockCircleOutlined style={{ color: "#d4b895" }} />
                  </Tooltip>
                )}
              </Space>
            )}
          />
          <Table.Column
            title={t("governance.actions", { defaultMessage: "Aksiyonlar" })}
            dataIndex="actions"
            render={(_, record: any) => (
              <Button 
                type="primary" 
                icon={<SearchOutlined />}
                  onClick={() => show("governance/inbox/governor/cases", record.id)}
              >
                {t("governance.review", { defaultMessage: "İncele" })}
              </Button>
            )}
          />
        </Table>
      </Card>
    </div>
  );
}
