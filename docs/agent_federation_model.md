# Agent Federation Model — Phase 19

## Overview
This document describes the structural model of "Agent Clusters" and how they are registered and managed within the federation.

---

## 🧩 1. The Cluster Architecture
A **Cluster** is a logical grouping of agents sharing a domain expertise and resource pool.

### Specialized Clusters (Standard):
1.  **SEC-OVERWATCH (Security Cluster):** Hardening, RBAC auditing, vulnerability patching.
2.  **OPS-REFLEX (DevOps Cluster):** Scaling, infra-stability, rollback management.
3.  **LOGIC-CORTEX (Domain Experts):** Business logic, workflow optimization, accuracy.
4.  **COST-GUARDIAN (Economy Cluster):** Token efficiency, provider routing, budget enforcement.

---

## 🛠️ 2. Cluster Metadata (Registry Schema)
Registered in `configs/agent_cluster_registry.yaml`, each cluster must define:
- `cluster_id`: Unique identifier (e.g., `logic-cortex-01`).
- `expertise`: List of tags describing domain knowledge.
- `autonomy_limit`: Maximum allowed autonomy level (L1-L4).
- `cost_limit_daily`: Maximum token cost per 24h.
- `priority`: Global priority ranking (Security = 10, Improvement = 5).

---

## 🛰️ 3. Inter-Cluster Communication
Clusters communicate through the **Federation Service Bus (FSB)**:
- **Request:** Cluster A requests a "Security Review" from SEC-OVERWATCH before execution.
- **Evidence:** Communications involve sharing JSON-LD based "Thought Fragments" for auditability.
- **Handover:** A task can be handed over from `LOGIC` to `OPS` once the core code is generated.

---

## 📊 4. Trust & Confidence Scoring (TCS)
A cluster's influence on the Global Overlord depends on its TCS score (0.0 - 1.0).
- **Gain:** Successful autonomous resolution, positive operator feedback.
- **Loss:** Rollback triggered by their proposal, budget breach, security regression.

---

> [!TIP]
> Clusters are "sandboxed" in terms of resources but "federated" in terms of knowledge. A breach in one cluster is quarantined immediately by the **Emergency Gate** (Phase 18).
