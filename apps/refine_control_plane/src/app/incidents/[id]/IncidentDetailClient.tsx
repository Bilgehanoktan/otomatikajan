"use client";

import React from "react";
import { App, Alert, Button, Card, Col, Divider, Input, Row, Space, Statistic, Tag, Timeline, Typography } from "antd";
import ArrowLeftOutlined from "@ant-design/icons/lib/icons/ArrowLeftOutlined";
import BranchesOutlined from "@ant-design/icons/lib/icons/BranchesOutlined";
import CheckCircleOutlined from "@ant-design/icons/lib/icons/CheckCircleOutlined";
import DeploymentUnitOutlined from "@ant-design/icons/lib/icons/DeploymentUnitOutlined";
import HistoryOutlined from "@ant-design/icons/lib/icons/HistoryOutlined";
import NodeIndexOutlined from "@ant-design/icons/lib/icons/NodeIndexOutlined";
import ToolOutlined from "@ant-design/icons/lib/icons/ToolOutlined";
import WarningOutlined from "@ant-design/icons/lib/icons/WarningOutlined";
import { safeFetchJson } from "@/lib/api";

const { Title, Text, Paragraph } = Typography;

interface Incident {
    id: string;
    incident_type: string;
    status: string;
    severity: string;
    message: string;
    project_id?: string | null;
    created_at?: string | null;
    resolved_at?: string | null;
    payload?: Record<string, unknown> | null;
    trace?: string | Record<string, unknown> | null;
}

type IncidentDetailClientProps = {
    id: string;
};

export default function IncidentDetailClient({ id }: IncidentDetailClientProps) {
    const { notification } = App.useApp();
    const [isClient, setIsClient] = React.useState(false);
    const [incident, setIncident] = React.useState<Incident | null>(null);
    const [isLoading, setIsLoading] = React.useState(true);
    const [isError, setIsError] = React.useState(false);
    const [isSubmitting, setIsSubmitting] = React.useState(false);

    React.useEffect(() => setIsClient(true), []);

    const apiBase = React.useMemo(() => {
        if (typeof window === "undefined") {
            return "http://127.0.0.1:8000/api/v1";
        }
        return `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;
    }, []);

    const getAuthHeaders = React.useCallback(async () => {
        const tokenKey = "sqv_access_token";
        const cached = typeof window !== "undefined" ? window.localStorage.getItem(tokenKey) : null;

        if (cached) {
            return { Authorization: `Bearer ${cached}` };
        }

        if (process.env.NODE_ENV === "development") {
            const auto = await fetch(`${apiBase}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ email: "admin@sovereign.agi", password: "admin1234" }),
            });

            if (auto.ok) {
                const payload = await auto.json();
                const token = payload?.access_token as string | undefined;
                if (token && typeof window !== "undefined") {
                    window.localStorage.setItem(tokenKey, token);
                    return { Authorization: `Bearer ${token}` };
                }
            }
        }

        return {};
    }, [apiBase]);

    const loadIncident = React.useCallback(async () => {
        if (!id || id === "index") {
            setIncident(null);
            setIsLoading(false);
            setIsError(true);
            return;
        }

        setIsLoading(true);
        setIsError(false);

        try {
            const authHeaders = await getAuthHeaders();
            const response = await safeFetchJson<Incident>(`${apiBase}/incidents/${id}`, {
                headers: authHeaders,
            });
            setIncident(response);
        } catch {
            setIsError(true);
            setIncident(null);
        } finally {
            setIsLoading(false);
        }
    }, [apiBase, getAuthHeaders, id]);

    React.useEffect(() => {
        if (!isClient) return;
        void loadIncident();
    }, [isClient, loadIncident]);

    const handleResolve = React.useCallback(async () => {
        if (!incident) return;

        const notes = (document.getElementById("resolution-notes") as HTMLTextAreaElement | null)?.value?.trim() || "Manually resolved";
        setIsSubmitting(true);

        try {
            const authHeaders = await getAuthHeaders();
            const response = await safeFetchJson<Incident>(`${apiBase}/incidents/${incident.id}`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    ...authHeaders,
                },
                body: JSON.stringify({
                    status: "resolved",
                    resolution_notes: notes,
                }),
            });

            setIncident(response);
            notification.success({
                message: "Olay çözüldü",
                description: "Kayıt resolved durumuna geçirildi.",
            });
        } catch (err) {
            notification.error({
                message: "Aksiyon uygulanamadı",
                description: err instanceof Error ? err.message : "API ile iletişim kurulamadı.",
            });
        } finally {
            setIsSubmitting(false);
        }
    }, [apiBase, getAuthHeaders, incident, notification]);

    if (!isClient) {
        return <div className="min-h-screen bg-[#060a12]" />;
    }

    if (isLoading) {
        return <Card loading />;
    }

    if (isError || !incident) {
        return (
            <Alert
                message="Kayıt bulunamadı"
                description="Incident kaydı yüklenemedi ya da temizlenmiş olabilir. Audit ledger üzerinden geçmiş logları kontrol edebilirsiniz."
                type="error"
                showIcon
                action={
                    <Button size="small" type="primary" onClick={() => window.history.back()}>
                        Geri Dön
                    </Button>
                }
            />
        );
    }

    const getSeverityTag = (severity: string) => {
        const normalized = (severity || "unknown").toUpperCase();
        switch (normalized) {
            case "CRITICAL":
                return <Tag color="error" style={{ fontWeight: 800 }}>CRITICAL</Tag>;
            case "HIGH":
                return <Tag color="volcano" style={{ fontWeight: 800 }}>HIGH</Tag>;
            case "MEDIUM":
                return <Tag color="warning" style={{ fontWeight: 800 }}>MEDIUM</Tag>;
            case "LOW":
                return <Tag color="blue" style={{ fontWeight: 800 }}>LOW</Tag>;
            default:
                return <Tag>{normalized}</Tag>;
        }
    };

    return (
        <div style={{ padding: "24px" }}>
            <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => window.history.back()}
                style={{ marginBottom: "16px", background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "#aaa" }}
            >
                Incident Akışına Dön
            </Button>

            <Card variant="borderless" style={{ background: "linear-gradient(90deg, rgba(20,10,10,0.8) 0%, rgba(30,20,20,0.4) 100%)", borderRadius: "12px", border: "1px solid rgba(255, 77, 79, 0.15)", marginBottom: "20px" }}>
                <Row gutter={16} align="middle">
                    <Col span={8}>
                        <div style={{ paddingLeft: "10px" }}>
                            <Text type="secondary" style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>Anomali Kaydı</Text>
                            <Title level={3} style={{ color: "#fff", margin: 0, fontWeight: 900 }}>{incident.incident_type || "System Anomaly"}</Title>
                            <Space style={{ marginTop: "4px" }}>
                                {getSeverityTag(incident.severity)}
                                <Tag color={incident.status === "resolved" ? "success" : "processing"}>
                                    {incident.status ? incident.status.toUpperCase() : "OPEN"}
                                </Tag>
                            </Space>
                        </div>
                    </Col>
                    <Col span={4}>
                        <Statistic
                            title={<span style={{ color: "#ff7875", fontSize: "10px" }}>ETKİ ALANI</span>}
                            value={incident.project_id ? "PROJECT-SCOPE" : "SYSTEM-WIDE"}
                            valueStyle={{ color: "#fff", fontSize: "16px", fontWeight: "bold" }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic
                            title={<span style={{ color: "#ff7875", fontSize: "10px" }}>BİLDİREN</span>}
                            value="CORTEX-V13"
                            valueStyle={{ color: "#aaa", fontSize: "16px", fontFamily: "monospace" }}
                        />
                    </Col>
                    <Col span={8} style={{ textAlign: "right" }}>
                        <Space>
                            <Button icon={<BranchesOutlined />} onClick={() => window.open("/governor/proof/events", "_blank")} style={{ background: "rgba(255, 77, 79, 0.1)", color: "#ff4d4f", border: "1px solid rgba(255, 77, 79, 0.3)" }}>
                                Drift Lineage
                            </Button>
                            {incident.project_id ? (
                                <Button icon={<NodeIndexOutlined />} onClick={() => window.open(`/workflows/${incident.project_id}`, "_blank")} style={{ background: "rgba(255, 255, 255, 0.05)", color: "#c5c6c7", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
                                    Workflow Analizi
                                </Button>
                            ) : null}
                        </Space>
                    </Col>
                </Row>
            </Card>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "20px" }}>
                <Card variant="borderless" className="glass-card" style={{ background: "rgba(18, 10, 10, 0.6)", backdropFilter: "blur(20px)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px" }}>
                    <Title level={5} style={{ color: "#ff7875", display: "flex", alignItems: "center", gap: "8px" }}>
                        <WarningOutlined /> Manifest ve Loglar
                    </Title>
                    <Paragraph style={{ color: "#c5c6c7", background: "rgba(0,0,0,0.3)", padding: "24px", borderRadius: "12px", border: "1px solid rgba(255, 77, 79, 0.05)", fontSize: "16px", lineHeight: "1.6" }}>
                        {incident.message || "Arka plan sürecinde bir anomali tespit edildi. Detay mesajı kaydedilmedi."}
                    </Paragraph>

                    {incident.trace ? (
                        <div style={{ marginTop: "24px" }}>
                            <Title level={5} style={{ color: "#8c8c8c", fontSize: "12px" }}>Ham Telemetri Çıktısı</Title>
                            <pre style={{ background: "rgba(0,0,0,0.5)", padding: "20px", borderRadius: "12px", overflowX: "auto", border: "1px solid rgba(255, 77, 79, 0.1)", color: "#ff7875", fontSize: "11px", fontFamily: "monospace" }}>
                                {typeof incident.trace === "string" ? incident.trace : JSON.stringify(incident.trace, null, 2)}
                            </pre>
                        </div>
                    ) : null}

                    {incident.status?.toLowerCase() !== "resolved" ? (
                        <>
                            <Divider style={{ borderColor: "rgba(255,255,255,0.05)" }} />
                            <div style={{ marginTop: "24px", padding: "20px", background: "rgba(255, 77, 79, 0.03)", borderRadius: "12px", border: "1px dashed rgba(255, 77, 79, 0.2)" }}>
                                <Title level={5} style={{ color: "#ff7875" }}><DeploymentUnitOutlined /> Manuel Çözüm</Title>
                                <Space direction="vertical" style={{ width: "100%" }}>
                                    <Input.TextArea
                                        placeholder="Alınan aksiyonu ve çözüm gerekçesini buraya yazın..."
                                        rows={4}
                                        style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", borderRadius: "8px" }}
                                        id="resolution-notes"
                                    />
                                    <Button
                                        type="primary"
                                        danger
                                        icon={<ToolOutlined />}
                                        style={{ marginTop: "12px", fontWeight: "bold", height: "40px", padding: "0 24px" }}
                                        onClick={() => void handleResolve()}
                                        loading={isSubmitting}
                                    >
                                        ÇÖZ VE KAPAT
                                    </Button>
                                </Space>
                            </div>
                        </>
                    ) : null}
                </Card>

                <Card variant="borderless" className="glass-card" style={{ background: "rgba(11, 12, 16, 0.4)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "16px" }}>
                    <Title level={5} style={{ color: "#fff", marginBottom: "24px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <HistoryOutlined /> Incident Yaşam Döngüsü
                    </Title>
                    <Timeline
                        mode="left"
                        items={[
                            {
                                label: <Text style={{ color: "#ff7875", fontSize: "11px" }}>{incident.created_at ? new Date(incident.created_at).toLocaleTimeString() : ""}</Text>,
                                children: (
                                    <div style={{ marginBottom: "10px" }}>
                                        <Text strong style={{ color: "#fff" }}>Tespit edildi</Text>
                                        <br />
                                        <Text type="secondary" style={{ fontSize: "11px" }}>Health scan failure</Text>
                                    </div>
                                ),
                                color: "#ff4d4f",
                            },
                            incident.status?.toLowerCase() === "resolved"
                                ? {
                                      label: <Text style={{ color: "#52c41a", fontSize: "11px" }}>{incident.resolved_at ? new Date(incident.resolved_at).toLocaleTimeString() : "RESOLVED"}</Text>,
                                      children: (
                                          <div>
                                              <Text strong style={{ color: "#fff" }}>Durum kapatıldı</Text>
                                              <br />
                                              <Text type="secondary" style={{ fontSize: "11px" }}>Manual intervention complete</Text>
                                          </div>
                                      ),
                                      color: "#52c41a",
                                  }
                                : {
                                      label: <Text style={{ color: "#faad14", fontSize: "11px" }}>ACTIVE</Text>,
                                      children: (
                                          <div>
                                              <Text strong style={{ color: "#fff" }}>İnceleme sürüyor</Text>
                                              <br />
                                              <Text type="secondary" style={{ fontSize: "11px" }}>Bekleyen olay</Text>
                                          </div>
                                      ),
                                      color: "#faad14",
                                  },
                        ]}
                    />
                </Card>
            </div>
        </div>
    );
}
