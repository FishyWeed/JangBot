"""Intent classifier supporting dense semantic embeddings and TF-IDF."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.settings import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INTENTS_PATH = BASE_DIR / config["paths"]["rules_dir"] / "intents.yaml"

_SHARED_ENCODER = None
_SHARED_EMBEDDINGS: Dict[Tuple[str, int], object] = {}


class IntentClassifier:
    """Classify user queries into predefined intents."""

    def __init__(self, intents_path: Path = INTENTS_PATH):
        self.intent_labels: List[str] = []
        self.training_sentences: List[str] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.training_tfidf = None
        self.encoder = None
        self.training_embeddings = None

        self._load_intents(intents_path)
        self._init_dense_encoder()

    def _load_intents(self, path: Path) -> None:
        """Load intent training samples from YAML and train TF-IDF model."""
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for intent, details in data.items():
            samples = details.get("samples", [])
            for sample in samples:
                self.intent_labels.append(intent)
                self.training_sentences.append(sample.lower())

        if self.training_sentences:
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            self.training_tfidf = self.vectorizer.fit_transform(self.training_sentences)

    def _init_dense_encoder(self) -> None:
        """Initialize sentence-transformers model if installed (cached across instances)."""
        global _SHARED_ENCODER
        try:
            if _SHARED_ENCODER is None:
                from sentence_transformers import SentenceTransformer
                try:
                    _SHARED_ENCODER = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
                except Exception:
                    _SHARED_ENCODER = SentenceTransformer("all-MiniLM-L6-v2")
            self.encoder = _SHARED_ENCODER
            if self.training_sentences:
                cache_key = (str(INTENTS_PATH), len(self.training_sentences))
                if cache_key not in _SHARED_EMBEDDINGS:
                    _SHARED_EMBEDDINGS[cache_key] = self.encoder.encode(
                        self.training_sentences,
                        normalize_embeddings=True,
                    )
                self.training_embeddings = _SHARED_EMBEDDINGS[cache_key]
        except Exception:
            self.encoder = None
            self.training_embeddings = None

    def predict(self, query: str) -> Tuple[Optional[str], float]:
        """Return highest matching intent and confidence score."""
        if not self.training_sentences:
            return None, 0.0

        clean_query = query.lower().strip()

        # Try dense semantic embedding model first
        if self.encoder is not None and self.training_embeddings is not None:
            try:
                query_emb = self.encoder.encode([clean_query], normalize_embeddings=True)
                similarities = np.dot(self.training_embeddings, query_emb.T).flatten()
                best_idx = int(similarities.argmax())
                best_score = float(similarities[best_idx])
                return self.intent_labels[best_idx], best_score
            except Exception:
                pass

        # Fallback to TF-IDF cosine similarity
        if self.vectorizer is not None and self.training_tfidf is not None:
            query_vec = self.vectorizer.transform([clean_query])
            similarities = cosine_similarity(query_vec, self.training_tfidf)[0]
            best_idx = int(similarities.argmax())
            best_score = float(similarities[best_idx])
            return self.intent_labels[best_idx], best_score

        return None, 0.0
