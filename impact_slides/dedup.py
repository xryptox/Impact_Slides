"""Tiered semantic dedup engine (v3 #20).

Pure module: numpy / sentence-transformers / rapidfuzz are all optional with
graceful fallback. Extracted verbatim from the monolith; the
``_deduplicate_evidence`` orchestration stays on the trunk (it threads
``self.dedup_engine`` and the source-merging provenance fields).
"""
from __future__ import annotations

import re
from typing import List, Optional

# numpy powers the pure-Python TF-IDF + cosine tier (no sklearn dependency).
try:
    import numpy as np
except ImportError:  # pragma: no cover - graceful degradation
    np = None


def _text_similarity(a: str, b: str) -> float:
    """Similarity ratio 0-1 between two strings. Uses rapidfuzz if available
    (fast), else falls back to stdlib difflib so the feature works without the
    optional dependency."""
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a or not b:
        return 0.0
    try:
        from rapidfuzz import fuzz
        return fuzz.ratio(a, b) / 100.0
    except ImportError:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio()


# v3: tiered semantic similarity for the dedup clustering pass.
# Tries (1) sentence-transformers embeddings, (2) pure-numpy TF-IDF + cosine,
# (3) rapidfuzz char-similarity — in that order — so the dedup pass can cluster
# TRUE semantic near-duplicates (sharing few character n-grams, e.g.
# "North America revenue grew 12%" vs "US & Canada sales up a tenth") rather
# than only lexical rephrasings. Each tier is optional; the next is the graceful
# fallback. Thresholds are mode-aware because cosine-of-embeddings, TF-IDF
# cosine, and char-similarity have different score distributions.

_SENTENCE_MODEL = None  # lazily-loaded sentence-transformers model (singleton)


def _load_sentence_model():
    """Lazily load a small sentence-transformers model. Returns None if the
    optional dependency is unavailable or fails to load."""
    global _SENTENCE_MODEL
    if _SENTENCE_MODEL is False:
        return None
    if _SENTENCE_MODEL is not None:
        return _SENTENCE_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _SENTENCE_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        return _SENTENCE_MODEL
    except Exception:
        _SENTENCE_MODEL = False  # cache the failure so we don't retry per call
        return None


_TFIDF_TOKEN_RE = re.compile(r"[a-z0-9]{2,}")


def _tfidf_vectors(texts: List[str]):
    """Build L2-normalized TF-IDF row vectors using pure numpy (no sklearn).
    Returns an [n x vocab] matrix, or None if numpy is unavailable or no text
    has any tokens."""
    if np is None or not texts:
        return None
    tokenized = [_TFIDF_TOKEN_RE.findall((t or "").lower()) for t in texts]
    vocab = {}
    for toks in tokenized:
        for tok in toks:
            if tok not in vocab:
                vocab[tok] = len(vocab)
    if not vocab:
        return None
    n, V = len(texts), len(vocab)
    df = np.zeros(V)
    for toks in tokenized:
        for tok in set(toks):
            df[vocab[tok]] += 1
    idf = np.log((1.0 + n) / (1.0 + df)) + 1.0  # smoothed idf
    mat = np.zeros((n, V))
    for i, toks in enumerate(tokenized):
        if not toks:
            continue
        total = len(toks)
        counts = {}
        for tok in toks:
            counts[tok] = counts.get(tok, 0) + 1
        for tok, c in counts.items():
            mat[i, vocab[tok]] = (c / total) * idf[vocab[tok]]
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


# Per-mode near-duplicate thresholds.
# - embeddings: sentence-cosine; 0.75 catches semantic near-dups (incl.
#   synonyms) without over-merging distinct short insights. This is the only
#   tier that bridges synonyms / no-shared-vocabulary near-dups.
# - tfidf: word-overlap cosine; conservative 0.85 because empirical testing on
#   the real-world dataset showed token-overlap similarity is fundamentally
#   unsuitable for TEMPLATED evidence (numeric ranges / aggregates share
#   boilerplate + numeric values across DISTINCT metrics, e.g.
#   "'Tax 5%' ranges from 0.6045 to 49.26" vs "'gross income' ranges from
#   0.6045 to 49.26" score ~0.78). Retained as an opt-in for prose-heavy,
#   non-templated registers; NOT the auto default.
# - fuzzy: char-similarity; 0.85 catches lexical rephrasings reliably.
# In embeddings mode we ALSO accept a fuzzy match (OR) so exact lexical
# near-dups a sentence model might underweight are still caught.
_SEM_THRESHOLD = {"embeddings": 0.75, "tfidf": 0.85, "fuzzy": 0.85}


class _SemanticDedupEngine:
    """Tiered similarity engine for the dedup pass. Precomputes a cosine
    similarity matrix once (for the embeddings/TF-IDF tiers) so the greedy
    clustering loop stays cheap; the fuzzy tier computes pairwise on demand.

    engine: 'auto' (best available) | 'embeddings' | 'tfidf' | 'fuzzy'

    Tier order in 'auto': sentence-transformers embeddings -> rapidfuzz
    char-similarity. (TF-IDF is intentionally NOT the auto fallback: empirical
    testing on short evidence texts showed it has an inverted precision/recall
    tradeoff versus char-similarity — distinct texts sharing a common keyword
    can score higher than genuine rephrasings. It remains available as an
    explicit opt-in tier.)
    """

    def __init__(self, texts: List[str], engine: str = "auto"):
        self.texts = [t or "" for t in texts]
        self.engine_requested = (engine or "auto").lower()
        self.matrix = None      # cosine-similarity matrix (embeddings or tfidf)
        self.mode = "fuzzy"     # resolved mode after _build
        self.threshold = _SEM_THRESHOLD["fuzzy"]
        self._build()

    def _build(self):
        want = self.engine_requested
        # Tier 1: sentence-transformers embeddings (true semantic similarity;
        # the only tier that bridges synonyms / no shared vocabulary).
        if want in ("auto", "embeddings"):
            model = _load_sentence_model()
            if model is not None:
                try:
                    emb = model.encode(self.texts, normalize_embeddings=True,
                                       convert_to_numpy=True)
                    if emb is not None and len(emb) == len(self.texts):
                        self.matrix = np.dot(emb, emb.T)
                        self.mode = "embeddings"
                        self.threshold = _SEM_THRESHOLD["embeddings"]
                        return
                except Exception:
                    pass  # fall through to next tier
        # Tier 2 (opt-in): pure-numpy TF-IDF + cosine. Only used when explicitly
        # requested; not an auto fallback (see class docstring).
        if want == "tfidf":
            mat = _tfidf_vectors(self.texts)
            if mat is not None:
                self.matrix = np.dot(mat, mat.T)
                self.mode = "tfidf"
                self.threshold = _SEM_THRESHOLD["tfidf"]
                return
        # Tier 3 (auto fallback): rapidfuzz char-similarity.
        self.mode = "fuzzy"
        self.threshold = _SEM_THRESHOLD["fuzzy"]

    def similar(self, i: int, j: int) -> bool:
        """True if texts[i] and texts[j] are near-duplicates at this tier's
        threshold. In embeddings mode a fuzzy match is also accepted (OR) so
        exact lexical near-dups a sentence model underweights are still caught."""
        if self.mode == "embeddings" and self.matrix is not None:
            if float(self.matrix[i, j]) >= self.threshold:
                return True
            return _text_similarity(self.texts[i], self.texts[j]) >= _SEM_THRESHOLD["fuzzy"]
        if self.matrix is not None:
            return float(self.matrix[i, j]) >= self.threshold
        return _text_similarity(self.texts[i], self.texts[j]) >= self.threshold
