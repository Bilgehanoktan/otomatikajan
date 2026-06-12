import os
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional
from apps.bilgeapi.schemas.skills import SkillMetadataResponse

logger = logging.getLogger(__name__)

ALLOWED_SELECTED_SKILLS = [
    'spec-driven-development',
    'planning-and-task-breakdown',
    'api-and-interface-design',
    'test-driven-development',
    'security-and-hardening',
    'code-review-and-quality',
    'observability-and-instrumentation',
    'documentation-and-adrs',
    'incremental-implementation'
]

ALLOWED_BILGEAPI_SKILLS = [
    'bilgeapi-repair-request-safety',
    'bilgeapi-diagnostic-state-machine',
    'bilgeapi-webhook-security',
    'bilgeapi-audit-ledger',
    'bilgeapi-self-healing-policy',
    'bilgeapi-pr-verification-gate',
    'bilgeapi-skill-integrity'
]

class SkillRegistryService:
    def __init__(self, ledger_service: Optional[Any] = None, base_dir: Optional[str] = None):
        self.ledger_service = ledger_service
        # Resolve project root base dir
        if not base_dir:
            self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        else:
            self.base_dir = os.path.abspath(base_dir)
            
        self.selected_dir = os.path.join(self.base_dir, "docs", "agent-skills", "selected")
        self.bilgeapi_dir = os.path.join(self.base_dir, "docs", "agent-skills", "bilgeapi")
        self.manifest_path = os.path.join(self.base_dir, "docs", "agent-skills", "hash_manifest.json")
        
        self.verified_cache: Dict[str, SkillMetadataResponse] = {}
        self.hash_manifest: Dict[str, str] = {}
        self.initialized = False

    def validate_safe_path(self, base_dir: str, file_path: str) -> str:
        """
        Validates that file_path resides strictly within base_dir to prevent path traversal.
        """
        canonical_base = os.path.realpath(base_dir)
        canonical_file = os.path.realpath(file_path)
        if not canonical_file.startswith(canonical_base + os.sep) and canonical_file != canonical_base:
            raise ValueError(f"Security violation: path traversal detected! Path: {file_path}")
        return canonical_file

    def compute_sha256(self, filepath: str) -> str:
        """
        Computes SHA-256 hash of a file.
        """
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def parse_markdown_frontmatter(self, content: str) -> tuple[dict, str]:
        """
        Parses YAML-like frontmatter enclosed in --- at the top of markdown files.
        """
        metadata = {}
        remaining_content = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                header = parts[1]
                remaining_content = parts[2].strip()
                for line in header.splitlines():
                    if ":" in line:
                        key, val = line.split(":", 1)
                        metadata[key.strip()] = val.strip()
        return metadata, remaining_content

    def generate_manifest(self) -> Dict[str, str]:
        """
        Build-time/Setup-time function to generate the hash manifest of allowlisted skills.
        """
        manifest = {}
        # Selected skills
        for skill_name in ALLOWED_SELECTED_SKILLS:
            filepath = os.path.join(self.selected_dir, f"{skill_name}.md")
            if os.path.exists(filepath):
                safe_path = self.validate_safe_path(self.selected_dir, filepath)
                manifest[f"selected/{skill_name}"] = self.compute_sha256(safe_path)

        # BilgeAPI skills
        for skill_name in ALLOWED_BILGEAPI_SKILLS:
            filepath = os.path.join(self.bilgeapi_dir, f"{skill_name}.md")
            if os.path.exists(filepath):
                safe_path = self.validate_safe_path(self.bilgeapi_dir, filepath)
                manifest[f"bilgeapi/{skill_name}"] = self.compute_sha256(safe_path)

        # Ensure directory exists and write manifest
        os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    async def initialize_registry(self):
        """
        Startup-time initialization. Loads manifest, validates hashes,
        verifies allowlists, parses files, and builds the in-memory verified cache.
        Fails-closed on any mismatch or unauthorized file.
        """
        self.verified_cache.clear()
        self.hash_manifest.clear()
        self.initialized = False

        try:
            # 1. Enforce directory safety and verify files exist
            if not os.path.exists(self.manifest_path):
                # Generate a transient manifest if missing in dev/test, but in strict mode we raise.
                # To be secure, we try to load it.
                raise FileNotFoundError(f"Hash manifest file missing: {self.manifest_path}")

            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.hash_manifest = json.load(f)

            # 1b. Exact manifest key set validation — reject extra or missing keys
            expected_keys = set()
            for skill_name in ALLOWED_SELECTED_SKILLS:
                expected_keys.add(f"selected/{skill_name}")
            for skill_name in ALLOWED_BILGEAPI_SKILLS:
                expected_keys.add(f"bilgeapi/{skill_name}")
            
            manifest_keys = set(self.hash_manifest.keys())
            extra_keys = manifest_keys - expected_keys
            missing_keys = expected_keys - manifest_keys
            
            if extra_keys:
                raise ValueError(
                    f"Security breach: hash_manifest.json contains un-allowlisted keys: {sorted(extra_keys)}"
                )
            if missing_keys:
                raise ValueError(
                    f"Security error: hash_manifest.json is missing required keys: {sorted(missing_keys)}"
                )

            # 2. Strict Directory Scan - Reject any un-allowlisted markdown files (Fail-closed)
            #    Uses exact canonical path matching to prevent traversal/injection.
            for directory, allowlist, source_prefix in [
                (self.selected_dir, ALLOWED_SELECTED_SKILLS, "selected"),
                (self.bilgeapi_dir, ALLOWED_BILGEAPI_SKILLS, "bilgeapi")
            ]:
                if not os.path.exists(directory):
                    raise FileNotFoundError(f"Expected skill directory missing: {directory}")
                
                # Pre-compute the exact set of allowed canonical paths
                canonical_dir = os.path.realpath(directory)
                allowed_canonical_paths = set()
                for skill_name in allowlist:
                    allowed_canonical_paths.add(
                        os.path.realpath(os.path.join(canonical_dir, f"{skill_name}.md"))
                    )
                
                # Walk directory and verify every .md file is in the exact allowed set
                for root, dirs, files in os.walk(directory):
                    canonical_root = os.path.realpath(root)
                    # Reject any nested subdirectories — skills must be flat
                    if canonical_root != canonical_dir:
                        md_files_in_subdir = [f for f in files if f.endswith(".md")]
                        if md_files_in_subdir:
                            raise ValueError(
                                f"Security breach: .md files found in unexpected subdirectory: {root}"
                            )
                        continue
                    
                    for file in files:
                        if file.endswith(".md"):
                            file_path = os.path.join(root, file)
                            canonical_file = os.path.realpath(file_path)
                            
                            # Exact canonical path match — not prefix, not basename
                            if canonical_file not in allowed_canonical_paths:
                                raise ValueError(
                                    f"Security breach: Un-allowlisted skill file detected: {file} "
                                    f"(canonical: {canonical_file})"
                                )

            # 3. Verify hashes and parse metadata
            # Selected skills
            for skill_name in ALLOWED_SELECTED_SKILLS:
                filepath = os.path.join(self.selected_dir, f"{skill_name}.md")
                key = f"selected/{skill_name}"
                await self._load_and_verify_skill(filepath, key, skill_name, "external-vendor", self.selected_dir)

            # BilgeAPI skills
            for skill_name in ALLOWED_BILGEAPI_SKILLS:
                filepath = os.path.join(self.bilgeapi_dir, f"{skill_name}.md")
                key = f"bilgeapi/{skill_name}"
                await self._load_and_verify_skill(filepath, key, skill_name, "bilgeapi-custom", self.bilgeapi_dir)

            self.initialized = True
            
            # Log success to Ledger
            await self._append_ledger_event(
                event_type="SKILL_CATALOG_LOADED",
                payload={"status": "success", "skill_count": len(self.verified_cache)}
            )

        except Exception as exc:
            # Fail-closed: Ensure registry is not marked initialized
            self.verified_cache.clear()
            self.initialized = False
            
            # Log failure to Ledger
            await self._append_ledger_event(
                event_type="SKILL_POLICY_BLOCKED",
                payload={"status": "failed", "error": str(exc)}
            )
            logger.error("Skill registry initialization failed (Fail-closed): %s", exc)
            raise exc

    async def _load_and_verify_skill(self, filepath: str, key: str, skill_name: str, source: str, base_dir: str):
        # Path traversal check
        safe_path = self.validate_safe_path(base_dir, filepath)
        
        # Check existence
        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"Skill file missing: {filepath}")

        # Compute hash and match manifest
        computed_hash = self.compute_sha256(safe_path)
        expected_hash = self.hash_manifest.get(key)
        if not expected_hash:
            raise ValueError(f"Security error: Skill {key} not registered in manifest.")
        if computed_hash != expected_hash:
            await self._append_ledger_event(
                event_type="SKILL_CHECK_FAILED",
                payload={"skill": skill_name, "error": "Hash mismatch"}
            )
            raise ValueError(f"Security error: Hash mismatch for skill {key}. Expected: {expected_hash}, Computed: {computed_hash}")

        # Log hash verified event
        await self._append_ledger_event(
            event_type="SKILL_HASH_VERIFIED",
            payload={"skill": skill_name, "hash": computed_hash}
        )

        # Parse markdown frontmatter
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()

        metadata, body = self.parse_markdown_frontmatter(content)
        
        # Parse basic fields
        parsed_name = metadata.get("name", skill_name)
        if parsed_name != skill_name:
            raise ValueError(f"Security error: Declared skill name '{parsed_name}' does not match file name '{skill_name}'")

        # Map description
        description = metadata.get("description", "")
        if not description and body:
            # Extract first paragraph if no description in frontmatter
            lines = [line.strip() for line in body.splitlines() if line.strip()]
            if lines:
                description = lines[0]

        # Allowed / Forbidden uses parsing
        # (Default settings for custom vs general)
        allowed_use = ["development_checklist", "review_gate", "evidence_requirement"]
        forbidden_use = ["execute_commands", "auto_patch", "auto_merge", "auto_deploy", "force_push"]
        
        risk_level = "low"
        if source == "bilgeapi-custom":
            risk_level = "high_value_policy"

        # Construct Schema object
        self.verified_cache[skill_name] = SkillMetadataResponse(
            name=skill_name,
            source=source,
            version="1.0.0",
            license="MIT",
            risk_level=risk_level,
            allowed_use=allowed_use,
            forbidden_use=forbidden_use,
            hash=computed_hash,
            enabled=True,
            description=description[:250],
            category="Review" if source == "bilgeapi-custom" else "General"
        )

    async def _append_ledger_event(self, event_type: str, payload: Dict[str, Any]):
        if not self.ledger_service:
            return
        try:
            await self.ledger_service.append_event(
                chain_id="skill_registry_chain",
                event_type=event_type,
                entity_type="skill_registry",
                entity_id="registry_singleton",
                actor_id="system",
                payload=payload
            )
        except Exception as exc:
            logger.warning("Failed to log skill registry event to review ledger: %s", exc)

    def get_skill(self, name: str) -> SkillMetadataResponse:
        """
        Retrieves a skill from verified cache. Ensures no runtime disk read.
        """
        if not self.initialized:
            raise RuntimeError("Skill registry has not been initialized or initialization failed (fail-closed).")
        if name not in self.verified_cache:
            raise ValueError(f"Skill {name} not found in verified cache.")
        return self.verified_cache[name]

    def list_skills(self) -> List[SkillMetadataResponse]:
        """
        Lists all verified skills from cache. Ensures no runtime disk read.
        """
        if not self.initialized:
            raise RuntimeError("Skill registry has not been initialized or initialization failed (fail-closed).")
        return list(self.verified_cache.values())
