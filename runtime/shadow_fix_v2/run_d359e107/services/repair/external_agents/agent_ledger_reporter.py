import hashlib
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.repair_models import AgentRunModel

class AgentLedgerReporter:
    SECRET_PATTERNS = [
        re.compile(r'(?i)(api[-_]?key|token|password|secret|auth|bearer|credential|passphrase|pwd|ssh[-_]?key)\s*[:=]\s*([a-zA-Z0-9_\-\.\~]+)'),
        re.compile(r'(?i)(db_url|database_url)\s*[:=]\s*([a-zA-Z0-9_+:\-\./\\@]+)'),
        # Pattern for connection URI passwords
        re.compile(r'(?i)(mongodb(?:\+srv)?|postgres(?:ql)?|mysql|redis(?:s)?)://[^:]+:([^@/]+)@'),
        # Pattern for generic JWT tokens
        re.compile(r'[a-zA-Z0-9_\-]{20,}\.[a-zA-Z0-9_\-]{20,}\.[a-zA-Z0-9_\-]{20,}')
    ]

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """Redacts sensitive credentials, tokens, and credentials from log texts."""
        if not text:
            return ""
        
        redacted = text
        for pattern in cls.SECRET_PATTERNS:
            # For match group replacements
            def replace_match(m):
                # If there are groups, redact the sensitive part (group 2 usually)
                if len(m.groups()) >= 2:
                    full_match = m.group(0)
                    secret_part = m.group(2)
                    # Keep the key identifier part, replace the secret, preserve the rest of the match
                    parts = full_match.split(secret_part, 1)
                    prefix = parts[0]
                    suffix = parts[1] if len(parts) > 1 else ""
                    return f"{prefix}[REDACTED]{suffix}"
                return "[REDACTED]"
                
            redacted = pattern.sub(replace_match, redacted)
        return redacted

    @classmethod
    def truncate_text(cls, text: str, max_chars: int = 20000) -> str:
        """Truncates text to maximum allowed character boundary."""
        if not text:
            return ""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n... [TRUNCATED DUE TO LENGTH LIMIT]"

    @classmethod
    def compute_sha256(cls, data: Any) -> str:
        """Computes SHA256 hex string for a given payload (string or json structure)."""
        if isinstance(data, (dict, list)):
            serialized = json.dumps(data, sort_keys=True)
        else:
            serialized = str(data or "")
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    async def create_run_record(
        cls,
        db: AsyncSession,
        run_id: str,
        agent_key: str,
        input_parameters: Dict[str, Any],
        sandbox_mode: str,
        network_policy: str,
        created_by: Optional[str] = None,
        timeout_seconds: int = 300
    ) -> AgentRunModel:
        """Creates a PENDING execution record in the ledger database."""
        input_hash = cls.compute_sha256(input_parameters)
        
        run = AgentRunModel(
            id=None, # Will be set by default UUID generator or manually
            run_id=run_id,
            agent_key=agent_key,
            status="PENDING",
            input_parameters=input_parameters,
            input_hash=input_hash,
            sandbox_mode=sandbox_mode,
            network_policy=network_policy,
            timeout_seconds=timeout_seconds,
            created_by=created_by,
            created_at=datetime.now(timezone.utc)
        )
        db.add(run)
        await db.commit()

        # Log event to immutable governance proof chain
        await cls._log_to_governor_chain(
            db, 
            run_id=run_id, 
            agent_key=agent_key, 
            event_name="AGENT_RUN_REQUESTED", 
            payload={
                "run_id": run_id,
                "agent_key": agent_key,
                "sandbox_mode": sandbox_mode,
                "network_policy": network_policy,
                "input_hash": input_hash
            },
            actor=created_by
        )
        return run

    @classmethod
    async def start_run_record(
        cls,
        db: AsyncSession,
        run_id: str,
        workspace_path: str
    ) -> None:
        """Updates the run record to RUNNING status and records workspace details."""
        stmt = select(AgentRunModel).where(AgentRunModel.run_id == run_id)
        res = await db.execute(stmt)
        run = res.scalars().first()
        if run:
            run.status = "RUNNING"
            run.workspace_path = workspace_path
            run.started_at = datetime.now(timezone.utc)
            
            # Compute hash of workspace path
            run.workspace_hash = cls.compute_sha256(workspace_path)
            
            await db.commit()

            await cls._log_to_governor_chain(
                db,
                run_id=run_id,
                agent_key=run.agent_key,
                event_name="AGENT_RUN_STARTED",
                payload={
                    "run_id": run_id,
                    "agent_key": run.agent_key,
                    "workspace_path": workspace_path
                },
                actor=run.created_by
            )

    @classmethod
    async def complete_run_record(
        cls,
        db: AsyncSession,
        run_id: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        cost: float,
        commands_executed: List[str],
        policy_violations: List[str],
        status: str = "COMPLETED"
    ) -> None:
        """Redacts, truncates outputs, computes integrity hashes and completes execution ledger entry."""
        stmt = select(AgentRunModel).where(AgentRunModel.run_id == run_id)
        res = await db.execute(stmt)
        run = res.scalars().first()
        if not run:
            return

        # Redact and truncate output logs
        clean_stdout = cls.truncate_text(cls.redact_secrets(stdout))
        clean_stderr = cls.truncate_text(cls.redact_secrets(stderr))

        # Update run record fields
        run.status = status
        run.exit_code = exit_code
        run.stdout = clean_stdout
        run.stderr = clean_stderr
        run.cost = cost
        run.commands_executed = commands_executed
        run.policy_violations = policy_violations
        run.completed_at = datetime.now(timezone.utc)

        # Integrity hashes
        run.command_hash = cls.compute_sha256(commands_executed)
        run.output_hash = cls.compute_sha256({"stdout": clean_stdout, "stderr": clean_stderr})

        # Logic for policy violations / sandboxing events
        event_name = "AGENT_RUN_COMPLETED"
        if status == "BLOCKED":
            event_name = "AGENT_RUN_BLOCKED_BY_POLICY"
        elif policy_violations:
            event_name = "AGENT_SANDBOX_VIOLATION"
        elif status == "FAILED" or exit_code != 0:
            event_name = "AGENT_RUN_FAILED"

        await db.commit()

        # Append to governor ledger chain
        proof_event = await cls._log_to_governor_chain(
            db,
            run_id=run_id,
            agent_key=run.agent_key,
            event_name=event_name,
            payload={
                "run_id": run_id,
                "agent_key": run.agent_key,
                "status": status,
                "exit_code": exit_code,
                "cost": cost,
                "violations": policy_violations,
                "command_hash": run.command_hash,
                "output_hash": run.output_hash
            },
            actor=run.created_by
        )

        if proof_event:
            run.ledger_chain_id = proof_event.event_hash
            await db.commit()

    @classmethod
    async def log_capability_evolution(
        cls,
        db: AsyncSession,
        agent_key: str,
        action: str, # ENABLED | DISABLED
        actor: Optional[str] = None
    ) -> None:
        """Logs change of agent capabilities to immutable governance proof chain."""
        event_name = "AGENT_CAPABILITY_ENABLED" if action == "ENABLED" else "AGENT_CAPABILITY_DISABLED"
        await cls._log_to_governor_chain(
            db,
            run_id=agent_key,
            agent_key=agent_key,
            event_name=event_name,
            payload={
                "agent_key": agent_key,
                "action": action,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            actor=actor
        )

    @classmethod
    async def _log_to_governor_chain(
        cls,
        db: AsyncSession,
        run_id: str,
        agent_key: str,
        event_name: str,
        payload: Dict[str, Any],
        actor: Optional[str] = None
    ) -> Optional[Any]:
        """Wrapper to append events to the immutable governance proof chain."""
        try:
            from services.governance.proof_chain_service import ProofChainService
            from libs.db.models.governance_models import ProofEventType, GovernorDomain
            
            # Wrap the event payload with the descriptive event name
            wrapped_payload = dict(payload)
            wrapped_payload["event_name"] = event_name

            pcs = ProofChainService(db)
            event = await pcs.append_event_async(
                event_type=ProofEventType.RUNTIME_EVENT,
                domain=GovernorDomain.REPAIR,
                entity_id=run_id,
                payload=wrapped_payload,
                actor=actor
            )
            return event
        except Exception as e:
            # Do not block the primary operation if the proof chain service fails
            print(f"Error logging to governor proof chain: {e}")
            return None
