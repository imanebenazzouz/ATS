"""Réindexe tout le contenu existant : (re)calcule les chunks + embeddings.

À lancer après `seed.py` (ou après avoir installé le pipeline) pour que les CV et
offres déjà en base soient embeddés et donc matchables. Les CV sont réindexés
depuis leurs champs (skills/experience/education) faute de PDF d'origine.

Usage :  python -m backend.reindex
"""
from backend.ai import pipeline
from backend.db import get_connection, loads


def reindex():
    if not pipeline.AVAILABLE:
        print("Pipeline IA indisponible — installe backend/requirements.txt d'abord.")
        return

    conn = get_connection()

    cvs = conn.execute("SELECT id, skills, experience, education FROM cvs").fetchall()
    for cv in cvs:
        pipeline.index_cv_from_fields(conn, cv["id"], loads(cv["skills"]),
                                      cv["experience"], cv["education"])
    print(f"{len(cvs)} CV réindexés.")

    offres = conn.execute(
        "SELECT id, titre, domaine, description, competences_requises FROM offres"
    ).fetchall()
    for o in offres:
        pipeline.index_offre(conn, o["id"], o["titre"], o["domaine"],
                             o["description"], loads(o["competences_requises"]))
    print(f"{len(offres)} offres réindexées.")

    conn.commit()
    conn.close()
    print("Réindexation terminée.")


if __name__ == "__main__":
    reindex()
