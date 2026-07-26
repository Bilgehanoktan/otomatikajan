import os
import pytest
import asyncio
import httpx
import unittest.mock
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy import select

from bilgeapi.llm.base import LLMResult
from bilgeapi.llm.ollama_provider import OllamaProvider, MockLLMProvider, validate_ollama_url
from bilgeapi.llm.router import LLMRouter
from bilgeapi.memory.db import init_workspace_db, get_workspace_db_session, get_workspace_engine, _engines
from bilgeapi.memory.models import AuditLogModel, DecisionModel
from bilgeapi.memory.repositories import SystemRepository
from bilgeapi.core.workspace import WorkspaceManager

@pytest.fixture
async def mock_db(monkeypatch):
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()
        
        def mock_init(self, *args, **kwargs):
            self.start_path = tmp_path
            self.project_root = tmp_path
            self.workspace_dir = tmp_path
            
        monkeypatch.setattr(WorkspaceManager, "__init__", mock_init)
        await init_workspace_db(tmp_path)
        
        yield tmp_path
        
        from bilgeapi.memory.db import _engines
        for eng in list(_engines.values()):
            await eng.dispose()
        _engines.clear()

def test_mock_llm_provider():
    # Test MockLLMProvider generate
    provider = MockLLMProvider()
    
    # Check default behavior
    res1 = asyncio.run(provider.generate("Hello, password = 'my_secret_key'"))
    assert "[MASKED_SECRET]" in res1.text
    assert res1.model == "mock-model"
    assert res1.fallback_used is False
    
    # Check preset response behavior
    provider.preset_response = "Preset response: api_key = 'token_abc123'"
    res2 = asyncio.run(provider.generate("test"))
    assert "[MASKED_SECRET]" in res2.text
    assert "token_abc123" not in res2.text

    # Test MockLLMProvider chat
    messages = [{"role": "user", "content": "hello, password = 'abc123'"}]
    provider.preset_response = None
    res_chat = asyncio.run(provider.chat(messages))
    assert "[MASKED_SECRET]" in res_chat.text
    assert "password = 'abc123'" not in res_chat.text

def test_ollama_url_validation(monkeypatch):
    # Safe URLs
    validate_ollama_url("http://localhost:11434")
    validate_ollama_url("http://127.0.0.1:11434")
    validate_ollama_url("https://[::1]:11434")
    
    # Allowlisted hosts
    monkeypatch.setenv("BILGEAPI_OLLAMA_ALLOWLIST_HOSTS", "internal-ollama,10.0.0.5")
    validate_ollama_url("http://internal-ollama:11434")
    validate_ollama_url("https://10.0.0.5")

    # Unsafe base URLs
    with pytest.raises(ValueError, match="not allowlisted"):
        validate_ollama_url("http://google.com")
        
    with pytest.raises(ValueError, match="not allowlisted"):
        validate_ollama_url("http://192.168.1.100:11434")
        
    with pytest.raises(ValueError, match="Scheme must be HTTP or HTTPS"):
        validate_ollama_url("ftp://localhost")
        
    with pytest.raises(ValueError, match="embedded credentials"):
        validate_ollama_url("http://user:pass@localhost:11434")

@pytest.mark.asyncio
async def test_ollama_successful_execution():
    provider = OllamaProvider(base_url="http://localhost:11434")
    
    mock_response = unittest.mock.AsyncMock()
    mock_response.status_code = 200
    # Simulate generate output
    mock_response.json = unittest.mock.Mock(return_value={
        "response": "Hello world, api_key = 'super_secret'",
        "prompt_eval_count": 5,
        "eval_count": 10
    })
    mock_response.raise_for_status = unittest.mock.Mock()

    with unittest.mock.patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        res = await provider.generate("Simple prompt")
        assert mock_post.called
        assert res.model == "llama3.1:8b"
        assert res.fallback_used is False
        assert "[MASKED_SECRET]" in res.text
        assert "super_secret" not in res.text
        assert res.usage["prompt_eval_count"] == 5

    # Test chat successful execution
    mock_chat_response = unittest.mock.AsyncMock()
    mock_chat_response.status_code = 200
    mock_chat_response.json = unittest.mock.Mock(return_value={
        "message": {"role": "assistant", "content": "Chat output, token = 'chat_token'"},
        "prompt_eval_count": 8,
        "eval_count": 12
    })
    mock_chat_response.raise_for_status = unittest.mock.Mock()

    with unittest.mock.patch("httpx.AsyncClient.post", return_value=mock_chat_response) as mock_post:
        res_chat = await provider.chat([{"role": "user", "content": "hi"}])
        assert mock_post.called
        assert res_chat.model == "llama3.1:8b"
        assert "[MASKED_SECRET]" in res_chat.text
        assert "chat_token" not in res_chat.text

@pytest.mark.asyncio
async def test_ollama_fallback_event(mock_db, monkeypatch):
    tmp_path = mock_db
    monkeypatch.setenv("BILGEAPI_LOG_RAW_PROMPT", "true")
    
    provider = OllamaProvider(base_url="http://localhost:11434")
    
    # We want: 
    # 1. First call (llama3.1:8b) fails with ConnectionError containing secret token.
    # 2. Second call (mistral:7b) succeeds and returns redacted output.
    fail_response = httpx.RequestError("Failed to connect with token = 'secret_connect_token'")
    
    success_response = unittest.mock.AsyncMock()
    success_response.status_code = 200
    success_response.json = unittest.mock.Mock(return_value={
        "response": "Fallback successful. api_key = 'fallback_secret'",
        "prompt_eval_count": 2,
        "eval_count": 4
    })
    success_response.raise_for_status = unittest.mock.Mock()

    call_count = 0
    async def mock_post_call(url, json, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise fail_response
        return success_response

    with unittest.mock.patch("httpx.AsyncClient.post", side_effect=mock_post_call):
        async with get_workspace_db_session(tmp_path) as session:
            res = await provider.generate(
                prompt="password = 'my_super_secret_prompt'",
                db_session=session
            )
            
            assert res.model == "mistral:7b"
            assert res.fallback_used is True
            assert "[MASKED_SECRET]" in res.text
            assert "fallback_secret" not in res.text

        # Verify Audit Log and Decision Log in DB
        async with get_workspace_db_session(tmp_path) as session:
            # Audit log check
            stmt_audit = select(AuditLogModel).where(AuditLogModel.event_type == "LLM_FALLBACK_TRIGGERED")
            audit = (await session.execute(stmt_audit)).scalar_one()
            assert audit.status == "ALLOWED"
            assert audit.target == "model:llama3.1:8b"
            
            # Check prompt and error redaction in audit log
            assert "[MASKED_SECRET]" in audit.before_state["prompt"]
            assert "my_super_secret_prompt" not in audit.before_state["prompt"]
            assert "[MASKED_SECRET]" in audit.after_state["error"]
            assert "secret_connect_token" not in audit.after_state["error"]
            assert audit.after_state["next_model"] == "mistral:7b"

            # Decision log check
            stmt_dec = select(DecisionModel).where(DecisionModel.classification == "LLM_FALLBACK")
            dec = (await session.execute(stmt_dec)).scalar_one()
            assert dec.risk_level == "LOW"
            assert "fallback" in dec.decision_reason.lower()

@pytest.mark.asyncio
async def test_ollama_all_models_failing():
    provider = OllamaProvider(base_url="http://localhost:11434")
    
    # Mock post to always raise a ConnectionError containing a secret token
    async def mock_post_call(url, json, **kwargs):
        raise httpx.RequestError("Connection timeout on token = 'last_fail_token'")

    with unittest.mock.patch("httpx.AsyncClient.post", side_effect=mock_post_call):
        with pytest.raises(RuntimeError, match="Ollama generation failed for all models"):
            try:
                await provider.generate("test")
            except Exception as e:
                # Assert error message is redacted
                assert "[MASKED_SECRET]" in str(e)
                assert "last_fail_token" not in str(e)
                raise

@pytest.mark.asyncio
async def test_router_model_selection(monkeypatch):
    monkeypatch.setenv("BILGEAPI_LLM_PROVIDER", "mock")
    router = LLMRouter()
    
    # 'low' complexity -> gemma3:4b
    res_low = await router.generate("test", options={"complexity": "low"})
    assert res_low.model == "gemma3:4b"

    # 'medium' complexity -> mistral:7b
    res_med = await router.generate("test", options={"complexity": "medium"})
    assert res_med.model == "mistral:7b"

    # 'high' complexity -> llama3.1:8b
    res_high = await router.generate("test", options={"complexity": "high"})
    assert res_high.model == "llama3.1:8b"

    # Default -> llama3.1:8b
    res_default = await router.generate("test")
    assert res_default.model == "mock-model"  # Since no specific model is set, default is passed to mock provider
