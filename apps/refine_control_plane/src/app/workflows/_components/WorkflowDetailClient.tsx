"use client";

import React from "react";
import {
    Alert,
    App,
    Button,
    Card,
    Col,
    Divider,
    Empty,
    Input,
    List,
    Row,
    Space,
    Statistic,
    Steps,
    Tag,
    Typography,
} from "antd";
import { useNavigation } from "@refinedev/core";
import ArrowLeftOutlined from "@ant-design/icons/lib/icons/ArrowLeftOutlined";
import BranchesOutlined from "@ant-design/icons/lib/icons/BranchesOutlined";
import CheckCircleOutlined from "@ant-design/icons/lib/icons/CheckCircleOutlined";
import ClockCircleOutlined from "@ant-design/icons/lib/icons/ClockCircleOutlined";
import ExclamationCircleOutlined from "@ant-design/icons/lib/icons/ExclamationCircleOutlined";
import RocketOutlined from "@ant-design/icons/lib/icons/RocketOutlined";
import SafetyOutlined from "@ant-design/icons/lib/icons/SafetyOutlined";
import SyncOutlined from "@ant-design/icons/lib/icons/SyncOutlined";
import ThunderboltOutlined from "@ant-design/icons/lib/icons/ThunderboltOutlined";
import { safeFetchJson } from "@/lib/api";

const { Title, Text } = Typography;

interface WorkflowStep {
    id: string;
    name: string;
    action: string;
    status: string;
    started_at?: string | null;
    completed_at?: string | null;
    retries?: number;
    max_retries?: number;
    error?: string | null;
    dependencies?: string[];
    output_summary?: string | null;
}

interface RelatedApproval {
    id: string;
    request_type: string;
    status: string;
}

interface RelatedIncident {
    id: string;
    incident_type: string;
    status: string;
    severity: string;
    message: string;
    created_at?: string | null;
}

interface WorkflowHistoryItem {
    step: string;
    msg: string;
    timestamp: string;
}

interface WorkflowDetail {
    id: string;
    name: string;
    workflow_type: string;
    status: string;
    source: string;
    steps: WorkflowStep[];
    context_keys: string[];
    payload: Record<string, unknown>;
    created_at?: string | null;
    started_at?: string | null;
    completed_at?: string | null;
    final_report?: string | null;
    history?: WorkflowHistoryItem[];
    related_approvals?: RelatedApproval[];
    related_incidents?: RelatedIncident[];
}

type WorkflowDetailClientProps = {
    id: string;
};

const suspiciousEncodingPattern = /[ÃÄÅ]/;

const repairMojibake = (value: string): string => {
    if (!value || !suspiciousEncodingPattern.test(value)) {
        return value;
    }

    try {
        const bytes = Uint8Array.from(Array.from(value).map((char) => char.charCodeAt(0) & 0xff));
        const repaired = new TextDecoder("utf-8").decode(bytes);
        return repaired || value;
    } catch {
        return value;
    }
};

const cleanText = (value?: string | null, fallback = "-"): string => {
    if (!value) {
        return fallback;
    }
    return repairMojibake(value).trim() || fallback;
};

const formatStatusText = (status?: string | null): string => {
    const normalized = String(status || "").toLowerCase();
    switch (normalized) {
        case "running":
            return "ÇALIŞIYOR";
        case "completed":
        case "success":
            return "TAMAMLANDI";
        case "failed":
        case "error":
            return "HATA";
        case "waiting_approval":
        case "pending_approval":
            return "ONAY BEKLİYOR";
        case "queued":
            return "KUYRUKTA";
        default:
            return cleanText(status, "BİLİNMİYOR").toUpperCase();
    }
};

const formatSourceText = (source?: string | null): string => {
    const normalized = String(source || "").toLowerCase();
    switch (normalized) {
        case "api":
            return "API";
        case "manual":
            return "MANUEL";
        case "scheduler":
            return "ZAMANLAYICI";
        case "governor":
            return "YÖNETİŞİM";
        default:
            return cleanText(source, "MANUEL").toUpperCase();
    }
};

const formatTypeText = (workflowType?: string | null): string => {
    const normalized = String(workflowType || "").toLowerCase();
    switch (normalized) {
        case "default":
            return "GENEL";
        case "repair":
            return "ONARIM";
        case "deployment":
            return "DAĞITIM";
        case "analysis":
            return "ANALİZ";
        default:
            return cleanText(workflowType, "GENEL").toUpperCase();
    }
};

const humanizeStepLabel = (stepName?: string | null): string => {
    const cleaned = cleanText(stepName, "Adsız Adım");
    const map: Record<string, string> = {
        planner_alpha: "Planlama",
        planner_alpha_01: "Planlama",
        executor_beta: "Uygulama",
        reviewer_gamma: "Gözden Geçirme",
        governor_prime: "Yönetişim Ön Kontrolü",
        auditor_theta: "Denetim Onayı",
        plan_subtasks: "Alt Görev Planlama",
        validate_context: "Bağlam Doğrulama",
        finalize_report: "Final Raporu",
    };
    const normalized = cleaned.toLowerCase().replace(/[\s-]+/g, "_");
    return map[normalized] || cleaned;
};

const formatTimestamp = (value?: string | null): string => {
    if (!value) {
        return "-";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return cleanText(value);
    }

    return date.toLocaleString("tr-TR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

export default function WorkflowDetailClient({ id }: WorkflowDetailClientProps) {
    const { notification } = App.useApp();
    const { list } = useNavigation();
    const [workflow, setWorkflow] = React.useState<WorkflowDetail | null>(null);
    const [isLoading, setIsLoading] = React.useState(true);
    const [isError, setIsError] = React.useState(false);
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [autoRefresh, setAutoRefresh] = React.useState(true);
    const [isClient, setIsClient] = React.useState(false);

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

    const loadWorkflow = React.useCallback(async () => {
        if (!id || id === "index") {
            setWorkflow(null);
            setIsLoading(false);
            setIsError(true);
            return;
        }

        setIsLoading(true);
        setIsError(false);

        try {
            const authHeaders = await getAuthHeaders();
            const response = await safeFetchJson<WorkflowDetail>(`${apiBase}/workflows/${id}`, {
                headers: authHeaders,
            });
            setWorkflow(response);
        } catch {
            setWorkflow(null);
            setIsError(true);
        } finally {
            setIsLoading(false);
        }
    }, [apiBase, getAuthHeaders, id]);

    React.useEffect(() => {
        if (!isClient) return;
        void loadWorkflow();
    }, [isClient, loadWorkflow]);

    React.useEffect(() => {
        let interval: ReturnType<typeof setInterval> | undefined;
        const normalizedStatus = String(workflow?.status || "").toLowerCase();
        if (autoRefresh && workflow && ["running", "waiting_approval", "pending_approval"].includes(normalizedStatus)) {
            interval = setInterval(() => {
                void loadWorkflow();
            }, 5000);
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [autoRefresh, workflow, loadWorkflow]);

    const handleApprove = React.useCallback(async () => {
        const notes = (document.getElementById("approval-notes") as HTMLTextAreaElement | null)?.value || "";
        if (!workflow?.id) {
            notification.error({ message: "Hata", description: "İş akışı bulunamadı." });
            return;
        }

        setIsSubmitting(true);
        try {
            const authHeaders = await getAuthHeaders();
            const pendingApproval = (workflow.related_approvals || []).find(
                (item) => String(item.status || "").toLowerCase() === "pending",
            );

            const response = pendingApproval
                ? await safeFetchJson(`${apiBase}/approvals/${pendingApproval.id}`, {
                      method: "PATCH",
                      headers: { "Content-Type": "application/json", ...authHeaders },
                      body: JSON.stringify({
                          status: "APPROVED",
                          comment: notes || `Workflow ${workflow.id} approved from workflow detail surface.`,
                      }),
                  })
                : await safeFetchJson(`${apiBase}/workflows/${workflow.id}/approve`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json", ...authHeaders },
                      body: JSON.stringify({
                          operator_id: "admin_human",
                          notes,
                      }),
                  });

            if (
                (response as { status?: string }).status === "success" ||
                (response as { status?: string }).status === "APPROVED" ||
                (response as { message?: string }).message ||
                (response as { decided_at?: string }).decided_at
            ) {
                notification.success({
                    message: "İş akışı onaylandı",
                    description: pendingApproval
                        ? "Onay kapısı imzalandı ve kayıt zincirine işlendi."
                        : "İş akışı yetkilendirildi ve tekrar kuyruğa alındı.",
                    placement: "topRight",
                });
                await loadWorkflow();
            } else {
                notification.error({
                    message: "Onay başarısız",
                    description: "Sistem onay isteğini kabul etmedi.",
                });
            }
        } catch (err) {
            notification.error({
                message: "Ağ hatası",
                description: err instanceof Error ? err.message : "Mission Control API ile bağlantı kurulamadı.",
            });
        } finally {
            setIsSubmitting(false);
        }
    }, [apiBase, getAuthHeaders, loadWorkflow, notification, workflow]);

    if (!isClient) return <div className="min-h-screen bg-[#060a12]" />;
    if (isLoading) return <Card loading />;
    if (isError || !workflow) {
        return (
            <Alert
                message="Hata"
                description="İş akışı bulunamadı ya da yüklenemedi."
                type="error"
                showIcon
                action={
                    <Button size="small" type="primary" onClick={() => list("workflows")}>
                        Akış listesine dön
                    </Button>
                }
            />
        );
    }

    const getStatusTag = (status: string) => {
        const normalized = String(status || "").toLowerCase();
        switch (normalized) {
            case "running":
                return (
                    <Tag icon={<SyncOutlined spin />} color="processing">
                        ÇALIŞIYOR
                    </Tag>
                );
            case "completed":
            case "success":
                return (
                    <Tag icon={<CheckCircleOutlined />} color="success">
                        TAMAMLANDI
                    </Tag>
                );
            case "failed":
            case "error":
                return (
                    <Tag icon={<ExclamationCircleOutlined />} color="error">
                        HATA
                    </Tag>
                );
            case "waiting_approval":
            case "pending_approval":
                return (
                    <Tag icon={<ClockCircleOutlined />} color="warning">
                        ONAY BEKLİYOR
                    </Tag>
                );
            default:
                return <Tag color="default">{formatStatusText(status)}</Tag>;
        }
    };

    const steps = workflow.steps || [];
    const currentStepIndex = steps.findIndex((step) =>
        ["running", "processing", "pending", "queued"].includes(String(step.status || "").toLowerCase()),
    );
    const activeIndex = currentStepIndex === -1 ? steps.length : currentStepIndex;
    const finalReport = cleanText(workflow.final_report, "");
    const history = workflow.history || [];

    return (
        <div
            style={{
                padding: "24px",
                minHeight: "100%",
                backgroundColor: "#060a12",
                display: "flex",
                flexDirection: "column",
                gap: "24px",
            }}
        >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px" }}>
                <Button
                    icon={<ArrowLeftOutlined />}
                    onClick={() => list("workflows")}
                    style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "#aaa" }}
                >
                    İş akışlarına dön
                </Button>
                <Space>
                    {String(workflow.status || "").toLowerCase() === "running" ? (
                        <Tag
                            color="cyan"
                            style={{
                                border: "1px solid rgba(102, 252, 241, 0.4)",
                                background: "rgba(102, 252, 241, 0.05)",
                            }}
                        >
                            <SyncOutlined spin /> CANLI GÜNCELLENİYOR
                        </Tag>
                    ) : null}
                    <Button
                        size="small"
                        type={autoRefresh ? "primary" : "default"}
                        onClick={() => setAutoRefresh(!autoRefresh)}
                        style={{ fontSize: "10px", height: "24px" }}
                    >
                        Otomatik eşitleme: {autoRefresh ? "Açık" : "Kapalı"}
                    </Button>
                </Space>
            </div>

            <Card
                variant="borderless"
                style={{
                    background: "linear-gradient(90deg, rgba(10,12,18,0.8) 0%, rgba(20,25,35,0.4) 100%)",
                    borderRadius: "12px",
                    border: "1px solid rgba(102, 252, 241, 0.15)",
                    marginBottom: "20px",
                }}
            >
                <Row gutter={16} align="middle">
                    <Col span={8}>
                        <div style={{ paddingLeft: "10px" }}>
                            <Text
                                type="secondary"
                                style={{ fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}
                            >
                                Operasyonel İş Akışı
                            </Text>
                            <Title level={3} style={{ color: "#fff", margin: 0, fontWeight: 900 }}>
                                {cleanText(workflow.name, "Adsız Sekans")}
                            </Title>
                            <Space style={{ marginTop: "4px" }}>
                                {getStatusTag(workflow.status)}
                                <Text type="secondary" style={{ fontSize: "11px", fontFamily: "monospace" }}>
                                    #{String(workflow.id).substring(0, 8)}
                                </Text>
                            </Space>
                        </div>
                    </Col>
                    <Col span={4}>
                        <Statistic
                            title={<span style={{ color: "#45a29e", fontSize: "10px" }}>KAYNAK</span>}
                            value={formatSourceText(workflow.source)}
                            valueStyle={{ color: "#fff", fontSize: "18px", fontWeight: "bold" }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic
                            title={<span style={{ color: "#45a29e", fontSize: "10px" }}>TÜR</span>}
                            value={formatTypeText(workflow.workflow_type)}
                            valueStyle={{ color: "#66fcf1", fontSize: "18px", fontWeight: "bold" }}
                        />
                    </Col>
                    <Col span={8} style={{ textAlign: "right" }}>
                        <Space>
                            <Button
                                icon={<BranchesOutlined />}
                                onClick={() => window.open("/governor/proof/events", "_blank")}
                                style={{
                                    background: "rgba(102, 252, 241, 0.1)",
                                    color: "#66fcf1",
                                    border: "1px solid rgba(102, 252, 241, 0.3)",
                                }}
                            >
                                Karar zincirini aç
                            </Button>
                        </Space>
                    </Col>
                </Row>
            </Card>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 400px", gap: "24px" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    <Card
                        variant="borderless"
                        className="glass-card"
                        style={{
                            background: "rgba(11, 12, 16, 0.6)",
                            backdropFilter: "blur(20px)",
                            border: "1px solid rgba(255, 255, 255, 0.05)",
                            borderRadius: "16px",
                        }}
                        title={
                            <span
                                style={{
                                    color: "#fff",
                                    fontSize: "14px",
                                    fontWeight: "bold",
                                    textTransform: "uppercase",
                                    letterSpacing: "1px",
                                }}
                            >
                                <ThunderboltOutlined style={{ color: "#66fcf1" }} /> Yürütme Planı
                            </span>
                        }
                    >
                        {steps.length === 0 ? (
                            <Empty description={<span style={{ color: "#666" }}>Henüz tanımlı adım yok.</span>} />
                        ) : (
                            <Steps
                                direction="vertical"
                                current={activeIndex}
                                items={steps.map((step, index) => {
                                    const normalizedStatus = String(step.status || "").toLowerCase();
                                    const isCurrent = index === activeIndex;
                                    const isStepError = normalizedStatus === "failed" || normalizedStatus === "error";
                                    const isFinished = normalizedStatus === "completed" || normalizedStatus === "success";

                                    return {
                                        title: (
                                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                                <span
                                                    style={{
                                                        color: isCurrent ? "#66fcf1" : isStepError ? "#f5222d" : "#fff",
                                                        fontWeight: isCurrent ? "900" : "bold",
                                                    }}
                                                >
                                                    {humanizeStepLabel(step.name)}
                                                </span>
                                                <Tag
                                                    color={
                                                        isFinished ? "green" : isStepError ? "red" : isCurrent ? "blue" : "default"
                                                    }
                                                    style={{ fontSize: "9px", borderRadius: "4px" }}
                                                >
                                                    {formatStatusText(step.status)}
                                                </Tag>
                                            </div>
                                        ),
                                        description: (
                                            <div
                                                style={{
                                                    marginTop: "8px",
                                                    padding: "12px",
                                                    background: "rgba(255,255,255,0.02)",
                                                    border: "1px solid rgba(255,255,255,0.05)",
                                                    borderRadius: "8px",
                                                }}
                                            >
                                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                                                    <Text type="secondary" style={{ fontSize: "11px", color: "#666" }}>
                                                        Aksiyon: <span style={{ color: "#aaa" }}>{cleanText(step.action)}</span>
                                                    </Text>
                                                    {step.completed_at ? (
                                                        <Text type="secondary" style={{ fontSize: "10px" }}>
                                                            {formatTimestamp(step.completed_at)}
                                                        </Text>
                                                    ) : null}
                                                </div>
                                                {step.output_summary ? (
                                                    <div
                                                        style={{
                                                            color: "#45a29e",
                                                            fontSize: "12px",
                                                            background: "rgba(69,162,158,0.05)",
                                                            padding: "8px",
                                                            borderRadius: "4px",
                                                        }}
                                                    >
                                                        <Text
                                                            strong
                                                            style={{
                                                                color: "#66fcf1",
                                                                fontSize: "10px",
                                                                display: "block",
                                                                marginBottom: "4px",
                                                            }}
                                                        >
                                                            ÇIKTI ÖZETİ
                                                        </Text>
                                                        {cleanText(step.output_summary)}
                                                    </div>
                                                ) : null}
                                                {step.error ? (
                                                    <Alert
                                                        type="error"
                                                        message={<span style={{ fontSize: "11px", fontWeight: "bold" }}>HATA SAPTANDI</span>}
                                                        description={
                                                            <span style={{ fontSize: "11px", fontFamily: "monospace" }}>
                                                                {cleanText(step.error)}
                                                            </span>
                                                        }
                                                        style={{
                                                            marginTop: "8px",
                                                            border: "none",
                                                            background: "rgba(245,34,45,0.1)",
                                                        }}
                                                    />
                                                ) : null}
                                            </div>
                                        ),
                                        icon:
                                            isCurrent && normalizedStatus === "running" ? (
                                                <SyncOutlined spin style={{ color: "#66fcf1" }} />
                                            ) : undefined,
                                        status: isStepError ? "error" : isFinished ? "finish" : isCurrent ? "process" : "wait",
                                    };
                                })}
                            />
                        )}
                    </Card>

                    {finalReport ? (
                        <Card
                            variant="borderless"
                            className="glass-card"
                            style={{
                                background: "rgba(11, 12, 16, 0.4)",
                                border: "1px solid rgba(255, 255, 255, 0.05)",
                                borderRadius: "16px",
                            }}
                        >
                            <Title level={5} style={{ color: "#45a29e", fontSize: "12px", textTransform: "uppercase" }}>
                                Final Rapor
                            </Title>
                            <Text style={{ color: "#d5d8df", whiteSpace: "pre-wrap", lineHeight: 1.7 }}>
                                {finalReport}
                            </Text>
                        </Card>
                    ) : null}

                    {history.length > 0 ? (
                        <Card
                            variant="borderless"
                            className="glass-card"
                            style={{
                                background: "rgba(11, 12, 16, 0.4)",
                                border: "1px solid rgba(255, 255, 255, 0.05)",
                                borderRadius: "16px",
                            }}
                        >
                            <Title level={5} style={{ color: "#45a29e", fontSize: "12px", textTransform: "uppercase" }}>
                                Akış Geçmişi
                            </Title>
                            <List
                                size="small"
                                dataSource={history}
                                renderItem={(item) => (
                                    <List.Item style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", padding: "10px 0" }}>
                                        <List.Item.Meta
                                            title={
                                                <Space split={<Divider type="vertical" style={{ borderColor: "rgba(255,255,255,0.1)" }} />}>
                                                    <Text style={{ color: "#fff" }}>{humanizeStepLabel(item.step)}</Text>
                                                    <Text type="secondary" style={{ fontSize: "11px" }}>
                                                        {formatTimestamp(item.timestamp)}
                                                    </Text>
                                                </Space>
                                            }
                                            description={<Text style={{ color: "#9ca3af" }}>{cleanText(item.msg)}</Text>}
                                        />
                                    </List.Item>
                                )}
                            />
                        </Card>
                    ) : null}

                    <Card
                        variant="borderless"
                        className="glass-card"
                        style={{
                            background: "rgba(11, 12, 16, 0.4)",
                            border: "1px solid rgba(255, 255, 255, 0.05)",
                            borderRadius: "16px",
                        }}
                    >
                        <Title level={5} style={{ color: "#45a29e", fontSize: "12px", textTransform: "uppercase" }}>
                            Çekirdek Bağlam Yükü
                        </Title>
                        <pre
                            style={{
                                background: "rgba(0,0,0,0.5)",
                                padding: "16px",
                                borderRadius: "12px",
                                border: "1px solid rgba(69, 162, 158, 0.1)",
                                color: "#c5c6c7",
                                overflowX: "auto",
                                fontSize: "11px",
                                fontFamily: "monospace",
                            }}
                        >
                            {JSON.stringify(workflow.payload || {}, null, 2)}
                        </pre>
                    </Card>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    {["waiting_approval", "pending_approval"].includes(String(workflow.status || "").toLowerCase()) ? (
                        <Card
                            variant="borderless"
                            style={{ background: "rgba(102, 252, 241, 0.05)", border: "1px dashed #66fcf1", borderRadius: "16px" }}
                        >
                            <Title level={5} style={{ color: "#66fcf1" }}>
                                Aksiyon Gerekli
                            </Title>
                            <Text style={{ color: "#c5c6c7", fontSize: "13px" }}>
                                Bu görev kurumsal onay beklediği için duraklatıldı. Gerekçeyi yazıp imza vererek devam ettirebilirsiniz.
                            </Text>
                            <Space direction="vertical" style={{ width: "100%", marginTop: "16px" }}>
                                <Input.TextArea
                                    id="approval-notes"
                                    placeholder="Denetim defteri için karar gerekçesini girin..."
                                    rows={3}
                                    style={{ background: "rgba(0,0,0,0.2)", color: "#fff", border: "1px solid rgba(102,252,241,0.2)" }}
                                />
                                <Button
                                    type="primary"
                                    icon={<RocketOutlined />}
                                    block
                                    style={{ background: "#66fcf1", color: "#060a12", fontWeight: "bold", border: "none" }}
                                    onClick={() => void handleApprove()}
                                    loading={isSubmitting}
                                >
                                    Onayla ve devam ettir
                                </Button>
                            </Space>
                        </Card>
                    ) : null}

                    <Card
                        variant="borderless"
                        className="glass-card"
                        style={{
                            background: "linear-gradient(135deg, rgba(11,12,16,0.6) 0%, rgba(20,25,35,0.4) 100%)",
                            border: "1px solid rgba(102, 252, 241, 0.1)",
                            borderRadius: "16px",
                        }}
                    >
                        <Title level={5} style={{ color: "#66fcf1", fontSize: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
                            <SafetyOutlined /> Yönetişim Bütünlüğü
                        </Title>
                        <Divider style={{ borderColor: "rgba(255,255,255,0.05)", margin: "12px 0" }} />

                        <Space direction="vertical" style={{ width: "100%" }} size="large">
                            <div>
                                <Text strong style={{ color: "#45a29e", fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>
                                    Quorum İstekleri
                                </Text>
                                {workflow.related_approvals && workflow.related_approvals.length > 0 ? (
                                    <List
                                        size="small"
                                        dataSource={workflow.related_approvals}
                                        renderItem={(item) => (
                                            <List.Item
                                                actions={[
                                                    <Button
                                                        key="view-approval"
                                                        size="small"
                                                        type="link"
                                                        onClick={() => window.open(`/approvals/${item.id}`, "_blank")}
                                                    >
                                                        Aç
                                                    </Button>,
                                                ]}
                                                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", padding: "8px 0" }}
                                            >
                                                <List.Item.Meta
                                                    title={<Text style={{ color: "#fff", fontSize: "12px" }}>{cleanText(item.request_type)}</Text>}
                                                    description={
                                                        <Tag
                                                            color={String(item.status).toUpperCase() === "APPROVED" ? "success" : "warning"}
                                                            style={{ fontSize: "9px" }}
                                                        >
                                                            {formatStatusText(item.status)}
                                                        </Tag>
                                                    }
                                                />
                                            </List.Item>
                                        )}
                                    />
                                ) : (
                                    <Text style={{ color: "#555", fontSize: "11px", marginTop: "12px", fontStyle: "italic" }}>
                                        Engelleyici onay kaydı yok.
                                    </Text>
                                )}
                            </div>

                            <div>
                                <Text strong style={{ color: "#ff4d4f", fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>
                                    Anomali Günlüğü
                                </Text>
                                {workflow.related_incidents && workflow.related_incidents.length > 0 ? (
                                    <List
                                        size="small"
                                        dataSource={workflow.related_incidents}
                                        renderItem={(item) => (
                                            <List.Item
                                                actions={[
                                                    <Button
                                                        key="debug-incident"
                                                        size="small"
                                                        type="link"
                                                        danger
                                                        onClick={() => window.open(`/incidents/${item.id}`, "_blank")}
                                                    >
                                                        İncele
                                                    </Button>,
                                                ]}
                                                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", padding: "8px 0" }}
                                            >
                                                <List.Item.Meta
                                                    title={<Text style={{ color: "#fff", fontSize: "12px" }}>{cleanText(item.incident_type)}</Text>}
                                                    description={
                                                        <Space direction="vertical" size={4}>
                                                            <Tag color="error" style={{ fontSize: "9px", width: "fit-content" }}>
                                                                {cleanText(item.severity).toUpperCase()} SEVİYE
                                                            </Tag>
                                                            <Text style={{ color: "#8a8f98", fontSize: "11px" }}>
                                                                {cleanText(item.message)}
                                                            </Text>
                                                        </Space>
                                                    }
                                                />
                                            </List.Item>
                                        )}
                                    />
                                ) : (
                                    <Text style={{ color: "#555", fontSize: "11px", marginTop: "12px", fontStyle: "italic" }}>
                                        Ortam tarafında aktif anomali görünmüyor.
                                    </Text>
                                )}
                            </div>
                        </Space>
                    </Card>
                </div>
            </div>
        </div>
    );
}
