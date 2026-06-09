# BilgeAPI v1.1.0 Release Summary

## Release Identity

- Release: `BilgeAPI v1.1.0`
- Baseline commit: `2069a36864270244c3714ead9c2efdc0d7ee12ea`
- Final commit: `see git tag target for bilgeapi-v1.1.0`
- Tag: `bilgeapi-v1.1.0`
- Tag object/hash: `reported by final seal command output`
- Migration head: `a29c4f83b2d1`

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| OpenAPI export | PASS | `openapi_export.txt` |
| OpenAPI freeze validation | PASS | `openapi_freeze_check.txt` |
| Backend regression | PASS, `206 passed` | `backend_regression.txt` |
| Coverage | PASS, `80.80%` | `backend_regression.txt` |
| Migration audit | PASS | `migration_audit.txt` |
| Container migration current | PASS, `a29c4f83b2d1 (head)` | `container_alembic_current.txt` |
| Release gate | PASS, `GO` | `release_gate.txt` |
| Docker build | PASS | `docker_build.txt` |
| Docker health | PASS, `healthy` | `docker_ps_final.txt` |
| Docker smoke | PASS, `6/6 passed` | `docker_smoke.txt` |
| Endpoint smoke | PASS | `endpoint_smoke.txt` |
| Frontend build | PASS | `frontend_build.txt` |
| Frontend route smoke | PASS, HTTP 200 | `frontend_smoke.txt` |
| Ops Console panel text source contract | PASS | `frontend_panel_text_check.txt` |

## Notes

- `py -3.13` launcher was blocked by local Windows App execution permissions. Verification ran with the accessible Python environment after dependency repair.
- `requirements.txt` contains pins incompatible with Python 3.14 for full install (`numpy==1.26.0`); minimal BilgeAPI verification dependencies were installed and used for the release checks.
- `/openapi.json` is verified by release gate and live smoke, but it is not expected to appear as a `paths` entry inside the OpenAPI document itself.
- `docker compose exec worker alembic current` could not run because `worker` was not running. Equivalent container migration evidence was collected from the running `bilgeapi` container.
