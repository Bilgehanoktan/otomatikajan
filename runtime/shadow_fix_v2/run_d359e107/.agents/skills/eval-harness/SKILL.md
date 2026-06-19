---
name: eval-harness
description: Formal evaluation framework for agent-assisted workflows, eval-driven development, pass/fail criteria, and regression checks.
origin: ECC
---

# Eval Harness Skill

Use this skill when defining measurable success criteria for AI-assisted development workflows, prompt changes, agent behavior, or reliability-sensitive automation.

## When to Activate

- Setting up eval-driven development for agent or automation workflows.
- Defining pass/fail criteria before implementation.
- Measuring reliability with pass@k or repeated-run checks.
- Creating regression suites for prompt, tool, or workflow changes.
- Benchmarking behavior across model or agent versions.

## Core Principle

Eval-driven development treats evals as tests for AI behavior:

- Define expected behavior before implementation.
- Prefer deterministic code graders when possible.
- Track regressions over time.
- Require human review for security-sensitive or ambiguous outputs.

## Eval Types

### Capability Eval

```markdown
[CAPABILITY EVAL: feature-name]
Task: Description of what the agent should accomplish.
Success Criteria:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
Expected Output: Concrete expected artifact or behavior.
```

### Regression Eval

```markdown
[REGRESSION EVAL: feature-name]
Baseline: Commit, checkpoint, or known-good behavior.
Tests:
- existing-test-1: PASS/FAIL
- existing-test-2: PASS/FAIL
- existing-test-3: PASS/FAIL
Result: X/Y passed.
```

## Grader Types

### Code-Based Grader

Use deterministic checks first.

```bash
rg "export function handleAuth" src/auth.ts
npm test -- --testPathPattern auth
npm run build
```

### Model-Based Grader

Use only when deterministic checks cannot capture the quality bar.

```markdown
[MODEL GRADER PROMPT]
Evaluate the change:
1. Does it solve the stated problem?
2. Is it well-structured?
3. Are edge cases handled?
4. Is error handling appropriate?

Score: 1-5
Reasoning: Short explanation.
```

### Human Grader

Require human review for high-risk behavior.

```markdown
[HUMAN REVIEW REQUIRED]
Change: Description of what changed.
Reason: Why manual review is needed.
Risk Level: LOW/MEDIUM/HIGH
```

## Metrics

- `pass@1`: first-attempt success rate.
- `pass@3`: success within three attempts.
- `pass^3`: three consecutive successful runs.

Use `pass^k` for critical regressions where consistency matters more than occasional success.

## Workflow

### 1. Define

```markdown
## EVAL DEFINITION: feature-xyz

Capability Evals:
- [ ] Can create the required artifact.
- [ ] Handles invalid input safely.
- [ ] Produces a clear report.

Regression Evals:
- [ ] Existing tests still pass.
- [ ] Existing API contract is unchanged.
- [ ] Existing security constraints still hold.

Success Metrics:
- Capability evals pass at pass@3.
- Regression evals pass at pass^3 for critical paths.
```

### 2. Implement

Build the smallest change that can satisfy the evals.

### 3. Evaluate

Run deterministic tests first, then model or human graders only where needed.

### 4. Report

```markdown
EVAL REPORT: feature-xyz

Capability Evals:
- create-artifact: PASS
- invalid-input: PASS
- report-quality: PASS

Regression Evals:
- test-suite: PASS
- api-contract: PASS
- security-constraints: PASS

Status: READY FOR REVIEW
```

## Storage Pattern

Prefer a repo-local path when a persistent eval suite is needed:

```text
tests/
  evals/
    feature-xyz.md
    feature-xyz.log
    baseline.json
```

## Best Practices

- Define evals before code or prompt changes.
- Keep evals fast enough to run often.
- Version evals with the code they protect.
- Use code graders for objective checks.
- Keep model graders short and scoped.
- Never fully automate security approval.
