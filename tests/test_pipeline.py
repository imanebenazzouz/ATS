"""Tests unitaires purs du pipeline IA.

Le chunking n'utilise que la stdlib -> toujours testé. Les tests embeddings/matching
sont ignorés si les dépendances lourdes ne sont pas installées.
"""
import pytest

from backend.ai import chunking


# --------------------------------------------------------------------------- #
# Chunking — cas nominal et cas tordus
# --------------------------------------------------------------------------- #
def test_chunk_exemple_du_sujet():
    cv = "John Doe\nSkills:\nPython, Flask, Docker, NLP\nExperience: 2 years dev\nEducation:\nMaster IA"
    chunks = chunking.chunk_text(cv)
    types = {c["type_section"] for c in chunks}
    assert {"skills", "experience", "education"} <= types


def test_chunk_titre_inline():
    chunks = chunking.chunk_text("Skills: Python, Go, Rust")
    assert chunks == [{"type_section": "skills", "contenu": "Python, Go, Rust"}]


def test_chunk_titre_accentue():
    chunks = chunking.chunk_text("Compétences\nPython\nFormation\nMaster")
    types = {c["type_section"] for c in chunks}
    assert "skills" in types and "education" in types


def test_chunk_sans_section_renvoie_divers():
    chunks = chunking.chunk_text("juste du texte libre sans aucun titre de section")
    assert len(chunks) == 1 and chunks[0]["type_section"] == "divers"


def test_chunk_texte_vide():
    assert chunking.chunk_text("") == []
    assert chunking.chunk_text("   \n  \n") == []


def test_extract_skills_delimiteurs_varies():
    chunks = [{"type_section": "skills", "contenu": "Python; Java / C++ • SQL\nGo"}]
    skills = chunking.extract_skills(chunks)
    assert {"Python", "Java", "C++", "SQL", "Go"} <= set(skills)


def test_extract_skills_aucune_section():
    assert chunking.extract_skills([{"type_section": "experience", "contenu": "x"}]) == []


def test_section_text_concatene():
    chunks = [{"type_section": "experience", "contenu": "A"},
              {"type_section": "experience", "contenu": "B"}]
    assert chunking.section_text(chunks, "experience") == "A B"


# --------------------------------------------------------------------------- #
# Embeddings / matching — ignorés si deps absentes
# --------------------------------------------------------------------------- #
def _ai_available():
    from backend.ai import pipeline
    return pipeline.AVAILABLE


@pytest.mark.skipif(not _ai_available(), reason="pipeline IA non installé")
def test_embeddings_dimension_et_normalisation():
    import numpy as np
    from backend.ai import embeddings as emb
    v = emb.embed(["Python data engineer", "Marketing SEO"])
    assert v.shape == (2, emb.EMBED_DIM)
    norms = np.linalg.norm(v, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3)   # vecteurs normalisés L2


@pytest.mark.skipif(not _ai_available(), reason="pipeline IA non installé")
def test_blob_roundtrip():
    import numpy as np
    from backend.ai import embeddings as emb
    v = emb.embed(["test"])[0]
    assert np.allclose(emb.from_blob(emb.to_blob(v)), v)
