"""LangGraph node implementations for JangBot conversational agent."""

import re
from typing import Any, Dict, List, Optional, Tuple
from langchain_core.messages import AIMessage, HumanMessage
from src.settings import config
from src.nlp.preprocessor import NLPPreprocessor
from src.nlp.classifier import IntentClassifier
from src.dialogue.followup import FollowUpHandler
from src.dialogue.variations import (
    BANNED_PHRASES,
    compose_variation,
    is_repetitive,
    pick_greeting,
    pick_variation,
    remember_reply,
)
from src.memory.session import SessionMemory
from src.memory.long_term import LongTermMemoryManager
from src.agent.tools import JangguToolchain
from src.agent.llm import HybridLLMClient
from src.agent.state import JangBotState

# Canonical entity -> primary intent alignment
ENTITY_INTENT_MAP: Dict[str, str] = {
    "gungpyeon": "ask_construction",
    "chaepyeon": "ask_construction",
    "ullimtong": "ask_construction",
    "jorongmok": "ask_construction",
    "joimjul": "ask_construction",
    "joigae": "ask_construction",
    "yeolchae": "ask_playing_technique",
    "gungchae": "ask_playing_technique",
    "strokes": "ask_playing_technique",
    "deong": "ask_playing_technique",
    "gung": "ask_playing_technique",
    "tta": "ask_playing_technique",
    "gideok": "ask_playing_technique",
    "jjak": "ask_playing_technique",
    "kkol": "ask_playing_technique",
    "goryeosa": "ask_chronology",
    "akhak_gwebeom": "ask_chronology",
    "jeongganbo": "ask_chronology",
    "sajanggu": "ask_chronology",
    "choi_seung_hee": "ask_chronology",
    "unesco": "ask_chronology",
    "jangdan": "ask_cultural_significance",
    "jungmori": "ask_cultural_significance",
    "hwimori": "ask_cultural_significance",
    "gutgeori": "ask_cultural_significance",
    "jinyangjo": "ask_cultural_significance",
    "jajinmori": "ask_cultural_significance",
    "eonmori": "ask_cultural_significance",
    "chuimsae": "ask_cultural_significance",
    "nongak_pungmul": "ask_cultural_significance",
    "seoljanggu": "ask_cultural_significance",
    "pansori": "ask_cultural_significance",
    "yogo": "ask_origin",
    "archaeology": "ask_origin",
    "seyogo": "ask_etymology",
    "daechwita": "ask_military_role",
    "bokpan": "ask_playing_technique",
    "ijanggu": "ask_evolution",
    "synthetic": "ask_construction",
    "hornbostel": "ask_construction",
    "galgo": "ask_chronology",
    "wood_anatomy": "ask_construction",
    "surface_finish": "ask_construction",
    "acoustics_physics": "ask_acoustics",
    "ml_dsp": "ask_evolution",
    "conservation": "ask_evolution",
    "microtonal_tuning": "ask_cultural_significance",
    "hide_curing": "ask_construction",
    "ebnf_grammar": "ask_evolution",
}

DOMAIN_KEYWORDS = {
    "janggu", "janggo", "changgo", "drum", "drums", "drummer", "drummers", "drumming",
    "stick", "sticks", "mallet", "mallets", "whip", "yeolchae", "gungchae",
    "head", "heads", "skin", "skins", "hide", "hides", "leather", "membrane", "membranes",
    "shell", "shells", "body", "waist", "ullimtong", "jorongmok", "tube", "wood", "paulownia",
    "cord", "cords", "rope", "ropes", "joimjul", "wedge", "wedges", "joigae",
    "stroke", "strokes", "strike", "strikes", "hit", "hitting", "tap", "taps", "slap",
    "rhythm", "rhythms", "jangdan", "beat", "beats", "tempo", "speed", "faster", "slower", "cycle", "cycles",
    "music", "musical", "percussion", "court", "folk", "royal", "village", "festival", "festivals",
    "goryeo", "joseon", "silla", "sejong", "history", "chronology", "origin", "origins",
    "created", "create", "creation", "invent", "invented", "play", "played", "playing",
    "player", "players", "technique", "techniques", "method", "methods", "posture", "stance",
    "hand", "hands", "palm", "finger", "fingers", "left", "right", "differ", "differs", "difference",
    "wrist", "tension", "sore", "fatigue", "beginner", "intermediate", "advanced",
    "tune", "tuning", "tuned", "tight", "tighten", "pitch", "sound", "sounds", "tone", "timbre", "acoustic", "acoustics",
    "bessel", "frequency", "frequencies", "overtone", "overtones", "choke", "volume", "loud", "resonance",
    "source", "sources", "cite", "citation", "citations", "reference", "evidence", "book", "treatise",
    "korea", "korean", "instrument", "instruments", "difficult", "hard", "easy", "learn", "practice", "practicing",
    "deong", "gung", "tta", "gideok", "kkol", "jjak", "jungmori", "hwimori", "gutgeori",
    "jinyangjo", "jajinmori", "eonmori", "chuimsae", "nongak", "pungmul", "samulnori",
    "jeongak", "sanjo", "sinawi", "pansori", "jeokbyeokga", "minyo", "galgo", "yogo", "idakka", "bukpyeon", "gungpyeon", "chaepyeon",
    "war", "battle", "battles", "military", "army", "daechwita", "yonggo", "etymology", "seyogo", "janggo",
    "evolution", "evolved", "synthetic", "mylar", "frp", "ijanggu", "umulsai", "omr", "piezo",
    "bokpan", "byeonjuk", "seoljanggu", "sangmo", "goguryeo", "baekje", "eumseongseo", "murals", "diameter",
    "sajanggu", "celadon", "ceramic", "hornbostel", "211.242", "classifies", "classification",
    "national", "gugak", "jangagwon",
    "density", "shrinkage", "earlywood", "latewood", "tyloses", "g-fibers", "crystallinity", "dendrochronology",
    "nakdong", "ottchil", "urushi", "isinglass", "q-factor", "tap-tuning", "wolf",
    "sldv", "vibrometry", "helmholtz", "tmm", "inertance", "adsr", "omnidirectional", "hygroscopicity",
    "melcnn", "mert", "f0cnn", "rmvpe", "fdtd", "dwm", "faust", "cfl", "bela", "accelerometer",
    "xrf", "microtomography", "photogrammetry", "peg", "duksu", "bisaek", "gangjin", "conservation",
    "440hz", "ajaeng", "piri", "microtonal", "fulcrum", "lever", "sigimsae", "gak", "jeonggan",
    "tanning", "curing", "collagen", "viscoelasticity", "viscoelastic", "ebnf", "subjeonggan", "rubato",
    "wave", "equation", "masculinization", "aak", "1921", "1987", "shaved", "micron",
    "dog", "doghide", "dogskin", "horse", "horsehide", "cow", "cowhide", "deer", "deerskin",
    "bamboo", "scorch", "scorched", "scorching", "fire", "flame", "lacquer", "glue",
    "grid", "notation", "score", "kiln", "stage", "stages", "workshop", "revival",
    "palace", "palaces", "shaman", "shamanic", "shamanistic", "musok", "gut",
    "dance", "dances", "dancer", "dancing", "choreography", "choi", "seung-hee", "unesco",
    "fastest", "slowest", "oldest", "earliest", "physics", "modern", "museum", "museums",
    "metropolitan", "met", "roka", "jongmyo", "jeryeak", "heritage", "chronicle", "chronicles", "treatises",
    "favorite", "popular", "cool", "interesting", "nice", "awesome", "thanks", "both"
}

NON_JANGGU_INSTRUMENTS = {
    "taiko", "djembe", "guitar", "piano", "violin", "cello", "viola", "flute", "trumpet",
    "saxophone", "trombone", "clarinet", "ukulele", "banjo", "bongo", "conga", "tabla",
    "guzheng", "erhu", "koto", "shamisen", "sitar", "gayageum", "geomungo", "haegeum", "snare",
}

SPECIFIC_TERMS = (
    "jinyangjo", "jungmori", "jungjungmori", "jajinmori", "hwimori", "gutgeori", "eonmori",
    "gungpyeon", "bukpyeon", "chaepyeon", "yeolchae", "gungchae", "ullimtong", "jorongmok",
    "joimjul", "joigae", "jeongganbo", "akhak gwebeom", "goryeosa", "chuimsae", "nongak",
    "jeongak", "samulnori", "sajanggu", "idakka", "yogo", "galgo", "pansori",
)

# Tokens excluded when checking whether a query asks about an uncovered topic
FRAMING_AND_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by", "can", "could",
    "did", "do", "does", "doing", "done", "for", "from", "had", "has", "have", "having", "how",
    "i", "if", "in", "into", "is", "it", "its", "just", "know", "like", "made", "make", "may",
    "me", "might", "more", "most", "much", "my", "need", "no", "not", "now", "nowadays", "of", "on", "or",
    "our", "out", "people", "really", "say", "see", "should", "so", "some", "still", "tell", "than", "that",
    "the", "their", "them", "then", "there", "these", "they", "this", "those", "to", "too", "up",
    "us", "use", "used", "using", "very", "wanna", "want", "was", "way", "we", "were", "what",
    "when", "where", "which", "who", "whom", "whose", "why", "will", "with", "would", "you", "your",
    "about", "actually", "affect", "affected", "also", "any", "ask", "called", "changgo", "compare", "compared",
    "differ", "difference", "differences", "different", "drum", "drums", "explain", "give", "happen",
    "happened", "help", "historically", "information", "instrument", "instruments", "janggo", "janggu", "korean",
    "korea", "list", "mean", "meaning", "name", "named", "number", "often", "role", "show", "something", "stuff",
    "system", "term", "terms", "thing", "things", "word", "words",
    "ever", "ways", "awesome", "best", "cool", "easy", "favorite", "fun", "good", "great", "hard",
    "interesting", "nice", "please", "thank", "thanks", "play", "played", "playing", "practice",
    "practicing", "fast", "faster", "slow", "slower", "loud", "louder", "soft", "softer", "tempo", "speed",
    "standard", "typical", "real", "exist", "exists", "instead", "rather", "versus",
    "apply", "applies", "biomechanically", "protect", "keep", "kept", "keeps",
    "bring", "take", "taken", "hold", "behavior", "chronological", "chronology", "timeline",
    "hmm", "hm", "uh", "um", "oh", "ah", "well", "wait", "ok", "okay", "neat", "wow", "whoa",
    "seriously", "wild", "crazy", "huh", "yep", "yeah", "alright", "gotcha", "basically",
    "honestly", "anyway", "back", "chapter", "part", "section", "story", "workshop", "stages",
    "stage", "century", "revival", "kiln", "next", "else", "continue", "again", "relate",
    "relates", "related", "connect", "connects", "connected",
    "pretty", "curious", "even", "originally", "came", "come", "comes", "coming", "wondering",
    "wonder", "hear", "heard", "hearing", "talk", "talking", "chat", "danbi", "friend",
    "kind", "sort", "bit", "little", "lot", "lots", "super", "totally", "literally", "maybe",
    "probably", "guess", "suppose", "imagine", "remember", "today", "first", "second", "third",
    "last", "other", "another", "same", "whole", "entire", "quick", "brief", "deep", "closer",
    "detail", "details", "example", "examples", "specific", "general", "simply", "mainly",
    "always", "never", "sometimes", "already", "before", "after", "since", "during", "while",
    "through", "across", "around", "between", "inside", "outside", "without", "under", "over",
    "against", "toward", "towards", "regarding", "feel", "feels", "feeling", "look", "looks",
    "looking", "seem", "seems", "think", "thinking", "start", "started", "starting", "begin",
    "began", "going", "get", "getting", "got", "let", "lets", "walk", "zoom", "dive", "jump",
    "switch", "move", "step", "focus", "explore", "listen", "picture", "love", "mind", "sure",
    "actually", "definitely", "certainly", "apparently", "though", "although", "however",
    "anyways", "btw", "hey", "hi", "hello", "morning", "afternoon", "evening", "doing",
    "side", "one", "ones", "two", "three", "both", "either", "neither", "vs", "versus",
    "history", "historical", "significance", "significant", "important", "importance",
    "purpose", "function", "overview", "background", "context", "tradition", "traditional",
    "culture", "cultural", "style", "styles", "type", "types", "form", "forms",
    "feature", "features", "aspect", "aspects", "character", "characteristic",
    "characteristics", "concept", "idea", "reason", "reasons", "process", "method",
    "work", "works", "working", "big", "all", "every", "each", "many", "several", "few",
    "various", "main", "major", "core", "basic", "key", "top", "summary", "summarize",
    "recap", "fair", "enough", "check", "checking", "ancient", "old", "older", "early",
    "earlier", "past", "present", "future", "times", "modern", "beginner", "beginners",
    "gets", "sore", "tense", "tired", "hurts", "hurt", "ache", "stories", "yes",
}

# Context adjectives/eras that must not create false DB hits when probing whether a specific gap topic is in janggu.db
NON_GAP_ANCHORS = {
    "wooden", "wood", "paulownia", "ullimtong", "fiberglass", "frp", "synthetic", "standard",
    "exact", "typical", "average", "goryeo", "joseon", "silla", "court", "banquet", "banquets",
    "meter", "century", "musician", "musicians", "folk", "royal",
}

# Specific quantitative metrics, measurements, shops or commercial terms absent from janggu.db
UNVERIFIED_GAP_TERMS = {
    "kilogram", "kilograms", "gram", "grams", "pound", "pounds", "weigh", "weight",
    "percent", "percentage", "crack", "cracks", "decibel", "decibels", "spl",
    "currency", "market", "markets", "tax", "taxes", "insadong", "shop", "store",
    "price", "cost", "worth", "salary", "mirrored", "left-handed",
}

JANGDAN_NAMES = ("jinyangjo", "jungmori", "jungjungmori", "jajinmori", "hwimori", "gutgeori", "eonmori")

COMPOUND_HIDE_PREFIXES = {
    "dog": ("doghide", "dogskin"),
    "horse": ("horsehide", "horseskin"),
    "cow": ("cowhide", "cowskin"),
    "deer": ("deerskin", "deerhide"),
}

WEATHER_OR_IDIOM_HINTS = {"weather", "raining", "rain", "snow", "sunny", "temperature", "time", "today", "outside"}


class JangBotNodes:
    """Collection of graph nodes orchestrating memory, context rewriting, tools and synthesis."""

    def __init__(
        self,
        toolchain: JangguToolchain,
        memory_manager: LongTermMemoryManager,
        nlp: Optional[NLPPreprocessor] = None,
        classifier: Optional[IntentClassifier] = None,
        llm_client: Optional[HybridLLMClient] = None,
    ) -> None:
        self.toolchain = toolchain
        self.repository = toolchain.repository
        self.memory = memory_manager
        self.nlp = nlp or NLPPreprocessor()
        self.classifier = classifier or IntentClassifier()
        self.llm = llm_client or memory_manager.llm_client

    @staticmethod
    def _build_session_proxy(state: JangBotState) -> SessionMemory:
        """Rehydrate lightweight SessionMemory from checkpointed graph state."""
        session = SessionMemory(state.get("session_id", "default"))
        session.active_topic = state.get("active_topic")
        session.last_fact_ids = list(state.get("last_fact_ids") or [])
        session.pending_offer = state.get("pending_offer")
        session.user_mood = state.get("user_mood")
        session.conversation_turn = int(state.get("conversation_turn") or 0)
        session.used_variants = dict(state.get("used_variants") or {})
        prior_ai = [
            getattr(m, "content", "")
            for m in (state.get("messages") or [])
            if isinstance(m, AIMessage) and getattr(m, "content", "")
        ]
        stored_replies = list(state.get("recent_replies") or [])
        for text in prior_ai:
            if text not in stored_replies:
                stored_replies.append(text)
        session.recent_replies = stored_replies[-120:]
        return session

    @staticmethod
    def _detect_social(text: str) -> Optional[str]:
        cleaned = re.sub(r"[!?.,;:]+", " ", (text or "").lower()).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        greetings = {
            "hi", "hello", "hey", "yo", "good morning", "good afternoon", "good evening", "hiya",
            "hi danbi", "hello danbi", "hey danbi", "yo danbi", "hiya danbi",
            "hi there", "hello there", "hey there", "how are you", "how are you doing",
            "how s it going", "hows it going", "what s up", "whats up", "nice to meet you",
            "good to meet you", "good to see you",
        }
        if cleaned in greetings:
            return "greeting"

        words = cleaned.split()
        if len(words) > 6:
            return None

        # Never hijack a question, topic pivot or domain query as a pure social mood reply
        if "?" in (text or ""):
            return None
        non_mood_domain = DOMAIN_KEYWORDS - {"cool", "nice", "awesome", "interesting", "favorite", "thanks", "both"}
        question_or_pivot = {
            "what", "why", "how", "when", "where", "which", "who", "about", "back",
            "tell", "explain", "more", "next", "other", "first", "second", "third", "last",
        }
        word_set = set(words)
        if (word_set & non_mood_domain) or (word_set & question_or_pivot):
            return None

        mood_positive = ("good", "fine", "great", "well", "doing well", "not bad", "ok", "cool")
        if any(re.search(rf"\b{re.escape(m)}\b", cleaned) for m in mood_positive):
            return "mood_positive"

        mood_negative = ("tired", "exhausted", "stressed", "bad", "not good", "sad")
        if any(re.search(rf"\b{re.escape(m)}\b", cleaned) for m in mood_negative):
            return "mood_negative"

        return None

    @staticmethod
    def _extract_last_ai_question(state: JangBotState) -> str:
        """Extract the final question sentence from Danbi's most recent assistant message."""
        for m in reversed(list(state.get("messages") or [])):
            if isinstance(m, AIMessage):
                content = (getattr(m, "content", "") or "").strip()
                if not content:
                    continue
                questions = re.findall(r"[^.!?\n]*\?", content)
                if questions:
                    return questions[-1].strip()
                lines = [
                    ln.strip()
                    for ln in content.splitlines()
                    if ln.strip()
                    and not ln.strip().startswith(("Beginner tip:", "Starter note:", "Practice reminder", "If you are starting out"))
                ]
                return lines[-1] if lines else ""
        return ""

    @staticmethod
    def _extract_last_ai_topics(state: JangBotState) -> List[str]:
        """Extract ordered domain entities/milestones mentioned in Danbi's most recent assistant message."""
        for m in reversed(list(state.get("messages") or [])):
            if isinstance(m, AIMessage):
                low = (getattr(m, "content", "") or "").lower()
                if not low:
                    continue
                candidates = list(SPECIFIC_TERMS) + [
                    "king yejong", "king sejong", "choi seung-hee", "national gugak center",
                    "unesco", "paulownia", "cowhide", "horsehide", "doghide", "deerskin",
                ]
                found: List[Tuple[int, str]] = []
                for term in candidates:
                    pos = low.find(term)
                    if pos != -1:
                        found.append((pos, term))
                found.sort(key=lambda pair: pair[0])
                ordered: List[str] = []
                for _, term in found:
                    if term not in ordered:
                        ordered.append(term)
                return ordered
        return []

    @staticmethod
    def _extract_question_options(question: str) -> List[str]:
        """Parse comma/or/dash-delimited topic options offered in Danbi's last question."""
        if not question:
            return []
        q = question.strip().rstrip("?").strip()
        # Focus on text after em-dash, colon, or lead-in verbs like "between", "about", "like", "into", "on"
        for sep in ("—", "–", ":"):
            if sep in q:
                tail = q.split(sep)[-1].strip()
                if len(tail.split()) >= 2:
                    q = tail
                    break
        if " or " not in q.lower():
            return []
        # Strip trailing framing clauses like "sounds closest to what you want to hear next"
        q = re.sub(r"\s+(?:sounds|catches|next|first|best|more|today).*$", "", q, flags=re.IGNORECASE).strip()
        # Strip common question lead-ins when no dash/colon split happened
        q = re.sub(
            r"^(?:would you like to|want to|should we|curious|which|where|do you want to|"
            r"are you asking about|feel free to|we can look at|from here we could)\b.*?\b(?:between|about|into|on|at|explore|compare|cover|hear|linger|zoom in on)\s+",
            "",
            q,
            flags=re.IGNORECASE,
        ).strip()
        parts = [p.strip(" ,.-—–") for p in re.split(r",\s*|\s+or\s+", q, flags=re.IGNORECASE) if p.strip(" ,.-—–")]
        # Trim overlong prefix on the first option if a framing phrase stayed attached
        cleaned_opts: List[str] = []
        for idx, part in enumerate(parts):
            p = re.sub(r"^(?:whether|either|maybe|perhaps|like|such as|how|the)\s+", "", part, flags=re.IGNORECASE).strip()
            if idx == 0 and len(p.split()) > 6:
                p = " ".join(p.split()[-4:])
            if p:
                cleaned_opts.append(p)
        return cleaned_opts

    def _resolve_reply_to_last_question(self, raw_query: str, cleaned: str, state: JangBotState) -> Optional[str]:
        """Resolve ordinals, bare continuations, superlatives and short replies against Danbi's previous turn."""
        low = re.sub(r"[!?.,;:]+", " ", cleaned.lower()).strip()
        low = re.sub(r"\s+", " ", low)
        words = low.split()
        if not words:
            return None

        last_q = self._extract_last_ai_question(state)
        options = self._extract_question_options(last_q)
        prior_messages = [m for m in (state.get("messages") or [])[:-1] if getattr(m, "content", "")]
        has_history = bool(prior_messages or state.get("active_topic"))

        # 1. Ordinal selection against options in Danbi's own last question
        ordinal_map = {
            "1": 0, "first": 0, "first one": 0, "the first": 0, "the first one": 0, "option 1": 0, "number 1": 0,
            "2": 1, "second": 1, "second one": 1, "the second": 1, "the second one": 1, "option 2": 1, "number 2": 1,
            "middle": 1, "middle one": 1, "the middle one": 1,
            "3": 2, "third": 2, "third one": 2, "the third": 2, "the third one": 2, "option 3": 2, "number 3": 2,
            "last": -1, "last one": -1, "the last": -1, "the last one": -1,
        }
        if low in ordinal_map and has_history:
            idx = ordinal_map[low]
            if options:
                chosen = options[idx] if (-len(options) <= idx < len(options)) else options[-1]
                return f"tell me about {chosen} on the janggu"
            topics = self._extract_last_ai_topics(state)
            if topics:
                chosen = topics[idx] if (-len(topics) <= idx < len(topics)) else topics[-1]
                return f"tell me about {chosen} on the janggu"
            anchor = self._find_recent_anchor(state) or "the janggu"
            return f"tell me more about {anchor} on the janggu"

        # 2. Superlative / shorthand topic references inside an active conversation
        if has_history and len(words) <= 7:
            if any(p in low for p in ("fastest", "fast one", "quickest")):
                return "tell me about hwimori fast jangdan rhythm on the janggu"
            if any(p in low for p in ("slowest", "slow one", "calmest")):
                return "tell me about jinyangjo slow jangdan rhythm on the janggu"
            if any(p in low for p in ("oldest", "earliest", "very first")):
                return "tell me about the oldest historical origin yogo and goryeosa records of the janggu"
            if any(p in low for p in ("left one", "bass one", "thick one", "heavier side", "thick side")):
                return "tell me about gungpyeon left bass head of the janggu"
            if any(p in low for p in ("right one", "treble one", "thin one", "thin side")):
                return "tell me about chaepyeon right treble head of the janggu"
            if any(p in low for p in ("other side", "other head", "opposite side", "opposite head")):
                prior_entities = state.get("last_entities") or {}
                if "gungpyeon" in prior_entities and "chaepyeon" not in prior_entities:
                    return "tell me about chaepyeon right head of the janggu"
                if "chaepyeon" in prior_entities and "gungpyeon" not in prior_entities:
                    return "tell me about gungpyeon left head of the janggu"
                return "compare gungpyeon and chaepyeon drumheads on the janggu"

        # 3. Bare affirmation / continuation when pending_offer was None
        bare_continue = {
            "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "please", "yes please",
            "sure thing", "sounds good", "go on", "go ahead", "continue", "keep going",
            "tell me", "tell me more", "more", "both", "either", "why", "how", "and",
            "really", "wait why", "wait really", "what else", "tell me about that",
            "more about that", "elaborate", "explain", "explain more",
        }
        if has_history and low in bare_continue:
            if options:
                return f"tell me about {options[0]} on the janggu"
            if last_q and not any(p in last_q.lower() for p in ("clarify which aspect", "be a bit more specific", "narrow that down")):
                q_clean = re.sub(
                    r"^(?:want to|would you like to|should we|curious|ready to|do you want to|where|which)\b[^a-z]*",
                    "",
                    last_q.rstrip("?").strip(),
                    flags=re.IGNORECASE,
                ).strip()
                if q_clean and len(q_clean.split()) >= 2:
                    return f"tell me about {q_clean} on the janggu"
            anchor = self._find_recent_anchor(state) or "the janggu"
            if low in {"why", "wait why"}:
                return f"why is {anchor} designed or used that way on the janggu"
            if low == "how":
                return f"how does {anchor} work on the janggu"
            return f"tell me more about {anchor} on the janggu"

        # 4. Mid-conversation short continuation fragments ("what about X?", "and X?", "how about X?", "back to X")
        weather_or_off = WEATHER_OR_IDIOM_HINTS | NON_JANGGU_INSTRUMENTS
        if has_history and len(words) <= 6 and not (set(words) & weather_or_off):
            m = re.match(r"^(?:(?:hmm|hm|uh|um|oh|ah|well|wait|ok|okay|cool|nice|neat|so)\s+)*(?:what about|how about|and what about|and|back to|more on|more about)\s+(.+)$", low)
            if m:
                frag = m.group(1).strip()
                if frag and "janggu" not in frag and "drum" not in frag:
                    return f"tell me about {frag} for the janggu"

        return None

    def _find_recent_anchor(self, state: JangBotState) -> Optional[str]:
        """Locate the most recent user-referenced component/rhythm or fall back to the janggu."""
        messages = list(state.get("messages") or [])
        prior = messages[:-1] if len(messages) > 1 else []
        user_prior = [m for m in prior[-6:] if isinstance(m, HumanMessage)]

        # Prioritize specific sub-topics (e.g., gutgeori, gungpyeon, jorongmok) explicitly raised by the user
        for msg in reversed(user_prior):
            low = (getattr(msg, "content", "") or "").lower()
            for term in SPECIFIC_TERMS:
                if term in {"idakka", "yogo"}:
                    continue
                if re.search(rf"\b{re.escape(term)}\b", low):
                    return term

        internal_bucket_keys = {
            "janggu", "yogo", "archaeology", "wood_anatomy", "surface_finish",
            "acoustics_physics", "ml_dsp", "conservation", "microtonal_tuning",
            "hide_curing", "ebnf_grammar", "nongak_pungmul", "synthetic", "hornbostel",
        }
        last_entities = state.get("last_entities") or {}
        for key in last_entities:
            if key not in internal_bucket_keys:
                return key

        # If prior context already established janggu (or generic history), resolve pronoun to "the janggu"
        if prior or state.get("active_topic"):
            return "the janggu"
        return None

    # ------------------------------------------------------------ Node 1: Retrieve Memory

    def retrieve_memory(self, state: JangBotState) -> Dict[str, Any]:
        """Search Mem0 / local long-term store for user-specific context."""
        user_id = state.get("user_id") or "default_user"
        raw_query = state.get("raw_query", "")
        memories = self.memory.search(raw_query, user_id=user_id)
        turn_count = int(state.get("conversation_turn") or 0) + 1
        return {
            "user_memories": memories,
            "conversation_turn": turn_count,
            "retrieved_facts": [],
            "citations": [],
            "baseline_reply": "",
        }

    # ------------------------------------------------------------ Node 2: Rewrite Context

    def rewrite_context(self, state: JangBotState) -> Dict[str, Any]:
        """Clean shorthand and resolve pronouns/ellipsis against recent history and memories."""
        raw_query = state.get("raw_query", "")
        cleaned = self.nlp.clean_text(raw_query)

        session_proxy = self._build_session_proxy(state)
        is_meta_citation = any(
            p in cleaned for p in ("how do you know", "source", "sources", "cite", "citation", "where did you", "prove")
        )
        if FollowUpHandler.can_handle(raw_query, session_proxy) or self._detect_social(raw_query) or is_meta_citation:
            return {"cleaned_query": cleaned, "resolved_query": cleaned}

        resolved = cleaned
        low = cleaned.lower()

        # Dynamic resolution of ordinals, bare continuations, superlatives and short fragments against Danbi's last question
        last_q_resolved = self._resolve_reply_to_last_question(raw_query, cleaned, state)
        if last_q_resolved:
            return {"cleaned_query": cleaned, "resolved_query": last_q_resolved}

        # Complementary side resolution (e.g., "the other side" after gungpyeon -> chaepyeon)
        prior_entities = state.get("last_entities") or {}
        if any(p in low for p in ["other side", "other head", "opposite side", "opposite head"]):
            if "gungpyeon" in prior_entities:
                resolved = re.sub(r"\b(?:the )?(?:other|opposite) (?:side|head)\b", "chaepyeon", low)
            elif "chaepyeon" in prior_entities:
                resolved = re.sub(r"\b(?:the )?(?:other|opposite) (?:side|head)\b", "gungpyeon", low)

        # Pronoun / deictic resolution against recent entity anchor or implicit janggu subject
        has_pronoun = bool(re.search(r"\b(it|its|that|this|they|them|those)\b", resolved))
        self_contained_beginner = bool(
            set(resolved.split()) & {"beginner", "beginners", "difficulty", "difficult", "learn", "learning"}
        )
        explicit_concepts = [
            c for c in self.toolchain.semantic_network.extract_concepts_from_text(resolved) if c != "janggu"
        ]
        is_elliptic_followup = (
            not self_contained_beginner
            and not explicit_concepts
            and len(resolved.split()) <= 6
            and any(
                w in resolved.split()
                for w in [
                    "faster", "slower", "louder", "softer", "technique", "practice", "why", "more",
                    "how", "when", "where", "heavier", "lighter", "bigger", "smaller", "compare", "difference",
                ]
            )
        )
        asks_about_it_usage = (
            bool(re.search(r"\b(it|its)\b", resolved))
            and not (set(resolved.split()) & WEATHER_OR_IDIOM_HINTS)
            and any(p in resolved for p in ("used in", "used for", "made of", "made from", "invented", "created", "play", "tune", "weigh", "cost", "sound", "called", "name"))
        )

        if has_pronoun or is_elliptic_followup:
            anchor = self._find_recent_anchor(state)
            if not anchor and asks_about_it_usage:
                anchor = "the janggu"
            if anchor:
                if has_pronoun:
                    rewritten = re.sub(r"\b(that|this|they|them|those)\b", anchor, resolved)
                    rewritten = re.sub(r"\bits\b", f"{anchor}'s", rewritten)
                    rewritten = re.sub(r"\bit\b", anchor, rewritten)
                    resolved = rewritten
                elif anchor not in resolved:
                    resolved = f"{resolved} {anchor}"

        # Optional LLM coreference polish when credentials are configured (skip if query already names an explicit entity without pronouns)
        _, direct_entities = self.nlp.map_synonyms(self.nlp.correct_typos(resolved))
        raw_tokens_check = set(re.findall(r"[a-zA-Z0-9\uAC00-\uD7A3-]+", cleaned.lower()))
        is_explicit_off = bool(raw_tokens_check & (NON_JANGGU_INSTRUMENTS | WEATHER_OR_IDIOM_HINTS)) and not bool(
            raw_tokens_check & {"janggu", "janggo", "changgo", "장구"}
        )
        is_short_conversational = (
            not is_explicit_off
            and not direct_entities
            and len(resolved.split()) <= 6
            and bool((state.get("messages") or [])[:-1])
        )
        if self.llm.is_available and (has_pronoun or (is_elliptic_followup and not direct_entities) or is_short_conversational):
            recent_lines = []
            for m in (state.get("messages") or [])[-5:-1]:
                role = "User" if isinstance(m, HumanMessage) else "Danbi"
                recent_lines.append(f"{role}: {m.content[:220]}")
            if recent_lines:
                llm_rewritten = self.llm.complete(
                    system_prompt=(
                        "Rewrite the latest user message into a standalone query by resolving pronouns, fragments or choices "
                        "referencing Danbi's previous question. Keep it concise. Never invent facts. "
                        "If the user is clearly changing to an unrelated off-topic subject (like weather, food, sports, coding or another non-janggu instrument), return it unchanged."
                    ),
                    user_prompt="History:\n" + "\n".join(recent_lines) + f"\n\nLatest query: {raw_query}",
                    max_tokens=80,
                    temperature=0.2,
                )
                if llm_rewritten and len(llm_rewritten.split()) <= 25:
                    resolved = self.nlp.clean_text(llm_rewritten)

        return {"cleaned_query": cleaned, "resolved_query": resolved}

    # ------------------------------------------------------------ Node 3: Classify & Guardrail

    def classify_and_guard(self, state: JangBotState) -> Dict[str, Any]:
        """Evaluate follow-ups, social turns, entities, intent confidence and strict domain scope."""
        raw_query = state.get("raw_query", "")
        cleaned = state.get("cleaned_query") or self.nlp.clean_text(raw_query)
        resolved = state.get("resolved_query") or cleaned
        session_proxy = self._build_session_proxy(state)

        # 1. Pending offer follow-up handler
        if FollowUpHandler.can_handle(raw_query, session_proxy):
            reply, fact_ids = FollowUpHandler.resolve(raw_query, session_proxy)
            all_by_id = {f["id"]: f for f in self.repository.get_verified_facts()}
            for df in self.repository.get_disputed_facts():
                all_by_id.setdefault(df["id"], df)
            retrieved = [all_by_id[fid] for fid in fact_ids if fid in all_by_id]
            citations: List[Dict[str, Any]] = []
            for fid in fact_ids:
                for c in self.repository.get_citations_for_fact(fid):
                    rec = dict(c)
                    rec["fact_id"] = fid
                    citations.append(rec)
            return {
                "intent": "followup_resolved",
                "confidence": 1.0,
                "entities": state.get("last_entities") or {},
                "guardrail_status": "followup",
                "response_status": "answered",
                "retrieved_facts": retrieved,
                "citations": citations,
                "baseline_reply": reply,
                "last_fact_ids": fact_ids,
                "pending_offer": session_proxy.pending_offer,
                "active_topic": state.get("active_topic") or "general",
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        # 2. Social greeting and mood
        social_type = self._detect_social(raw_query)
        if social_type == "greeting":
            greeting_reply = pick_greeting(config["bot"]["name"], session=session_proxy)
            return {
                "intent": "social_greeting",
                "confidence": 1.0,
                "guardrail_status": "social",
                "response_status": "social",
                "pending_offer": None,
                "baseline_reply": greeting_reply,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }
        if social_type == "mood_positive":
            mood_reply = pick_variation(
                "social::mood_positive",
                (
                    "I am glad to hear that! What would you like to know about the janggu?",
                    "Glad to hear that—are you curious about janggu rhythms, craftsmanship or history today?",
                    "So glad to hear that! Feel free to ask about the drum's techniques, origins or acoustics.",
                    "I'm really glad to hear that. Where would you like to start exploring Korean percussion?",
                ),
                session=session_proxy,
            )
            return {
                "intent": "social_mood",
                "confidence": 1.0,
                "guardrail_status": "social",
                "response_status": "social",
                "user_mood": "positive",
                "pending_offer": None,
                "baseline_reply": mood_reply,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }
        if social_type == "mood_negative":
            mood_reply = pick_variation(
                "social::mood_negative",
                (
                    "I understand. I hope exploring Korean percussion brings a welcome lift today—what can I share about the janggu?",
                    "Sorry things feel heavy right now. If music sounds like a good break, we can dive into any side of the janggu you want.",
                    "I hear you—take things easy, and whenever you're up for it, ask anything about Korean janggu rhythms or history.",
                    "Thanks for sharing that honestly. Whenever you feel ready, I'd be glad to explore some soothing or energetic janggu rhythms with you.",
                ),
                session=session_proxy,
            )
            return {
                "intent": "social_mood",
                "confidence": 1.0,
                "guardrail_status": "social",
                "response_status": "social",
                "user_mood": "negative",
                "pending_offer": None,
                "baseline_reply": mood_reply,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        def _off_topic_payload() -> Dict[str, Any]:
            if "guard::off_topic" not in session_proxy.used_variants:
                msg = config["bot"]["off_topic_message"]
                session_proxy.used_variants["guard::off_topic"] = 0
                remember_reply(msg, session_proxy)
            else:
                msg = pick_variation(
                    "guard::off_topic",
                    (
                        "I focus solely on the Korean janggu, so I can't answer questions outside that instrument and its traditions.",
                        "My scope is restricted solely to the Korean janggu—feel free to ask about its history, rhythms, acoustics or construction instead.",
                        "I am dedicated solely to the Korean janggu and cannot assist with other topics.",
                        "Since I cover solely the Korean janggu, try steering us back toward Korean drumming, technique or organology.",
                    ),
                    session=session_proxy,
                )
            return {
                "intent": "off_topic",
                "confidence": 1.0,
                "entities": {},
                "pending_offer": None,
                "guardrail_status": "off_topic",
                "response_status": "off_topic",
                "baseline_reply": msg,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        # Reject non-janggu instruments or explicit weather queries unless discussing the janggu
        raw_tokens = set(re.findall(r"[a-zA-Z0-9\uAC00-\uD7A3-]+", cleaned.lower()))
        weather_only = {"weather", "raining", "rain", "snow", "sunny", "forecast"}
        if ((raw_tokens & NON_JANGGU_INSTRUMENTS) or (raw_tokens & weather_only)) and not (
            raw_tokens & {"janggu", "janggo", "changgo", "장구"}
        ):
            return _off_topic_payload()

        # 3. Typo correction, synonym mapping, intent prediction
        corrected = self.nlp.correct_typos(resolved)
        canonical, entities = self.nlp.map_synonyms(corrected)
        corr_low = corrected.lower()
        for j_name in JANGDAN_NAMES:
            if re.search(rf"\b{j_name}\b", corr_low):
                entities[j_name] = j_name
        if "choi seung" in corr_low or "seung-hee" in corr_low:
            entities["choi_seung_hee"] = "choi_seung_hee"
        if "national gugak center" in corr_low or "jangagwon" in corr_low:
            entities["ngc_jangagwon"] = "ngc_jangagwon"
        if "met museum" in corr_low or "the met" in corr_low or "metropolitan museum" in corr_low:
            entities["met_museum"] = "met_museum"
        if "unesco" in corr_low:
            entities["unesco"] = "unesco"
        if "galgo" in corr_low:
            entities["galgo"] = "galgo"
        if "jongmyo" in corr_low or "jeryeak" in corr_low:
            entities["jongmyo"] = "jongmyo"
        intent, confidence = self.classifier.predict(canonical)

        conf_threshold = config["nlp"]["confidence_threshold"]
        clarification_threshold = config["nlp"]["clarification_threshold"]

        # Context overrides for pitch-tightening, court-vs-folk technique, acoustics, conservation and sajanggu/NGC chronology
        canon_tokens = set(canonical.split())
        override_applied = True
        if ("gungpyeon" in entities or "chaepyeon" in entities) and (canon_tokens & {"tighten", "tight", "pitch", "tune", "tuned", "tuning"}):
            entities["joimjul"] = "joimjul"
            intent = "ask_construction"
            confidence = max(confidence, 0.85)
        elif "sajanggu" in entities and any(w in canonical for w in ("replace", "fragile", "heavy", "why", "ceramic")):
            intent = "ask_evolution"
            confidence = max(confidence, 0.85)
        elif "nongak_pungmul" in entities and (canon_tokens & {"left", "hand", "palm", "stick", "sticks", "play", "playing", "technique", "jeongak"}):
            if not (canon_tokens & {"controversy", "debate", "term", "minjung", "calling", "name"}):
                entities.pop("nongak_pungmul", None)
                intent = "ask_playing_technique"
                confidence = max(confidence, 0.85)
        elif "national gugak center" in canonical or "jangagwon" in canonical or "galgo" in canon_tokens or "met_museum" in entities or "choi_seung_hee" in entities:
            intent = "ask_chronology"
            confidence = max(confidence, 0.85)
        elif "bokpan" in entities and not (canon_tokens & {"sldv", "helmholtz", "tmm", "adsr", "vibrometry"}):
            intent = "ask_playing_technique"
            confidence = max(confidence, 0.85)
        elif "acoustics_physics" in entities or (canon_tokens & {"overtone", "overtones", "inharmonic", "bessel", "frequency", "frequencies", "acoustics", "acoustic"}):
            intent = "ask_acoustics"
            confidence = max(confidence, 0.85)
        elif "ml_dsp" in entities or "conservation" in entities:
            intent = "ask_evolution"
            confidence = max(confidence, 0.85)
        elif "wood_anatomy" in entities or "surface_finish" in entities or "hide_curing" in entities:
            intent = "ask_construction"
            confidence = max(confidence, 0.85)
        elif "ebnf_grammar" in entities and "ijanggu" not in entities:
            intent = "ask_evolution"
            confidence = max(confidence, 0.85)
        elif "microtonal_tuning" in entities:
            corrected_low = corrected.lower()
            if any(w in corrected_low for w in ("lever", "fulcrum", "biomechanic")):
                intent = "ask_playing_technique"
            else:
                intent = "ask_cultural_significance"
            confidence = max(confidence, 0.85)
        elif "pansori" in entities or "jongmyo" in entities or (canon_tokens & {"shaman", "shamanic", "shamanistic", "musok", "gut"}):
            intent = "ask_cultural_significance"
            confidence = max(confidence, 0.85)
        else:
            override_applied = False

        # Align intent using recognized entities and active context when no specific override applied
        strong_structural = {"joigae", "joimjul", "ullimtong", "jorongmok", "gungpyeon", "chaepyeon", "chuimsae", "sajanggu"}
        if not override_applied and entities and (
            confidence < conf_threshold or state.get("active_topic") or bool(set(entities) & strong_structural)
        ):
            for ent_key in entities:
                if ent_key in ENTITY_INTENT_MAP:
                    mapped = ENTITY_INTENT_MAP[ent_key]
                    active_topic = state.get("active_topic")
                    # Preserve construction vs technique distinction when entity clarifies a drill-down
                    if active_topic in {"ask_construction", "ask_playing_technique", "ask_chronology", "ask_cultural_significance"}:
                        if mapped == active_topic or (ent_key in {"gungpyeon", "chaepyeon"} and active_topic == "ask_construction"):
                            intent = active_topic
                        else:
                            intent = mapped
                    else:
                        intent = mapped
                    confidence = max(confidence, 0.85)
                    break

        # Re-check whether tempo/play question about a jangdan should route to playing/rhythm guidance
        if "jangdan" in entities and any(w in canon_tokens for w in ["faster", "tempo", "speed", "play", "practice", "walking"]):
            intent = "ask_cultural_significance"
            confidence = max(confidence, 0.85)
        has_explicit_jangdan_name = any(j in raw_query.lower() for j in JANGDAN_NAMES)
        if canon_tokens & {"beginner", "beginners", "difficulty", "difficult"} and intent != "ask_playing_technique" and not has_explicit_jangdan_name:
            intent = "ask_difficulty"
            confidence = max(confidence, 0.85)
        if ("popular" in canon_tokens or "popularity" in canon_tokens) and not (
            set(entities) & {"ijanggu", "synthetic", "ml_dsp", "conservation", "ebnf_grammar"}
        ):
            intent = "ask_modern_popularity"
            confidence = max(confidence, 0.85)
        if "favorite" in canon_tokens and not (
            set(entities) & {"ijanggu", "synthetic", "ml_dsp", "conservation", "ebnf_grammar"}
        ):
            intent = "ask_favorite"
            confidence = max(confidence, 0.85)

        tokens = set(canonical.split())
        has_domain_kw = bool(tokens & DOMAIN_KEYWORDS)
        semnet_concepts = self.toolchain.semantic_network.extract_concepts_from_text(resolved)
        has_semnet_concepts = bool([c for c in semnet_concepts if c != "janggu"])
        in_domain_intents = {
            "ask_origin", "ask_etymology", "ask_evolution", "ask_military_role",
            "ask_construction", "ask_playing_technique", "ask_rhythm",
            "ask_acoustics", "ask_notation", "ask_cultural_significance", "ask_chronology",
            "ask_source_explanation", "conversational_acknowledgment", "ask_difficulty",
            "ask_favorite", "ask_modern_popularity",
        }
        has_janggu_context = (
            bool(entities)
            or has_domain_kw
            or has_semnet_concepts
            or (intent in in_domain_intents and confidence >= 0.62)
        )
        if has_semnet_concepts and len([c for c in semnet_concepts if c != "janggu"]) >= 2 and intent != "off_topic":
            confidence = max(confidence, conf_threshold)

        # Accept clear appreciative reactions & concise domain-keyword fragments without bouncing to clarification
        ack_words = {"thanks", "thank", "neat", "cool", "awesome", "interesting", "wow", "whoa", "gotcha", "makes", "sense", "nice", "lovely", "fascinating"}
        if (
            (intent == "conversational_acknowledgment" or ("thanks" in tokens or "thank" in tokens))
            and "?" not in raw_query
            and not entities
            and len(cleaned.split()) <= 10
            and (tokens & ack_words)
        ):
            intent = "conversational_acknowledgment"
            confidence = max(confidence, conf_threshold)
        elif has_domain_kw and confidence >= clarification_threshold and len(tokens) <= 4:
            confidence = max(confidence, conf_threshold)

        # 4. Deterministic routing
        if intent == "off_topic" or not has_janggu_context:
            return _off_topic_payload()

        if confidence < clarification_threshold and not entities:
            fallback_msg = pick_variation(
                "guard::low_conf_fallback",
                (
                    config["bot"]["fallback_message"],
                    f"{config['bot']['fallback_message']} Could you try asking about a specific drum part, historical period or jangdan rhythm?",
                    f"{config['bot']['fallback_message']} Try naming an area like its Silk Road origins, Paulownia construction or playing strokes.",
                    f"{config['bot']['fallback_message']} My verified knowledge focuses on janggu organology, history, playing techniques and rhythms.",
                ),
                session=session_proxy,
            )
            return {
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "pending_offer": None,
                "guardrail_status": "fallback",
                "response_status": "fallback",
                "baseline_reply": fallback_msg,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        if clarification_threshold <= confidence < conf_threshold and not entities:
            clarify_msg = pick_variation(
                "guard::clarification",
                (
                    "Could you clarify which aspect of the janggu you mean—history, construction, acoustics or playing technique?",
                    "I want to give you an accurate verified answer—are you asking about the drum's origins, physical build, strokes or jangdan rhythms?",
                    "Could you be a bit more specific about what you'd like to learn regarding the janggu?",
                    "Which angle of the janggu are you aiming at: how it's made, how it's played, how it sounds or where it came from?",
                    "Help me narrow that down—are we talking about craftsmanship, technique, rhythms or historical records?",
                ),
                session=session_proxy,
            )
            return {
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "pending_offer": None,
                "guardrail_status": "clarification",
                "response_status": "clarification",
                "baseline_reply": clarify_msg,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "pending_offer": None,
            "guardrail_status": "in_domain",
            "response_status": "answered",
        }

    # ------------------------------------------------------------ Node 4: Execute Tools

    @staticmethod
    def _norm_stem(word: str) -> str:
        """Normalize regular English inflections while keeping distinct roots separate."""
        w = word.lower().strip("-")
        if len(w) <= 3:
            return w
        if w in {"musok", "gut"} or w.startswith("shaman"):
            return "shaman"
        if w.endswith("al") and len(w) > 6:
            w = w[:-2]
        if w.endswith("ies") and len(w) > 4:
            return w[:-3] + "y"
        w = re.sub(r"(ing|ed|s)$", "", w)
        if w.endswith("e") and len(w) > 3:
            w = w[:-1]
        return w

    def _term_in_word_set(self, tok: str, words: set) -> bool:
        """Check word-level equality or stem equivalence without substring false positives."""
        if tok in words or f"{tok}s" in words:
            return True
        if tok in COMPOUND_HIDE_PREFIXES and any(alias in words for alias in COMPOUND_HIDE_PREFIXES[tok]):
            return True
        norm_tok = self._norm_stem(tok)
        if any(self._norm_stem(w) == norm_tok for w in words):
            return True
        if len(tok) >= 4:
            stem = self.toolchain._stem(tok)
            if len(stem) >= 4 and any(self.toolchain._stem(w) == stem for w in words):
                return True
        return False

    def _assess_and_build_gap_response(
        self,
        resolved_query: str,
        intent: Optional[str],
        entities: Dict[str, str],
        eval_facts: List[Dict[str, Any]],
        baseline_text: str,
        session: Optional[SessionMemory] = None,
    ) -> Optional[Dict[str, Any]]:
        """Detect when the user asks a specific question not answered by the matched rule template."""
        if intent in {"ask_source_explanation", "conversational_acknowledgment", "ask_difficulty", "ask_favorite", "ask_modern_popularity"}:
            return None

        corrected = self.nlp.correct_typos(resolved_query)
        canonical_for_gap, _ = self.nlp.map_synonyms(corrected)
        raw_tokens = [
            t for t in re.findall(r"[a-zA-Z0-9\uAC00-\uD7A3μ°]+", canonical_for_gap.lower())
            if len(t) >= 3 or t.isdigit()
        ]
        topic_tokens = [t for t in raw_tokens if t not in FRAMING_AND_STOPWORDS]
        if not topic_tokens:
            return None

        intent_samples = " ".join(
            sent
            for lbl, sent in zip(self.classifier.intent_labels, self.classifier.training_sentences)
            if lbl == intent
        )
        entity_terms = " ".join(f"{k} {v}" for k, v in entities.items())
        evidence_text = f"{baseline_text} {' '.join(f['statement'] for f in eval_facts)} {intent_samples} {entity_terms}".lower()
        evidence_words = set(re.findall(r"[a-z0-9\uAC00-\uD7A3μ°]+", evidence_text))

        uncovered = []
        for tok in topic_tokens:
            if not self._term_in_word_set(tok, evidence_words):
                if tok not in uncovered:
                    uncovered.append(tok)

        if not uncovered:
            return None

        # Keep the matched intent's answer when the majority of topic terms are already addressed by its evidence
        matched_count = len(topic_tokens) - len(uncovered)
        if matched_count > len(uncovered) and not any(t in UNVERIFIED_GAP_TERMS for t in uncovered):
            return None

        # Search only concrete non-generic uncovered terms in janggu.db and verify word-level match
        probe_terms = [t for t in uncovered if t not in NON_GAP_ANCHORS] or uncovered
        raw_matched = self.toolchain.search_facts_sync(" ".join(probe_terms), limit=3)
        matched_facts = []
        for f in raw_matched:
            f_words = set(re.findall(r"[a-z0-9\uAC00-\uD7A3μ°]+", f["statement"].lower()))
            if any(self._term_in_word_set(t, f_words) for t in probe_terms):
                matched_facts.append(f)

        matched_text = " ".join(f["statement"].lower() for f in matched_facts)
        matched_words = set(re.findall(r"[a-z0-9\uAC00-\uD7A3μ°]+", matched_text))
        probe_missing = [t for t in probe_terms if not self._term_in_word_set(t, matched_words)]
        matched_probe_count = len(probe_terms) - len(probe_missing)

        if (
            not matched_facts
            or matched_probe_count == 0
            or any(t in UNVERIFIED_GAP_TERMS for t in probe_missing)
            or (len(probe_missing) >= 4 and matched_probe_count <= 1)
        ):
            missing_str = ", ".join(uncovered[:3])
            gap_fallback = compose_variation(
                "gap::fallback",
                (
                    f"{config['bot']['fallback_message']} My verified database does not contain records on {missing_str} for the janggu.",
                    f"{config['bot']['fallback_message']} I checked my verified janggu sources and couldn't find figures covering {missing_str}.",
                    f"{config['bot']['fallback_message']} Available verified records do not address {missing_str} regarding the janggu.",
                ),
                (
                    "You can ask instead about its history, craftsmanship, acoustics, playing strokes or jangdan rhythms.",
                    "Feel free to explore verified details on its wood construction, acoustics, techniques or traditional time cycles.",
                    "I can happily walk you through documented facts on its Silk Road origins, design or rhythms instead.",
                ),
                session=session,
                separator=" ",
            )
            return {
                "facts": [],
                "citations": [],
                "fact_ids": [],
                "baseline_text": gap_fallback,
                "status": "fallback",
                "active_topic": None,
                "pending_offer": None,
            }

        still_missing = [t for t in uncovered if not self._term_in_word_set(t, matched_words)]

        # Append F06 role context only when partial hits relate to cultural/performance roles
        all_by_id = {f["id"]: f for f in self.repository.get_verified_facts()}
        relevant_facts = list(matched_facts)
        wants_f06 = any(f.get("category") == "cultural_use" for f in matched_facts)
        if wants_f06 and "F06" in all_by_id and all(f["id"] != "F06" for f in relevant_facts):
            relevant_facts.append(all_by_id["F06"])

        citations: List[Dict[str, Any]] = []
        for f in relevant_facts:
            for c in self.repository.get_citations_for_fact(f["id"]):
                rec = dict(c)
                rec["fact_id"] = f["id"]
                citations.append(rec)

        fact_summaries = " ".join(f["statement"] for f in matched_facts)
        documented_roles = all_by_id["F06"]["statement"] if wants_f06 and "F06" in all_by_id else ""
        extra_role_para = (
            f"\n\nIn the wider story of Korean music, {documented_roles[0].lower()}{documented_roles[1:]}"
            if documented_roles and "F06" not in {f["id"] for f in matched_facts}
            else ""
        )

        if still_missing:
            missing_list = ", ".join(still_missing[:3])
            lead = pick_variation(
                "gap::partial_lead",
                (
                    f"My verified sources don't actually tell a story about {missing_list} on the janggu—though here is what history does preserve. ",
                    f"While our records stay silent on {missing_list} directly, the documented story that surrounds it is worth hearing. ",
                    f"Nothing verified in my notes covers {missing_list} yet, so I won't guess—instead, here is what the sources actually show. ",
                ),
                session=session,
            )
        else:
            lead = pick_variation(
                "gap::verified_story_lead",
                (
                    "Looking at what historical and organological records tell us, ",
                    "Here is the story those verified accounts preserve: ",
                    "Tracing that detail through the verified archives, ",
                ),
                session=session,
            )

        cat = matched_facts[0].get("category") or "general"
        offer_by_cat = {
            "construction": {"type": "tuning_or_acoustics"},
            "acoustics": {"type": "tuning_or_acoustics"},
            "technique": {"type": "sticks_or_strokes"},
            "rhythm": {"type": "slow_or_fast_rhythms"},
            "cultural_use": {"type": "court_or_folk"},
            "history": {"type": "silla_evolution"},
            "origin": {"type": "court_or_folk"},
        }
        closing_by_cat = {
            "construction": (
                "Want to look at how the cords and leather wedges tune the drumheads, or dive into the acoustic choke inside the waist?",
                "Should we move from the physical craft into mechanical tuning wedges or cavity acoustics next?",
            ),
            "acoustics": (
                "Want to see how the tuning wedges shift those frequencies, or inspect how the wood shell is built?",
                "Curious how sliding joigae wedges tighten those hides, or how the jorongmok waist filters the sound?",
            ),
            "technique": (
                "Want to compare the bamboo yeolchae and mallet sticks, or hear how the five named strokes work?",
                "Should we break down the two sticks next, or walk through the five signature strokes?",
            ),
            "rhythm": (
                "Want to feel the contrast between slow 24-beat Jinyangjo and blazing 4-beat Hwimori?",
                "Should we slow down into tragic Jinyangjo or sprint into festival Hwimori next?",
            ),
        }
        closing_pool = closing_by_cat.get(
            cat,
            (
                "Want to pull on another thread from that story—maybe royal court ceremonies versus village folk festivals?",
                "Should we follow how that connects to court Jeongak or lively folk drumming next?",
                "Curious to trace royal court traditions versus countryside festivals from here?",
                "Where should we wander next in the story of the janggu?",
            ),
        )
        closing_q = pick_variation(f"gap::closing::{cat}", closing_pool, session=session)
        body_text = fact_summaries
        if lead.endswith(", ") and len(body_text) > 1 and body_text[0].isupper():
            first_word = re.match(r"([A-Za-z]+)", body_text)
            keep_cap = {
                "Jeongganbo", "King", "Goryeo", "Goryeosa", "Joseon", "Silla", "Korean",
                "Korea", "Paulownia", "UNESCO", "KAIST", "SLDV", "MelCNN", "MERT", "FDTD",
                "DWM", "FAUST", "CFL", "EBNF", "Bessel", "Helmholtz", "Transfer", "Akhak",
                "Seong", "Choi", "National", "Nongak", "Pungmul", "Pansori", "Jeongak",
                "Samulnori", "Seoljanggu", "Daechwita", "Hornbostel", "Synchrotron", "Jongmyo",
            }
            if first_word and first_word.group(1) not in keep_cap:
                body_text = body_text[0].lower() + body_text[1:]
        baseline = f"{lead}{body_text}{extra_role_para}\n\n{closing_q}"
        return {
            "facts": relevant_facts,
            "citations": citations,
            "fact_ids": [f["id"] for f in relevant_facts],
            "baseline_text": baseline,
            "status": "answered",
            "active_topic": cat,
            "pending_offer": offer_by_cat.get(cat, {"type": "general_followup"}),
        }

    def execute_tools(self, state: JangBotState) -> Dict[str, Any]:
        """Run verified knowledge-base tools and rule inference."""
        intent = state.get("intent")
        entities = dict(state.get("entities") or {})
        confidence = float(state.get("confidence") or 0.0)
        resolved_query = state.get("resolved_query") or state.get("raw_query", "")
        session_proxy = self._build_session_proxy(state)

        if intent == "ask_source_explanation":
            fact_ids = session_proxy.last_fact_ids
            explained = self.toolchain.explain_sources_sync(fact_ids, session=session_proxy)
            return {
                "retrieved_facts": [],
                "citations": explained["citations"],
                "baseline_reply": explained["text"],
                "last_fact_ids": fact_ids,
                "response_status": "answered",
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        # Multi-hop verified semantic network traversal for explicit relational/chained queries
        query_tokens_low = set(re.findall(r"[a-z0-9-]+", resolved_query.lower()))
        if not (query_tokens_low & UNVERIFIED_GAP_TERMS):
            rel_res = self.toolchain.answer_relational_query_sync(resolved_query)
            if rel_res and rel_res.get("found") and rel_res.get("hop_count", 0) >= 2 and rel_res.get("fact_ids"):
                story = self.toolchain.semantic_network.render_path_story(rel_res, session=session_proxy)
                return {
                    "retrieved_facts": rel_res["facts"],
                    "citations": rel_res["citations"],
                    "baseline_reply": story,
                    "response_status": "answered",
                    "active_topic": rel_res["target"].get("category") or "general",
                    "last_fact_ids": rel_res["fact_ids"],
                    "last_entities": entities or {rel_res["target"]["id"]: rel_res["target"]["id"]},
                    "pending_offer": None,
                    "used_variants": session_proxy.used_variants,
                    "recent_replies": session_proxy.recent_replies,
                }

        eval_result = self.toolchain.evaluate_rules_sync(intent or "", entities, confidence, session_proxy)
        facts = eval_result["facts"]
        citations = eval_result["citations"]
        baseline_text = eval_result["baseline_text"]

        # Check whether canned template leaves the user's actual core topic unaddressed
        gap_override = self._assess_and_build_gap_response(
            resolved_query=resolved_query,
            intent=intent,
            entities=entities,
            eval_facts=facts,
            baseline_text=baseline_text,
            session=session_proxy,
        )
        if gap_override is not None:
            return {
                "retrieved_facts": gap_override["facts"],
                "citations": gap_override["citations"],
                "baseline_reply": gap_override["baseline_text"],
                "response_status": gap_override["status"],
                "active_topic": gap_override["active_topic"],
                "last_fact_ids": gap_override["fact_ids"],
                "last_entities": entities or state.get("last_entities") or {},
                "pending_offer": gap_override["pending_offer"],
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        # Supplement with dynamic graph-neighbor follow-up when a concise reply has no closing invitation
        if (
            eval_result["status"] == "answered"
            and not session_proxy.pending_offer
            and baseline_text
            and not baseline_text.rstrip().endswith("?")
        ):
            active_concepts = self.toolchain.semantic_network.extract_concepts_from_text(resolved_query)
            if not active_concepts:
                active_concepts = [k for k in entities.keys() if self.toolchain.semantic_network.resolve_concept(k)]
            neighbors = self.toolchain.suggest_graph_followups_sync(active_concepts, limit=2)
            if len(neighbors) >= 2:
                baseline_text = f"{baseline_text}\n\nWant to follow a connected thread next—{neighbors[0]['label']} or {neighbors[1]['label']}?"
            elif len(neighbors) == 1:
                baseline_text = f"{baseline_text}\n\nCurious to explore {neighbors[0]['label']} next?"

        # Supplement with keyword search from janggu.db when useful
        extra_facts = self.toolchain.search_facts_sync(resolved_query, limit=3)
        seen_ids = {f["id"] for f in facts}
        for ef in extra_facts:
            if ef["id"] not in seen_ids:
                facts.append(ef)
                seen_ids.add(ef["id"])

        return {
            "retrieved_facts": facts,
            "citations": citations,
            "baseline_reply": baseline_text,
            "response_status": eval_result["status"],
            "active_topic": session_proxy.active_topic,
            "last_fact_ids": eval_result["fact_ids"] or session_proxy.last_fact_ids,
            "last_entities": entities or state.get("last_entities") or {},
            "pending_offer": session_proxy.pending_offer,
            "used_variants": session_proxy.used_variants,
            "recent_replies": session_proxy.recent_replies,
        }

    # ------------------------------------------------------------ Node 5: Synthesize Response

    def synthesize_response(self, state: JangBotState) -> Dict[str, Any]:
        """Synthesize natural, non-repeating response strictly grounded in verified facts."""
        guard = state.get("guardrail_status", "in_domain")
        baseline = state.get("baseline_reply", "")
        memories = state.get("user_memories") or []
        session_proxy = self._build_session_proxy(state)

        # Strict deterministic bypass for guardrails, source citations and social turns
        if guard in {"off_topic", "fallback", "clarification"}:
            remember_reply(baseline, session_proxy)
            return {
                "reply": baseline,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        if guard == "social":
            social_out = self._personalize_social(baseline, memories, session_proxy)
            remember_reply(social_out, session_proxy)
            return {
                "reply": social_out,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        if state.get("intent") == "ask_source_explanation":
            remember_reply(baseline, session_proxy)
            return {
                "reply": baseline,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        # Handle tempo/speed follow-up on a specific jangdan cleanly
        resolved_low = (state.get("resolved_query") or "").lower()
        tempo_note = self._tempo_guidance_note(
            resolved_low,
            session=session_proxy,
            intent=state.get("intent"),
        )

        # Synthesize with LLM whenever configured and verified facts are attached (including follow-ups!)
        if self.llm.is_available and state.get("retrieved_facts"):
            llm_reply = self._llm_synthesize(state, tempo_note, session_proxy)
            if llm_reply:
                remember_reply(llm_reply, session_proxy)
                return {
                    "reply": llm_reply,
                    "used_variants": session_proxy.used_variants,
                    "recent_replies": session_proxy.recent_replies,
                }

        # Offline deterministic synthesis enriched with Mem0 user context and varied baseline prose
        if guard == "followup":
            remember_reply(baseline, session_proxy)
            return {
                "reply": baseline,
                "used_variants": session_proxy.used_variants,
                "recent_replies": session_proxy.recent_replies,
            }

        offline_reply = self._offline_synthesize(baseline, memories, tempo_note, state, session_proxy)
        remember_reply(offline_reply, session_proxy)
        return {
            "reply": offline_reply,
            "used_variants": session_proxy.used_variants,
            "recent_replies": session_proxy.recent_replies,
        }

    @staticmethod
    def _personalize_social(
        baseline: str,
        memories: List[Dict[str, Any]],
        session: Optional[SessionMemory] = None,
    ) -> str:
        """Lightly personalize social follow-ups with varied practice prompts."""
        if baseline.startswith("Hi, I'm"):
            return baseline
        for mem in memories:
            text = mem.get("memory", "")
            if "practicing" in text.lower():
                tail = pick_variation(
                    "social::practice_tail",
                    (
                        "Want to pick back up on your rhythm practice?",
                        "Ready for another round working on your rhythm timing?",
                        "Feel like continuing from the jangdan you've been practicing?",
                    ),
                    session=session,
                )
                return f"{baseline} {tail}"
        return baseline

    @staticmethod
    def _tempo_guidance_note(
        resolved_low: str,
        session: Optional[SessionMemory] = None,
        intent: Optional[str] = None,
    ) -> str:
        """Provide varied, grounded tempo progression advice when user asks to play faster."""
        if intent not in {"ask_playing_technique", "ask_cultural_significance", "ask_difficulty", None}:
            return ""
        if any(p in resolved_low for p in ("wave speed", "wave propagation", "rho_s", "equation", "formula")):
            return ""
        words = re.findall(r"[a-z]+", resolved_low)
        if not any(w in words for w in ("faster", "speed", "tempo")):
            return ""
        if "gutgeori" in resolved_low:
            return pick_variation(
                "synth::tempo_gutgeori",
                (
                    "To speed up Gutgeori without losing its 12-beat swing, anchor the Deong downbeat on beat 1, keep your right wrist relaxed on the flexible yeolchae, and push toward Jajinmori or Hwimori only once Gung and Tta transitions flow smoothly.",
                    "When accelerating Gutgeori, lock beat 1 with a steady Deong strike and let the springy bamboo yeolchae bounce naturally—avoiding stiff wrists—before stepping up toward Jajinmori or Hwimori speeds.",
                    "Building tempo in Gutgeori starts by stabilizing the 12-beat lilt around Deong on beat 1 and staying loose through the right yeolchae wrist; once Gung and Tta alternate cleanly, faster patterns like Jajinmori and Hwimori follow naturally.",
                ),
                session=session,
            )
        return pick_variation(
            "synth::tempo_general",
            (
                "To increase speed cleanly without tenseness, build your pulse inside a steady 12-beat Jungmori framework, ground each cycle on a relaxed Deong downbeat and let the bamboo yeolchae flex and rebound rather than forcing it.",
                "Rather than rushing early, tighten your timing in unhurried 12-beat Jungmori first—anchoring beat 1 cleanly with Deong and letting the springy yeolchae whip rebound smoothly.",
                "Clean tempo gains come from relaxing your grip on the bamboo yeolchae inside a steady Jungmori pulse and landing Deong evenly at the top of each cycle instead of muscling fast strokes.",
            ),
            session=session,
        )

    def _offline_synthesize(
        self,
        baseline: str,
        memories: List[Dict[str, Any]],
        tempo_note: str,
        state: JangBotState,
        session: Optional[SessionMemory] = None,
    ) -> str:
        """Merge baseline verified prose with learner-specific Mem0 context without repeating phrases."""
        parts: List[str] = []
        if tempo_note:
            parts.append(tempo_note)
            parts.append("")
        parts.append(baseline)

        mem_texts = [m.get("memory", "") for m in memories if m.get("memory")]
        intent = state.get("intent") or ""
        coaching_tips: List[str] = []

        if intent in {"ask_playing_technique", "ask_difficulty", "ask_cultural_significance"}:
            if any("wrist tension" in t.lower() or "soreness" in t.lower() for t in mem_texts):
                coaching_tips.append(
                    pick_variation(
                        "synth::coach_wrist",
                        (
                            "Practice reminder for your wrist tension: let the light bamboo yeolchae whip cleanly from finger snap rather than locked forearm muscle, and rest whenever stiffness starts.",
                            "Keeping your earlier note about wrist tension in mind, relax your shoulder and let the flexible yeolchae rebound smoothly instead of forcing fast strokes.",
                            "Since you mentioned wrist tension before, keep the right-hand grip feather-light on the yeolchae and shake out tension between practice cycles.",
                        ),
                        session=session,
                    )
                )
            elif any("beginner" in t.lower() for t in mem_texts) and "jungmori" not in baseline.lower():
                coaching_tips.append(
                    pick_variation(
                        "synth::coach_beginner",
                        (
                            "Beginner tip: working through unhurried 12-beat Jungmori cycles first gives both hands time to coordinate smoothly.",
                            "Starter note: sticking with a calm 12-beat Jungmori pulse early on keeps your left and right strokes evenly balanced.",
                            "If you are starting out, grounding your timing in steady 12-beat Jungmori makes later faster patterns much easier.",
                        ),
                        session=session,
                    )
                )

        if coaching_tips:
            parts.append("")
            parts.extend(coaching_tips)

        return "\n".join(parts).strip()

    def _llm_synthesize(
        self,
        state: JangBotState,
        tempo_note: str,
        session: Optional[SessionMemory] = None,
    ) -> Optional[str]:
        """Use the configured LLM for fresh, non-repeating prose strictly grounded in verified facts."""
        facts_block = "\n".join(
            f"- [{f['id']}] ({f['category']}): {f['statement']}" for f in (state.get("retrieved_facts") or [])
        )
        mem_block = "\n".join(
            f"- {m.get('memory')}" for m in (state.get("user_memories") or []) if m.get("memory")
        ) or "- None recorded yet."
        baseline = state.get("baseline_reply", "")

        all_recent = list(session.recent_replies if session is not None else [])
        recent_replies = all_recent[-12:]
        recent_block = (
            "\n".join(f"- {r.splitlines()[0][:140]}" for r in recent_replies)
            if recent_replies
            else "- None yet in this session."
        )
        banned_list = ", ".join(f'"{b}"' for b in BANNED_PHRASES)

        convo_lines = []
        for m in (state.get("messages") or [])[-5:-1]:
            role = "User" if isinstance(m, HumanMessage) else config["bot"]["name"]
            convo_lines.append(f"{role}: {(getattr(m, 'content', '') or '')[:220]}")
        convo_block = "\n".join(convo_lines) if convo_lines else "- Start of conversation."

        offer = state.get("pending_offer") or {}
        offer_hint = ""
        if offer.get("type"):
            offer_hint = (
                f"Active follow-up topic ({offer['type']}): end with a short, fresh closing question aligned with the offer "
                "implied in the Reference Draft so a brief reply like 'yes', 'the first one', 'the second one' or 'both' still makes natural sense."
            )

        style_angles = (
            "Tell this as a vivid, continuous story—set the historical or physical scene first and let each fact unfold naturally in narrative flow.",
            "Narrate from a performer's or craftsperson's perspective—what his hands feel, what listeners hear and how the moment carries forward.",
            "Weave the chronology or mechanics like a living tale handed down across royal halls, artisan workshops and village yards.",
            "Begin with a striking scene or contrast between two worlds, then trace the story seamlessly across 2 to 3 natural paragraphs.",
            "Respond directly to the user's curiosity with conversational warmth first, then unfold the verified facts like a campfire story.",
            "Zoom into one tactile detail—a wood grain, a leather knot, a stick rebound or a sudden beat—and widen outward into the full picture.",
            "Frame the answer as an unfolding journey from problem to craft solution, keeping the rhythm of prose brisk and engaging.",
            "Contrast how it looks to an onlooker versus how it feels to the musician or artisan inside the tradition.",
        )
        turn_idx = int(state.get("conversation_turn") or 0)
        chosen_style = style_angles[turn_idx % len(style_angles)]

        prefers_story = bool(config.get("bot", {}).get("persona", {}).get("prefers_storytelling", True))
        story_rule = (
            "2. PERSONALITY (Storyteller, he/him): Danbi loves explaining through engaging, vivid stories rather than dry encyclopedia bullet lists. "
            "NEVER dump bulleted timelines or dash-separated fact lists (e.g., '- 1076 AD: ... - 1114 AD: ...'). "
            "Always weave verified dates, craftsmen, instruments and scenes into smooth storytelling paragraphs and acknowledge the user's previous turn naturally.\n"
            if prefers_story
            else "2. Present verified claims clearly and naturally.\n"
        )

        system_prompt = (
            f"You are {config['bot']['name']} ({config.get('bot', {}).get('pronouns', 'he/him')}), a warm Korean janggu tutor and passionate traditional storyteller.\n"
            "STRICT RULES:\n"
            "1. Ground EVERY detail strictly in Verified Facts and Reference Draft below—never invent dates, dimensions, characters, Korean terms or citations.\n"
            f"{story_rule}"
            "3. NEVER repeat openings, transition sentences, structures or closing questions from Recent Replies below.\n"
            f"4. NEVER use any of these banned stock clichés: {banned_list}.\n"
            f"5. Story direction for THIS turn: {chosen_style}\n"
            "6. Keep your reply tight and complete (2 short paragraphs plus 1 crisp closing question, roughly 110–190 words total) so it never gets cut off mid-sentence.\n"
            "7. Only weave in Learner Memories (skill level, practicing jangdan, wrist tension) when directly relevant to playing or practice."
        )
        user_prompt = (
            f"Recent Conversation:\n{convo_block}\n\n"
            f"User query: {state.get('raw_query')}\n"
            f"Resolved query: {state.get('resolved_query')}\n"
            f"Learner Memories:\n{mem_block}\n\n"
            f"Verified Facts:\n{facts_block}\n\n"
            f"Tempo Note: {tempo_note or 'None'}\n"
            f"{offer_hint}\n"
            f"Recent Replies (DO NOT repeat these openings or phrasing):\n{recent_block}\n\n"
            f"Reference Draft (rephrase completely into fresh natural prose):\n{baseline}"
        )

        synth_temp = max(self.llm.temperature, 0.72)
        reply = self.llm.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=650,
            temperature=synth_temp,
        )
        if reply and is_repetitive(reply, all_recent):
            retry = self.llm.complete(
                system_prompt=system_prompt + "\nIMPORTANT: Your previous draft echoed an earlier opening; rewrite using a completely fresh first sentence and closing.",
                user_prompt=user_prompt,
                max_tokens=650,
                temperature=min(synth_temp + 0.15, 0.9),
            )
            if retry and not is_repetitive(retry, all_recent):
                return retry
        return reply

    # ------------------------------------------------------------ Node 6: Update Memory & Log

    def update_memory(self, state: JangBotState) -> Dict[str, Any]:
        """Persist new Mem0 user facts, record messages into checkpoint and log query."""
        raw_query = state.get("raw_query", "")
        reply = state.get("reply", "")
        intent = state.get("intent")
        confidence = float(state.get("confidence") or 0.0)
        response_status = state.get("response_status", "answered")
        user_id = state.get("user_id") or "default_user"

        if response_status in {"answered", "clarification", "fallback", "off_topic"}:
            self.repository.log_query(raw_query, intent, confidence, response_status)

        # Persist user facts across sessions via Mem0 / local fallback (skip pure off-topic noise unless it includes user intro)
        if raw_query:
            self.memory.add(
                [
                    {"role": "user", "content": raw_query},
                    {"role": "assistant", "content": reply},
                ],
                user_id=user_id,
                metadata={"session_id": state.get("session_id", "default"), "intent": intent or "unknown"},
            )

        return {
            "messages": [AIMessage(content=reply)],
            "used_variants": dict(state.get("used_variants") or {}),
            "recent_replies": list(state.get("recent_replies") or []),
        }
