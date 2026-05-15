"use client";

import React, { useState, useEffect } from "react";
import { Card, Table, Typography, Tag, Space, Tooltip } from "antd";
import { AuditOutlined, InfoCircleOutlined } from "@ant-design/icons";

const { Text } = Typography;

export const OperatorActionLedgerPanel: React.FC<{ rolloutId?: string }> = ({ rolloutId }) => {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (rolloutId) {
            setLoading(true);
            fetch(`/api/v1/ui-repair/pilot/operator-actions?rollout_id=${rolloutId}`)
                .then(res => res.json())
                .then(items => {
                    setData(items);
                    setLoading(false);
                });
        }
    }, [rolloutId]);

    const columns = [
        {
            title: "Time",
            dataIndex: "created_at",
            key: "created_at",
            render: (val: string) => new Date(val).toLocaleString(),
            width: 180,
        },
        {
            title: "Operator",
            dataIndex: "operator",
            key: "operator",
            render: (val: string) => <Tag icon={<AuditOutlined />}>{val}</Tag>,
            width: 120,
        },
        {
            title: "Action",
            dataIndex: "action_type",
            key: "action_type",
            render: (val: string) => <Text strong>{val.replace(/_/g, ' ')}</Text>,
            width: 150,
        },
        {
            title: "Rationale",
            dataIndex: "rationale",
            key: "rationale",
            render: (val: string) => (
                <Tooltip title={val}>
                    <div style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {val}
                    </div>
                </Tooltip>
            ),
        },
        {
            title: "Target",
            key: "target",
            render: (_: any, record: any) => record.target_id ? <Tag>{record.target_type}: {record.target_id.slice(0,8)}</Tag> : "-",
            width: 150,
        }
    ];

    return (
        <Card title="Operator Action Ledger" size="small">
            <Table 
                dataSource={data} 
                columns={columns} 
                size="small" 
                loading={loading}
                pagination={{ pageSize: 5 }}
            />
        </Card>
    );
};
