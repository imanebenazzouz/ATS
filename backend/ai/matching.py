"""Étapes 4 à 7 du pipeline : stockage, FAISS et ranking par similarité cosinus.

cf. sujet §5.4, §6, §7 :
  - chaque chunk (CV ou offre) est stocké avec son embedding (table `chunks`) ;
  - la recherche RH (requête libre) embedde la requête, interroge un index FAISS
    des chunks de CV, récupère le top-k, regroupe par candidat et moyenne les
    similarités (score candidat) ;
  - le score CV<->offre est la moyenne, pour chaque chunk d'offre, de la meilleure
    similarité cosinus avec les chunks du CV (couverture des besoins de l'offre).
"""
import numpy as np

from backend.ai import embeddings as emb


# --------------------------------------------------------------------------- #
# Stockage des chunks + embeddings
# --------------------------------------------------------------------------- #
def _store_chunks(conn, source, owner_col, owner_id, chunks):
    """Insère les chunks d'un CV ou d'une offre avec leurs embeddings."""
    conn.execute(f"DELETE FROM chunks WHERE {owner_col} = ?", (owner_id,))
    if not chunks:
        return
    vecs = emb.embed([c["contenu"] for c in chunks])
    for chunk, vec in zip(chunks, vecs):
        conn.execute(
            f"""INSERT INTO chunks ({owner_col}, source, type_section, contenu, embedding)
                VALUES (?, ?, ?, ?, ?)""",
            (owner_id, source, chunk["type_section"], chunk["contenu"], emb.to_blob(vec)),
        )


def store_cv_chunks(conn, cv_id, chunks):
    _store_chunks(conn, "cv", "cv_id", cv_id, chunks)


def store_offre_chunks(conn, offre_id, chunks):
    _store_chunks(conn, "offre", "offre_id", offre_id, chunks)


# --------------------------------------------------------------------------- #
# Chargement des vecteurs
# --------------------------------------------------------------------------- #
def _load_vectors(conn, where, params):
    """Retourne (matrice (n, dim), liste de lignes) pour les chunks filtrés."""
    rows = conn.execute(
        f"SELECT id, cv_id, offre_id, embedding FROM chunks WHERE {where}", params
    ).fetchall()
    rows = [r for r in rows if r["embedding"]]
    if not rows:
        return np.empty((0, emb.EMBED_DIM), dtype=np.float32), []
    mat = np.vstack([emb.from_blob(r["embedding"]) for r in rows]).astype(np.float32)
    return mat, rows


def _cv_vectors(conn, cv_id):
    mat, _ = _load_vectors(conn, "source = 'cv' AND cv_id = ?", (cv_id,))
    return mat


def _offre_vectors(conn, offre_id):
    mat, _ = _load_vectors(conn, "source = 'offre' AND offre_id = ?", (offre_id,))
    return mat


# --------------------------------------------------------------------------- #
# Scores
# --------------------------------------------------------------------------- #
def _clamp(x):
    return float(max(0.0, min(1.0, x)))


def cv_offre_score(conn, cv_id, offre_id):
    """Score de correspondance CV<->offre dans [0,1], ou None si pas d'embeddings.

    Pour chaque chunk d'offre, on prend la meilleure similarité cosinus avec les
    chunks du CV, puis on moyenne (couverture des besoins de l'offre par le CV).
    """
    cv = _cv_vectors(conn, cv_id)
    offre = _offre_vectors(conn, offre_id)
    if cv.shape[0] == 0 or offre.shape[0] == 0:
        return None
    sims = offre @ cv.T              # vecteurs normalisés -> cosinus
    return round(_clamp(sims.max(axis=1).mean()), 2)


def rank_offres_for_candidate(conn, cv_id, offre_ids):
    """Classe des offres pour un CV (CV -> offres). Retourne [(offre_id, score)] triée."""
    scored = []
    for offre_id in offre_ids:
        score = cv_offre_score(conn, cv_id, offre_id)
        if score is not None:
            scored.append((offre_id, score))
    return sorted(scored, key=lambda t: -t[1])


# --------------------------------------------------------------------------- #
# Recherche RH par requête libre (FAISS) — sujet §7 et §10.2
# --------------------------------------------------------------------------- #
def search_candidates(conn, query_text, top_k=20):
    """Requête RH en langage naturel -> candidats classés.

    Embedde la requête, interroge un index FAISS de tous les chunks de CV,
    récupère les top_k chunks, regroupe par candidat et moyenne les similarités.
    Retourne [{candidat_id, score, n_chunks}] trié par score décroissant.
    """
    import faiss

    rows = conn.execute(
        """SELECT ch.embedding AS embedding, c.candidat_id AS candidat_id
           FROM chunks ch JOIN cvs c ON c.id = ch.cv_id
           WHERE ch.source = 'cv' AND ch.embedding IS NOT NULL"""
    ).fetchall()
    if not rows:
        return []

    mat = np.vstack([emb.from_blob(r["embedding"]) for r in rows]).astype(np.float32)
    candidat_ids = [r["candidat_id"] for r in rows]

    index = faiss.IndexFlatIP(mat.shape[1])     # produit scalaire = cosinus (vecteurs normalisés)
    index.add(mat)
    query = emb.embed(query_text)
    k = min(top_k, mat.shape[0])
    sims, idx = index.search(query, k)

    # regroupement par candidat : moyenne des similarités de ses chunks dans le top-k
    par_candidat = {}
    for sim, i in zip(sims[0], idx[0]):
        if i < 0:
            continue
        par_candidat.setdefault(candidat_ids[i], []).append(float(sim))

    resultats = [
        {"candidat_id": cid, "score": round(_clamp(sum(s) / len(s)), 2), "n_chunks": len(s)}
        for cid, s in par_candidat.items()
    ]
    return sorted(resultats, key=lambda r: -r["score"])


def rank_candidates_for_offre(conn, offre_id, top_k=20):
    """Classe les candidats pour une offre (offre -> CV), via la recherche FAISS.

    On utilise le texte de l'offre (concat de ses chunks) comme requête.
    """
    rows = conn.execute(
        "SELECT contenu FROM chunks WHERE source = 'offre' AND offre_id = ?", (offre_id,)
    ).fetchall()
    query_text = " ".join(r["contenu"] for r in rows).strip()
    if not query_text:
        return []
    return search_candidates(conn, query_text, top_k=top_k)
