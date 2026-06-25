import os
import pytest
from libs.llm.model_orchestrator import ModelOrchestrator, PROVIDERS

def test_anthropic_config_override(monkeypatch):
    # Setup environment
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://test.proxy/v1")
    monkeypatch.setenv("ANTHROPIC_MODEL", "test-model-123")
    
    orchestrator = ModelOrchestrator()
    anthropic = orchestrator.providers.get("anthropic")
    
    assert anthropic is not None
    # Current behavior: this might fail because it's hardcoded in PROVIDERS list at module level
    # We want it to be dynamic or re-loaded.
    assert anthropic.base_url == "https://test.proxy/v1"
    assert anthropic.model == "test-model-123"

def test_openrouter_prefix_validation(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-or-v1-testkey123-long-enough-for-validation")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://openrouter.ai/api")
    
    orchestrator = ModelOrchestrator()
    anthropic = orchestrator.providers.get("anthropic")
    
    # Current behavior: is_placeholder_key() returns True because it doesn't start with sk-ant-
    assert anthropic.is_placeholder_key() is False
