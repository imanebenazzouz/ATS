"""Étape 3 du pipeline : embeddings (sentence-transformers/all-MiniLM-L6-v2).

cf. sujet §5.3 : chaque chunk -> vecteur R^n via all-MiniLM-L6-v2.
Le modèle est chargé une seule fois (singleton) car son chargement est coûteux.
Les vecteurs sont normalisés L2 -> le produit scalaire vaut alors la similarité cosinus.
"""
import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384

_model = None


def get_model():
    """Charge (paresseusement) et met en cache le modèle MiniLM."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts):
    """Encode une liste de textes en vecteurs float32 normalisés L2 (n, EMBED_DIM)."""
    if isinstance(texts, str):
        texts = [texts]
    vecs = get_model().encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype=np.float32)


def to_blob(vector):
    """Sérialise un vecteur numpy en bytes pour stockage SQLite (BLOB)."""
    return np.asarray(vector, dtype=np.float32).tobytes()


def from_blob(blob):
    """Désérialise un BLOB SQLite en vecteur numpy float32."""
    return np.frombuffer(blob, dtype=np.float32)
