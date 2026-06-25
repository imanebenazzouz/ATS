"""API Flask de la plateforme ATS (Lot A).

Expose l'authentification et le CRUD (offres, CV, candidatures, utilisateurs, stats)
au-dessus de SQLite. Le frontend Streamlit consomme cette API via `frontend/api_client.py`.

Hors périmètre (volontairement laissé aux autres lots) :
  - le matching sémantique réel (embeddings MiniLM + FAISS + cosinus) -> Lot B,
    ici le score est une simple intersection de compétences (placeholder) ;
  - le LLM copilote (explication, chatbot) -> Lot C.

Lancer :  python -m backend.app   (depuis la racine du projet)
"""
import os

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from backend import llm
from backend.ai import pipeline
from backend.db import dumps, get_connection, loads

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)


# --------------------------------------------------------------------------- #
# Sérialisation : ligne SQLite -> dict attendu par le frontend
# --------------------------------------------------------------------------- #
def user_to_dict(row):
    return {
        "id": row["id"],
        "email": row["email"],
        "role": row["role"],
        "nom": row["nom"],
        "prenom": row["prenom"],
        "entreprise": row["entreprise"],
    }


def offre_to_dict(row):
    return {
        "id": row["id"],
        "recruteur_id": row["recruteur_id"],
        "titre": row["titre"],
        "entreprise": row["entreprise"],          # vient du JOIN sur users
        "domaine": row["domaine"],
        "description": row["description"],
        "competences_requises": loads(row["competences_requises"]),
        "statut": row["statut"],
        "date_publication": row["date_publication"],
    }


def cv_to_dict(row):
    return {
        "id": row["id"],
        "candidat_id": row["candidat_id"],
        "fichier": os.path.basename(row["fichier_path"]),
        "skills": loads(row["skills"]),
        "experience": row["experience"],
        "education": row["education"],
        "date_upload": row["date_upload"],
    }


def candidature_to_dict(row):
    return {
        "id": row["id"],
        "candidat_id": row["candidat_id"],
        "offre_id": row["offre_id"],
        "date": row["date"],
        "statut": row["statut"],
        "score_matching": row["score_matching"],
        "message_recruteur": row["message_recruteur"],
        "date_reponse": row["date_reponse"],
    }


def today():
    """Date du jour 'YYYY-MM-DD' (même format que l'ancien front mocké)."""
    from datetime import date
    return date.today().isoformat()


# --------------------------------------------------------------------------- #
# Authentification
# --------------------------------------------------------------------------- #
@app.post("/auth/register")
def register():
    data = request.get_json(force=True)
    required = ("email", "password", "role", "nom", "prenom")
    if not all(data.get(k) for k in required):
        return jsonify({"error": "Champs obligatoires manquants."}), 400
    if data["role"] not in ("candidat", "recruteur"):
        return jsonify({"error": "Rôle invalide."}), 400

    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO users (email, password_hash, role, nom, prenom, entreprise)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data["email"], generate_password_hash(data["password"]), data["role"],
             data["nom"], data["prenom"], data.get("entreprise")),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(user_to_dict(row)), 201
    except Exception as exc:  # IntegrityError -> email déjà pris
        if "UNIQUE" in str(exc):
            return jsonify({"error": "Cet email est déjà utilisé."}), 409
        return jsonify({"error": str(exc)}), 400
    finally:
        conn.close()


@app.post("/auth/login")
def login():
    data = request.get_json(force=True)
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (data.get("email"),)).fetchone()
    conn.close()
    if row and check_password_hash(row["password_hash"], data.get("password", "")):
        return jsonify(user_to_dict(row))
    return jsonify({"error": "Email ou mot de passe incorrect."}), 401


# --------------------------------------------------------------------------- #
# Utilisateurs (admin)
# --------------------------------------------------------------------------- #
@app.get("/users")
def list_users():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    conn.close()
    return jsonify([user_to_dict(r) for r in rows])


@app.get("/users/<int:user_id>")
def get_user(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Utilisateur introuvable."}), 404
    return jsonify(user_to_dict(row))


@app.put("/users/<int:user_id>/role")
def update_user_role(user_id):
    role = request.get_json(force=True).get("role")
    if role not in ("candidat", "recruteur", "admin"):
        return jsonify({"error": "Rôle invalide."}), 400
    conn = get_connection()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.delete("/users/<int:user_id>")
def delete_user(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# --------------------------------------------------------------------------- #
# Offres
# --------------------------------------------------------------------------- #
OFFRE_SELECT = """
    SELECT o.*, u.entreprise AS entreprise
    FROM offres o JOIN users u ON u.id = o.recruteur_id
"""


@app.get("/offres")
def list_offres():
    clauses, params = [], []
    if request.args.get("statut"):
        clauses.append("o.statut = ?")
        params.append(request.args["statut"])
    if request.args.get("recruteur_id"):
        clauses.append("o.recruteur_id = ?")
        params.append(request.args["recruteur_id"])
    sql = OFFRE_SELECT + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY o.id"
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([offre_to_dict(r) for r in rows])


@app.post("/offres")
def create_offre():
    data = request.get_json(force=True)
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO offres (recruteur_id, titre, domaine, description,
                               competences_requises, statut, date_publication)
           VALUES (?, ?, ?, ?, ?, 'active', ?)""",
        (data["recruteur_id"], data["titre"], data.get("domaine"), data.get("description"),
         dumps(data.get("competences_requises", [])), today()),
    )
    offre_id = cur.lastrowid
    # Pipeline IA (Lot B) : l'offre est aussi chunked + embedded (matching bidirectionnel).
    if pipeline.AVAILABLE:
        try:
            pipeline.index_offre(conn, offre_id, data["titre"], data.get("domaine"),
                                 data.get("description"), data.get("competences_requises", []))
        except Exception as exc:
            app.logger.warning("Pipeline offre échoué: %s", exc)
    conn.commit()
    row = conn.execute(OFFRE_SELECT + " WHERE o.id = ?", (offre_id,)).fetchone()
    conn.close()
    return jsonify(offre_to_dict(row)), 201


@app.put("/offres/<int:offre_id>")
def update_offre(offre_id):
    statut = request.get_json(force=True).get("statut")
    if statut not in ("active", "inactive"):
        return jsonify({"error": "Statut invalide."}), 400
    conn = get_connection()
    conn.execute("UPDATE offres SET statut = ? WHERE id = ?", (statut, offre_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.delete("/offres/<int:offre_id>")
def delete_offre(offre_id):
    conn = get_connection()
    conn.execute("DELETE FROM offres WHERE id = ?", (offre_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# --------------------------------------------------------------------------- #
# CV
# --------------------------------------------------------------------------- #
@app.get("/cvs")
def get_cv():
    candidat_id = request.args.get("candidat_id")
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM cvs WHERE candidat_id = ? ORDER BY id DESC LIMIT 1", (candidat_id,)
    ).fetchone()
    conn.close()
    return jsonify(cv_to_dict(row) if row else None)


@app.post("/cvs")
def upload_cv():
    """Reçoit le PDF (multipart) + candidat_id, le stocke et lance le pipeline IA.

    Pipeline (Lot B) : extraction PDF -> chunking -> embeddings -> stockage des chunks.
    Si les dépendances du pipeline sont absentes, on retombe sur des valeurs placeholder
    pour que le front reste fonctionnel.
    """
    candidat_id = request.form.get("candidat_id")
    file = request.files.get("file")
    if not candidat_id or not file:
        return jsonify({"error": "candidat_id et file requis."}), 400

    filename = secure_filename(f"{candidat_id}_{file.filename}")
    path = os.path.join(UPLOAD_DIR, filename)
    file.save(path)

    conn = get_connection()
    # un seul CV courant par candidat : on remplace l'ancien
    conn.execute("DELETE FROM cvs WHERE candidat_id = ?", (candidat_id,))
    cur = conn.execute(
        "INSERT INTO cvs (candidat_id, fichier_path, date_upload) VALUES (?, ?, ?)",
        (candidat_id, path, today()),
    )
    cv_id = cur.lastrowid

    # Pipeline IA (Lot B) : extraction PDF -> chunking -> embeddings -> stockage chunks.
    # Si indisponible, on garde des valeurs placeholder (le front reste fonctionnel).
    if pipeline.AVAILABLE:
        try:
            infos = pipeline.index_cv(conn, cv_id, path)
        except Exception as exc:  # PDF illisible, etc. -> placeholder
            app.logger.warning("Pipeline CV échoué: %s", exc)
            infos = None
    else:
        infos = None
    if infos is None:
        infos = {"texte_brut": None, "skills": ["Python", "NLP", "Docker"],
                 "experience": "Expérience extraite (placeholder)",
                 "education": "Formation extraite (placeholder)"}

    conn.execute(
        "UPDATE cvs SET texte_brut = ?, skills = ?, experience = ?, education = ? WHERE id = ?",
        (infos["texte_brut"], dumps(infos["skills"]), infos["experience"], infos["education"], cv_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM cvs WHERE id = ?", (cv_id,)).fetchone()
    conn.close()
    return jsonify(cv_to_dict(row)), 201


# --------------------------------------------------------------------------- #
# Candidatures
# --------------------------------------------------------------------------- #
def _compute_score(conn, candidat_id, offre):
    """Score placeholder = part des compétences de l'offre couvertes par le CV.

    Remplacé par la similarité cosinus (embeddings + FAISS) au Lot B.
    """
    cv = conn.execute(
        "SELECT skills FROM cvs WHERE candidat_id = ? ORDER BY id DESC LIMIT 1", (candidat_id,)
    ).fetchone()
    comps = loads(offre["competences_requises"])
    if not cv or not comps:
        return 0.0
    communes = set(loads(cv["skills"])) & set(comps)
    return round(len(communes) / len(comps), 2)


@app.get("/candidatures")
def list_candidatures():
    clauses, params = [], []
    if request.args.get("candidat_id"):
        clauses.append("candidat_id = ?")
        params.append(request.args["candidat_id"])
    if request.args.get("offre_id"):
        clauses.append("offre_id = ?")
        params.append(request.args["offre_id"])
    sql = "SELECT * FROM candidatures" + (" WHERE " + " AND ".join(clauses) if clauses else "")
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([candidature_to_dict(r) for r in rows])


@app.post("/candidatures")
def create_candidature():
    data = request.get_json(force=True)
    candidat_id, offre_id = data["candidat_id"], data["offre_id"]
    conn = get_connection()
    offre = conn.execute("SELECT * FROM offres WHERE id = ?", (offre_id,)).fetchone()
    if not offre:
        conn.close()
        return jsonify({"error": "Offre introuvable."}), 404

    # Score réel par similarité cosinus (Lot B) si disponible, sinon intersection (Lot A).
    score = None
    if pipeline.AVAILABLE:
        cv = conn.execute(
            "SELECT id FROM cvs WHERE candidat_id = ? ORDER BY id DESC LIMIT 1", (candidat_id,)
        ).fetchone()
        if cv:
            score = pipeline.score_cv_offre(conn, cv["id"], offre_id)
    if score is None:
        score = _compute_score(conn, candidat_id, offre)
    try:
        cur = conn.execute(
            """INSERT INTO candidatures (candidat_id, offre_id, date, statut, score_matching)
               VALUES (?, ?, ?, 'en_attente', ?)""",
            (candidat_id, offre_id, today(), score),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM candidatures WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(candidature_to_dict(row)), 201
    except Exception as exc:
        if "UNIQUE" in str(exc):
            return jsonify({"error": "Déjà postulé à cette offre."}), 409
        return jsonify({"error": str(exc)}), 400
    finally:
        conn.close()


@app.put("/candidatures/<int:cand_id>")
def respond_candidature(cand_id):
    data = request.get_json(force=True)
    statut = data.get("statut")
    if statut not in ("acceptee", "refusee"):
        return jsonify({"error": "Statut invalide."}), 400
    conn = get_connection()
    conn.execute(
        "UPDATE candidatures SET statut = ?, message_recruteur = ?, date_reponse = ? WHERE id = ?",
        (statut, data.get("message_recruteur"), today(), cand_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM candidatures WHERE id = ?", (cand_id,)).fetchone()
    conn.close()
    return jsonify(candidature_to_dict(row))


# --------------------------------------------------------------------------- #
# Matching sémantique (Lot B) — embeddings MiniLM + FAISS + cosinus
# --------------------------------------------------------------------------- #
def _require_pipeline():
    if not pipeline.AVAILABLE:
        return jsonify({"error": "Pipeline IA indisponible (dépendances non installées)."}), 503
    return None


@app.get("/matching/candidats")
def matching_candidats():
    """offre -> CV : candidats les plus pertinents pour une offre (cosinus)."""
    err = _require_pipeline()
    if err:
        return err
    offre_id = request.args.get("offre_id")
    conn = get_connection()
    resultats = pipeline.rank_candidates_for_offre(conn, offre_id)
    for r in resultats:
        u = conn.execute("SELECT prenom, nom FROM users WHERE id = ?", (r["candidat_id"],)).fetchone()
        r["prenom"], r["nom"] = (u["prenom"], u["nom"]) if u else (None, None)
    conn.close()
    return jsonify(resultats)


@app.get("/matching/offres")
def matching_offres():
    """CV -> offres : offres actives les plus pertinentes pour un candidat (cosinus)."""
    err = _require_pipeline()
    if err:
        return err
    candidat_id = request.args.get("candidat_id")
    conn = get_connection()
    cv = conn.execute(
        "SELECT id FROM cvs WHERE candidat_id = ? ORDER BY id DESC LIMIT 1", (candidat_id,)
    ).fetchone()
    if not cv:
        conn.close()
        return jsonify([])
    offre_ids = [r["id"] for r in conn.execute("SELECT id FROM offres WHERE statut = 'active'").fetchall()]
    classement = pipeline.rank_offres_for_candidate(conn, cv["id"], offre_ids)
    resultats = []
    for offre_id, score in classement:
        o = conn.execute(OFFRE_SELECT + " WHERE o.id = ?", (offre_id,)).fetchone()
        resultats.append({"offre_id": offre_id, "score": score, "titre": o["titre"],
                          "entreprise": o["entreprise"], "domaine": o["domaine"]})
    conn.close()
    return jsonify(resultats)


@app.post("/search/candidats")
def search_candidats():
    """Recherche RH en langage naturel -> candidats classés (requête FAISS). Sujet §7."""
    err = _require_pipeline()
    if err:
        return err
    query = request.get_json(force=True).get("query", "").strip()
    if not query:
        return jsonify({"error": "Requête vide."}), 400
    conn = get_connection()
    resultats = pipeline.search_candidates(conn, query)
    for r in resultats:
        u = conn.execute("SELECT prenom, nom FROM users WHERE id = ?", (r["candidat_id"],)).fetchone()
        r["prenom"], r["nom"] = (u["prenom"], u["nom"]) if u else (None, None)
    conn.close()
    return jsonify(resultats)


# --------------------------------------------------------------------------- #
# LLM copilote (Lot C) — explication des matchs + chatbot
# --------------------------------------------------------------------------- #
@app.post("/matching/explain")
def explain_match():
    """Sujet §8.1 : explication LLM d'un score de matching CV <-> offre (persistée)."""
    data = request.get_json(force=True)
    candidat_id, offre_id = data.get("candidat_id"), data.get("offre_id")
    conn = get_connection()

    cv = conn.execute(
        "SELECT skills, experience FROM cvs WHERE candidat_id = ? ORDER BY id DESC LIMIT 1", (candidat_id,)
    ).fetchone()
    offre = conn.execute(OFFRE_SELECT + " WHERE o.id = ?", (offre_id,)).fetchone()
    cand = conn.execute(
        "SELECT score_matching FROM candidatures WHERE candidat_id = ? AND offre_id = ?",
        (candidat_id, offre_id),
    ).fetchone()
    if not offre:
        conn.close()
        return jsonify({"error": "Offre introuvable."}), 404

    skills = loads(cv["skills"]) if cv else []
    experience = cv["experience"] if cv else None
    score = cand["score_matching"] if cand else None

    try:
        explication = llm.explain_match(skills, experience, offre["titre"],
                                        loads(offre["competences_requises"]), score)
    except Exception as exc:
        conn.close()
        return jsonify({"error": f"LLM indisponible : {exc}"}), 503

    conn.execute(
        """INSERT INTO matching_results (candidat_id, offre_id, score, explication_llm)
           VALUES (?, ?, ?, ?)""",
        (candidat_id, offre_id, score or 0.0, explication),
    )
    conn.commit()
    conn.close()
    return jsonify({"explication": explication})


@app.post("/chatbot/message")
def chatbot_message():
    """Sujet §8 : message du copilote, persisté dans chatbot_sessions/conseils_llm."""
    data = request.get_json(force=True)
    user_id, role, question = data.get("user_id"), data.get("role"), data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question vide."}), 400

    conn = get_connection()
    session = conn.execute(
        "SELECT id FROM chatbot_sessions WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone()
    if session:
        session_id = session["id"]
    else:
        cur = conn.execute(
            "INSERT INTO chatbot_sessions (user_id, role_user) VALUES (?, ?)", (user_id, role)
        )
        session_id = cur.lastrowid

    try:
        reponse = llm.chat_reply(question, role)
    except Exception as exc:
        conn.close()
        return jsonify({"error": f"LLM indisponible : {exc}"}), 503

    conn.execute(
        "INSERT INTO conseils_llm (session_id, question, reponse_llm) VALUES (?, ?, ?)",
        (session_id, question, reponse),
    )
    conn.commit()
    conn.close()
    return jsonify({"reponse": reponse})


@app.get("/chatbot/history")
def chatbot_history():
    user_id = request.args.get("user_id")
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.question, c.reponse_llm, c.timestamp
           FROM conseils_llm c JOIN chatbot_sessions s ON s.id = c.session_id
           WHERE s.user_id = ? ORDER BY c.id""",
        (user_id,),
    ).fetchall()
    conn.close()
    return jsonify([{"question": r["question"], "reponse": r["reponse_llm"], "timestamp": r["timestamp"]}
                    for r in rows])


# --------------------------------------------------------------------------- #
# Statistiques (admin)
# --------------------------------------------------------------------------- #
@app.get("/stats")
def stats():
    conn = get_connection()
    q = lambda sql: conn.execute(sql).fetchone()[0]
    nb_candidats = q("SELECT COUNT(*) FROM users WHERE role = 'candidat'")
    nb_recruteurs = q("SELECT COUNT(*) FROM users WHERE role = 'recruteur'")
    nb_offres = q("SELECT COUNT(*) FROM offres")
    nb_candidatures = q("SELECT COUNT(*) FROM candidatures")
    score_moyen = conn.execute("SELECT AVG(score_matching) FROM candidatures").fetchone()[0] or 0.0
    conn.close()
    return jsonify({
        "nb_candidats": nb_candidats,
        "nb_recruteurs": nb_recruteurs,
        "nb_offres": nb_offres,
        "nb_candidatures": nb_candidatures,
        "score_moyen_matching": round(score_moyen, 2),
    })


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # threaded=True : sans ça, le serveur ne traite qu'une requête à la fois - le
    # temps que le pipeline IA traite un CV (upload), tout le reste (offres, chat...)
    # reste bloqué en file d'attente jusqu'au timeout côté front.
    # use_reloader=False : le reloader watchdog surveille aussi les fichiers importés
    # dans site-packages (transformers, etc.) ; le premier appel au pipeline IA importe
    # d'un coup des centaines de sous-modules, ce que watchdog prend pour des
    # changements et redémarre le serveur en pleine requête (ConnectionResetError côté client).
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True, use_reloader=False)
