"""Optional LLM client wrapper supporting local PyTorch LoRA adapters, API endpoints and offline fallback."""

import os
import time
from pathlib import Path
from typing import List, Optional, Sequence, Tuple
from src.settings import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent


_GEMINI_FALLBACK_MODELS: Tuple[str, ...] = (
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
)
_KNOWN_UNSUPPORTED_GEMINI_ALIASES = {"gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite"}


class HybridLLMClient:
    """Thin LLM wrapper supporting hot-swappable local PyTorch LoRA adapters and optional endpoints."""

    def __init__(self) -> None:
        agent_cfg = config.get("agent", {})
        train_cfg = config.get("training", {})
        self.enabled: bool = bool(agent_cfg.get("use_llm_when_available", True))
        self.provider: str = os.getenv("LLM_PROVIDER", agent_cfg.get("llm_provider", "openai")).lower()
        self.model: str = os.getenv("LLM_MODEL", agent_cfg.get("llm_model", "gpt-4o-mini"))
        if self.provider == "gemini" and self.model in _KNOWN_UNSUPPORTED_GEMINI_ALIASES:
            self.model = _GEMINI_FALLBACK_MODELS[0]
        self.temperature: float = float(agent_cfg.get("temperature", 0.3))
        self._cooldown_until: float = 0.0
        self._local_lora = None
        self.lora_adapter_path: Optional[Path] = None

        use_local_lora = (
            os.getenv("DANBI_USE_LOCAL_LORA", "").lower() in {"1", "true", "yes"}
            or bool(train_cfg.get("use_local_lora_adapter", False))
            or self.provider == "local_lora"
        )
        configured_adapter = os.getenv("DANBI_LORA_ADAPTER_PATH", train_cfg.get("lora_adapter_path", "")).strip()
        if use_local_lora and configured_adapter:
            adapter_dir = Path(configured_adapter)
            if not adapter_dir.is_absolute():
                adapter_dir = BASE_DIR / adapter_dir
            if (adapter_dir / "adapter.pt").exists() and (adapter_dir / "tokenizer.json").exists():
                self.load_lora_adapter(adapter_dir)

        self._client = None if self.provider == "local_lora" else self._build_client()

    def load_lora_adapter(self, adapter_dir: Path) -> bool:
        """Load or hot-swap a locally trained PyTorch LoRA adapter without Ollama or HuggingFace."""
        target = Path(adapter_dir)
        if not target.is_absolute():
            target = BASE_DIR / target
        if not (target / "adapter.pt").exists():
            return False
        from src.training.local_lora import LocalLoRARuntime

        if self._local_lora is not None and (target / "adapter.pt").exists():
            try:
                self._local_lora.hotswap_adapter(target)
                self.lora_adapter_path = target
                return True
            except Exception:
                pass
        self._local_lora = LocalLoRARuntime(target)
        self.lora_adapter_path = target
        return True

    def hotswap_lora_adapter(self, adapter_dir: Path) -> bool:
        """Alias for hot-swapping an updated LoRA adapter checkpoint at runtime."""
        return self.load_lora_adapter(adapter_dir)

    @property
    def has_local_lora(self) -> bool:
        """True when a local GRPO/SFT LoRA adapter is loaded in memory."""
        return self._local_lora is not None

    def score_candidates_with_lora(
        self,
        system_prompt: str,
        mem0_context: Sequence[str],
        user_query: str,
        candidates: Sequence[str],
    ) -> Optional[List[float]]:
        """Score local candidate responses via the loaded LoRA adapter policy."""
        if self._local_lora is None or not candidates:
            return None
        return self._local_lora.score_candidates(system_prompt, mem0_context, user_query, candidates)

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
        """Whether an external/local completion endpoint (not just LoRA reranker) is active."""
        return self._client is not None or (self.provider == "local_lora" and self._local_lora is not None)

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
        """Generate text from the configured local LoRA policy or endpoint, stripping `<think>` tags."""
        temp = self.temperature if temperature is None else temperature

        if self.provider == "local_lora" and self._local_lora is not None:
            _think, final_ans = self._local_lora.generate_response(
                system_prompt=system_prompt,
                mem0_context=[],
                user_query=user_prompt,
                max_new_tokens=min(max_tokens, 160),
                temperature=temp,
            )
            return final_ans or None

        if self._client is None or self.in_cooldown:
            return None

        candidates = [self.model]
        if self.provider == "gemini":
            for fb in _GEMINI_FALLBACK_MODELS:
                if fb not in candidates:
                    candidates.append(fb)

        from src.training.local_lora import strip_think_tags

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
                    _think, clean_answer = strip_think_tags(content.strip())
                    return clean_answer or content.strip()
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
