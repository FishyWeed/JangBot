"""Text canonicalization, shorthand expansion, synonym mapping and entity extraction."""

import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import yaml
from rapidfuzz import process, fuzz
from src.settings import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LEXICON_PATH = BASE_DIR / config["paths"]["lexicon_dir"] / "synonyms.yaml"
SHORT_FORMS_PATH = BASE_DIR / config["paths"]["lexicon_dir"] / "short_forms.yaml"


class NLPPreprocessor:
    """Preprocess text, normalize shorthand aliases and extract entities."""

    def __init__(
        self,
        lexicon_path: Path = LEXICON_PATH,
        short_forms_path: Path = SHORT_FORMS_PATH,
    ):
        self.synonyms: Dict[str, List[str]] = {}
        self.reverse_synonyms: Dict[str, str] = {}
        self.short_forms: Dict[str, str] = {}
        self.vocabulary: Set[str] = set()
        self._load_lexicon(lexicon_path)
        self._load_short_forms(short_forms_path)

    def _load_lexicon(self, path: Path) -> None:
        """Load synonym mappings from YAML."""
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            self.synonyms = data.get("synonyms", {})
            for canonical, aliases in self.synonyms.items():
                self.vocabulary.add(canonical.lower())
                for alias in aliases:
                    alias_lower = alias.lower()
                    self.reverse_synonyms[alias_lower] = canonical
                    self.vocabulary.add(alias_lower)

    def _load_short_forms(self, path: Path) -> None:
        """Load shorthand mappings from YAML."""
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            self.short_forms = data.get("replacements", {})

    def expand_short_forms(self, text: str) -> str:
        """Expand abbreviations and casual short forms."""
        # Handle word contractions with apostrophes first
        contractions = {
            r"\bwhat's\b": "what is",
            r"\bhow's\b": "how is",
            r"\bwhere's\b": "where is",
            r"\bwhen's\b": "when is",
            r"\bit's\b": "it is",
            r"\bcan't\b": "cannot",
            r"\bdon't\b": "do not",
            r"\bdoesn't\b": "does not",
            r"\bdidn't\b": "did not",
            r"\bthere's\b": "there is",
            r"\bwho's\b": "who is",
        }
        lowered = text.lower()
        for pattern, replacement in contractions.items():
            lowered = re.sub(pattern, replacement, lowered)

        # Expand registered short forms
        for short, expanded in self.short_forms.items():
            pattern = rf"\b{re.escape(short)}\b"
            lowered = re.sub(pattern, expanded, lowered)

        return lowered

    def clean_text(self, text: str) -> str:
        """Expand short forms, lowercase text and normalize spacing."""
        text = self.expand_short_forms(text)
        text = re.sub(r"[^\w\s\uAC00-\uD7A3-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    SAFE_ENGLISH_WORDS: Set[str] = {
        "world", "could", "would", "should", "about", "where", "there", "their", "these", "those",
        "which", "first", "other", "after", "still", "using", "sound", "right", "light", "stage",
        "state", "court", "short", "small", "large", "heart", "black", "white", "water", "plant",
        "plants", "metal", "music", "dance", "drums", "shell", "shells", "stick", "sticks",
        "hands", "heads", "tones", "notes", "waves", "walls", "trees", "pores", "crack", "weigh",
        "price", "today", "tempo", "speed", "faster", "slower", "louder", "apply", "protect",
    }

    def correct_typos(self, text: str, threshold: int = 85) -> str:
        """Correct misspelled domain keywords using RapidFuzz without mutating standard English words."""
        words = text.split()
        corrected_words = []
        for word in words:
            if len(word) <= 3 or word in self.vocabulary or word in self.SAFE_ENGLISH_WORDS:
                corrected_words.append(word)
                continue
            match = process.extractOne(
                word,
                self.vocabulary,
                scorer=fuzz.ratio,
                score_cutoff=threshold,
            )
            if match:
                corrected_words.append(match[0])
            else:
                corrected_words.append(word)
        return " ".join(corrected_words)

    def map_synonyms(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Replace aliases with canonical terms and record extracted entities."""
        extracted_entities = {}
        sorted_aliases = sorted(
            self.reverse_synonyms.keys(),
            key=lambda k: len(k.split()),
            reverse=True,
        )

        canonical_text = f" {text} "
        for alias in sorted_aliases:
            canonical = self.reverse_synonyms[alias]
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, canonical_text):
                extracted_entities[canonical] = alias
                canonical_text = re.sub(pattern, canonical, canonical_text)

        return canonical_text.strip(), extracted_entities
