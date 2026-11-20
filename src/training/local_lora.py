"""Self-contained local PyTorch Causal Transformer + LoRA adapter engine (zero Ollama/HuggingFace)."""

import json
import math
import platform
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

SPECIAL_TOKENS: Tuple[str, ...] = (
    "<pad>",
    "<bos>",
    "<eos>",
    "<unk>",
    "<system>",
    "<mem0>",
    "<user>",
    "<assistant>",
    "<think>",
    "</think>",
)


def detect_hardware_backend() -> Dict[str, Any]:
    """Auto-detect local compute backend (Apple Silicon MLX vs PyTorch CUDA/MPS/CPU)."""
    sys_name = platform.system()
    machine = platform.machine().lower()
    mlx_available = False
    if sys_name == "Darwin" and ("arm" in machine or "aarch64" in machine):
        try:
            import mlx.core  # type: ignore  # noqa: F401
            mlx_available = True
        except Exception:
            mlx_available = False

    if mlx_available:
        return {"backend": "mlx", "device": "mlx", "dtype": "float16", "cuda": False}
    if torch.cuda.is_available():
        return {
            "backend": "pytorch",
            "device": "cuda",
            "dtype": "bfloat16" if torch.cuda.is_bf16_supported() else "float16",
            "cuda": True,
            "gpu_name": torch.cuda.get_device_name(0),
        }
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return {"backend": "pytorch", "device": "mps", "dtype": "float32", "cuda": False}
    return {"backend": "pytorch", "device": "cpu", "dtype": "float32", "cuda": False}


def strip_think_tags(text: str) -> Tuple[str, str]:
    """Split an output containing `<think>...</think>` into (thinking_trace, final_answer)."""
    raw = (text or "").strip()
    match = re.search(r"<think>(.*?)</think>\s*(.*)", raw, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    cleaned = re.sub(r"</?think>", "", raw, flags=re.IGNORECASE).strip()
    return "", cleaned


class LocalWordTokenizer:
    """Compact deterministic local tokenizer preserving `<think>` tags, Korean Hangul and punctuation."""

    TOKEN_RE = re.compile(
        r"<(?:pad|bos|eos|unk|system|mem0|user|assistant|/?think)>"
        r"|[A-Za-z0-9_'\-μ°]+"
        r"|[\uAC00-\uD7A3]+"
        r"|\n"
        r"|[^\sA-Za-z0-9\uAC00-\uD7A3]"
    )

    def __init__(self, vocab: Optional[Dict[str, int]] = None) -> None:
        if vocab is not None:
            self.token_to_id: Dict[str, int] = dict(vocab)
        else:
            self.token_to_id = {tok: idx for idx, tok in enumerate(SPECIAL_TOKENS)}
        self.id_to_token: Dict[int, str] = {idx: tok for tok, idx in self.token_to_id.items()}

    @property
    def pad_id(self) -> int:
        return self.token_to_id["<pad>"]

    @property
    def bos_id(self) -> int:
        return self.token_to_id["<bos>"]

    @property
    def eos_id(self) -> int:
        return self.token_to_id["<eos>"]

    @property
    def unk_id(self) -> int:
        return self.token_to_id["<unk>"]

    @property
    def vocab_size(self) -> int:
        return len(self.token_to_id)

    def tokenize(self, text: str) -> List[str]:
        return self.TOKEN_RE.findall(text or "")

    def fit(self, texts: Sequence[str], max_vocab: int = 8192) -> None:
        freq: Dict[str, int] = {}
        for text in texts:
            for tok in self.tokenize(text):
                if tok in self.token_to_id:
                    continue
                freq[tok] = freq.get(tok, 0) + 1
        for tok, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])):
            if len(self.token_to_id) >= max_vocab:
                break
            idx = len(self.token_to_id)
            self.token_to_id[tok] = idx
            self.id_to_token[idx] = tok

    def encode(self, text: str, add_bos: bool = False, add_eos: bool = False) -> List[int]:
        ids = [self.token_to_id.get(tok, self.unk_id) for tok in self.tokenize(text)]
        if add_bos:
            ids = [self.bos_id] + ids
        if add_eos:
            ids = ids + [self.eos_id]
        return ids

    def decode(self, ids: Sequence[int], skip_special: bool = False) -> str:
        skip_set = {"<pad>", "<bos>", "<eos>", "<unk>"} if skip_special else {"<pad>", "<bos>", "<eos>"}
        tokens = [self.id_to_token.get(int(i), "") for i in ids]
        tokens = [t for t in tokens if t and t not in skip_set]
        if not tokens:
            return ""
        out: List[str] = []
        no_space_before = {".", ",", "!", "?", ";", ":", ")", "]", "}", "%"}
        no_space_after = {"(", "[", "{", "\n"}
        for tok in tokens:
            if tok == "\n":
                out.append("\n")
                continue
            if not out or out[-1] in no_space_after or tok in no_space_before:
                out.append(tok)
            else:
                out.append(" " + tok)
        return "".join(out).strip()

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"vocab": self.token_to_id}, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "LocalWordTokenizer":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(vocab=data["vocab"])


class LoRALinear(nn.Module):
    """Low-Rank Adaptation wrapper freezing base linear weights and training rank-r A/B matrices."""

    def __init__(self, base_linear: nn.Linear, r: int = 8, alpha: float = 16.0, dropout: float = 0.05) -> None:
        super().__init__()
        self.base = base_linear
        self.base.weight.requires_grad = False
        if self.base.bias is not None:
            self.base.bias.requires_grad = False

        self.r = int(r)
        self.alpha = float(alpha)
        self.scaling = self.alpha / max(self.r, 1)
        self.dropout = nn.Dropout(p=dropout) if dropout > 0 else nn.Identity()

        self.lora_A = nn.Parameter(torch.empty(self.r, base_linear.in_features))
        self.lora_B = nn.Parameter(torch.zeros(base_linear.out_features, self.r))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base_out = self.base(x)
        lora_out = F.linear(F.linear(self.dropout(x), self.lora_A), self.lora_B) * self.scaling
        return base_out + lora_out


class _CausalTransformerBlock(nn.Module):
    """Pre-norm causal Transformer block with LoRA-wrapped attention and feed-forward layers."""

    def __init__(self, d_model: int, n_heads: int, d_ff: int, lora_r: int, lora_alpha: float, dropout: float) -> None:
        super().__init__()
        assert d_model % n_heads == 0
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.ln1 = nn.LayerNorm(d_model)
        self.q_proj = LoRALinear(nn.Linear(d_model, d_model, bias=False), r=lora_r, alpha=lora_alpha, dropout=dropout)
        self.k_proj = LoRALinear(nn.Linear(d_model, d_model, bias=False), r=lora_r, alpha=lora_alpha, dropout=dropout)
        self.v_proj = LoRALinear(nn.Linear(d_model, d_model, bias=False), r=lora_r, alpha=lora_alpha, dropout=dropout)
        self.o_proj = LoRALinear(nn.Linear(d_model, d_model, bias=False), r=lora_r, alpha=lora_alpha, dropout=dropout)

        self.ln2 = nn.LayerNorm(d_model)
        self.fc1 = LoRALinear(nn.Linear(d_model, d_ff), r=lora_r, alpha=lora_alpha, dropout=dropout)
        self.fc2 = LoRALinear(nn.Linear(d_ff, d_model), r=lora_r, alpha=lora_alpha, dropout=dropout)
        self.drop = nn.Dropout(p=dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        bsz, seqlen, dim = x.shape
        h = self.ln1(x)
        q = self.q_proj(h).view(bsz, seqlen, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(h).view(bsz, seqlen, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(h).view(bsz, seqlen, self.n_heads, self.head_dim).transpose(1, 2)

        attn = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        attn = attn.transpose(1, 2).contiguous().view(bsz, seqlen, dim)
        x = x + self.drop(self.o_proj(attn))

        ff = self.fc2(F.gelu(self.fc1(self.ln2(x))))
        return x + self.drop(ff)


class LocalReasoningLM(nn.Module):
    """Lightweight local causal Transformer with frozen base weights and swappable LoRA adapters."""

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 192,
        n_heads: int = 6,
        n_layers: int = 4,
        d_ff: int = 512,
        max_seq_len: int = 512,
        lora_r: int = 8,
        lora_alpha: float = 16.0,
        dropout: float = 0.05,
    ) -> None:
        super().__init__()
        self.cfg: Dict[str, Any] = {
            "vocab_size": int(vocab_size),
            "d_model": int(d_model),
            "n_heads": int(n_heads),
            "n_layers": int(n_layers),
            "d_ff": int(d_ff),
            "max_seq_len": int(max_seq_len),
            "lora_r": int(lora_r),
            "lora_alpha": float(lora_alpha),
            "dropout": float(dropout),
        }
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_seq_len, d_model)
        self.blocks = nn.ModuleList(
            [
                _CausalTransformerBlock(d_model, n_heads, d_ff, lora_r, lora_alpha, dropout)
                for _ in range(n_layers)
            ]
        )
        self.ln_f = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)

    def freeze_base_enable_lora(self) -> Tuple[int, int]:
        """Freeze base transformer weights so only LoRA A/B adapters train; returns (trainable, total)."""
        for name, param in self.named_parameters():
            param.requires_grad = ("lora_A" in name) or ("lora_B" in name)
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.parameters())
        return trainable, total

    def unfreeze_all_for_base_warmup(self) -> None:
        """Allow optional brief base warmup when initializing from scratch without a pre-existing base checkpoint."""
        for param in self.parameters():
            param.requires_grad = True

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        _, seqlen = input_ids.shape
        if seqlen > self.cfg["max_seq_len"]:
            input_ids = input_ids[:, -self.cfg["max_seq_len"] :]
            seqlen = input_ids.shape[1]
        pos = torch.arange(seqlen, device=input_ids.device).unsqueeze(0)
        x = self.tok_emb(input_ids) + self.pos_emb(pos)
        for blk in self.blocks:
            x = blk(x)
        return self.lm_head(self.ln_f(x))

    def lora_state_dict(self) -> Dict[str, torch.Tensor]:
        """Extract only LoRA adapter tensors for lightweight adapter persistence."""
        return {k: v.detach().cpu().clone() for k, v in self.state_dict().items() if "lora_A" in k or "lora_B" in k}

    def load_lora_state_dict(self, lora_weights: Dict[str, torch.Tensor]) -> None:
        """Hot-swap LoRA weights without reloading base model parameters."""
        own = self.state_dict()
        for k, v in lora_weights.items():
            if k in own and own[k].shape == v.shape:
                own[k].copy_(v.to(own[k].device))

    @torch.no_grad()
    def sequence_logprob(self, prompt_ids: List[int], completion_ids: List[int], device: torch.device) -> float:
        """Compute average log-probability of completion_ids conditioned on prompt_ids."""
        if not completion_ids:
            return -10.0
        max_len = self.cfg["max_seq_len"]
        full = (prompt_ids + completion_ids)[-max_len:]
        comp_len = min(len(completion_ids), len(full) - 1)
        if comp_len <= 0:
            return -10.0
        inp = torch.tensor([full[:-1]], dtype=torch.long, device=device)
        tgt = torch.tensor([full[1:]], dtype=torch.long, device=device)
        logits = self.forward(inp)
        log_probs = F.log_softmax(logits, dim=-1)
        token_lp = log_probs.gather(-1, tgt.unsqueeze(-1)).squeeze(-1)[0, -comp_len:]
        return float(token_lp.mean().item())

    @torch.no_grad()
    def generate(
        self,
        prompt_ids: List[int],
        eos_id: int,
        max_new_tokens: int = 120,
        temperature: float = 0.8,
        top_k: int = 40,
        device: Optional[torch.device] = None,
    ) -> List[int]:
        """Autoregressively sample a local completion at the requested temperature."""
        dev = device or next(self.parameters()).device
        generated: List[int] = []
        seq = list(prompt_ids)
        max_len = self.cfg["max_seq_len"]

        for _ in range(max_new_tokens):
            window = seq[-max_len:]
            inp = torch.tensor([window], dtype=torch.long, device=dev)
            logits = self.forward(inp)[0, -1, :]
            if temperature <= 1e-4:
                next_id = int(torch.argmax(logits).item())
            else:
                scaled = logits / float(temperature)
                if top_k > 0 and top_k < scaled.numel():
                    vals, idxs = torch.topk(scaled, k=top_k)
                    probs = F.softmax(vals, dim=-1)
                    pick = torch.multinomial(probs, num_samples=1).item()
                    next_id = int(idxs[pick].item())
                else:
                    probs = F.softmax(scaled, dim=-1)
                    next_id = int(torch.multinomial(probs, num_samples=1).item())
            generated.append(next_id)
            seq.append(next_id)
            if next_id == eos_id:
                break
        return generated


class LocalLoRARuntime:
    """Hot-swappable runtime loader wrapping LocalReasoningLM + LocalWordTokenizer."""

    def __init__(self, adapter_dir: Path) -> None:
        self.adapter_dir = Path(adapter_dir)
        hw = detect_hardware_backend()
        self.device = torch.device(hw["device"] if hw["backend"] == "pytorch" else "cpu")
        self.tokenizer = LocalWordTokenizer.load(self.adapter_dir / "tokenizer.json")
        cfg = json.loads((self.adapter_dir / "adapter_config.json").read_text(encoding="utf-8"))
        self.config = cfg
        self.model = LocalReasoningLM(**cfg["model_config"]).to(self.device)
        base_path = self.adapter_dir / "base_model.pt"
        if base_path.exists():
            self.model.load_state_dict(torch.load(base_path, map_location=self.device, weights_only=True), strict=False)
        adapter_path = self.adapter_dir / "adapter.pt"
        if adapter_path.exists():
            self.model.load_lora_state_dict(torch.load(adapter_path, map_location=self.device, weights_only=True))
        self.model.eval()

    def hotswap_adapter(self, new_adapter_dir: Path) -> None:
        """Hot-swap LoRA weights from another adapter directory without recreating the base model."""
        adapter_file = Path(new_adapter_dir) / "adapter.pt"
        if not adapter_file.exists():
            raise FileNotFoundError(f"LoRA adapter weights not found: {adapter_file}")
        self.model.load_lora_state_dict(torch.load(adapter_file, map_location=self.device, weights_only=True))
        self.adapter_dir = Path(new_adapter_dir)
        self.model.eval()

    def format_prompt(self, system_prompt: str, mem0_context: Sequence[str], user_query: str) -> str:
        mem_text = "; ".join(mem0_context) if mem0_context else "None"
        return (
            f"<system> {system_prompt}\n"
            f"<mem0> {mem_text}\n"
            f"<user> {user_query}\n"
            f"<assistant> "
        )

    def score_candidates(
        self,
        system_prompt: str,
        mem0_context: Sequence[str],
        user_query: str,
        candidates: Sequence[str],
    ) -> List[float]:
        """Rank local response candidates using the GRPO-tuned LoRA policy log-likelihood."""
        prompt_ids = self.tokenizer.encode(self.format_prompt(system_prompt, mem0_context, user_query), add_bos=True)
        scores: List[float] = []
        for cand in candidates:
            comp_ids = self.tokenizer.encode(cand, add_eos=True)
            scores.append(self.model.sequence_logprob(prompt_ids, comp_ids, self.device))
        return scores

    def generate_response(
        self,
        system_prompt: str,
        mem0_context: Sequence[str],
        user_query: str,
        max_new_tokens: int = 120,
        temperature: float = 0.7,
    ) -> Tuple[str, str]:
        """Generate a raw `<think>...</think>` completion and return (thinking_trace, final_answer)."""
        prompt_ids = self.tokenizer.encode(self.format_prompt(system_prompt, mem0_context, user_query), add_bos=True)
        gen_ids = self.model.generate(
            prompt_ids,
            eos_id=self.tokenizer.eos_id,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            device=self.device,
        )
        decoded = self.tokenizer.decode(gen_ids, skip_special=False)
        return strip_think_tags(decoded)
