import React, { useState } from "react";
import { Card, Button, Input, Space, Typography, Alert, Divider } from "antd";
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  PauseCircleOutlined,
  SendOutlined 
} from "@ant-design/icons";

const { TextArea } = Input;
const { Title, Text } = Typography;

interface Props {
  alertId: string;
  status: string;
  onAck: () => void;
  onResolve: (justification: string) => void;
  onSuppress: (reason: string) => void;
}

export const AlertActionPanel: React.FC<Props> = ({ 
  alertId, 
  status, 
  onAck, 
  onResolve, 
  onSuppress 
}) => {
  const [justification, setJustification] = useState("");

  const isResolved = status === "RESOLVED";
  const isSuppressed = status === "SUPPRESSED";
  const isAck = status === "ACKNOWLEDGED";

  return (
    <Card 
      title={<Title level={5} style={{ margin: 0 }}>Operator Actions</Title>}
      size="small"
      style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
    >
      <Space direction="vertical" style={{ width: "100%" }} size={16}>
        <Alert
          message={`Current Status: ${status}`}
          type={status === "OPEN" ? "warning" : "info"}
          showIcon
        />

        <div style={{ background: "#f5f5f5", padding: "12px", borderRadius: "8px" }}>
          <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
            JUSTIFICATION / NOTES
          </Text>
          <TextArea 
            rows={3} 
            placeholder="Explain why this alert is being resolved or suppressed..." 
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            disabled={isResolved || isSuppressed}
          />
        </div>

        <Divider style={{ margin: "8px 0" }} />

        <Space wrap style={{ justifyContent: "center", width: "100%" }}>
          <Button 
            icon={<CheckCircleOutlined />} 
            onClick={onAck}
            disabled={status !== "OPEN"}
            loading={false}
          >
            Acknowledge
          </Button>

          <Button 
            type="primary"
            icon={<SendOutlined />} 
            onClick={() => onResolve(justification)}
            disabled={status === "RESOLVED" || status === "SUPPRESSED" || !justification}
          >
            Resolve
          </Button>

          <Button 
            danger
            icon={<PauseCircleOutlined />} 
            onClick={() => onSuppress(justification)}
            disabled={status === "SUPPRESSED" || status === "RESOLVED" || !justification}
          >
            Suppress
          </Button>
        </Space>

        {(isResolved || isSuppressed) && (
          <Text type="secondary" style={{ fontSize: "12px", textAlign: "center", display: "block" }}>
            This alert is closed. No further actions required.
          </Text>
        )}
      </Space>
    </Card>
  );
};
