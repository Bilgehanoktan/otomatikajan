# BilgeAPI Phase 15 Live Smoke Evidence

- Base URL: `http://127.0.0.1:8100`
- Generated at: `2026-06-12T19:44:34.714103+00:00`
- Authenticated catalog check: `skipped/no key`

| Check | Endpoint | Expected | Actual | Result | Sample |
|---|---|---:|---:|---:|---|
| Health | `GET /health` | 200 | 200 | PASS | `{"status":"ok","service":"bilgeapi","version":"1.2.0","auth_mode":"api_key","skill_registry":"HEALTHY"}` |
| Root | `GET /` | 200/404 | 404 | PASS | `{"detail":"Not Found"}` |
| Metrics | `GET /metrics` | 200/401/403 | 200 | PASS | `# HELP python_gc_objects_collected_total Objects collected during gc # TYPE python_gc_objects_collected_total counter py` |
| Swagger docs | `GET /docs` | 200 | 200 | PASS | `     <!DOCTYPE html>     <html>     <head>     <meta name="viewport" content="width=device-width, initial-scale=1.0">   ` |
| OpenAPI JSON | `GET /openapi.json` | 200 | 200 | PASS | `{"openapi":"3.1.0","info":{"title":"BilgeAPI","description":"Independent Incident Intake, Diagnostic and Repair-Orchestr` |
| Catalog | `GET /v1/catalog` | 200/401/403 | 401 | PASS | `{"detail":"Unauthorized: Missing API key"}` |

Overall: PASS
