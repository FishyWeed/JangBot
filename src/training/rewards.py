"""Deterministic rule-based verifier and GRPO reward functions grounded in janggu.db and Mem0."""

import re
from typing import Any, Dict, List, Optional, Sequence
from src.dialogue.variations import BANNED_PHRASES
from src.knowledge.repository import KnowledgeRepository
from src.knowledge.semantic_network import SemanticNetwork
from src.training.local_lora import strip_think_tags

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "had", "into", "onto", "about", "what", "which", "when",
    "where", "while", "how", "why", "who", "its", "their", "your", "our",
    "can", "could", "would", "should", "also", "more", "most", "very", "such",
    "used", "using", "make", "makes", "made", "than", "then", "there", "these",
    "those", "only", "both", "each", "over", "under", "through", "between",
}


def _content_tokens(text: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-z0-9\uAC00-\uD7A3]+", (text or "").lower())
        if len(tok) >= 4 and tok not in _STOPWORDS
    }


def reasoning_structure_reward(candidate: str) -> float:
    """Reward valid `<think>...</think>` blocks containing explicit NLP intent/constraint breakdown before final answer."""
    raw = (candidate or "").strip()
    if not raw:
        return 0.0

    think_match = re.search(r"<think>(.*?)</think>\s*(.*)", raw, flags=re.DOTALL | re.IGNORECASE)
    if not think_match:
        return 0.0

    think_body = think_match.group(1).strip()
    final_answer = think_match.group(2).strip()
    if not think_body or not final_answer:
        return 0.1

    score = 0.35
    think_low = think_body.lower()

    # Check explicit structured NLP reasoning facets inside <think>
    facet_checks = (
        ("intent", ("intent", "topic", "asking", "question")),
        ("nuance", ("nuance", "sentiment", "tone", "mood", "fragment", "follow-up")),
        ("mem0", ("mem0", "memory", "memories", "learner", "preference", "wrist", "beginner")),
        ("rules", ("rule", "verified", "fact", "source", "citation", "story", "ground")),
    )
    for _, markers in facet_checks:
        if any(m in think_low for m in markers):
            score += 0.125

    # Reward clean final answer without leaked tags or dry bullet dumps
    if "<think>" not in final_answer.lower() and "</think>" not in final_answer.lower():
        score += 0.08
    if "\n- " not in final_answer:
        score += 0.07
    else:
        score -= 0.15

    return max(0.0, min(1.0, round(score, 4)))


def mem0_adherence_reward(candidate: str, mem0_context: Sequence[str], user_query: str = "") -> float:
    """Reward responses that strictly respect retrieved Mem0 learner facts without contradiction."""
    think_body, final_answer = strip_think_tags(candidate)
    combined_low = f"{think_body}\n{final_answer}".lower()
    ans_low = final_answer.lower()
    if not final_answer:
        return 0.0

    mem_lines = [m.strip() for m in (mem0_context or []) if m and m.strip()]
    if not mem_lines:
        # Clean neutral score when no user memories exist (rewards noting empty memory in <think>)
        return 1.0 if ("none" in think_body.lower() or "no prior" in think_body.lower() or "mem0" in think_body.lower()) else 0.85

    mem_joined = " ".join(mem_lines).lower()
    score = 0.70

    # Strict contradiction checks
    if "wrist" in mem_joined or "sore" in mem_joined or "tension" in mem_joined:
        bad_advice = ("grip tightly", "lock your wrist", "force the stroke", "ignore wrist pain", "stiff wrist")
        if any(p in ans_low for p in bad_advice):
            return 0.0
        good_cues = ("relax", "relaxed", "wrist", "light", "rebound", "tension", "rest", "finger")
        if any(c in combined_low for c in good_cues):
            score += 0.20

    if "beginner" in mem_joined:
        if "only for advanced" in ans_low or "skip jungmori" in ans_low:
            return 0.0
        if any(c in combined_low for c in ("beginner", "jungmori", "steady", "starting", "newcomer", "gradual")):
            score += 0.15

    for jangdan in ("jinyangjo", "jungmori", "jungjungmori", "jajinmori", "hwimori", "gutgeori", "eonmori"):
        if jangdan in mem_joined and jangdan in combined_low:
            score += 0.10
            break

    # Bonus for referencing Mem0 constraints inside <think>
    if any(tok in think_body.lower() for tok in ("mem0", "memory", "learner", "wrist", "beginner")):
        score += 0.10

    return max(0.0, min(1.0, round(score, 4)))


def expert_kb_accuracy_reward(
    candidate: str,
    expected_facts: Sequence[Dict[str, Any]],
    user_query: str = "",
    semantic_network: Optional[SemanticNetwork] = None,
) -> float:
    """Reward factual alignment with verified janggu.db facts & semantic triples; penalize clichés/drift."""
    _think, final_answer = strip_think_tags(candidate)
    ans_low = final_answer.lower()
    if not final_answer or len(final_answer.split()) < 8:
        return 0.0

    # Hard penalty for banned stock clichés or dry timeline bullet dumps
    if any(phrase in ans_low for phrase in BANNED_PHRASES):
        return 0.0
    if "\n- " in final_answer and "verified sources" not in ans_low:
        return 0.15

    # Honest-gap fallback check when no verified facts exist
    if not expected_facts:
        if "don't have verified information" in ans_low or "verified" in ans_low:
            return 0.90
        return 0.25

    fact_tokens: set[str] = set()
    for f in expected_facts:
        stmt = f.get("statement", "") if isinstance(f, dict) else str(f)
        fact_tokens |= _content_tokens(stmt)

    ans_tokens = _content_tokens(final_answer)
    if not fact_tokens:
        return 0.5

    overlap = len(fact_tokens & ans_tokens)
    coverage = min(1.0, overlap / max(min(len(fact_tokens), 14), 4))
    score = 0.25 + 0.55 * coverage

    # Bonus if semantic network concepts from query also appear grounded in answer
    if semantic_network is not None and user_query:
        q_concepts = [c for c in semantic_network.extract_concepts_from_text(user_query) if c != "janggu"]
        if q_concepts:
            a_concepts = set(semantic_network.extract_concepts_from_text(final_answer))
            hit_ratio = sum(1 for c in q_concepts if c in a_concepts) / len(q_concepts)
            score += 0.20 * hit_ratio
        else:
            score += 0.15
    else:
        score += 0.15

    # Penalize accidental off-topic boilerplate on an in-domain verified query
    if "solely to the korean janggu" in ans_low:
        return 0.0

    return max(0.0, min(1.0, round(score, 4)))


def verify_candidate(
    candidate: str,
    *,
    user_query: str,
    mem0_context: Sequence[str],
    expected_facts: Sequence[Dict[str, Any]],
    semantic_network: Optional[SemanticNetwork] = None,
    min_total_score: float = 0.72,
) -> Dict[str, Any]:
    """Deterministically verify a `<think>...</think>` + answer candidate against KB, Mem0 and formatting rules."""
    r_struct = reasoning_structure_reward(candidate)
    r_mem0 = mem0_adherence_reward(candidate, mem0_context, user_query=user_query)
    r_kb = expert_kb_accuracy_reward(
        candidate,
        expected_facts,
        user_query=user_query,
        semantic_network=semantic_network,
    )
    total = round((0.30 * r_struct) + (0.25 * r_mem0) + (0.45 * r_kb), 4)

    reasons: List[str] = []
    if r_struct < 0.70:
        reasons.append("missing_or_incomplete_think_reasoning")
    if r_mem0 < 0.65:
        reasons.append("mem0_constraint_violation")
    if r_kb < 0.60:
        reasons.append("insufficient_kb_grounding_or_style_violation")

    passed = (len(reasons) == 0) and (total >= min_total_score)
    return {
        "passed": passed,
        "total_reward": total,
        "rewards": {
            "reasoning_structure": r_struct,
            "mem0_adherence": r_mem0,
            "expert_kb_accuracy": r_kb,
        },
        "reasons": reasons,
    }


def resolve_expected_facts_for_query(
    query: str,
    fact_ids: Optional[Sequence[str]],
    repository: KnowledgeRepository,
    semantic_network: Optional[SemanticNetwork] = None,
) -> List[Dict[str, Any]]:
    """Collect ground-truth verified facts from explicit fact_ids or local KB/semantic-network lookup."""
    if fact_ids:
        rows = repository.get_facts_by_ids(list(fact_ids))
        if rows:
            return rows

    if semantic_network is not None:
        rel = semantic_network.answer_relational_query(query)
        if rel and rel.get("facts"):
            return list(rel["facts"])
        concepts = [c for c in semantic_network.extract_concepts_from_text(query) if c != "janggu"]
        if concepts:
            fids: List[str] = []
            for cid in concepts[:2]:
                for edge in semantic_network.get_neighbors(cid, direction="both"):
                    if edge["fact_id"] not in fids:
                        fids.append(edge["fact_id"])
            if fids:
                return repository.get_facts_by_ids(fids[:4])

    # Fallback lexical match over verified facts
    q_tokens = _content_tokens(query)
    if not q_tokens:
        return []
    scored = []
    for fact in repository.get_verified_facts():
        f_tokens = _content_tokens(fact["statement"])
        overlap = len(q_tokens & f_tokens)
        if overlap > 0:
            scored.append((overlap, fact))
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [f for _, f in scored[:4]]
