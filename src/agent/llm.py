"""Optional LLM client wrapper supporting OpenAI, Gemini, Ollama and offline fallback."""

import os
import time
from typing import Optional, Tuple
from src.settings import config


_GEMINI_FALLBACK_MODELS: Tuple[str, ...] = (
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
)
_KNOWN_UNSUPPORTED_GEMINI_ALIASES = {"gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite"}


class HybridLLMClient:
    """Thin LLM wrapper that activates when an API key or Ollama endpoint is configured."""

    def __init__(self) -> None:
        agent_cfg = config.get("agent", {})
        self.enabled: bool = bool(agent_cfg.get("use_llm_when_available", True))
        self.provider: str = os.getenv("LLM_PROVIDER", agent_cfg.get("llm_provider", "openai")).lower()
        self.model: str = os.getenv("LLM_MODEL", agent_cfg.get("llm_model", "gpt-4o-mini"))
        if self.provider == "gemini" and self.model in _KNOWN_UNSUPPORTED_GEMINI_ALIASES:
            self.model = _GEMINI_FALLBACK_MODELS[0]
        self.temperature: float = float(agent_cfg.get("temperature", 0.3))
        self._cooldown_until: float = 0.0
        self._client = self._build_client()

    @property
    def effective_model(self) -> str:
        """Return resolved active model identifier suitable for downstream integrations (e.g. Mem0)."""
        return self.model

    def _build_client(self):
        """Construct an OpenAI-compatible client only if credentials or Ollama are present."""
        if not self.enabled:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            return None

        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        openai_base = os.getenv("OPENAI_BASE_URL", "").strip() or None
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

        if self.provider == "gemini" and gemini_key:
            return OpenAI(
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=5.0,
                max_retries=0,
            )

        if self.provider == "ollama":
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
            if not self._is_ollama_reachable(ollama_url):
                return None
            return OpenAI(api_key="ollama", base_url=f"{ollama_url}/v1", timeout=10.0, max_retries=0)

        if openai_key:
            return OpenAI(api_key=openai_key, base_url=openai_base, timeout=5.0, max_retries=0)

        if gemini_key:
            self.provider = "gemini"
            if self.model.startswith("gpt-") or self.model in _KNOWN_UNSUPPORTED_GEMINI_ALIASES:
                self.model = _GEMINI_FALLBACK_MODELS[0]
            return OpenAI(
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=5.0,
                max_retries=0,
            )

        return None

    @staticmethod
    def _is_ollama_reachable(base_url: str) -> bool:
        """Return True only when a local Ollama daemon responds quickly."""
        try:
            import requests
            resp = requests.get(f"{base_url}/api/tags", timeout=0.6)
            return resp.status_code == 200
        except Exception:
            return False

    @property
    def is_available(self) -> bool:
        """Whether an active LLM backend is ready for inference."""
        return self._client is not None

    @property
    def in_cooldown(self) -> bool:
        """True while backing off after a transient timeout or rate limit."""
        return time.monotonic() < self._cooldown_until

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 350,
        temperature: Optional[float] = None,
    ) -> Optional[str]:
        """Generate text from the configured LLM with fast 404 failover and timeout backoff."""
        if self._client is None or self.in_cooldown:
            return None

        temp = self.temperature if temperature is None else temperature
        candidates = [self.model]
        if self.provider == "gemini":
            for fb in _GEMINI_FALLBACK_MODELS:
                if fb not in candidates:
                    candidates.append(fb)

        for candidate in candidates:
            try:
                resp = self._client.chat.completions.create(
                    model=candidate,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temp,
                    max_tokens=max_tokens,
                )
                content = resp.choices[0].message.content
                if content and content.strip():
                    self.model = candidate
                    return content.strip()
            except Exception as exc:
                err_name = type(exc).__name__.lower()
                err_str = str(exc).lower()
                # Try alternate model IDs only when the model name is missing/unsupported (404)
                if "notfound" in err_name or "404" in err_str:
                    continue
                break

        # Short backoff prevents cascading stalls on live endpoints when network or quota is congested
        self._cooldown_until = time.monotonic() + 45.0
        return None
