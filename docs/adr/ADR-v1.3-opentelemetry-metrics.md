# Architectural Decision Record — ADR-v1.3-opentelemetry-metrics

* **Status:** Proposed
* **Date:** 2026-06-12
* **Decider:** AI Coding Agent (Antigravity) & Operator

---

## 1. Context

Operations teams require real-time visibility into BilgeAPI performance metrics (such as latency percentiles, error rates, and connection pool status) to detect anomalies quickly and prevent degradation. Currently, only basic Traefik logging is active.

---

## 2. Decision

We will integrate the OpenTelemetry Python SDK and expose a Prometheus-formatted `/metrics` endpoint in BilgeAPI v1.3.

1. **Prometheus Metrics Exporter:** Expose a secure route `/metrics` restricted to the `bilgeapi.admin` role.
2. **Metrics Tracked:**
   * `bilgeapi_http_requests_total`: Counter by route, method, status code.
   * `bilgeapi_http_request_duration_seconds`: Histogram of response latency.
   * `bilgeapi_db_connections_active`: Gauge of database connection pool utilization.
   * `bilgeapi_watchdog_findings_total`: Counter of security warnings cataloged by severity.
3. **OpenTelemetry Integration:** Support optional exporting of request traces to OTel collectors (e.g. Jaeger) when configured.

---

## 3. Consequences

* **Pros:**
  * Enables standard monitoring dashboard integrations (e.g. Grafana).
  * Promotes early error detection and automated scaling triggers.
* **Cons:**
  * Introduces minor runtime overhead for metric calculations.
  * Adds dependencies (`opentelemetry-api`, `opentelemetry-sdk`, `prometheus-client`).
