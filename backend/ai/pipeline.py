"""Orchestration du pipeline IA + détection de disponibilité (fallback gracieux).

L'API importe ce module. Si les dépendances lourdes (PyMuPDF, sentence-transformers,
faiss, numpy) ne sont pas installées, `AVAILABLE` vaut False et l'API retombe sur
le comportement du Lot A (score par intersection de compétences). L'app reste donc
fonctionnelle même sans le pipeline installé.
"""
import importlib.util

# Dépendances requises par le pipeline
_DEPS = ("fitz", "sentence_transformers", "faiss", "numpy")
AVAILABLE = all(importlib.util.find_spec(dep) is not None for dep in _DEPS)


def index_cv(conn, cv_id, pdf_path):
    """Extraction -> chunking -> embeddings -> stockage des chunks du CV.

    Retourne un dict {texte_brut, skills, experience, education} pour mettre à jour
    la fiche CV affichée par le front. Ne committe pas (le caller s'en charge).
    """
    from backend.ai import chunking, extract, matching

    texte = extract.extract_text(pdf_path)
    chunks = chunking.chunk_text(texte)
    matching.store_cv_chunks(conn, cv_id, chunks)
    return {
        "texte_brut": texte,
        "skills": chunking.extract_skills(chunks),
        "experience": chunking.section_text(chunks, "experience"),
        "education": chunking.section_text(chunks, "education"),
    }


def index_cv_from_fields(conn, cv_id, skills, experience, education):
    """Indexe un CV à partir de ses champs déjà en base (sans PDF).

    Utile pour réindexer les données de démonstration (le CV seedé n'a pas de PDF).
    """
    from backend.ai import matching

    chunks = []
    if skills:
        chunks.append({"type_section": "skills", "contenu": ", ".join(skills)})
    if experience:
        chunks.append({"type_section": "experience", "contenu": experience})
    if education:
        chunks.append({"type_section": "education", "contenu": education})
    matching.store_cv_chunks(conn, cv_id, chunks)


def index_offre(conn, offre_id, titre, domaine, description, competences):
    """Construit les chunks d'une offre et les embedde pour le matching bidirectionnel."""
    from backend.ai import matching

    chunks = []
    if titre:
        chunks.append({"type_section": "titre", "contenu": titre})
    if domaine:
        chunks.append({"type_section": "domaine", "contenu": domaine})
    if description:
        chunks.append({"type_section": "description", "contenu": description})
    if competences:
        chunks.append({"type_section": "skills", "contenu": ", ".join(competences)})
    matching.store_offre_chunks(conn, offre_id, chunks)


def score_cv_offre(conn, cv_id, offre_id):
    from backend.ai import matching
    return matching.cv_offre_score(conn, cv_id, offre_id)


def rank_candidates_for_offre(conn, offre_id):
    from backend.ai import matching
    return matching.rank_candidates_for_offre(conn, offre_id)


def rank_offres_for_candidate(conn, cv_id, offre_ids):
    from backend.ai import matching
    return matching.rank_offres_for_candidate(conn, cv_id, offre_ids)


def search_candidates(conn, query_text):
    from backend.ai import matching
    return matching.search_candidates(conn, query_text)
