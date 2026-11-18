"""Optional LLM client wrapper supporting OpenAI, Gemini, Ollama and offline fallback."""

import os
from typing import Optional
from src.settings import config


class HybridLLMClient:
    """Thin LLM wrapper that activates when an API key or Ollama endpoint is configured."""

    def __init__(self) -> None:
        agent_cfg = config.get("agent", {})
        self.enabled: bool = bool(agent_cfg.get("use_llm_when_available", True))
        self.provider: str = os.getenv("LLM_PROVIDER", agent_cfg.get("llm_provider", "openai")).lower()
        self.model: str = os.getenv("LLM_MODEL", agent_cfg.get("llm_model", "gpt-4o-mini"))
        self.temperature: float = float(agent_cfg.get("temperature", 0.3))
        self._client = self._build_client()

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
                timeout=12.0,
                max_retries=1,
            )

        if self.provider == "ollama":
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
            if not self._is_ollama_reachable(ollama_url):
                return None
            return OpenAI(api_key="ollama", base_url=f"{ollama_url}/v1", timeout=15.0, max_retries=1)

        if openai_key:
            return OpenAI(api_key=openai_key, base_url=openai_base, timeout=12.0, max_retries=1)

        if gemini_key:
            self.provider = "gemini"
            if self.model.startswith("gpt-"):
                self.model = "gemini-2.5-flash"
            return OpenAI(
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=12.0,
                max_retries=1,
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

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 350,
        temperature: Optional[float] = None,
    ) -> Optional[str]:
        """Generate text from the configured LLM, or return None if unavailable/failing."""
        if self._client is None:
            return None
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature if temperature is None else temperature,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content
            return content.strip() if content else None
        except Exception:
            return None
