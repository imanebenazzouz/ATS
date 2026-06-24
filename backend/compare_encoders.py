"""
Comparaison de 3 encodeurs (embeddings) pour le matching CV <-> offres de l'ATS.

Le sujet ATS n'exige pas explicitement cette comparaison (contrairement au sujet
du chatbot médical), mais on la fait quand même pour la même rigueur méthodologique.

- all-MiniLM-L6-v2 (actuel en prod)         : généraliste léger multilingue, 384 dim
- sentence-camembert-base                   : spécialisé français, 768 dim
- paraphrase-multilingual-mpnet-base-v2     : multilingue haute qualité, 768 dim

Reprend les données seedées (backend/seed.py) : 1 CV (John Doe) et 7 offres.
Pour chaque encodeur, on calcule le score CV<->offre (même formule que matching.py :
moyenne, pour chaque chunk d'offre, de la meilleure similarité cosinus avec les
chunks du CV) et on compare le classement obtenu.

Lancer : python -m backend.compare_encoders
"""
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.seed import CV_JOHN, OFFRES

ENCODERS = {
    "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-camembert-base": "dangvantuan/sentence-camembert-base",
    "paraphrase-multilingual-mpnet-base-v2": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
}


def cv_chunks():
    skills, experience, education = CV_JOHN["skills"], CV_JOHN["experience"], CV_JOHN["education"]
    chunks = []
    if skills:
        chunks.append(("skills", ", ".join(skills)))
    if experience:
        chunks.append(("experience", experience))
    if education:
        chunks.append(("education", education))
    return chunks


def offre_chunks(titre, domaine, description, competences):
    chunks = []
    if titre:
        chunks.append(("titre", titre))
    if domaine:
        chunks.append(("domaine", domaine))
    if description:
        chunks.append(("description", description))
    if competences:
        chunks.append(("skills", ", ".join(competences)))
    return chunks


def score(model, cv_texts, offre_texts):
    cv_vecs = model.encode(cv_texts, normalize_embeddings=True)
    offre_vecs = model.encode(offre_texts, normalize_embeddings=True)
    sims = np.array(offre_vecs) @ np.array(cv_vecs).T
    return round(float(max(0.0, min(1.0, sims.max(axis=1).mean()))), 3)


def run_comparison():
    cv_texts = [c for _, c in cv_chunks()]
    print(f"CV de test : {len(cv_texts)} chunks (skills/experience/education)\n")

    for label, model_name in ENCODERS.items():
        print(f"=== {label} ({model_name}) ===")
        model = SentenceTransformer(model_name)
        scores = []
        for titre, domaine, description, competences, _date in OFFRES:
            offre_texts = [c for _, c in offre_chunks(titre, domaine, description, competences)]
            s = score(model, cv_texts, offre_texts)
            scores.append((titre, s))
        for titre, s in sorted(scores, key=lambda t: -t[1]):
            print(f"  {s:.0%}  {titre}")
        print()


if __name__ == "__main__":
    run_comparison()
