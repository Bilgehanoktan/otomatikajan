import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apps.bilgeapi.repositories.interface import ReviewLedgerRepository


REDACTED_VALUE = "[REDACTED]"


class PayloadRedactor:
    SENSITIVE_KEYS = {
        "plaintext_key",
        "api_key",
        "token",
        "secret",
        "authorization",
        "github_token",
        "webhook_secret",
        "password",
        "raw_content",
    }

    def redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: REDACTED_VALUE if self._is_sensitive_key(key) else self.redact(child)
                for key, child in value.items()
            }
        if isinstance(value, list):
            return [self.redact(item) for item in value]
        return value

    def _is_sensitive_key(self, key: str) -> bool:
        normalized = key.lower()
        return normalized in self.SENSITIVE_KEYS or any(marker in normalized for marker in self.SENSITIVE_KEYS)


class CanonicalPayloadHasher:
    @staticmethod
    def canonicalize(payload: Any) -> str:
        return json.dumps(payload or {}, sort_keys=True, separators=(",", ":"), default=str)

    def hash_payload(self, payload: Any) -> str:
        canonical = self.canonicalize(payload)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def hash_event(
        self,
        *,
        previous_hash: Optional[str],
        entity_type: str,
        entity_id: str,
        event_type: str,
        canonical_payload: str,
        created_at: datetime,
    ) -> str:
        base = "|".join(
            [
                previous_hash or "",
                entity_type,
                entity_id,
                event_type,
                canonical_payload,
                self.timestamp(created_at),
            ]
        )
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    @staticmethod
    def timestamp(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()


class ReviewLedgerService:
    def __init__(self, repo: ReviewLedgerRepository):
        self.repo = repo
        self.redactor = PayloadRedactor()
        self.hasher = CanonicalPayloadHasher()

    async def append_event(
        self,
        *,
        chain_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_id: Optional[str],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        latest = await self.repo.get_latest_entry(chain_id)
        previous_hash = latest["event_hash"] if latest else None
        sequence_no = int(latest["sequence_no"]) + 1 if latest else 1
        created_at = datetime.now(timezone.utc)
        redacted_payload = self.redactor.redact(payload or {})
        canonical_payload = self.hasher.canonicalize(redacted_payload)
        payload_hash = self.hasher.hash_payload(redacted_payload)
        event_hash = self.hasher.hash_event(
            previous_hash=previous_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            canonical_payload=canonical_payload,
            created_at=created_at,
        )

        return await self.repo.append_entry(
            {
                "id": f"rle_{uuid.uuid4().hex[:8]}",
                "chain_id": chain_id,
                "sequence_no": sequence_no,
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "actor_id": actor_id,
                "previous_hash": previous_hash,
                "payload_hash": payload_hash,
                "event_hash": event_hash,
                "payload_summary": redacted_payload,
                "created_at": created_at,
            }
        )

    async def list_chain(self, chain_id: str) -> List[Dict[str, Any]]:
        return await self.repo.list_by_chain(chain_id)

    async def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.repo.list_recent(limit=limit)

    async def export_chain_markdown(self, chain_id: str, verification: Dict[str, Any]) -> str:
        entries = await self.list_chain(chain_id)
        lines = [
            f"# Immutable Review Ledger Export: {chain_id}",
            "",
            f"- Valid: {verification['valid']}",
            f"- Entry Count: {verification['entry_count']}",
            f"- Head Hash: `{verification.get('head_hash') or ''}`",
            "",
            "## Entries",
        ]
        for entry in entries:
            lines.extend(
                [
                    "",
                    f"### {entry['sequence_no']}. {entry['event_type']}",
                    f"- Entity: `{entry['entity_type']}:{entry['entity_id']}`",
                    f"- Actor: `{entry.get('actor_id') or 'unknown'}`",
                    f"- Payload Hash: `{entry['payload_hash']}`",
                    f"- Event Hash: `{entry['event_hash']}`",
                    "```json",
                    CanonicalPayloadHasher.canonicalize(entry.get("payload_summary") or {}),
                    "```",
                ]
            )
        return "\n".join(lines)


class ReviewLedgerVerifier:
    def __init__(self, repo: ReviewLedgerRepository):
        self.repo = repo
        self.hasher = CanonicalPayloadHasher()

    async def verify_chain(self, chain_id: str) -> Dict[str, Any]:
        entries = await self.repo.list_by_chain(chain_id)
        issues: List[Dict[str, Any]] = []
        previous_hash: Optional[str] = None

        for index, entry in enumerate(entries, start=1):
            if entry["sequence_no"] != index:
                issues.append(
                    {
                        "type": "sequence_gap",
                        "entry_id": entry["id"],
                        "expected": index,
                        "actual": entry["sequence_no"],
                    }
                )

            if entry.get("previous_hash") != previous_hash:
                issues.append(
                    {
                        "type": "previous_hash_mismatch",
                        "entry_id": entry["id"],
                        "expected": previous_hash,
                        "actual": entry.get("previous_hash"),
                    }
                )

            payload_summary = entry.get("payload_summary") or {}
            computed_payload_hash = self.hasher.hash_payload(payload_summary)
            if computed_payload_hash != entry["payload_hash"]:
                issues.append(
                    {
                        "type": "payload_hash_mismatch",
                        "entry_id": entry["id"],
                        "expected": entry["payload_hash"],
                        "actual": computed_payload_hash,
                    }
                )

            created_at = entry["created_at"]
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            computed_event_hash = self.hasher.hash_event(
                previous_hash=entry.get("previous_hash"),
                entity_type=entry["entity_type"],
                entity_id=entry["entity_id"],
                event_type=entry["event_type"],
                canonical_payload=self.hasher.canonicalize(payload_summary),
                created_at=created_at,
            )
            if computed_event_hash != entry["event_hash"]:
                issues.append(
                    {
                        "type": "event_hash_mismatch",
                        "entry_id": entry["id"],
                        "expected": entry["event_hash"],
                        "actual": computed_event_hash,
                    }
                )

            previous_hash = entry["event_hash"]

        return {
            "chain_id": chain_id,
            "valid": len(issues) == 0,
            "entry_count": len(entries),
            "head_hash": entries[-1]["event_hash"] if entries else None,
            "issues": issues,
        }
