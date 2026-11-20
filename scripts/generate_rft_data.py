"""Offline Rejection Sampling Fine-Tuning (RFT) data generator and verifier.

Reads logged LangGraph + Mem0 trajectories from ``data/trajectories.jsonl`` (and optionally
seeds additional verified queries from ``knowledge-base/janggu.db`` and
``tools/eval/golden_questions.yaml``), samples ``N=5`` local candidates per query at
``temperature=0.8`` with explicit ``<think>...</think>`` NLP reasoning traces, filters every
candidate through deterministic ``verify_candidate()`` checks against the local knowledge base
and Mem0 constraints, discards failing candidates and exports verified pairs to
``data/rft_verified.jsonl``.

Runs 100% locally with zero external APIs, zero Ollama and zero HuggingFace downloads.
"""

import argparse
import json
import math
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.dialogue.variations import pick_variation
from src.engine.inference import InferenceEngine
from src.knowledge.repository import KnowledgeRepository
from src.knowledge.semantic_network import SemanticNetwork
from src.memory.session import SessionMemory
from src.nlp.classifier import IntentClassifier
from src.nlp.preprocessor import NLPPreprocessor
from src.settings import config
from src.training.local_lora import LocalLoRARuntime
from src.training.rewards import resolve_expected_facts_for_query, verify_candidate

DEFAULT_SYSTEM_PROMPT = (
    "You are Danbi (he/him), a warm Korean janggu tutor and traditional storyteller. "
    "Reason explicitly inside <think>...</think> tags about user intent, nuance, Mem0 learner context "
    "and verified expert rules before writing a vivid, non-repetitive storyteller reply grounded "
    "strictly in verified janggu.db facts."
)

_MEM0_SEED_PROFILES: Tuple[List[str], ...] = (
    [],
    ["User is a beginner learning the janggu."],
    ["User is practicing gutgeori rhythm and mentioned wrist tension when playing fast."],
    ["User is a beginner practicing 12-beat jungmori rhythm."],
    ["User is interested in traditional construction and cavity acoustics."],
)

_STORY_LEADS: Tuple[str, ...] = (
    "Picture how this unfolds inside the Korean janggu tradition:",
    "Looking closely at what verified historical and organological records preserve,",
    "Step into the craft and rhythm behind that question:",
    "Tracing the verified evidence from workshop and stage,",
    "From the perspective of a drummer and craftsperson working with the instrument,",
    "Across centuries of court halls and village yards, the documented story is vivid:",
)

_CLOSING_QUESTIONS: Tuple[str, ...] = (
    "Would you like to trace how that connects to the drum's tuning wedges or cavity acoustics next?",
    "Want to explore how royal court Jeongak and lively folk festivals shape this tradition differently?",
    "Should we look closely at the five named strokes or the wood craft inside the hourglass shell next?",
    "Curious to compare slow 24-beat Jinyangjo with blazing 4-beat Hwimori from here?",
    "Where would you like to wander next in the story of the janggu?",
)

_WRIST_COACHING_NOTES: Tuple[str, ...] = (
    "Keeping your wrist tension in mind, let the light bamboo yeolchae rebound from relaxed finger snap instead of forcing fast strokes, and take brief breaks whenever stiffness builds.",
    "Since you mentioned wrist tension earlier, keep your right-hand grip feather-light on the yeolchae and let natural rebound carry the tempo rather than tightening your forearm.",
)

_BEGINNER_COACHING_NOTES: Tuple[str, ...] = (
    "As a beginner, settling into an unhurried 12-beat Jungmori pulse first gives both hands room to coordinate smoothly before accelerating.",
    "Starting out on the janggu feels much steadier when you anchor your timing inside calm 12-beat Jungmori cycles before chasing faster festival tempos.",
)


def _temperature_pick(rng: random.Random, items: Sequence[Any], weights: Sequence[float], temperature: float) -> Any:
    """Sample an item using temperature-scaled softmax weights."""
    if not items:
        return None
    temp = max(float(temperature), 0.05)
    scaled = [math.exp(w / temp) for w in weights]
    total = sum(scaled) or 1.0
    probs = [v / total for v in scaled]
    r = rng.random()
    acc = 0.0
    for item, p in zip(items, probs):
        acc += p
        if r <= acc:
            return item
    return items[-1]


def _detect_query_nuance(query: str, feedback_score: Optional[float] = None) -> str:
    low = (query or "").strip().lower()
    words = low.split()
    tags: List[str] = []
    if feedback_score is not None and feedback_score < 0:
        tags.append("user-correction recovery (prior reply missed the mark)")
    if len(words) <= 4:
        tags.append("short or elliptical phrasing")
    elif "?" in query:
        tags.append("direct curious question")
    else:
        tags.append("conversational statement or prompt")
    if any(w in low for w in ("fast", "faster", "speed", "tempo", "hard", "difficult", "sore", "tension")):
        tags.append("practical playing concern")
    if any(w in low for w in ("why", "how", "compare", "difference", "connect", "link")):
        tags.append("analytical or multi-hop curiosity")
    return "; ".join(tags)


def _clean_story_body(text: str) -> str:
    """Ensure storyteller prose has no raw markdown bullet dumps."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    cleaned: List[str] = []
    for ln in lines:
        if ln.startswith("- ") or ln.startswith("* "):
            cleaned.append(ln[2:].strip())
        else:
            cleaned.append(ln)
    return "\n\n".join(cleaned).strip()


def _compose_fact_story(
    facts: Sequence[Dict[str, Any]],
    lead: str,
    closing_q: str,
    mem0_context: Sequence[str],
    rng: random.Random,
    include_coaching: bool = True,
) -> str:
    """Weave verified fact statements into warm storytelling paragraphs without bullets."""
    if not facts:
        return (
            "I don't have verified information on that specific point in my current janggu records, "
            "so I won't guess. Ask instead about its verified history, construction, acoustics or rhythms."
        )
    ordered = list(facts)
    if len(ordered) > 2 and rng.random() < 0.45:
        tail = ordered[1:]
        rng.shuffle(tail)
        ordered = [ordered[0]] + tail

    statements = [f["statement"].strip() for f in ordered if f.get("statement")]
    first_stmt = statements[0]
    if lead.endswith(",") and len(first_stmt) > 1 and first_stmt[0].isupper():
        first_word = re.match(r"([A-Za-z]+)", first_stmt)
        keep_cap = {
            "Jeongganbo", "King", "Goryeo", "Goryeosa", "Joseon", "Silla", "Korean",
            "Korea", "Paulownia", "UNESCO", "KAIST", "SLDV", "Akhak", "Seong", "Choi",
            "National", "Nongak", "Pungmul", "Pansori", "Jeongak", "Samulnori", "Seoljanggu",
            "Daechwita", "Hornbostel", "Bessel", "Helmholtz", "Jongmyo", "Transfer",
        }
        if first_word and first_word.group(1) not in keep_cap:
            first_stmt = first_stmt[0].lower() + first_stmt[1:]

    paragraphs: List[str] = [f"{lead} {first_stmt}"]
    if len(statements) > 1:
        paragraphs.append(" ".join(statements[1:3]))

    mem_joined = " ".join(mem0_context).lower()
    if include_coaching and mem_joined:
        if "wrist" in mem_joined or "tension" in mem_joined or "sore" in mem_joined:
            paragraphs.append(rng.choice(_WRIST_COACHING_NOTES))
        elif "beginner" in mem_joined:
            paragraphs.append(rng.choice(_BEGINNER_COACHING_NOTES))

    paragraphs.append(closing_q)
    return "\n\n".join(p for p in paragraphs if p)


def _build_think_block(
    *,
    intent: str,
    confidence: float,
    entities: Dict[str, str],
    nuance: str,
    mem0_context: Sequence[str],
    expected_facts: Sequence[Dict[str, Any]],
    concepts: Sequence[str],
    style_note: str,
) -> str:
    mem_summary = "; ".join(mem0_context) if mem0_context else "None recorded yet (no prior learner constraints)"
    ent_summary = ", ".join(sorted(entities.keys())) if entities else "general janggu"
    concept_summary = ", ".join(concepts[:4]) if concepts else "janggu"
    fact_ids = ", ".join(f["id"] for f in expected_facts[:5]) if expected_facts else "none (honest fallback required)"
    return (
        "<think>\n"
        f"Intent & Topic: {intent} (conf={confidence:.2f}); entities=[{ent_summary}]; concepts=[{concept_summary}].\n"
        f"Nuance & Sentiment: {nuance}.\n"
        f"Mem0 Constraints: {mem_summary}.\n"
        f"Expert KB Rules: Ground strictly in verified facts [{fact_ids}]; honor Mem0 preferences without contradiction; "
        f"deliver warm storytelling prose with zero bullet dumps or clichés ({style_note}).\n"
        "</think>"
    )


def load_trajectory_queries(trajectories_path: Path, max_queries: int) -> List[Dict[str, Any]]:
    """Load unique logged queries from data/trajectories.jsonl, prioritizing user corrections."""
    if not trajectories_path.exists():
        return []
    records: List[Dict[str, Any]] = []
    for raw_line in trajectories_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        query = (rec.get("user_query") or "").strip()
        status = rec.get("response_status") or "answered"
        if not query or status in {"social", "off_topic"}:
            continue
        records.append(rec)

    # Prioritize turns where the user corrected the bot (feedback_score < 0), then most recent
    records.sort(
        key=lambda r: (
            0 if (r.get("feedback_score") is not None and float(r["feedback_score"]) < 0) else 1,
            -int(r.get("turn") or 0),
        )
    )

    seen_keys = set()
    selected: List[Dict[str, Any]] = []
    for rec in records:
        key = (rec.get("resolved_query") or rec.get("user_query") or "").strip().lower()
        if key in seen_keys:
            continue
        seen_keys.add(key)
        selected.append(
            {
                "source": "trajectory",
                "trajectory_id": rec.get("trajectory_id"),
                "system_prompt": rec.get("system_prompt") or DEFAULT_SYSTEM_PROMPT,
                "user_query": rec.get("user_query", ""),
                "resolved_query": rec.get("resolved_query") or rec.get("user_query", ""),
                "mem0_retrieved_context": list(rec.get("mem0_retrieved_context") or []),
                "fact_ids": list(rec.get("fact_ids") or []),
                "feedback_score": rec.get("feedback_score"),
            }
        )
        if len(selected) >= max_queries:
            break
    return selected


def build_kb_seed_queries(
    repository: KnowledgeRepository,
    semantic_network: SemanticNetwork,
    max_queries: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """Construct verified local seed queries from golden_questions.yaml and the semantic network."""
    seeds: List[Dict[str, Any]] = []
    golden_path = BASE_DIR / "tools" / "eval" / "golden_questions.yaml"
    if golden_path.exists():
        data = yaml.safe_load(golden_path.read_text(encoding="utf-8")) or {}
        cases: List[Dict[str, Any]] = []
        if isinstance(data, dict) and isinstance(data.get("categories"), dict):
            for cat_items in data["categories"].values():
                if isinstance(cat_items, list):
                    cases.extend(c for c in cat_items if isinstance(c, dict))
        elif isinstance(data, dict) and isinstance(data.get("cases"), list):
            cases = [c for c in data["cases"] if isinstance(c, dict)]
        elif isinstance(data, list):
            cases = [c for c in data if isinstance(c, dict)]
        for idx, case in enumerate(cases):
            status = case.get("expected_status", "answered")
            if status != "answered":
                continue
            q = (case.get("query") or "").strip()
            if not q:
                continue
            # Assign realistic Mem0 learner profiles to technique/rhythm/practice prompts
            low = q.lower()
            if any(w in low for w in ("play", "stroke", "stick", "yeolchae", "jungmori", "gutgeori", "hwimori", "beginner", "faster")):
                mem_profile = list(_MEM0_SEED_PROFILES[1 + (idx % 3)])
            else:
                mem_profile = list(_MEM0_SEED_PROFILES[idx % len(_MEM0_SEED_PROFILES)])
            seeds.append(
                {
                    "source": "kb_golden",
                    "trajectory_id": None,
                    "system_prompt": DEFAULT_SYSTEM_PROMPT,
                    "user_query": q,
                    "resolved_query": q,
                    "mem0_retrieved_context": mem_profile,
                    "fact_ids": list(case.get("expected_fact_ids") or []),
                    "feedback_score": None,
                }
            )

    # Add curated multi-hop relational queries grounded in the semantic network
    relational_prompts = [
        ("What wood makes up the body that creates the acoustic choke?", []),
        ("How is the Indian Idakka connected to the Korean janggu?", []),
        ("How do the leather tuning wedges affect pitch on the janggu heads?", ["User is curious about tuning and acoustics."]),
        ("How does the bamboo yeolchae differ from the gungchae mallet when playing fast rhythms?", ["User is practicing gutgeori rhythm and mentioned wrist tension when playing fast."]),
        ("How does King Sejong's Jeongganbo connect to janggu rhythmic cycles?", ["User is a beginner learning the janggu."]),
    ]
    for q, mem in relational_prompts:
        rel = semantic_network.answer_relational_query(q)
        seeds.insert(
            0,
            {
                "source": "semantic_network",
                "trajectory_id": None,
                "system_prompt": DEFAULT_SYSTEM_PROMPT,
                "user_query": q,
                "resolved_query": q,
                "mem0_retrieved_context": mem,
                "fact_ids": list(rel["fact_ids"]) if (rel and rel.get("fact_ids")) else [],
                "feedback_score": None,
            },
        )

    # Deduplicate and slice to max_queries while preserving relational + diverse coverage
    seen = set()
    unique: List[Dict[str, Any]] = []
    for item in seeds:
        k = item["user_query"].lower()
        if k not in seen:
            seen.add(k)
            unique.append(item)

    if len(unique) <= max_queries:
        return unique
    head = unique[:5]
    tail = unique[5:]
    rng.shuffle(tail)
    return head + tail[: max(0, max_queries - len(head))]


def generate_candidates_for_item(
    item: Dict[str, Any],
    *,
    num_candidates: int,
    temperature: float,
    nlp: NLPPreprocessor,
    classifier: IntentClassifier,
    engine: InferenceEngine,
    repository: KnowledgeRepository,
    semantic_network: SemanticNetwork,
    rng: random.Random,
    lora_runtime: Optional[LocalLoRARuntime] = None,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Sample N diverse local candidates with `<think>...</think>` traces at the target temperature."""
    user_query = item["user_query"]
    resolved_query = item.get("resolved_query") or user_query
    mem0_ctx = list(item.get("mem0_retrieved_context") or [])
    fb_score = item.get("feedback_score")

    cleaned = nlp.clean_text(resolved_query)
    corrected = nlp.correct_typos(cleaned)
    canonical, entities = nlp.map_synonyms(corrected)
    intent, confidence = classifier.predict(canonical)

    expected_facts = resolve_expected_facts_for_query(
        resolved_query,
        item.get("fact_ids"),
        repository,
        semantic_network=semantic_network,
    )
    concepts = semantic_network.extract_concepts_from_text(resolved_query)
    nuance = _detect_query_nuance(user_query, fb_score)

    # Pull deterministic rule-engine story and optional semantic-network multi-hop story
    session_tmp = SessionMemory("rft_gen")
    rule_eval = engine.evaluate(intent or "", entities, max(confidence, 0.75), session_tmp)
    rule_baseline = _clean_story_body(rule_eval.get("baseline_text") or "")
    rule_facts = list(rule_eval.get("facts") or [])
    if not expected_facts and rule_facts:
        expected_facts = rule_facts

    rel_res = semantic_network.answer_relational_query(resolved_query)
    rel_story = ""
    if rel_res and rel_res.get("found") and rel_res.get("fact_ids"):
        rel_story = _clean_story_body(semantic_network.render_path_story(rel_res, session=session_tmp))
        if not expected_facts:
            expected_facts = list(rel_res.get("facts") or [])

    strategies = [
        ("story_verified_facts", 1.3),
        ("rule_baseline_story", 1.15),
        ("relational_graph_story", 1.0 if rel_story else 0.2),
        ("focused_craft_narrative", 1.1),
        ("exploratory_high_temp", 0.55),
    ]

    candidates: List[str] = []
    for idx in range(num_candidates):
        # If an already-trained local LoRA adapter is provided, sample 1 candidate directly from it
        if lora_runtime is not None and idx == num_candidates - 1:
            think_gen, ans_gen = lora_runtime.generate_response(
                item.get("system_prompt") or DEFAULT_SYSTEM_PROMPT,
                mem0_ctx,
                user_query,
                max_new_tokens=110,
                temperature=temperature,
            )
            if think_gen and ans_gen:
                candidates.append(f"<think>\n{think_gen}\n</think>\n{ans_gen}")
                continue

        strat_names = [s[0] for s in strategies]
        strat_weights = [s[1] for s in strategies]
        chosen = strat_names[idx % len(strat_names)] if idx < 3 else _temperature_pick(rng, strat_names, strat_weights, temperature)

        lead = _temperature_pick(rng, _STORY_LEADS, [1.0] * len(_STORY_LEADS), temperature)
        closing_q = _temperature_pick(rng, _CLOSING_QUESTIONS, [1.0] * len(_CLOSING_QUESTIONS), temperature)

        if chosen == "rule_baseline_story" and rule_baseline and len(rule_baseline.split()) >= 14:
            body = rule_baseline
            mem_joined = " ".join(mem0_ctx).lower()
            if "wrist" in mem_joined and "wrist" not in body.lower():
                body = f"{body}\n\n{rng.choice(_WRIST_COACHING_NOTES)}"
            elif "beginner" in mem_joined and "jungmori" not in body.lower():
                body = f"{body}\n\n{rng.choice(_BEGINNER_COACHING_NOTES)}"
            think = _build_think_block(
                intent=intent or "general",
                confidence=confidence,
                entities=entities,
                nuance=nuance,
                mem0_context=mem0_ctx,
                expected_facts=expected_facts,
                concepts=concepts,
                style_note="rule-engine narrative synthesis",
            )
            candidates.append(f"{think}\n{body}")
        elif chosen == "relational_graph_story" and rel_story:
            body = rel_story
            mem_joined = " ".join(mem0_ctx).lower()
            if "wrist" in mem_joined:
                body = f"{body}\n\n{rng.choice(_WRIST_COACHING_NOTES)}"
            elif "beginner" in mem_joined:
                body = f"{body}\n\n{rng.choice(_BEGINNER_COACHING_NOTES)}"
            think = _build_think_block(
                intent=intent or "relational",
                confidence=confidence,
                entities=entities,
                nuance=nuance,
                mem0_context=mem0_ctx,
                expected_facts=expected_facts,
                concepts=concepts,
                style_note="semantic-network multi-hop traversal",
            )
            candidates.append(f"{think}\n{body}")
        elif chosen == "exploratory_high_temp" and temperature >= 0.75 and rng.random() < 0.45:
            # High-temperature stochastic slip (missing <think> or bullet list) so rejection sampling exercises real filtering
            if rng.random() < 0.5:
                body = _compose_fact_story(expected_facts, lead, closing_q, mem0_ctx, rng, include_coaching=False)
                candidates.append(body)
            else:
                bullet_body = "\n".join(f"- {f['statement']}" for f in expected_facts[:2]) or "- Verified janggu detail."
                candidates.append(f"<think>Quick note.</think>\n{bullet_body}")
        else:
            body = _compose_fact_story(
                expected_facts,
                lead=lead,
                closing_q=closing_q,
                mem0_context=mem0_ctx,
                rng=rng,
                include_coaching=True,
            )
            think = _build_think_block(
                intent=intent or "general",
                confidence=confidence,
                entities=entities,
                nuance=nuance,
                mem0_context=mem0_ctx,
                expected_facts=expected_facts,
                concepts=concepts,
                style_note=chosen.replace("_", " "),
            )
            candidates.append(f"{think}\n{body}")

    return candidates, expected_facts


def run_rft_generation(
    *,
    trajectories_path: Path,
    output_path: Path,
    num_candidates: int = 5,
    temperature: float = 0.8,
    min_score: float = 0.72,
    seed_from_kb: bool = False,
    max_queries: int = 40,
    max_per_query: int = 3,
    adapter_path: Optional[Path] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """Run local Rejection Sampling Fine-Tuning (RFT) data generation and deterministic verification."""
    rng = random.Random(seed)
    repository = KnowledgeRepository()
    semantic_network = SemanticNetwork(repository)
    nlp = NLPPreprocessor()
    classifier = IntentClassifier()
    engine = InferenceEngine(repository)

    lora_runtime: Optional[LocalLoRARuntime] = None
    if adapter_path and (Path(adapter_path) / "adapter_config.json").exists():
        lora_runtime = LocalLoRARuntime(Path(adapter_path))

    items = load_trajectory_queries(trajectories_path, max_queries=max_queries)
    if seed_from_kb or len(items) == 0:
        kb_seeds = build_kb_seed_queries(repository, semantic_network, max_queries=max_queries, rng=rng)
        seen = {(it.get("resolved_query") or it["user_query"]).strip().lower() for it in items}
        for s in kb_seeds:
            if len(items) >= max_queries:
                break
            k = s["user_query"].strip().lower()
            if k not in seen:
                seen.add(k)
                items.append(s)

    total_candidates = 0
    total_passed = 0
    total_discarded = 0
    verified_records: List[Dict[str, Any]] = []

    for item in items:
        candidates, expected_facts = generate_candidates_for_item(
            item,
            num_candidates=num_candidates,
            temperature=temperature,
            nlp=nlp,
            classifier=classifier,
            engine=engine,
            repository=repository,
            semantic_network=semantic_network,
            rng=rng,
            lora_runtime=lora_runtime,
        )
        scored_passing: List[Tuple[float, str, Dict[str, Any]]] = []
        seen_cands = set()
        for cand in candidates:
            total_candidates += 1
            verdict = verify_candidate(
                cand,
                user_query=item.get("resolved_query") or item["user_query"],
                mem0_context=item.get("mem0_retrieved_context") or [],
                expected_facts=expected_facts,
                semantic_network=semantic_network,
                min_total_score=min_score,
            )
            if verdict["passed"] and cand not in seen_cands:
                seen_cands.add(cand)
                total_passed += 1
                scored_passing.append((verdict["total_reward"], cand, verdict))
            else:
                total_discarded += 1

        scored_passing.sort(key=lambda tup: -tup[0])
        for total_r, cand, verdict in scored_passing[:max_per_query]:
            verified_records.append(
                {
                    "source": item["source"],
                    "trajectory_id": item.get("trajectory_id"),
                    "system_prompt": item.get("system_prompt") or DEFAULT_SYSTEM_PROMPT,
                    "mem0_retrieved_context": list(item.get("mem0_retrieved_context") or []),
                    "user_query": item["user_query"],
                    "resolved_query": item.get("resolved_query") or item["user_query"],
                    "expected_fact_ids": [f["id"] for f in expected_facts],
                    "completion": cand,
                    "total_reward": total_r,
                    "rewards": verdict["rewards"],
                    "temperature": float(temperature),
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for rec in verified_records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return {
        "queries_processed": len(items),
        "candidates_generated": total_candidates,
        "candidates_passed": total_passed,
        "candidates_discarded": total_discarded,
        "records_exported": len(verified_records),
        "output_path": str(output_path),
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    train_cfg = config.get("training", {})
    parser = argparse.ArgumentParser(
        description="Generate and deterministically verify local RFT (<think> + answer) training pairs."
    )
    parser.add_argument(
        "--trajectories",
        type=Path,
        default=BASE_DIR / train_cfg.get("trajectory_log", "data/trajectories.jsonl"),
        help="Input JSONL trajectory log (default: data/trajectories.jsonl).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BASE_DIR / train_cfg.get("rft_output", "data/rft_verified.jsonl"),
        help="Output verified RFT JSONL path (default: data/rft_verified.jsonl).",
    )
    parser.add_argument(
        "--num-candidates",
        type=int,
        default=5,
        help="Number of candidate responses sampled per query (default: 5).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.8,
        help="Sampling temperature for candidate generation (default: 0.8).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.72,
        help="Minimum aggregate verification score to keep a candidate (default: 0.72).",
    )
    parser.add_argument(
        "--seed-from-kb",
        action="store_true",
        help="Include verified KB/golden/semantic-network seed queries alongside trajectories.",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=40,
        help="Maximum number of queries to process (default: 40).",
    )
    parser.add_argument(
        "--max-per-query",
        type=int,
        default=3,
        help="Maximum verified candidates retained per query (default: 3).",
    )
    parser.add_argument(
        "--adapter-path",
        type=Path,
        default=None,
        help="Optional existing local LoRA adapter directory to sample an additional candidate from.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42).")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    stats = run_rft_generation(
        trajectories_path=args.trajectories,
        output_path=args.output,
        num_candidates=args.num_candidates,
        temperature=args.temperature,
        min_score=args.min_score,
        seed_from_kb=args.seed_from_kb,
        max_queries=args.max_queries,
        max_per_query=args.max_per_query,
        adapter_path=args.adapter_path,
        seed=args.seed,
    )
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
