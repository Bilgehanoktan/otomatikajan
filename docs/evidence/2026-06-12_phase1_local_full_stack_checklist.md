# Phase 1 Local and Full-Stack Checklist

Date: 2026-06-12
Environment: Local developer machine / Docker local stack
Branch: codex/project-factory-policy-governance
Related issue: #2

## Checks

| Check | Command | Result |
|---|---|---|
| Install dependencies | `make install` | Not run in GitHub connector |
| Local API | `make dev` | Not run in GitHub connector |
| API health | `curl -f http://localhost:8000/health` | Not run in GitHub connector |
| API docs | `curl -f http://localhost:8000/docs` | Not run in GitHub connector |
| Minimal Docker | `docker compose up --build` | Not run in GitHub connector |
| Full-stack Docker | `docker compose --profile full-stack up --build` | Not run in GitHub connector |
| PowerShell smoke | `powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1` | Not run in GitHub connector |
| Full-stack smoke | `powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_dev.ps1 -Mode full-stack-local` | Not run in GitHub connector |
| BilgeAPI smoke | `make bilgeapi-smoke` | Not run in GitHub connector |

## Result

Pending local execution.

## Notes

This file is the evidence checklist for Phase 1. The GitHub connector cannot execute local Docker or host-level smoke tests. Results should be filled after running the commands on the target developer machine or CI runner.
