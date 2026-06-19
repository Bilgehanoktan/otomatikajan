"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Card, Result, Button, List, Typography, Space, Tag, Divider } from "antd";
import { CheckCircleTwoTone, StopTwoTone, WarningTwoTone, RocketTwoTone } from "@ant-design/icons";
import { safeFetchJson } from "@/lib/api";

const { Title, Text, Paragraph } = Typography;

export const ReleaseGatePanel: React.FC = () => {
    const t = useTranslations("repair_lab");
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const fetchOverview = async () => {
        setLoading(true);
        try {
            const result = await safeFetchJson<any>("/api/v1/ui-repair/readiness/overview");
            setData(result);
        } catch (error) {
            console.error("Failed to fetch overview", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchOverview();
    }, []);

    const evaluateGate = async () => {
        if (!data?.assessment?.id) return;
        setLoading(true);
        try {
            await safeFetchJson(`/api/v1/ui-repair/release-gate/evaluate?assessment_id=${data.assessment.id}&approver=Admin`, { method: "POST" });
            fetchOverview();
        } catch (error) {
            console.error("Gate evaluation failed", error);
        } finally {
            setLoading(false);
        }
    };

    if (!data || data.status === "NO_DATA") {
        return <Result status="info" title="Awaiting Readiness Assessment" subTitle="Please complete an enterprise readiness assessment before evaluating the release gate." />;
    }

    const { gate } = data;

    const getGateStatus = () => {
        switch (gate?.decision) {
            case "GO": return { status: "success", icon: <RocketTwoTone twoToneColor="#52c41a" />, title: "GO" };
            case "GO_WITH_WARNINGS": return { status: "warning", icon: <WarningTwoTone twoToneColor="#faad14" />, title: "GO WITH WARNINGS" };
            case "PILOT_ONLY": return { status: "warning", icon: <RocketTwoTone twoToneColor="#1890ff" />, title: "PILOT ONLY" };
            case "NO_GO": return { status: "error", icon: <StopTwoTone twoToneColor="#f5222d" />, title: "NO GO" };
            default: return { status: "info", icon: <CheckCircleTwoTone />, title: "NOT EVALUATED" };
        }
    };

    const statusInfo = getGateStatus();

    return (
        <Space direction="vertical" style={{ width: "100%" }} size="large">
            <Card>
                <Result
                    icon={statusInfo.icon}
                    title={statusInfo.title}
                    subTitle={gate?.rationale || "Release gate status depends on mandatory security and governance criteria."}
                    extra={[
                        <Button type="primary" key="evaluate" onClick={evaluateGate} loading={loading}>
                            {t("evaluate_gate")}
                        </Button>
                    ]}
                />
            </Card>

            {gate && (
                <Card title="Gate Condition Checklist">
                    <List
                        dataSource={Object.entries(gate.gate_conditions_json)}
                        renderItem={([key, passed]: [string, any]) => (
                            <List.Item>
                                <Space>
                                    {passed ? <CheckCircleTwoTone twoToneColor="#52c41a" /> : <StopTwoTone twoToneColor="#f5222d" />}
                                    <Text delete={!passed} type={passed ? "success" : "danger"}>
                                        {key.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")}
                                    </Text>
                                </Space>
                                <Tag color={passed ? "green" : "red"}>{passed ? "PASSED" : "FAILED"}</Tag>
                            </List.Item>
                        )}
                    />
                </Card>
            )}
        </Space>
    );
};
