# Architectural Decision Record — ADR-v1.3-ast-skill-check-service

* **Status:** Proposed
* **Date:** 2026-06-12
* **Decider:** AI Coding Agent (Antigravity) & Operator

---

## 1. Context

The current `SkillCheckService` relies on text-based keyword matching and regex checks to detect forbidden execution attempts by external agents. This regex approach suffers from high false-positive rates (e.g., matching keywords inside string literals or comments) and is vulnerable to evasion (e.g., using string concatenation or dynamic execution wrappers).

---

## 2. Decision

We will upgrade `SkillCheckService` to perform structure-aware Abstract Syntax Tree (AST) analysis on all incoming agent patch suggestions in v1.3.

1. **AST Parsing:** Parse code using Python's native `ast` library before verification.
2. **Custom NodeVisitor:** Implement an `ast.NodeVisitor` subclass (`SkillVisitor`) to inspect:
   * **Imports:** Block imports like `os`, `sys`, `subprocess`, `shutil` unless permitted.
   * **Function Calls:** Flag unsafe functions (e.g. `eval`, `exec`, `open`, `write`).
   * **Subprocess execution:** Block arguments containing `rm -rf`, `chmod`, etc.
3. **Structured Warnings:** Return diagnostic logs detailing the exact line, column, and matched node type for any validation failure.

---

## 3. Consequences

* **Pros:**
  * Eliminates false positives from comments and string literals.
  * Significantly increases evasion resistance against obfuscated python code.
  * Provides granular audit logs containing node location.
* **Cons:**
  * Restricts analysis to valid Python code (non-python files must still use secondary checks).
  * Marginally increases execution time during parsing.
