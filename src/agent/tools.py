"""LangGraph tools wrapping verified Janggu SQLite knowledge and rule inference."""

import json
import math
import re
from typing import Any, Dict, List
from langchain_core.tools import tool
from src.knowledge.repository import KnowledgeRepository
from src.engine.inference import InferenceEngine
from src.engine.explainer import Explainer
from src.memory.session import SessionMemory


class JangguToolchain:
    """Factory binding verified read-only knowledge tools to a repository instance."""

    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository
        self.engine = InferenceEngine(repository)
        self.explainer = Explainer(repository)
        self.tools = self._build_tools()

    @staticmethod
    def _stem(token: str) -> str:
        """Apply light suffix normalization so plurals/inflections match verified facts."""
        t = token.lower()
        for suffix in ("ing", "ies", "es", "ed", "s"):
            if len(t) > len(suffix) + 3 and t.endswith(suffix):
                return "y" if suffix == "ies" else t[: -len(suffix)]
        return t

    def search_facts_sync(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Rank verified and disputed facts in janggu.db using IDF-weighted word/stem overlap."""
        raw_tokens = [
            t.lower()
            for t in re.findall(r"[a-zA-Z0-9\uAC00-\uD7A3μ°]+", query)
            if len(t) >= 3 or t.isdigit()
        ]
        if not raw_tokens:
            return []

        facts = list(self.repository.get_verified_facts()) + list(self.repository.get_disputed_facts())
        fact_word_sets = [
            (
                fact,
                set(re.findall(r"[a-z0-9\uAC00-\uD7A3μ°]+", f"{fact['category']} {fact['statement']} {fact.get('period') or ''}".lower())),
            )
            for fact in facts
        ]

        def _matches_word_set(tok: str, words: set) -> bool:
            if tok in words or f"{tok}s" in words:
                return True
            if len(tok) >= 4:
                stem = self._stem(tok)
                if len(stem) >= 4 and any(self._stem(w) == stem or w.startswith(stem) for w in words):
                    return True
            return False

        # IDF weighting ensures rare organology/physics tokens outrank generic terms like 'drum' or 'wood'
        doc_freq = {
            tok: sum(1 for _, words in fact_word_sets if _matches_word_set(tok, words))
            for tok in set(raw_tokens)
        }

        scored: List[tuple[float, Dict[str, Any]]] = []
        for fact, words in fact_word_sets:
            score = 0.0
            for tok in set(raw_tokens):
                if _matches_word_set(tok, words):
                    score += 1.0 / math.log(2.0 + doc_freq[tok])
            if score > 0.0:
                enriched = dict(fact)
                enriched["citations"] = self.repository.get_citations_for_fact(fact["id"])
                scored.append((score, enriched))

        scored.sort(
            key=lambda item: (
                -round(item[0], 6),
                item[1].get("status") != "Verified",
                item[1].get("year_exact") or 9999,
                item[1]["id"],
            )
        )
        return [item[1] for item in scored[:limit]]

    def explain_sources_sync(self, fact_ids: List[str], session: Any = None) -> Dict[str, Any]:
        """Return formatted explanation text and citation records for given fact IDs."""
        text = self.explainer.explain_facts(fact_ids, session=session)
        citations: List[Dict[str, Any]] = []
        for fid in fact_ids:
            for c in self.repository.get_citations_for_fact(fid):
                rec = dict(c)
                rec["fact_id"] = fid
                citations.append(rec)
        return {"text": text, "citations": citations, "fact_ids": fact_ids}

    def evaluate_rules_sync(
        self,
        intent: str,
        entities: Dict[str, str],
        confidence: float,
        session: SessionMemory,
    ) -> Dict[str, Any]:
        """Run the deterministic inference engine and return facts, citations and baseline reply."""
        result = self.engine.evaluate(intent, entities, confidence, session)
        fact_ids = result.get("fact_ids", [])
        all_verified = {f["id"]: f for f in self.repository.get_verified_facts()}
        for df in self.repository.get_disputed_facts():
            all_verified.setdefault(df["id"], df)
        facts = [all_verified[fid] for fid in fact_ids if fid in all_verified]
        citations: List[Dict[str, Any]] = []
        for fid in fact_ids:
            for c in self.repository.get_citations_for_fact(fid):
                rec = dict(c)
                rec["fact_id"] = fid
                citations.append(rec)

        return {
            "status": result["status"],
            "baseline_text": result["text"],
            "fact_ids": fact_ids,
            "facts": facts,
            "citations": citations,
        }

    def _build_tools(self) -> List[Any]:
        """Build LangChain @tool wrappers for graph inspection and agent invocation."""
        repo = self.repository
        toolchain = self

        @tool("lookup_facts_by_category")
        def lookup_facts_by_category(category: str) -> str:
            """Fetch verified janggu facts by category: origin, etymology, chronology, construction, playing_technique, cultural_use, or evolution."""
            rows = repo.get_verified_facts(category=category)
            return json.dumps(rows, ensure_ascii=False)

        @tool("search_janggu_facts")
        def search_janggu_facts(query: str) -> str:
            """Search verified facts in janggu.db matching keywords in history, acoustics, rhythms, materials, or strokes."""
            rows = toolchain.search_facts_sync(query)
            return json.dumps(rows, ensure_ascii=False)

        @tool("get_fact_citations")
        def get_fact_citations(fact_ids: List[str]) -> str:
            """Retrieve verified academic/institutional citations for a list of fact IDs like ['F04', 'F16']."""
            payload = toolchain.explain_sources_sync(fact_ids)
            return json.dumps(payload, ensure_ascii=False)

        return [lookup_facts_by_category, search_janggu_facts, get_fact_citations]
