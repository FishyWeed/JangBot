"""Variation and anti-repetition engine for Danbi's conversational responses."""

from collections import deque
import re
from threading import Lock
from typing import Any, Deque, Dict, List, Optional, Sequence, Tuple

_LOCK = Lock()
_GLOBAL_CURSOR: Dict[str, int] = {}
_GLOBAL_RECENT_REPLIES: Deque[str] = deque(maxlen=200)
_GLOBAL_RECENT_OPENERS: Deque[str] = deque(maxlen=200)

# Stock clichés Danbi (both rule-based and LLM-synthesized) must never output
BANNED_PHRASES: Tuple[str, ...] = (
    "bridged both worlds",
    "really fascinating cross-continental journey",
    "have a soft spot for",
    "yes, very much so!",
    "it certainly takes practice!",
    "crafted with remarkable care",
    "delightfully tactile",
    "universally regarded",
    "major milestones mark",
    "what is verified in my records",
    "documented sources establish",
)

GREETING_VARIANTS: Tuple[str, ...] = (
    "Hi, I'm Danbi. Pull up a seat—which story or tradition behind the Korean janggu would you like to hear today?",
    "Hi, I'm Danbi! Good to meet you—ask me about the drum's history, craft or rhythms and I'll tell you how it all unfolded.",
    "Hi, I'm Danbi. How is your day going, and what part of the janggu's story can we explore together?",
    "Hi, I'm Danbi! Whether it is palace ceremonies, village harvest beats or how woodcarvers tune the shell, I always love sharing the story behind the sound.",
    "Hi, I'm Danbi. Are you practicing the janggu yourself, or looking to trace Korean percussion across history?",
    "Hi, I'm Danbi! Ask away about the drum's origins, strokes, craftsmanship or jangdan cycles.",
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def extract_opener(text: str) -> str:
    """Return normalized opening sentence or line for duplicate-hook detection."""
    stripped = (text or "").strip()
    if not stripped:
        return ""
    first_line = stripped.splitlines()[0].strip()
    match = re.match(r"^(.+?[.!?])(?:\s|$)", first_line)
    opener = match.group(1) if match else first_line
    return _norm(opener)


def is_repetitive(candidate: str, prior_texts: Sequence[str]) -> bool:
    """Return True if candidate matches a prior reply verbatim or reuses its exact opening sentence."""
    cand_norm = _norm(candidate)
    cand_opener = extract_opener(candidate)
    if not cand_norm:
        return False
    for prior in prior_texts:
        if not prior:
            continue
        if _norm(prior) == cand_norm:
            return True
        if cand_opener and len(cand_opener) >= 12 and extract_opener(prior) == cand_opener:
            return True
    return False


def remember_reply(reply: str, session: Any = None) -> None:
    """Record an emitted reply in session and global anti-repetition buffers."""
    clean = (reply or "").strip()
    if not clean:
        return
    opener = extract_opener(clean)
    with _LOCK:
        _GLOBAL_RECENT_REPLIES.append(_norm(clean))
        if opener:
            _GLOBAL_RECENT_OPENERS.append(opener)
    if session is not None and hasattr(session, "recent_replies"):
        if not session.recent_replies or _norm(session.recent_replies[-1]) != _norm(clean):
            session.recent_replies.append(clean)
            if len(session.recent_replies) > 120:
                del session.recent_replies[:-120]


def pick_variation(
    key: str,
    variants: Sequence[str],
    session: Any = None,
    avoid_texts: Optional[Sequence[str]] = None,
    reframe_prefixes: Optional[Sequence[str]] = None,
) -> str:
    """Select an unused response variant for `key`, avoiding recent replies and openers."""
    if not variants:
        return ""

    prior_list: List[str] = list(avoid_texts or [])
    if session is not None and hasattr(session, "recent_replies"):
        prior_list.extend(session.recent_replies)

    with _LOCK:
        seen_full = {_norm(p) for p in prior_list if p} | set(_GLOBAL_RECENT_REPLIES)
        seen_openers = {extract_opener(p) for p in prior_list if p} | set(_GLOBAL_RECENT_OPENERS)

        if session is not None and hasattr(session, "used_variants") and key in session.used_variants:
            start_idx = (int(session.used_variants[key]) + 1) % len(variants)
        else:
            start_idx = _GLOBAL_CURSOR.get(key, 0) % len(variants)

        chosen_idx: Optional[int] = None
        for offset in range(len(variants)):
            idx = (start_idx + offset) % len(variants)
            cand = variants[idx]
            if _norm(cand) not in seen_full and extract_opener(cand) not in seen_openers:
                chosen_idx = idx
                break

        if chosen_idx is None:
            for offset in range(len(variants)):
                idx = (start_idx + offset) % len(variants)
                if _norm(variants[idx]) not in seen_full:
                    chosen_idx = idx
                    break

        if chosen_idx is None:
            chosen_idx = start_idx

        chosen = variants[chosen_idx]
        needs_reframe = (_norm(chosen) in seen_full) or (extract_opener(chosen) in seen_openers)
        if needs_reframe and reframe_prefixes:
            prefix_idx = _GLOBAL_CURSOR.get(f"{key}::reframe", 0) % len(reframe_prefixes)
            _GLOBAL_CURSOR[f"{key}::reframe"] = prefix_idx + 1
            chosen = f"{reframe_prefixes[prefix_idx]} {chosen[0].lower() + chosen[1:] if len(chosen) > 1 and chosen[:2] != 'I ' else chosen}"

        _GLOBAL_CURSOR[key] = (chosen_idx + 1) % max(len(variants), 1)
        if session is not None and hasattr(session, "used_variants"):
            session.used_variants[key] = chosen_idx

    remember_reply(chosen, session=session)
    return chosen


def compose_variation(
    key: str,
    bodies: Sequence[str],
    closers: Sequence[str],
    session: Any = None,
    avoid_texts: Optional[Sequence[str]] = None,
    separator: str = " ",
) -> str:
    """Combine varied body paragraphs and follow-up closers so repeated asks yield fresh text."""
    combos: List[str] = []
    n_b = len(bodies)
    n_c = max(len(closers), 1)
    # Interleave bodies and closers across coprime steps so adjacent picks differ in BOTH body and closer
    for step in range(n_b * n_c):
        b_idx = step % n_b
        c_idx = (step + (step // n_b)) % n_c
        body = bodies[b_idx].strip()
        closer = closers[c_idx].strip() if closers else ""
        combos.append(f"{body}{separator}{closer}".strip() if closer else body)

    fallback_bridges = (
        "Coming back to that point from another angle:",
        "Putting the same verified details a bit differently:",
        "Here is another way to frame that:",
        "Stepping back into that chapter for a closer look:",
        "Looking at the same tradition through a slightly different lens:",
        "To revisit that piece of the janggu's story:",
    )
    reframe = None if (key.startswith("gap::fallback") or key.startswith("guard::")) else fallback_bridges
    return pick_variation(
        key,
        combos,
        session=session,
        avoid_texts=avoid_texts,
        reframe_prefixes=reframe,
    )


def pick_greeting(bot_name: str = "Danbi", session: Any = None) -> str:
    """Return a non-repeating greeting introducing Danbi."""
    variants = [g.replace("Danbi", bot_name) for g in GREETING_VARIANTS]
    return pick_variation("bot::greeting", variants, session=session)
