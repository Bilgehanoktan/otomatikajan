#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audits environment configuration files for production and staging safety.
Ensures zero exposure of raw secrets in stdout/stderr.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

def parse_env_file(filepath: Path) -> dict[str, str]:
    """Manually parse env file, stripping quotes and comments."""
    if not filepath.exists():
        raise FileNotFoundError(f"Environment file not found: {filepath}")
    
    config = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            
            # Split by first '='
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Strip surrounding quotes if present
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                config[key] = val
    return config

def audit_env(config: dict[str, str], filepath: Path, mode: str) -> bool:
    """Audits parsed configuration against production safety guidelines."""
    errors: list[str] = []
    output_lines: list[str] = []
    
    output_lines.append(f"=== AUDITING CONFIGURATION FILE: {filepath.name} (MODE: {mode}) ===")
    
    # 1. APP_ENV & ENVIRONMENT checks
    app_env = config.get("APP_ENV", "")
    env_var = config.get("ENVIRONMENT", "")
    
    if app_env.lower() != mode.lower():
        errors.append(f"APP_ENV is '{app_env}', expected '{mode}'")
        output_lines.append(f"APP_ENV: INVALID / '{app_env}' (Expected '{mode}')")
    else:
        output_lines.append(f"APP_ENV: PRESENT / {app_env} (SAFE)")
        
    if env_var.lower() != mode.lower():
        errors.append(f"ENVIRONMENT is '{env_var}', expected '{mode}'")
        output_lines.append(f"ENVIRONMENT: INVALID / '{env_var}' (Expected '{mode}')")
    else:
        output_lines.append(f"ENVIRONMENT: PRESENT / {env_var} (SAFE)")

    # 2. RUNTIME_PROFILE
    runtime_profile = config.get("RUNTIME_PROFILE", "")
    if mode.lower() == "production" and runtime_profile != "production":
        errors.append("RUNTIME_PROFILE must be 'production' in production mode")
        output_lines.append(f"RUNTIME_PROFILE: INVALID / '{runtime_profile}' (Expected 'production')")
    elif mode.lower() == "staging" and runtime_profile not in ("staging", "production", "full-stack-local"):
        errors.append("RUNTIME_PROFILE is not safe for staging")
        output_lines.append(f"RUNTIME_PROFILE: INVALID / '{runtime_profile}'")
    else:
        output_lines.append(f"RUNTIME_PROFILE: PRESENT / {runtime_profile} (SAFE)")

    # 3. DEBUG & LOG_LEVEL
    debug_val = config.get("DEBUG", "false").lower()
    if debug_val != "false":
        errors.append("DEBUG must be set to 'false' in staging/production")
        output_lines.append(f"DEBUG: INVALID / '{config.get('DEBUG')}' (Expected 'false')")
    else:
        output_lines.append("DEBUG: PRESENT / false (SAFE)")
        
    log_level = config.get("LOG_LEVEL", "").upper()
    if log_level == "DEBUG":
        errors.append("LOG_LEVEL must not be DEBUG in production")
        output_lines.append(f"LOG_LEVEL: INVALID / '{log_level}' (Expected INFO/WARNING/ERROR)")
    else:
        output_lines.append(f"LOG_LEVEL: PRESENT / {log_level or 'INFO'} (SAFE)")

    # 4. DATABASE_URL & BILGEAPI_DATABASE_URL
    for db_var in ("DATABASE_URL", "BILGEAPI_DATABASE_URL"):
        db_url = config.get(db_var, "")
        if not db_url:
            errors.append(f"{db_var} is missing")
            output_lines.append(f"{db_var}: MISSING")
            continue
            
        if "localhost" in db_url or "127.0.0.1" in db_url:
            if mode.lower() == "production":
                errors.append(f"{db_var} points to localhost in production mode")
                output_lines.append(f"{db_var}: INVALID / POINTS_TO_LOCALHOST")
                continue
        
        if "CHANGE_ME" in db_url:
            errors.append(f"{db_var} contains default template password 'CHANGE_ME'")
            output_lines.append(f"{db_var}: INVALID / DEFAULT_PASSWORD")
            continue
            
        # Parse host for display
        host_match = re.search(r"@([^/:]+)", db_url)
        host_str = host_match.group(1) if host_match else "unknown"
        output_lines.append(f"{db_var}: PRESENT / SAFE_PATTERN (Host: {host_str})")

    # 5. Secret fields verification
    secret_fields = ("JWT_SECRET", "ADMIN_SECRET", "BILGEAPI_JWT_SECRET")
    for secret in secret_fields:
        val = config.get(secret, "")
        if not val:
            errors.append(f"{secret} is missing")
            output_lines.append(f"{secret}: MISSING")
        elif "CHANGE_ME" in val:
            errors.append(f"{secret} contains default template placeholder 'CHANGE_ME'")
            output_lines.append(f"{secret}: INVALID / DEFAULT_TEMPLATE")
        elif len(val) < 32:
            errors.append(f"{secret} is too short (current: {len(val)} chars, min: 32)")
            output_lines.append(f"{secret}: PRESENT / WEAK ({len(val)} chars)")
        else:
            output_lines.append(f"{secret}: PRESENT / STRONG ({len(val)} chars)")

    # Webhook Secret
    webhook_secret = config.get("BILGEAPI_WEBHOOK_SECRET", "")
    if not webhook_secret:
        errors.append("BILGEAPI_WEBHOOK_SECRET is missing")
        output_lines.append("BILGEAPI_WEBHOOK_SECRET: MISSING")
    elif "CHANGE_ME" in webhook_secret:
        errors.append("BILGEAPI_WEBHOOK_SECRET contains default template placeholder 'CHANGE_ME'")
        output_lines.append("BILGEAPI_WEBHOOK_SECRET: INVALID / DEFAULT_TEMPLATE")
    elif len(webhook_secret) < 16:
        errors.append("BILGEAPI_WEBHOOK_SECRET is too short (< 16 chars)")
        output_lines.append(f"BILGEAPI_WEBHOOK_SECRET: PRESENT / WEAK ({len(webhook_secret)} chars)")
    else:
        output_lines.append(f"BILGEAPI_WEBHOOK_SECRET: PRESENT / STRONG ({len(webhook_secret)} chars)")

    # 6. API Authentication Hardening
    auth_mode = config.get("BILGEAPI_AUTH_MODE", "")
    if auth_mode != "api_key":
        errors.append("BILGEAPI_AUTH_MODE must be set to 'api_key'")
        output_lines.append(f"BILGEAPI_AUTH_MODE: INVALID / '{auth_mode}' (Expected 'api_key')")
    else:
        output_lines.append("BILGEAPI_AUTH_MODE: PRESENT / api_key (SAFE)")

    static_keys = config.get("BILGEAPI_STATIC_KEYS", "")
    if static_keys:
        errors.append("BILGEAPI_STATIC_KEYS must be empty in production/staging (plaintext keys forbidden)")
        output_lines.append("BILGEAPI_STATIC_KEYS: INVALID / PLAINTEXT_KEYS_PRESENT")
    else:
        output_lines.append("BILGEAPI_STATIC_KEYS: SAFE_EMPTY")

    static_hashes = config.get("BILGEAPI_STATIC_KEY_HASHES", "")
    if not static_hashes:
        errors.append("BILGEAPI_STATIC_KEY_HASHES must be configured with secure hashes")
        output_lines.append("BILGEAPI_STATIC_KEY_HASHES: MISSING")
    else:
        hash_count = len(static_hashes.split(","))
        output_lines.append(f"BILGEAPI_STATIC_KEY_HASHES: PRESENT / VALID_HASHES ({hash_count} keys)")

    # 7. Webhook Private loopbacks
    allow_private = config.get("BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", "false").lower()
    if allow_private != "false" and mode.lower() == "production":
        errors.append("BILGEAPI_ALLOW_PRIVATE_WEBHOOKS must be 'false' in production")
        output_lines.append("BILGEAPI_ALLOW_PRIVATE_WEBHOOKS: INVALID / ENABLED")
    else:
        output_lines.append("BILGEAPI_ALLOW_PRIVATE_WEBHOOKS: SAFE_DISABLED")

    # 8. Rate Limiting
    rate_limit = config.get("BILGEAPI_RATE_LIMIT_RPS", "")
    try:
        rps = int(rate_limit)
        if rps <= 0:
            errors.append("BILGEAPI_RATE_LIMIT_RPS must be greater than 0")
            output_lines.append(f"BILGEAPI_RATE_LIMIT_RPS: INVALID / {rps}")
        else:
            output_lines.append(f"BILGEAPI_RATE_LIMIT_RPS: PRESENT / {rps} RPS (SAFE)")
    except ValueError:
        errors.append("BILGEAPI_RATE_LIMIT_RPS must be an integer")
        output_lines.append(f"BILGEAPI_RATE_LIMIT_RPS: INVALID / '{rate_limit}'")

    # 9. Safety Flags (Self-Healing & External Agents)
    self_healing = config.get("BILGEAPI_SELF_HEALING_ENABLED", "false").lower()
    if self_healing != "false" and mode.lower() == "production":
        errors.append("BILGEAPI_SELF_HEALING_ENABLED must be 'false' in production safety mode")
        output_lines.append("BILGEAPI_SELF_HEALING_ENABLED: INVALID / ENABLED")
    else:
        output_lines.append("BILGEAPI_SELF_HEALING_ENABLED: SAFE_DISABLED")

    external_agents = config.get("BILGEAPI_EXTERNAL_AGENTS_ENABLED", "false").lower()
    if external_agents != "false" and mode.lower() == "production":
        errors.append("BILGEAPI_EXTERNAL_AGENTS_ENABLED must be 'false' in production safety mode")
        output_lines.append("BILGEAPI_EXTERNAL_AGENTS_ENABLED: INVALID / ENABLED")
    else:
        output_lines.append("BILGEAPI_EXTERNAL_AGENTS_ENABLED: SAFE_DISABLED")

    # Print summary output
    print("\n".join(output_lines))
    print("=" * 78)

    if errors:
        print(f"CRITICAL CONFIGURATION ERRORS DETECTED ({len(errors)}):", file=sys.stderr)
        for err in errors:
            print(f" - [ERROR] {err}", file=sys.stderr)
        return False
    
    print("STATUS: ALL SAFETY CHECKS PASSED.")
    return True

def main() -> int:
    parser = argparse.ArgumentParser(description="Verify production/staging environment configuration safety.")
    parser.add_argument("--env-file", default=".env.production.example", help="Path to environment file to audit")
    parser.add_argument("--mode", choices=["production", "staging"], default="production", help="Deployment target mode")
    args = parser.parse_args()

    filepath = Path(args.env_file)
    try:
        config = parse_env_file(filepath)
        ok = audit_env(config, filepath, args.mode)
        return 0 if ok else 1
    except Exception as e:
        print(f"Audit failed to execute: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
