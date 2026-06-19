"use client";

import React, { useState } from "react";
import { useLogin, useRegister } from "@refinedev/core";
import {
  Form,
  Input,
  Button,
  Checkbox,
  Card,
  Typography,
  Space,
  Layout,
  Alert,
  Tooltip
} from "antd";
import {
  LockOutlined,
  UserOutlined,
  RocketOutlined,
  SafetyOutlined,
  SafetyCertificateOutlined,
  IdcardOutlined
} from "@ant-design/icons";

const { Title, Text } = Typography;

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const { mutate: login, isPending: isLoginPending } = useLogin();
  const { mutate: register, isPending: isRegisterPending } = useRegister();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("expired") === "true") {
        setError("Oturumunuzun süresi doldu. Güvenliğiniz için lütfen tekrar giriş yapın.");
      }
    }
  }, []);

  const onFinishLogin = (values: any) => {
    setError(null);
    setSuccess(null);
    login(values, {
      onError: (err: any) => {
        setError(err?.message || "Kimlik doğrulama başarısız oldu.");
      }
    });
  };

  const onFinishRegister = (values: any) => {
    setError(null);
    setSuccess(null);
    register(values, {
      onSuccess: () => {
        setSuccess("Kayıt başarılı! Lütfen giriş yapın.");
        setMode("login");
      },
      onError: (err: any) => {
        setError(err?.message || "Kayıt işlemi başarısız oldu.");
      }
    });
  };

  return (
    <Layout style={{ minHeight: "100vh", background: "#060a12", display: "flex", justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, overflow: "hidden", pointerEvents: "none" }}>
         <div style={{
           position: "absolute",
           top: "-10%",
           right: "-5%",
           width: "40%",
           height: "60%",
           background: "radial-gradient(circle, rgba(102, 252, 241, 0.05) 0%, transparent 70%)",
           filter: "blur(60px)"
         }} />
         <div style={{
           position: "absolute",
           bottom: "-10%",
           left: "-5%",
           width: "40%",
           height: "60%",
           background: "radial-gradient(circle, rgba(102, 252, 241, 0.03) 0%, transparent 70%)",
           filter: "blur(60px)"
         }} />
      </div>

      <Card
        style={{
          width: 400,
          background: "rgba(26, 28, 34, 0.8)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(102, 252, 241, 0.15)",
          boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.8)",
          borderRadius: 16
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            display: "inline-flex",
            padding: 16,
            borderRadius: "50%",
            background: "rgba(102, 252, 241, 0.1)",
            marginBottom: 16,
            border: "1px solid rgba(102, 252, 241, 0.2)"
          }}>
            <RocketOutlined style={{ fontSize: 32, color: "#66fcf1" }} />
          </div>
          <Title level={3} style={{ color: "#66fcf1", margin: 0, fontWeight: 800, letterSpacing: "1px" }}>
            SOVEREIGN AGI
          </Title>
          <Text style={{ color: "#c5c6c7", fontSize: 12, textTransform: "uppercase", letterSpacing: "2px" }}>
            Control Plane Access
          </Text>
        </div>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 24, borderRadius: 8 }}
          />
        )}
        
        {success && (
          <Alert
            message={success}
            type="success"
            showIcon
            style={{ marginBottom: 24, borderRadius: 8 }}
          />
        )}

        {mode === "login" ? (
          <Form
            name="login"
            initialValues={{ remember: true }}
            onFinish={onFinishLogin}
            layout="vertical"
            requiredMark={false}
          >
            <Form.Item
              name="email"
              rules={[{ required: true, message: "Lütfen e-posta adresinizi girin!" }]}
            >
              <Input
                prefix={<UserOutlined style={{ color: "rgba(102, 252, 241, 0.5)" }} />}
                placeholder="E-posta"
                size="large"
                style={{
                  background: "rgba(11, 12, 16, 0.6)",
                  border: "1px solid rgba(102, 252, 241, 0.1)",
                  color: "#fff"
                }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: "Lütfen şifrenizi girin!" }]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: "rgba(102, 252, 241, 0.5)" }} />}
                placeholder="Şifre"
                size="large"
                style={{
                  background: "rgba(11, 12, 16, 0.6)",
                  border: "1px solid rgba(102, 252, 241, 0.1)",
                  color: "#fff"
                }}
              />
            </Form.Item>

            <Form.Item>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Form.Item name="remember" valuePropName="checked" noStyle>
                  <Checkbox style={{ color: "#c5c6c7" }}>Beni hatırla</Checkbox>
                </Form.Item>
                <a href="#" style={{ color: "#66fcf1", fontSize: 12 }}>Şifremi unuttum</a>
              </div>
            </Form.Item>

            <Form.Item style={{ marginBottom: 12 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={isLoginPending}
                block
                size="large"
                style={{
                  height: 48,
                  background: "#66fcf1",
                  color: "#0b0c10",
                  fontWeight: "bold",
                  border: "none",
                  borderRadius: 8,
                  boxShadow: "0 4px 14px 0 rgba(102, 252, 241, 0.3)"
                }}
              >
                OTURUM AÇ
              </Button>
            </Form.Item>
            
            <div style={{ textAlign: "center" }}>
              <Text style={{ color: "#c5c6c7" }}>Hesabınız yok mu? </Text>
              <a href="#" onClick={(e) => { e.preventDefault(); setMode("register"); setError(null); setSuccess(null); }} style={{ color: "#66fcf1", fontWeight: "bold" }}>Kayıt Ol</a>
            </div>
          </Form>
        ) : (
          <Form
            name="register"
            onFinish={onFinishRegister}
            layout="vertical"
            requiredMark={false}
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: "Lütfen adınızı girin!" }]}
            >
              <Input
                prefix={<IdcardOutlined style={{ color: "rgba(102, 252, 241, 0.5)" }} />}
                placeholder="Kullanıcı Adı / İsim"
                size="large"
                style={{
                  background: "rgba(11, 12, 16, 0.6)",
                  border: "1px solid rgba(102, 252, 241, 0.1)",
                  color: "#fff"
                }}
              />
            </Form.Item>
            
            <Form.Item
              name="email"
              rules={[{ required: true, message: "Lütfen e-posta adresinizi girin!" }, { type: "email", message: "Geçerli bir e-posta girin!" }]}
            >
              <Input
                prefix={<UserOutlined style={{ color: "rgba(102, 252, 241, 0.5)" }} />}
                placeholder="E-posta"
                size="large"
                style={{
                  background: "rgba(11, 12, 16, 0.6)",
                  border: "1px solid rgba(102, 252, 241, 0.1)",
                  color: "#fff"
                }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: "Lütfen şifrenizi girin!" }, { min: 6, message: "Şifre en az 6 karakter olmalı!" }]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: "rgba(102, 252, 241, 0.5)" }} />}
                placeholder="Şifre"
                size="large"
                style={{
                  background: "rgba(11, 12, 16, 0.6)",
                  border: "1px solid rgba(102, 252, 241, 0.1)",
                  color: "#fff"
                }}
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 12 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={isRegisterPending}
                block
                size="large"
                style={{
                  height: 48,
                  background: "transparent",
                  color: "#66fcf1",
                  fontWeight: "bold",
                  border: "1px solid #66fcf1",
                  borderRadius: 8,
                }}
              >
                KAYIT OL
              </Button>
            </Form.Item>
            
            <div style={{ textAlign: "center" }}>
              <Text style={{ color: "#c5c6c7" }}>Zaten hesabınız var mı? </Text>
              <a href="#" onClick={(e) => { e.preventDefault(); setMode("login"); setError(null); setSuccess(null); }} style={{ color: "#66fcf1", fontWeight: "bold" }}>Giriş Yap</a>
            </div>
          </Form>
        )}

        <div style={{ marginTop: 32, textAlign: "center", borderTop: "1px solid rgba(102, 252, 241, 0.05)", paddingTop: 24 }}>
          <Space size="large">
             <Tooltip title="Secure Connection">
                <SafetyOutlined style={{ color: "rgba(102, 252, 241, 0.4)", fontSize: 18 }} />
             </Tooltip>
             <Tooltip title="Certified Hardware">
                <SafetyCertificateOutlined style={{ color: "rgba(102, 252, 241, 0.4)", fontSize: 18 }} />
             </Tooltip>
          </Space>
          <div style={{ marginTop: 12 }}>
            <Text style={{ color: "#45a29e", fontSize: 10 }}>
              SIF-01 IDENTITY PROTOCOL ACTIVE
            </Text>
          </div>
        </div>
      </Card>
    </Layout>
  );
}

