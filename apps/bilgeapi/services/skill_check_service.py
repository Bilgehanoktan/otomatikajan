import ast
import re
import logging
from typing import List, Dict, Any, Optional
from apps.bilgeapi.schemas.skills import SkillCheckResponse, SkillCheckItem
from apps.bilgeapi.services.skill_registry import SkillRegistryService
from apps.bilgeapi.core.workspace import WorkspaceManager
from apps.bilgeapi.memory.db import get_workspace_db_session
from apps.bilgeapi.memory.models import AuditLogModel, DecisionModel

logger = logging.getLogger(__name__)

def evaluate_ast_node(node) -> Optional[str]:
    """Statically evaluates simple AST nodes into their string values if they are literals or concatenations of literals."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    elif hasattr(ast, "Str") and isinstance(node, getattr(ast, "Str")):  # Fallback for older python versions
        return node.s
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = evaluate_ast_node(node.left)
        right = evaluate_ast_node(node.right)
        if left is not None and right is not None:
            return left + right
    return None

class SkillVisitor(ast.NodeVisitor):
    def __init__(self):
        self.blocked_reasons = []
        self.detected_constructs = []

    def visit_Import(self, node):
        for name in node.names:
            parts = name.name.split('.')
            base_module = parts[0]
            if base_module in {"os", "sys", "subprocess", "shutil", "socket", "pty", "importlib"}:
                self.blocked_reasons.append(f"Forbidden import: {name.name}")
                self.detected_constructs.append(f"import {name.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            parts = node.module.split('.')
            base_module = parts[0]
            if base_module in {"os", "sys", "subprocess", "shutil", "socket", "pty", "importlib"}:
                self.blocked_reasons.append(f"Forbidden import from: {node.module}")
                self.detected_constructs.append(f"from {node.module} import ...")
        self.generic_visit(node)

    def visit_Call(self, node):
        # 1. Direct function calls: eval(), exec(), compile(), open(), __import__()
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # E.g. os.system, subprocess.run, subprocess.Popen
            value_name = None
            if isinstance(node.func.value, ast.Name):
                value_name = node.func.value.id
            if value_name:
                func_name = f"{value_name}.{node.func.attr}"
            else:
                func_name = node.func.attr

        # Check blocked direct functions
        if func_name in {"eval", "exec", "compile", "open", "__import__"}:
            self.blocked_reasons.append(f"Forbidden function call: {func_name}")
            self.detected_constructs.append(func_name)

        # Check os.system, subprocess.run, subprocess.Popen, importlib.import_module
        elif func_name in {"os.system", "subprocess.run", "subprocess.Popen", "importlib.import_module"}:
            self.blocked_reasons.append(f"Forbidden system/subprocess call: {func_name}")
            self.detected_constructs.append(func_name)

        # 2. getattr(builtins, ...) or getattr(anything, "eval"/"exec"...)
        if isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2:
            attr_val = evaluate_ast_node(node.args[1])
            if attr_val in {
                "eval", "exec", "compile", "open", "__import__",
                "system", "run", "Popen", "import_module", "subprocess",
                "os", "sys", "shutil", "socket", "pty", "importlib"
            }:
                self.blocked_reasons.append(f"Obfuscated getattr call fetching: {attr_val}")
                self.detected_constructs.append(f"getattr(..., {attr_val})")

        # 3. File write / delete operations
        method_name = None
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
        if method_name in {"write", "remove", "unlink", "rmdir", "rmtree"}:
            self.blocked_reasons.append(f"Forbidden file write/delete operation: {method_name}")
            self.detected_constructs.append(method_name)

        self.generic_visit(node)

    def visit_Attribute(self, node):
        value_name = None
        if isinstance(node.value, ast.Name):
            value_name = node.value.id
        if value_name:
            full_attr = f"{value_name}.{node.attr}"
            if full_attr in {"os.system", "subprocess.run", "subprocess.Popen", "importlib.import_module"}:
                self.blocked_reasons.append(f"Forbidden attribute access: {full_attr}")
                self.detected_constructs.append(full_attr)
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in {"eval", "exec", "compile", "open", "__import__"}:
            if isinstance(node.ctx, ast.Load):
                self.blocked_reasons.append(f"Forbidden name access: {node.id}")
                self.detected_constructs.append(node.id)
        self.generic_visit(node)


def check_regex_fallback(patch_code: str) -> Dict[str, Any]:
    blocked_keywords = [
        "eval", "exec", "compile", "open", "__import__",
        "subprocess", "os.system", "shutil", "socket", "pty",
        "importlib", "write", "remove", "unlink", "rmdir", "rmtree"
    ]
    detected = []
    reasons = []
    for kw in blocked_keywords:
        pattern = rf"\b{re.escape(kw)}\b"
        if re.search(pattern, patch_code):
            detected.append(kw)
            reasons.append(f"Forbidden construct '{kw}' detected by regex fallback")
            
    return {
        "allowed": len(detected) == 0,
        "blocked_reasons": reasons,
        "detected_constructs": detected
    }


class SkillCheckService:
    def __init__(self, registry: SkillRegistryService, ledger_service: Optional[Any] = None):
        self.registry = registry
        self.ledger_service = ledger_service

    async def _append_ledger_event(self, event_type: str, payload: Dict[str, Any]):
        if not self.ledger_service:
            return
        try:
            await self.ledger_service.append_event(
                chain_id="skill_check_chain",
                event_type=event_type,
                entity_type="skill_check",
                entity_id="check_service",
                actor_id="system",
                payload=payload
            )
        except Exception as exc:
            logger.warning("Failed to log skill check event to review ledger: %s", exc)

    async def _log_blocked_check_to_sqlite(
        self,
        tenant_id: str,
        target_id: str,
        blocked_reasons: List[str],
        detected_constructs: List[str],
        risk_level: str,
        risk_score: float,
        file_path: str
    ):
        try:
            workspace_dir = WorkspaceManager().workspace_dir
            async with get_workspace_db_session(workspace_dir) as session:
                audit = AuditLogModel(
                    tenant_id=tenant_id,
                    event_type="SKILL_CHECK_BLOCKED",
                    actor_id="system",
                    actor_type="system",
                    action="patch_check",
                    target=file_path,
                    status="BLOCKED",
                    risk_level=risk_level,
                    before_state={"patch_target": file_path, "detected_constructs": detected_constructs},
                    after_state={"blocked_reasons": blocked_reasons}
                )
                session.add(audit)

                decision = DecisionModel(
                    tenant_id=tenant_id,
                    task_id=target_id,
                    classification="SKILL_CHECK_BLOCKED",
                    risk_score=risk_score,
                    risk_level=risk_level,
                    eligibility="BLOCKED",
                    requires_human_gate=False,
                    decision_reason=f"Blocked construct(s) detected: {', '.join(detected_constructs)}",
                    reasons=blocked_reasons
                )
                session.add(decision)
                await session.flush()
        except Exception as e:
            logger.error(f"Failed to log blocked check to SQLite memory: {e}")

    def analyze_code(self, patch_code: str, language: str = "python", file_path: str = "") -> dict:
        analysis_mode = "AST" if language == "python" else "REGEX"
        allowed = True
        risk_level = "LOW"
        risk_score = 0.0
        blocked_reasons = []
        detected_constructs = []

        if language == "python":
            try:
                tree = ast.parse(patch_code)
                visitor = SkillVisitor()
                visitor.visit(tree)
                blocked_reasons = visitor.blocked_reasons
                detected_constructs = visitor.detected_constructs
            except SyntaxError as e:
                # Python syntax errors must fail closed.
                return {
                    "allowed": False,
                    "risk_level": "HIGH",
                    "risk_score": 1.0,
                    "blocked_reasons": [f"Python syntax error (fail-closed): {str(e)}"],
                    "detected_constructs": ["SyntaxError"],
                    "language": language,
                    "analysis_mode": "AST"
                }
        else:
            res = check_regex_fallback(patch_code)
            blocked_reasons = res["blocked_reasons"]
            detected_constructs = res["detected_constructs"]

        if len(blocked_reasons) > 0:
            allowed = False
            risk_level = "HIGH"
            risk_score = 1.0
        else:
            allowed = True
            risk_level = "LOW"
            risk_score = 0.0

        return {
            "allowed": allowed,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "blocked_reasons": blocked_reasons,
            "detected_constructs": detected_constructs,
            "language": language,
            "analysis_mode": analysis_mode
        }

    async def check_patch(self, target_type: str, target_id: str, skill_names: List[str], patch_code: str, tenant_id: Optional[str] = None) -> SkillCheckResponse:
        # SIF-01: missing tenant context fails closed
        if not tenant_id:
            raise ValueError("tenant_id is required (missing tenant context fails closed)")

        if not self.registry.initialized:
            await self._append_ledger_event(
                event_type="SKILL_POLICY_BLOCKED",
                payload={"target_type": target_type, "target_id": target_id, "error": "Registry not initialized"}
            )
            raise RuntimeError("Skill registry has not been initialized (fail-closed).")

        checks: List[SkillCheckItem] = []
        overall_status = "PASS"

        # Determine language based on patch_code characteristics and target_id
        is_python = False
        if target_id and target_id.endswith(".py"):
            is_python = True
        elif patch_code:
            # Check if it looks like python or parses cleanly
            python_indicators = ["def ", "class ", "import ", "print(", "import\n", "from ", " = ", "elif ", "return "]
            if any(ind in patch_code for ind in python_indicators):
                is_python = True
            elif any(func in patch_code for func in ["getattr(", "eval(", "exec(", "open(", "subprocess.", "os.system", "__import__"]):
                is_python = True
            else:
                # Try to parse it. If it successfully parses as AST, we can treat it as python
                try:
                    ast.parse(patch_code)
                    is_python = True
                except SyntaxError:
                    is_python = False

        language = "python" if is_python else "other"

        analysis = self.analyze_code(patch_code, language=language, file_path=target_id)
        
        # Log to SQLite if blocked
        if not analysis["allowed"]:
            await self._log_blocked_check_to_sqlite(
                tenant_id=tenant_id,
                target_id=target_id,
                blocked_reasons=analysis["blocked_reasons"],
                detected_constructs=analysis["detected_constructs"],
                risk_level=analysis["risk_level"],
                risk_score=analysis["risk_score"],
                file_path=target_id
            )

        for name in skill_names:
            try:
                skill_meta = self.registry.get_skill(name)
            except Exception as exc:
                await self._append_ledger_event(
                    event_type="SKILL_POLICY_BLOCKED",
                    payload={
                        "target_type": target_type,
                        "target_id": target_id,
                        "skill": name,
                        "error": f"Unknown or un-allowlisted skill: {str(exc)}"
                    }
                )
                raise ValueError(f"Security violation: Unknown or un-allowlisted skill '{name}' requested for check.") from exc

            skill_result = "passed"
            reason = None

            if not analysis["allowed"]:
                skill_result = "blocked"
                reason = f"Forbidden patterns detected: {'; '.join(analysis['blocked_reasons'])}"
            else:
                # Custom skill checks
                if name == "bilgeapi-pr-verification-gate":
                    sensitive_files = ["auth.py", "config.py", "database.py", "self_healing.py"]
                    found_sensitive = [f for f in sensitive_files if f in patch_code]
                    if found_sensitive:
                        skill_result = "review_required"
                        reason = f"Sensitive files modified: {', '.join(found_sensitive)}"

                elif name == "bilgeapi-skill-integrity":
                    if any(x in patch_code for x in ["docs/SKILL_POLICY.md", "hash_manifest.json", "docs/agent-skills/"]):
                        skill_result = "blocked"
                        reason = "Modifying skill policy or directory is strictly forbidden"

                elif name == "bilgeapi-self-healing-policy":
                    found_git = [x for x in ["git push", "git merge", "force"] if x in patch_code]
                    found_mutations = [x for x in ["subprocess.", "os.system", "shutil.rmtree", "os.remove", "os.unlink", "os.rmdir"] if x in patch_code]
                    if found_git:
                        skill_result = "blocked"
                        reason = f"Forbidden git operations: {', '.join(found_git)}"
                    elif found_mutations:
                        skill_result = "blocked"
                        reason = f"Dangerous mutations in self-healing: {', '.join(found_mutations)}"

            if skill_result == "blocked":
                overall_status = "BLOCKED"
            elif skill_result == "review_required" and overall_status != "BLOCKED":
                overall_status = "REVIEW_REQUIRED"

            checks.append(SkillCheckItem(skill=name, result=skill_result, reason=reason))

        event_type = "SKILL_CHECK_FAILED" if overall_status == "BLOCKED" else "SKILL_CHECK_APPLIED"
        await self._append_ledger_event(
            event_type=event_type,
            payload={
                "target_type": target_type,
                "target_id": target_id,
                "status": overall_status,
                "checks": [c.model_dump() for c in checks]
            }
        )

        return SkillCheckResponse(
            target_type=target_type,
            target_id=target_id,
            status=overall_status,
            passed=(overall_status == "PASS"),
            checks=checks
        )
