# Bulk Test Rerun Attempt

Date: 2026-06-12
Branch: codex/project-factory-policy-governance
Scope: full CI / frontend / backend / docker

## Checked commit

```text
718b7b356ac7478418950da14a32336917def566
```

## GitHub status check

Result:

```text
statuses: []
```

## Workflow run check

Result:

```text
workflow_runs: []
```

## CI coverage in workflow file

The CI workflow defines these gates:

- Ruff lint
- Ruff format check
- Bandit scan
- pip-audit scan
- Backend import smoke
- Backend production import smoke
- Pytest backend suite
- Playwright UI E2E
- Frontend lint
- Frontend build
- Docker build gate

## Interpretation

No completed GitHub status or workflow run was visible through the connector for the checked commit.

This record does not claim tests passed. It records that the test rerun was checked and no runner result was available.

## Required manual or Actions run

Run the workflow manually from GitHub Actions:

```text
Actions -> CI — Test, Lint, Security -> Run workflow -> branch codex/project-factory-policy-governance
```

Or run locally:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
make test
make lint
make security
docker build --target production-slim -t otomatikajan:ci .
```

## Status

Pending GitHub Actions or local runner execution.
