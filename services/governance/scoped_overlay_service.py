
"""
services/governance/scoped_overlay_service.py
Scoped Policy Engine - Applies regional/departmental overrides on top of the Global Constitution.
"""
from typing import Dict, Any, List
from services.observability.logging import get_logger

logger = get_logger("governance.scoped")

class ScopedOverlayService:
    @staticmethod
    def apply_overlay(base_policy: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merges an overlay onto a base policy.
        """
        result = base_policy.copy()
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ScopedOverlayService.apply_overlay(result[key], value)
            else:
                result[key] = value
        
        return result

    @staticmethod
    async def get_effective_policy(scope: str, global_config_path: str) -> Dict[str, Any]:
        """
        Resolves the final policy for a specific scope.
        Logic: Global Constitution -> Scoped Overlay (from file or DB).
        """
        import yaml
        import os
        
        # 1. Load Global Constitution
        with open(global_config_path, "r") as f:
            base = yaml.safe_load(f)
            
        # 2. Check for scoped overlay file (e.g. configs/scoped/FINANCE.yaml)
        scoped_path = f"configs/scoped/{scope}.yaml"
        if os.path.exists(scoped_path):
            with open(scoped_path, "r") as f:
                overlay = yaml.safe_load(f)
                logger.info(f"Applying file-based overlay for scope: {scope}")
                base = ScopedOverlayService.apply_overlay(base, overlay)
        
        # 3. Check for DB overrides (Phase 30 integration)
        # In a real scenario, we'd query PolicyProposal table for 'COMMITTED' overrides
        # that specifically target this scope.
        
        return base
