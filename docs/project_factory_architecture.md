# CEO Project Factory Mode — System Architecture

## 1. Executive Summary

The **CEO Project Factory Mode** is designed to transform high-level user ideas or system prompts into fully functional, production-ready, and thoroughly verified software applications. The entire process runs under strict governance, requiring explicit human approval before scaffolding code, executing sandboxed verification, or deploying.

---

## 2. Core Architecture & Workflow

```
[ User Prompt / Idea ]
        │
        ▼
 ┌──────────────┐
 │ System Spec  │◄─── (gpt-engineer patterns)
 │  Generator   │
 └──────┬───────┘
        │
        ▼
 ┌──────────────┐
 │ Scaffold     │◄─── (backstage/software-templates patterns)
 │ Engine       │
 └──────┬───────┘
        │
        ▼
 ┌──────────────┐
 │ Multi-Agent  │◄─── (crewai role-based synthesis)
 │ Coder Loop   │
 └──────┬───────┘
        │
        ▼
 ┌──────────────┐
 │ Sandbox &    │◄─── (stagehand visual testing)
 │ Verifier Mesh│
 └──────┬───────┘
        │
        ▼
 ┌──────────────┐
 │ Human-Gate   │
 │   Approval   │
 └──────┬───────┘
        │
        ▼
[ Production Deployment / Git Push ]
```

---

## 3. Workflow Steps

### Phase 1: Intake & System Spec Generation
* **Inspiration**: `AntonOsika/gpt-engineer`
* **Process**: The system processes the raw user prompt and runs a conceptual breakdown to generate a precise `system_spec.json` outlining files, folder architecture, dependencies, tech stack (e.g. Next.js, FastAPI, standard Tailwind CSS / Vanilla CSS), and API endpoints.

### Phase 2: Scaffold Engine & Template Rendering
* **Inspiration**: `backstage/software-templates`
* **Process**: The system reads declarative templates (yaml blueprints) that map typical application layouts. It renders initial project directories, configurations (e.g. package.json, eslint, docker-compose), and skeleton files in an isolated temporary project path:
  `E:\Users\bilge\Downloads\generated-projects\<project-id>\`

### Phase 3: Multi-Agent Coder & Implementation Loop
* **Inspiration**: `crewaiinc/crewai`, `OpenHands/software-agent-sdk`, `swe-agent/mini-swe-agent`
* **Process**: Specialized agents are dynamically defined and launched to fulfill components defined in the system spec:
  1. **Core Developer Agent**: Generates modules, files, services, and routes.
  2. **TDD / Test Generator Agent**: Writes unit, integration, and E2E test suites proactively before code execution.
  3. **Security Reviewer Agent**: Checks written code for hardcoded secrets, injection, and unsafe imports.

### Phase 4: Sandboxed Verification & Telemetry
* **Inspiration**: `browserbase/stagehand`, `browserbase/stagehand-python`
* **Process**: The project is built and started inside a secure local sandbox (e.g., Docker container or isolated workspace). The Verifier Mesh runs:
  1. Automated backend test suites (pytest/jest).
  2. Frontend Playwright assertions via Stagehand to verify UI accessibility, console errors, and page load completeness.

### Phase 5: Human Gate & Signoff Rollout
* **Process**: The full system spec, agent transcripts, verifier logs, and UI screenshots are aggregated into a unified deployment report. A Human Gate is triggered. Once the user clicks **Approve**, the code is pushed to the target Git repository or deployed locally.

---

## 4. Isolation & Workspace Model

To prevent project creation from interfering with the main **Egemen YAZ** core framework, the system enforces a strict isolation policy:

> [!IMPORTANT]
> * **Independent Workspace Directories**: New projects are created inside designated sub-folders under `E:\Users\bilge\Downloads\generated-projects\`. They never share the python environment, node_modules, or global environment variables of the main engine.
> * **Sandboxed Port Allocation**: During testing and verification, generated applications are bound to isolated ports (e.g., dynamic ports starting at `3000` to `4000`) verified as unused before boot.
> * **Docker Sandbox Limits**: Command execution for running test suites or starting dev servers uses isolated Docker profiles configured with memory limits (max 2GB) and restricted internet access.
