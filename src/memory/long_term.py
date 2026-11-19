"""Persistent cross-session long-term memory powered by Mem0 with offline SQLite fallback."""

import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from src.settings import config
from src.agent.llm import HybridLLMClient

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class LongTermMemoryManager:
    """Manage user-scoped persistent memories across separate JangBot sessions."""

    JANGDAN_NAMES = {
        "jinyangjo": "Jinyangjo",
        "jungmori": "Jungmori",
        "jungjungmori": "Jungjungmori",
        "jajinmori": "Jajinmori",
        "hwimori": "Hwimori",
        "gutgeori": "Gutgeori",
        "eonmori": "Eonmori",
    }

    STYLE_NAMES = {
        "nongak": "Nongak folk music",
        "pungmul": "Pungmul",
        "samulnori": "Samulnori",
        "samul nori": "Samul nori",
        "jeongak": "Jeongak royal court music",
        "court music": "Jeongak royal court music",
        "sanjo": "Sanjo solo music",
        "pansori": "Pansori accompaniment",
        "minyo": "Minyo folk songs",
    }

    def __init__(
        self,
        llm_client: Optional[HybridLLMClient] = None,
        local_db_path: Optional[Path] = None,
        qdrant_path: Optional[Path] = None,
        history_db_path: Optional[Path] = None,
        encoder: Any = None,
    ) -> None:
        mem_cfg = config.get("memory", {})
        self.enabled: bool = bool(mem_cfg.get("enabled", True))
        self.top_k: int = int(mem_cfg.get("top_k", 5))
        self.embedder_model: str = mem_cfg.get("embedder_model", "all-MiniLM-L6-v2")

        self.local_db_path = Path(local_db_path) if local_db_path else BASE_DIR / mem_cfg.get("local_fallback_db", "data/local_memories.db")
        self.qdrant_path = Path(qdrant_path) if qdrant_path else BASE_DIR / mem_cfg.get("qdrant_path", "data/mem0_qdrant")
        self.history_db_path = Path(history_db_path) if history_db_path else BASE_DIR / mem_cfg.get("history_db", "data/mem0_history.db")

        self.local_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_local_db()

        self.llm_client = llm_client or HybridLLMClient()
        self._encoder = encoder
        self._mem0 = self._init_mem0() if self.enabled else None

    @property
    def backend_mode(self) -> str:
        """Report whether live Mem0 LLM extraction or local offline store is active."""
        return "mem0" if self._mem0 is not None else "local_offline"

    def _init_local_db(self) -> None:
        """Initialize SQLite schema for deterministic offline/supplemental long-term memories."""
        conn = sqlite3.connect(self.local_db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                slot TEXT NOT NULL,
                memory TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, slot, memory)
            )
            """
        )
        conn.commit()
        conn.close()

    def _build_mem0_config(self) -> Optional[Dict[str, Any]]:
        """Construct Mem0 config dictionary for local Qdrant + HuggingFace + configured LLM."""
        if not self.llm_client.is_available:
            return None

        self.qdrant_path.mkdir(parents=True, exist_ok=True)
        self.history_db_path.parent.mkdir(parents=True, exist_ok=True)

        llm_block: Optional[Dict[str, Any]] = None
        provider = self.llm_client.provider
        model = self.llm_client.effective_model

        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            if api_key:
                llm_block = {
                    "provider": "gemini",
                    "config": {"model": model, "api_key": api_key, "temperature": 0.1},
                }
        elif provider == "ollama":
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
            llm_block = {
                "provider": "ollama",
                "config": {"model": model, "ollama_base_url": ollama_url, "temperature": 0.1},
            }
        else:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if api_key:
                cfg: Dict[str, Any] = {"model": model, "api_key": api_key, "temperature": 0.1}
                base_url = os.getenv("OPENAI_BASE_URL", "").strip()
                if base_url:
                    cfg["openai_base_url"] = base_url
                llm_block = {"provider": "openai", "config": cfg}

        if llm_block is None:
            return None

        return {
            "version": "v1.1",
            "llm": llm_block,
            "embedder": {
                "provider": "huggingface",
                "config": {"model": self.embedder_model, "embedding_dims": 384},
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "jangbot_user_memories",
                    "path": str(self.qdrant_path),
                    "embedding_model_dims": 384,
                },
            },
            "history_db_path": str(self.history_db_path),
        }

    def _init_mem0(self):
        """Initialize Mem0 Memory instance when an LLM backend is configured."""
        mem0_config = self._build_mem0_config()
        if mem0_config is None:
            return None
        try:
            from mem0 import Memory
            return Memory.from_config(mem0_config)
        except Exception:
            return None

    # ------------------------------------------------------------ deterministic fact extraction

    @classmethod
    def extract_user_facts(cls, user_text: str) -> List[Tuple[str, str]]:
        """Extract structured learner facts (slot, statement) from a user message."""
        text = user_text.strip()
        low = text.lower()
        extracted: List[Tuple[str, str]] = []

        # 1. Name
        name_match = re.search(r"\b(?:my name is|call me)\s+([A-Z]?[a-zA-Z]{2,20})\b", text, flags=re.I)
        if name_match:
            name = name_match.group(1).strip().capitalize()
            extracted.append(("user_name", f"User's name is {name}."))

        # 2. Skill level (ordered from specific/higher to beginner)
        if any(p in low for p in ["advanced player", "advanced level", "years of experience", "professional", "experienced player"]):
            extracted.append(("skill_level", "User has an advanced janggu skill level."))
        elif any(p in low for p in ["intermediate", "played for a year", "some experience", "getting better"]):
            extracted.append(("skill_level", "User has an intermediate janggu skill level."))
        elif any(p in low for p in ["beginner", "just started", "new to janggu", "new to this", "never played", "starting out"]):
            extracted.append(("skill_level", "User is a beginner learning the janggu."))

        # 3. Owned instrument
        if any(p in low for p in ["don't own", "do not own", "without a drum", "no janggu yet", "practicing on a pillow", "practice pad"]):
            extracted.append(("owned_instrument", "User does not own a physical janggu yet."))
        elif any(p in low for p in ["i have a", "i own a", "bought a", "my own", "my drum", "my janggu"]) and any(
            k in low for k in ["janggu", "janggo", "changgo", "drum"]
        ):
            if "paulownia" in low or "wood" in low or "wooden" in low:
                extracted.append(("owned_instrument", "User owns a wooden (Paulownia) janggu."))
            elif "ceramic" in low or "sajanggu" in low:
                extracted.append(("owned_instrument", "User owns a ceramic sajanggu."))
            else:
                extracted.append(("owned_instrument", "User owns a janggu drum."))

        # 4. Currently practicing rhythm / jangdan
        practicing_verbs = ("practic", "learn", "working on", "playing", "struggling with", "trying")
        for key, proper in cls.JANGDAN_NAMES.items():
            if key in low and any(v in low for v in practicing_verbs):
                extracted.append(("practicing_jangdan", f"User is currently practicing {proper} jangdan."))
                break

        # 5. Preferred musical tradition / style
        for key, proper in cls.STYLE_NAMES.items():
            if key in low and any(v in low for v in ["prefer", "focus", "like", "love", "interested in", "want to learn", "join"]):
                extracted.append(("preferred_style", f"User is interested in {proper}."))
                break

        # 6. Physical or technique challenges
        if any(p in low for p in ["wrist", "pain", "sore", "tension", "stiff", "cramp", "fatigue", "tire easily"]):
            if "wrist" in low or "tension" in low or "stiff" in low:
                extracted.append(("technique_issue", "User experiences wrist tension or stiffness while playing."))
            elif "sore" in low or "pain" in low or "fatigue" in low:
                extracted.append(("technique_issue", "User experiences hand soreness or fatigue during practice."))
        elif any(p in low for p in ["struggling with", "trouble with", "hard time with", "cannot get", "can't get"]):
            if "gi-deok" in low or "gideok" in low or "flam" in low:
                extracted.append(("technique_issue", "User has difficulty executing the Gi-deok flam stroke."))
            elif "yeolchae" in low or "whip" in low:
                extracted.append(("technique_issue", "User has difficulty controlling the yeolchae bamboo whip."))
            elif "tempo" in low or "speed" in low or "fast" in low:
                extracted.append(("technique_issue", "User wants help maintaining tempo at faster speeds."))

        return extracted

    def _upsert_local_fact(self, user_id: str, slot: str, memory: str) -> Optional[str]:
        """Insert or update a slot-based user memory so newer state supersedes old state."""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Singleton slots overwrite prior contradicting facts (Mem0 UPDATE semantics)
        singleton_slots = {"user_name", "skill_level", "owned_instrument", "practicing_jangdan", "preferred_style"}
        if slot in singleton_slots:
            cur.execute(
                "SELECT id, memory FROM user_memories WHERE user_id = ? AND slot = ?",
                (user_id, slot),
            )
            row = cur.fetchone()
            if row:
                if row["memory"] == memory:
                    conn.close()
                    return None
                cur.execute(
                    "UPDATE user_memories SET memory = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (memory, row["id"]),
                )
                conn.commit()
                conn.close()
                return str(row["id"])

        cur.execute(
            "SELECT id FROM user_memories WHERE user_id = ? AND memory = ?",
            (user_id, memory),
        )
        existing = cur.fetchone()
        if existing:
            conn.close()
            return None

        cur.execute(
            "INSERT INTO user_memories (user_id, slot, memory) VALUES (?, ?, ?)",
            (user_id, slot, memory),
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return str(new_id)

    # ------------------------------------------------------------ public Mem0-compatible API

    def add(self, messages: List[Dict[str, str]], user_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Extract, update and persist memories from a turn for the specified user_id."""
        if not self.enabled or not user_id:
            return []

        results: List[Dict[str, Any]] = []

        # Always run deterministic slot extraction locally for reliable offline persistence & fast lookup
        for msg in messages:
            if msg.get("role") == "user" and msg.get("content"):
                for slot, fact in self.extract_user_facts(msg["content"]):
                    mem_id = self._upsert_local_fact(user_id, slot, fact)
                    if mem_id:
                        results.append({"id": mem_id, "memory": fact, "slot": slot, "source": "local_slot"})

        # When Mem0 + LLM backend is active (and not in timeout cooldown), run Mem0's semantic extraction
        if self._mem0 is not None and not getattr(self.llm_client, "in_cooldown", False):
            try:
                mem0_resp = self._mem0.add(messages, user_id=user_id, metadata=metadata or {})
                mem_items = mem0_resp.get("results", []) if isinstance(mem0_resp, dict) else (mem0_resp or [])
                for item in mem_items:
                    if isinstance(item, dict) and item.get("memory"):
                        results.append(item)
            except Exception:
                pass

        return results

    def search(self, query: str, user_id: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant persisted memories for user_id given the current query."""
        if not self.enabled or not user_id:
            return []

        limit = top_k or self.top_k
        collected: List[Dict[str, Any]] = []
        seen_texts: set[str] = set()

        if self._mem0 is not None:
            try:
                resp = self._mem0.search(query, top_k=limit, filters={"user_id": user_id})
                mem_items = resp.get("results", []) if isinstance(resp, dict) else (resp or [])
                for item in mem_items:
                    text = item.get("memory") if isinstance(item, dict) else None
                    if text and text not in seen_texts:
                        seen_texts.add(text)
                        collected.append(item)
            except Exception:
                pass

        local_items = self._search_local(query, user_id, limit)
        for item in local_items:
            if item["memory"] not in seen_texts:
                seen_texts.add(item["memory"])
                collected.append(item)

        return collected[:limit]

    def _search_local(self, query: str, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Rank local SQLite memories for user_id via semantic similarity or keyword/profile priority."""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT id, slot, memory, updated_at FROM user_memories WHERE user_id = ? ORDER BY updated_at DESC, id DESC",
                (user_id,),
            ).fetchall()
        ]
        conn.close()

        if not rows:
            return []

        query_tokens = {t.lower() for t in re.findall(r"\w+", query) if len(t) >= 3}

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for row in rows:
            mem_text = row["memory"]
            mem_tokens = {t.lower() for t in re.findall(r"\w+", mem_text) if len(t) >= 3}
            overlap = len(query_tokens & mem_tokens)
            # Core personalization slots stay gently surfaced across turns
            profile_boost = 0.35 if row["slot"] in {"skill_level", "practicing_jangdan", "technique_issue", "owned_instrument"} else 0.1
            score = overlap + profile_boost

            if self._encoder is not None:
                try:
                    import numpy as np
                    vecs = self._encoder.encode([query, mem_text], normalize_embeddings=True)
                    score += float(np.dot(vecs[0], vecs[1]))
                except Exception:
                    pass

            scored.append((score, {"id": str(row["id"]), "memory": mem_text, "slot": row["slot"], "score": round(score, 4)}))

        scored.sort(key=lambda pair: -pair[0])
        return [item for _, item in scored[:limit]]

    def get_all(self, user_id: str) -> List[Dict[str, Any]]:
        """List all persisted memories for a user across Mem0 and local store."""
        if not self.enabled or not user_id:
            return []

        items: List[Dict[str, Any]] = []
        seen: set[str] = set()

        if self._mem0 is not None:
            try:
                resp = self._mem0.get_all(filters={"user_id": user_id})
                mem_items = resp.get("results", []) if isinstance(resp, dict) else (resp or [])
                for it in mem_items:
                    if isinstance(it, dict) and it.get("memory") and it["memory"] not in seen:
                        seen.add(it["memory"])
                        items.append(it)
            except Exception:
                pass

        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        for row in conn.execute(
            "SELECT id, slot, memory, updated_at FROM user_memories WHERE user_id = ? ORDER BY updated_at DESC, id DESC",
            (user_id,),
        ).fetchall():
            if row["memory"] not in seen:
                seen.add(row["memory"])
                items.append({"id": str(row["id"]), "slot": row["slot"], "memory": row["memory"]})
        conn.close()
        return items
