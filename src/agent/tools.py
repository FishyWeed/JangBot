"""LangGraph tools wrapping verified Janggu SQLite knowledge and rule inference."""

import json
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
        """Rank verified facts in janggu.db by keyword overlap and attach citations."""
        raw_tokens = [t.lower() for t in query.split() if len(t) >= 3]
        facts = self.repository.get_verified_facts()
        scored: List[tuple[int, Dict[str, Any]]] = []

        for fact in facts:
            haystack = f"{fact['category']} {fact['statement']} {fact.get('period') or ''}".lower()
            score = 0
            for tok in raw_tokens:
                stem = self._stem(tok)
                if tok in haystack or (len(stem) >= 3 and stem in haystack):
                    score += 1
            if score > 0:
                enriched = dict(fact)
                enriched["citations"] = self.repository.get_citations_for_fact(fact["id"])
                scored.append((score, enriched))

        scored.sort(key=lambda item: (-item[0], item[1].get("year_exact") or 9999, item[1]["id"]))
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
