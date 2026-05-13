# Egemen YAZ Repair Prompt

Incident: INC-001
Error type: AssertionError
Summary: Sample failed repair flow smoke case.

Failed command:
```text

```

Failed test:
```text
tests/repair/test_sample.py::test_sample
```

Suspected files:
- services/repair/repair_case_builder.py
- tests/repair/test_sample.py

Traceback:
```text
Traceback (most recent call last):
  File "services/repair/repair_case_builder.py", line 10, in build_repair_case
    assert False
AssertionError
```

Repair plan:
```text
repair_plan_id: RP-2e4b7d12adf0
root_cause_hypothesis: Sample failed repair flow smoke case.
target_files:
- services/repair/repair_case_builder.py
- tests/repair/test_sample.py
expected_tests:
```

Produce a minimal patch only for allowed files. Do not touch forbidden paths, secrets, production config, migrations, auth, governance guardrails, rollback, budget, or cost controls. The output must be a unified diff suitable for `git apply`.
