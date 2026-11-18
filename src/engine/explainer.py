"""Explanation facility for JangBot."""

from typing import Any, Dict, List, Optional
from src.knowledge.repository import KnowledgeRepository
from src.dialogue.variations import pick_variation


class Explainer:
    """Generate source citations and reasoning explanations."""

    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository

    def explain_facts(self, fact_ids: List[str], session: Any = None) -> str:
        """Construct a varied explanation for the given fact identifiers."""
        if not fact_ids:
            return pick_variation(
                "explainer::empty",
                (
                    "I haven't cited any specific verified records in this conversation yet.",
                    "No facts have been referenced in our chat so far—ask a janggu question first and I can cite the sources behind it.",
                    "There aren't any cited claims on screen yet; ask me about a janggu topic and I'll back it up with sources.",
                    "We haven't covered any verified facts in this thread yet, so there are no citations to list right now.",
                ),
                session=session,
            )

        lead = pick_variation(
            "explainer::lead",
            (
                "Here are the verified sources backing the points we just covered:",
                "Every factual claim from that answer comes from these verified records:",
                "You can trace those details directly to the following verified sources:",
                "These verified references support the information I just shared:",
                "Below are the verified historical and scholarly citations behind that response:",
            ),
            session=session,
        )
        lines = [lead]
        for fact_id in fact_ids:
            citations = self.repository.get_citations_for_fact(fact_id)
            for c in citations:
                detail = c.get("citation_detail") or c.get("title")
                pub = c.get("publisher", "Unknown Publisher")
                tier = c.get("tier", 1)
                url = c.get("url")
                if url:
                    lines.append(f"- Fact [{fact_id}]: {detail} ({pub}, Tier {tier}). Link: {url}")
                else:
                    lines.append(f"- Fact [{fact_id}]: {detail} ({pub}, Tier {tier})")

        return "\n".join(lines)
