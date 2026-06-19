"use client";

import React from "react";
import {
  Form,
  Input,
  Select,
  Button,
  Card,
  Typography,
  Space,
  message,
  Divider,
} from "antd";
import {
  RocketOutlined,
  ArrowLeftOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
} from "@ant-design/icons";
import { useNavigation, useCustomMutation } from "@refinedev/core";
import { useTranslations } from "next-intl";
import { getAuthHeaders } from "@/lib/auth";
import { getApiBaseUrl } from "@/lib/runtime";

const { Title, Text, Paragraph } = Typography;

export default function CreateWorkflowPage() {
  const t = useTranslations("workflow");
  const tCommon = useTranslations("common");
  const { list } = useNavigation();
  const { mutate, mutation } = useCustomMutation();
  const apiBase = getApiBaseUrl();
  const isLoading = mutation.isPending;

  const onFinish = async (values: any) => {
    console.log("[CreateWorkflow] Form submission started:", values);
    try {
      console.log("[CreateWorkflow] Ensuring session and fetching headers...");
      const authHeaders = await getAuthHeaders();
      console.log("[CreateWorkflow] Triggering mutation...");
      
      mutate(
        {
          url: `${apiBase}/workflows`,
          method: "post",
          values: {
            title: values.title,
            description: values.description,
            workflow_template: values.template || "default",
            priority: values.priority || "MEDIUM",
            quality_profile: values.quality || "standard",
          },
        },
        {
          onSuccess: (data) => {
            console.log("[CreateWorkflow] Mutation Success:", data);
            message.success(t("createSuccess"));
            list("workflows");
          },
          onError: (error: any) => {
            console.error("[CreateWorkflow] Mutation Error:", error);
            const rawDetail = error?.response?.data?.detail || error?.message || t("systemError");
            const status = error?.statusCode || error?.status || error?.response?.status;
            const detail = status === 403
              ? t("operatorRequired")
              : rawDetail;
            message.error(t("createError") + detail);
          },
        }
      );
    } catch (err: any) {
      console.error("[CreateWorkflow] Catch Error:", err);
      message.error(t("systemError") + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#060a12] p-8">
      <div className="mx-auto max-w-4xl">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => list("workflows")}
          className="mb-8 border-white/10 bg-transparent text-gray-400 hover:text-white"
        >
          {tCommon("cancel")}
        </Button>

        <Card
          variant="borderless"
          className="overflow-hidden rounded-[2rem] border border-white/5 bg-white/[0.02] shadow-2xl"
          styles={{ body: { padding: 0 } }}
        >
          <div className="relative overflow-hidden bg-gradient-to-br from-[var(--primary)]/10 via-transparent to-transparent p-12">
            <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[var(--primary)]/5 blur-[100px]" />
            
            <div className="relative z-10">
              <Space direction="vertical" size={0}>
                <Text className="text-[10px] font-black uppercase tracking-[0.4em] text-[var(--primary)]">
                  {t("otonomOrchestration")}
                </Text>
                <Title level={1} className="m-0 mt-2 text-5xl font-black italic tracking-tighter text-white">
                  {t("create")}
                </Title>
                <Paragraph className="mt-4 max-w-md text-gray-400">
                  {t("createDesc")}
                </Paragraph>
              </Space>
            </div>
          </div>

          <div className="p-12">
            <Form
              layout="vertical"
              onFinish={onFinish}
              initialValues={{ template: "default", priority: "MEDIUM", quality: "standard" }}
              requiredMark={false}
            >
              <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                <div className="space-y-6">
                  <Form.Item
                    name="title"
                    label={<span className="text-[10px] font-black uppercase tracking-widest text-gray-500">{t("taskTitle")}</span>}
                    rules={[{ required: true, message: t("taskTitleRequired") }]}
                  >
                    <Input 
                      placeholder={t("taskTitlePlaceholder")} 
                      className="rounded-xl border-white/10 bg-white/5 py-3 text-white hover:border-[var(--primary)]/50 focus:border-[var(--primary)]"
                    />
                  </Form.Item>

                  <Form.Item
                    name="description"
                    label={<span className="text-[10px] font-black uppercase tracking-widest text-gray-500">{t("detailedDescription")}</span>}
                  >
                    <Input.TextArea 
                      rows={6} 
                      placeholder={t("detailedDescriptionPlaceholder")} 
                      className="rounded-xl border-white/10 bg-white/5 text-white hover:border-[var(--primary)]/50 focus:border-[var(--primary)]"
                    />
                  </Form.Item>
                </div>

                <div className="space-y-6">
                  <Form.Item
                    name="template"
                    label={<span className="text-[10px] font-black uppercase tracking-widest text-gray-500">{t("workflowTemplate")}</span>}
                  >
                    <Select className="premium-select">
                      <Select.Option value="default">{t("templateOptions.default")}</Select.Option>
                      <Select.Option value="research">{t("templateOptions.research")}</Select.Option>
                      <Select.Option value="coding">{t("templateOptions.coding")}</Select.Option>
                      <Select.Option value="analysis">{t("templateOptions.analysis")}</Select.Option>
                    </Select>
                  </Form.Item>

                  <div className="grid grid-cols-2 gap-4">
                    <Form.Item
                      name="priority"
                      label={<span className="text-[10px] font-black uppercase tracking-widest text-gray-500">{t("priorityLevel")}</span>}
                    >
                      <Select className="premium-select">
                        <Select.Option value="LOW">{t("priorityOptions.LOW")}</Select.Option>
                        <Select.Option value="MEDIUM">{t("priorityOptions.MEDIUM")}</Select.Option>
                        <Select.Option value="HIGH">{t("priorityOptions.HIGH")}</Select.Option>
                        <Select.Option value="CRITICAL">{t("priorityOptions.CRITICAL")}</Select.Option>
                      </Select>
                    </Form.Item>

                    <Form.Item
                      name="quality"
                      label={<span className="text-[10px] font-black uppercase tracking-widest text-gray-500">{t("qualityProfile")}</span>}
                    >
                      <Select className="premium-select">
                        <Select.Option value="standard">{t("qualityOptions.standard")}</Select.Option>
                        <Select.Option value="high_precision">{t("qualityOptions.high_precision")}</Select.Option>
                        <Select.Option value="fast_track">{t("qualityOptions.fast_track")}</Select.Option>
                      </Select>
                    </Form.Item>
                  </div>

                  <div className="mt-8 rounded-2xl border border-[var(--primary)]/20 bg-[var(--primary)]/5 p-6">
                    <div className="flex items-center gap-4">
                      <SafetyOutlined className="text-2xl text-[var(--primary)]" />
                      <div>
                        <Text className="block text-xs font-bold text-white">{t("governanceActive")}</Text>
                        <Text className="text-[10px] text-gray-500">
                          {t("governanceActiveDesc")}
                        </Text>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <Divider className="my-12 border-white/5" />

              <div className="flex justify-end gap-4">
                <Button 
                  size="large" 
                  onClick={() => list("workflows")}
                  className="rounded-xl border-white/10 bg-transparent px-8 text-gray-400"
                >
                  {tCommon("cancel")}
                </Button>
                <Button
                  type="primary"
                  size="large"
                  icon={<RocketOutlined />}
                  htmlType="submit"
                  loading={isLoading}
                  className="rounded-xl border-none bg-gradient-to-r from-[var(--primary)] to-blue-500 px-12 font-black italic tracking-widest text-[#060a12] hover:scale-105 active:scale-95"
                >
                  {tCommon("save").toUpperCase()}
                </Button>
              </div>
            </Form>
          </div>
        </Card>
      </div>

      <style jsx global>{`
        .premium-select .ant-select-selector {
          background: rgba(255, 255, 255, 0.05) !important;
          border: 1px solid rgba(255, 255, 255, 0.1) !important;
          border-radius: 12px !important;
          color: white !important;
          height: 48px !important;
          display: flex !important;
          align-items: center !important;
        }
        .premium-select .ant-select-selection-item {
          font-weight: 600;
        }
        .premium-select:hover .ant-select-selector {
          border-color: rgba(102, 252, 241, 0.5) !important;
        }
        .ant-form-item-label label {
          height: auto !important;
        }
      `}</style>
    </div>
  );
}
