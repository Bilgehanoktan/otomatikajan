# Architectural Decision Record — ADR-v1.3-release-metadata-service

* **Status:** Proposed
* **Date:** 2026-06-12
* **Decider:** AI Coding Agent (Antigravity) & Operator

---

## 1. Context

During the BilgeAPI v1.2.0 release, we discovered a version metadata drift where the `/health` endpoint returned version `1.0.0` while the code baseline was at `1.2.0`. Version strings and deployment git SHAs are currently dispersed across config properties, routers, and scripts. We need a centralized, structured way to resolve and expose release metadata dynamically.

---

## 2. Decision

We will implement a centralized `ReleaseMetadataService` and expose a new endpoint `/v1/system/release` in BilgeAPI v1.3.

1. **Centralized Versioning:** Maintain version details in a single location (`apps/bilgeapi/config.py`).
2. **Build-Time Compilation:** Generate a static JSON file (`release_manifest.json`) during the Docker build process containing the build timestamp, target environment, and commit SHA.
3. **Endpoint Definition:** Expose a read-only endpoint `/v1/system/release` returning the compiled manifest and active settings state.

---

## 3. Consequences

* **Pros:**
  * Eliminates metadata drifts (single source of truth).
  * Exposes deployment trace (git commit SHA, build time) for easier debugging.
  * Allows automated deployment verification in CI/CD.
* **Cons:**
  * Requires generating the `release_manifest.json` during the CI build stage.
