import os
import time
import httpx
import logging
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional

from apps.bilgeapi.llm.base import BaseLLMProvider, LLMResult
from apps.bilgeapi.security.secret_scanner import SecretScanner
from apps.bilgeapi.memory.repositories import AuditLogRepository, DecisionRepository

logger = logging.getLogger("bilgeapi.llm.ollama_provider")

def validate_ollama_url(url_str: str) -> None:
    """
    Validates that the Ollama Base URL is a safe local-first URL.
    Rejects public IPs, credentials, non-HTTP/HTTPS, and unallowlisted private hosts.
    """
    if not url_str:
        raise ValueError("Ollama URL cannot be empty")
    
    parsed = urlparse(url_str)
    if parsed.scheme not in ["http", "https"]:
        raise ValueError("Unsafe URL: Scheme must be HTTP or HTTPS")
        
    if parsed.username or parsed.password:
        raise ValueError("Unsafe URL: URLs with embedded credentials are not allowed")
        
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Unsafe URL: Invalid hostname")
        
    # Allowlist check
    allowlist = os.getenv("BILGEAPI_OLLAMA_ALLOWLIST_HOSTS", "")
    allowed_hosts = [h.strip().lower() for h in allowlist.split(",") if h.strip()]
    
    safe_hosts = {"localhost", "127.0.0.1", "::1", "[::1]", "localhost.localdomain"}
    
    if hostname.lower() not in safe_hosts and hostname.lower() not in allowed_hosts:
        raise ValueError(f"Unsafe URL: Host '{hostname}' is not allowlisted (localhost or 127.0.0.1 only)")

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: Optional[str] = None, secret_scanner: Optional[SecretScanner] = None):
        from apps.bilgeapi.core.workspace import WorkspaceManager
        from apps.bilgeapi.core.settings_loader import SettingsLoader

        # Try loading configuration from workspace settings loader
        system_cfg = {}
        try:
            manager = WorkspaceManager()
            loader = SettingsLoader(manager.workspace_dir)
            system_cfg = loader.get_system_config()
        except Exception as e:
            logger.debug(f"Could not load workspace system config for Ollama: {e}")

        self.base_url = (
            base_url
            or system_cfg.get("ollama_base_url")
            or os.getenv("BILGEAPI_OLLAMA_BASE_URL", "http://localhost:11434")
        )
        validate_ollama_url(self.base_url)
        
        self.secret_scanner = secret_scanner or SecretScanner()
        
        # Load fallback model chain
        self.primary_model = (
            system_cfg.get("llm_model")
            or os.getenv("BILGEAPI_OLLAMA_DEFAULT_MODEL", "llama3.1:8b")
        )
        self.secondary_model = (
            system_cfg.get("llm_fallback_model")
            or os.getenv("BILGEAPI_OLLAMA_FALLBACK_MODEL", "mistral:7b")
        )
        self.tertiary_model = (
            system_cfg.get("llm_low_resource_model")
            or os.getenv("BILGEAPI_OLLAMA_LOW_HARDWARE_MODEL", "gemma3:4b")
        )
        self.timeout = float(
            system_cfg.get("llm_timeout_s")
            or os.getenv("BILGEAPI_LLM_TIMEOUT")
            or os.getenv("BILGEAPI_OLLAMA_TIMEOUT_S", "60.0")
        )

    def _get_fallback_chain(self, start_model: Optional[str]) -> List[str]:
        """
        Builds the ordered list of models to try.
        """
        all_models = [self.primary_model, self.secondary_model, self.tertiary_model]
        if start_model:
            # If a specific starting model is requested, try it first, followed by others
            chain = [start_model]
            for m in all_models:
                if m != start_model:
                    chain.append(m)
            return chain
        return all_models

    async def _log_fallback_event(
        self,
        failed_model: str,
        next_model: str,
        error_msg: str,
        prompt_content: str,
        db_session: Optional[Any]
    ) -> None:
        """
        Logs a model fallback event to database repositories and files.
        """
        redacted_error = self.secret_scanner.scan_and_mask(error_msg)
        redacted_prompt = self.secret_scanner.scan_and_mask(prompt_content) if os.getenv("BILGEAPI_LOG_RAW_PROMPT") == "true" else "[PROMPT_LOGGING_DISABLED]"
        
        logger.warning(f"Ollama model '{failed_model}' failed. Falling back to '{next_model}'. Error: {redacted_error}")

        if db_session:
            try:
                audit_repo = AuditLogRepository(db_session)
                dec_repo = DecisionRepository(db_session)

                await audit_repo.log_audit(
                    event_type="LLM_FALLBACK_TRIGGERED",
                    actor_id="system",
                    actor_type="SYSTEM",
                    action="FALLBACK",
                    target=f"model:{failed_model}",
                    status="ALLOWED",
                    risk_level="LOW",
                    before_state={"failed_model": failed_model, "prompt": redacted_prompt},
                    after_state={"next_model": next_model, "error": redacted_error}
                )

                await dec_repo.record_decision(
                    task_id=None,
                    classification="LLM_FALLBACK",
                    risk_score=1.0,
                    risk_level="LOW",
                    eligibility="FALLBACK",
                    requires_human_gate=False,
                    decision_reason=f"LLM model failed. Triggered fallback from {failed_model} to {next_model}.",
                    reasons=[f"Error: {redacted_error}"]
                )
                
                await db_session.commit()
            except Exception as e:
                logger.error(f"Failed to record fallback logs in database: {e}")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        db_session: Optional[Any] = None
    ) -> LLMResult:
        """
        Generates text with fallback chain handling.
        """
        chain = self._get_fallback_chain(model)
        last_exception = None
        timeout = self.timeout
        
        # Unpack options
        req_options = options or {}
        max_response_size = int(os.getenv("BILGEAPI_LLM_MAX_RESPONSE_SIZE", "1048576")) # default 1MB

        for i, current_model in enumerate(chain):
            fallback_used = (i > 0)
            start_time = time.perf_counter()
            
            try:
                url = f"{self.base_url}/api/generate"
                payload = {
                    "model": current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": req_options
                }

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    resp_json = response.json()
                    
                latency = time.perf_counter() - start_time
                resp_text = resp_json.get("response", "")
                
                # Check response size limit
                if len(resp_text) > max_response_size:
                    raise ValueError(f"Response size ({len(resp_text)} bytes) exceeded limit of {max_response_size} bytes")

                # Mask secrets in output
                redacted_text = self.secret_scanner.scan_and_mask(resp_text)
                
                # Extract usage info
                usage = {
                    "prompt_eval_count": resp_json.get("prompt_eval_count", 0),
                    "eval_count": resp_json.get("eval_count", 0)
                }

                return LLMResult(
                    text=redacted_text,
                    model=current_model,
                    fallback_used=fallback_used,
                    latency=latency,
                    usage=usage
                )

            except Exception as e:
                last_exception = e
                if i < len(chain) - 1:
                    # Log the fallback event and try the next model
                    await self._log_fallback_event(
                        failed_model=current_model,
                        next_model=chain[i+1],
                        error_msg=str(e),
                        prompt_content=prompt,
                        db_session=db_session
                    )
                else:
                    # All models failed!
                    break

        redacted_err = self.secret_scanner.scan_and_mask(str(last_exception))
        raise RuntimeError(f"Ollama generation failed for all models. Last error: {redacted_err}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        db_session: Optional[Any] = None
    ) -> LLMResult:
        """
        Chat completion with fallback chain handling.
        """
        chain = self._get_fallback_chain(model)
        last_exception = None
        timeout = self.timeout
        
        req_options = options or {}
        max_response_size = int(os.getenv("BILGEAPI_LLM_MAX_RESPONSE_SIZE", "1048576"))

        prompt_summary = " ".join([m.get("content", "") for m in messages[:3]])

        for i, current_model in enumerate(chain):
            fallback_used = (i > 0)
            start_time = time.perf_counter()
            
            try:
                url = f"{self.base_url}/api/chat"
                payload = {
                    "model": current_model,
                    "messages": messages,
                    "stream": False,
                    "options": req_options
                }

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    resp_json = response.json()
                    
                latency = time.perf_counter() - start_time
                resp_msg = resp_json.get("message", {})
                resp_text = resp_msg.get("content", "")
                
                # Check response size limit
                if len(resp_text) > max_response_size:
                    raise ValueError(f"Response size ({len(resp_text)} bytes) exceeded limit of {max_response_size} bytes")

                # Mask secrets in output
                redacted_text = self.secret_scanner.scan_and_mask(resp_text)
                
                # Extract usage info
                usage = {
                    "prompt_eval_count": resp_json.get("prompt_eval_count", 0),
                    "eval_count": resp_json.get("eval_count", 0)
                }

                return LLMResult(
                    text=redacted_text,
                    model=current_model,
                    fallback_used=fallback_used,
                    latency=latency,
                    usage=usage
                )

            except Exception as e:
                last_exception = e
                if i < len(chain) - 1:
                    # Log the fallback event
                    await self._log_fallback_event(
                        failed_model=current_model,
                        next_model=chain[i+1],
                        error_msg=str(e),
                        prompt_content=prompt_summary,
                        db_session=db_session
                    )
                else:
                    break

        redacted_err = self.secret_scanner.scan_and_mask(str(last_exception))
        raise RuntimeError(f"Ollama chat failed for all models. Last error: {redacted_err}")

class MockLLMProvider(BaseLLMProvider):
    def __init__(self, secret_scanner: Optional[SecretScanner] = None):
        self.secret_scanner = secret_scanner or SecretScanner()
        self.preset_response: Optional[str] = None

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        db_session: Optional[Any] = None
    ) -> LLMResult:
        """
        Mock generation returning pre-set responses or prompt-based echo.
        """
        start_time = time.perf_counter()
        
        # Redact prompt
        redacted_prompt = self.secret_scanner.scan_and_mask(prompt)
        
        if self.preset_response:
            resp_text = self.preset_response
        else:
            resp_text = f"Mock LLM Response for prompt: {redacted_prompt}"
            
        redacted_text = self.secret_scanner.scan_and_mask(resp_text)
        latency = time.perf_counter() - start_time
        
        return LLMResult(
            text=redacted_text,
            model=model or "mock-model",
            fallback_used=False,
            latency=latency,
            usage={"prompt_eval_count": 10, "eval_count": 20}
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        db_session: Optional[Any] = None
    ) -> LLMResult:
        """
        Mock chat completion.
        """
        start_time = time.perf_counter()
        
        last_msg = messages[-1].get("content", "") if messages else ""
        redacted_msg = self.secret_scanner.scan_and_mask(last_msg)
        
        if self.preset_response:
            resp_text = self.preset_response
        else:
            resp_text = f"Mock LLM Chat Response to: {redacted_msg}"
            
        redacted_text = self.secret_scanner.scan_and_mask(resp_text)
        latency = time.perf_counter() - start_time
        
        return LLMResult(
            text=redacted_text,
            model=model or "mock-model",
            fallback_used=False,
            latency=latency,
            usage={"prompt_eval_count": 10, "eval_count": 20}
        )
