# Egemen YAZ Repair Prompt

Incident: {incident_id}
Error type: {error_type}
Summary: {summary}

Failed command:
```text
{failed_command}
```

Failed test:
```text
{failed_test}
```

Suspected files:
{suspected_files}

Traceback:
```text
{traceback}
```

Repair plan:
```text
{repair_plan}
```

Produce a minimal patch only for allowed files. Do not touch forbidden paths, secrets, production config, migrations, auth, governance guardrails, rollback, budget, or cost controls. The output must be a unified diff suitable for `git apply`.
