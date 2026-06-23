"""Tests d'intégration de l'API ATS (Lots A et B).

S'exécutent sur une base SQLite jetable via le client de test Flask — aucun serveur
ni réseau requis. Les tests du pipeline IA sont ignorés si les dépendances lourdes
(PyMuPDF, sentence-transformers, faiss, numpy) ne sont pas installées.

Lancer :  pytest -q   (depuis la racine du projet)
"""
import io
import os
import tempfile

import pytest


@pytest.fixture(scope="session")
def client():
    # Base jetable + schéma + données de démo, avant d'importer l'app.
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    os.environ["ATS_DB_PATH"] = tmp.name

    import init_db
    from backend import seed
    init_db.init_db(tmp.name)
    seed.seed()

    from backend.app import app
    app.testing = True
    with app.test_client() as c:
        yield c
    os.unlink(tmp.name)


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
def test_health(client):
    assert client.get("/health").get_json()["status"] == "ok"


def test_login_ok(client):
    r = client.post("/auth/login", json={"email": "rh@test.com", "password": "1234"})
    assert r.status_code == 200
    assert r.get_json()["role"] == "recruteur"


def test_login_mauvais_mdp(client):
    assert client.post("/auth/login", json={"email": "rh@test.com", "password": "x"}).status_code == 401


def test_login_inconnu(client):
    assert client.post("/auth/login", json={"email": "no@no.com", "password": "x"}).status_code == 401


def test_register_et_login(client):
    r = client.post("/auth/register", json={
        "email": "alice@new.com", "password": "pwd", "role": "candidat",
        "nom": "Wonder", "prenom": "Alice"})
    assert r.status_code == 201
    assert client.post("/auth/login", json={"email": "alice@new.com", "password": "pwd"}).status_code == 200


def test_register_email_duplique(client):
    assert client.post("/auth/register", json={
        "email": "rh@test.com", "password": "x", "role": "recruteur",
        "nom": "A", "prenom": "B"}).status_code == 409


def test_register_champs_manquants(client):
    assert client.post("/auth/register", json={"email": "x@x.com"}).status_code == 400


def test_register_role_invalide(client):
    assert client.post("/auth/register", json={
        "email": "z@z.com", "password": "x", "role": "admin",
        "nom": "A", "prenom": "B"}).status_code == 400


def test_login_ne_renvoie_pas_le_hash(client):
    data = client.post("/auth/login", json={"email": "candidat@test.com", "password": "1234"}).get_json()
    assert "password_hash" not in data and "password" not in data


# --------------------------------------------------------------------------- #
# Offres
# --------------------------------------------------------------------------- #
def test_liste_offres_actives(client):
    offres = client.get("/offres?statut=active").get_json()
    assert len(offres) == 7
    assert all(o["statut"] == "active" for o in offres)


def test_offre_contient_entreprise_et_competences(client):
    o = client.get("/offres?statut=active").get_json()[0]
    assert o["entreprise"] == "TechCorp"
    assert isinstance(o["competences_requises"], list)


def test_creation_offre(client):
    rh = client.post("/auth/login", json={"email": "rh@test.com", "password": "1234"}).get_json()
    r = client.post("/offres", json={
        "recruteur_id": rh["id"], "titre": "DevOps", "domaine": "Tech",
        "description": "CI/CD", "competences_requises": ["Docker", "K8s"]})
    assert r.status_code == 201
    assert r.get_json()["titre"] == "DevOps"


def test_moderation_offre(client):
    assert client.put("/offres/1", json={"statut": "inactive"}).status_code == 200
    assert client.put("/offres/1", json={"statut": "active"}).status_code == 200
    assert client.put("/offres/1", json={"statut": "n_importe_quoi"}).status_code == 400


# --------------------------------------------------------------------------- #
# Candidatures
# --------------------------------------------------------------------------- #
def test_candidature_et_doublon(client):
    # candidat 1 a déjà postulé à l'offre 1 (seed) -> doublon
    assert client.post("/candidatures", json={"candidat_id": 1, "offre_id": 1}).status_code == 409
    # nouvelle candidature OK + score présent
    r = client.post("/candidatures", json={"candidat_id": 1, "offre_id": 3})
    assert r.status_code == 201
    assert 0.0 <= r.get_json()["score_matching"] <= 1.0


def test_candidature_offre_inexistante(client):
    assert client.post("/candidatures", json={"candidat_id": 1, "offre_id": 9999}).status_code == 404


def test_reponse_recruteur(client):
    client.post("/candidatures", json={"candidat_id": 1, "offre_id": 2})
    cid = [c for c in client.get("/candidatures?offre_id=2").get_json()][0]["id"]
    r = client.put(f"/candidatures/{cid}", json={"statut": "acceptée", "message_recruteur": "OK"})
    assert r.status_code == 200
    assert r.get_json()["statut"] == "acceptée" and r.get_json()["date_reponse"]


def test_reponse_statut_invalide(client):
    assert client.put("/candidatures/1", json={"statut": "peut-être"}).status_code == 400


# --------------------------------------------------------------------------- #
# Users (admin) & stats
# --------------------------------------------------------------------------- #
def test_liste_users(client):
    assert len(client.get("/users").get_json()) >= 3


def test_changement_role_et_suppression(client):
    u = client.post("/auth/register", json={
        "email": "todelete@x.com", "password": "x", "role": "candidat",
        "nom": "Z", "prenom": "Z"}).get_json()
    assert client.put(f"/users/{u['id']}/role", json={"role": "recruteur"}).status_code == 200
    assert client.get(f"/users/{u['id']}").get_json()["role"] == "recruteur"
    assert client.delete(f"/users/{u['id']}").status_code == 200
    assert client.get(f"/users/{u['id']}").status_code == 404


def test_stats(client):
    s = client.get("/stats").get_json()
    assert s["nb_offres"] >= 7 and s["nb_candidats"] >= 1
    assert 0.0 <= s["score_moyen_matching"] <= 1.0


# --------------------------------------------------------------------------- #
# Robustesse / sécurité (l'API stocke brut ; l'échappement est côté front)
# --------------------------------------------------------------------------- #
def test_unicode_et_payload_special(client):
    r = client.post("/auth/register", json={
        "email": "josé@accent.com", "password": "p", "role": "recruteur",
        "nom": "<script>alert(1)</script>", "prenom": "Élodie", "entreprise": "A&B « Cie »"})
    assert r.status_code == 201
    assert r.get_json()["prenom"] == "Élodie"


# --------------------------------------------------------------------------- #
# Cas limites
# --------------------------------------------------------------------------- #
def test_recruteur_sans_entreprise(client):
    r = client.post("/auth/register", json={
        "email": "rhsansboite@x.com", "password": "x", "role": "recruteur",
        "nom": "Sans", "prenom": "Boite"})
    assert r.status_code == 201 and r.get_json()["entreprise"] is None


def test_candidature_sans_cv(client):
    u = client.post("/auth/register", json={
        "email": "sanscv@x.com", "password": "x", "role": "candidat",
        "nom": "Sans", "prenom": "Cv"}).get_json()
    r = client.post("/candidatures", json={"candidat_id": u["id"], "offre_id": 5})
    assert r.status_code == 201
    assert r.get_json()["score_matching"] == 0.0   # pas de CV -> score nul


def test_offre_sans_competences(client):
    rh = client.post("/auth/login", json={"email": "rh@test.com", "password": "1234"}).get_json()
    o = client.post("/offres", json={
        "recruteur_id": rh["id"], "titre": "Stage", "domaine": "Tech",
        "description": "Découverte", "competences_requises": []}).get_json()
    r = client.post("/candidatures", json={"candidat_id": 1, "offre_id": o["id"]})
    assert r.status_code == 201 and 0.0 <= r.get_json()["score_matching"] <= 1.0


def test_json_malforme(client):
    r = client.post("/auth/login", data="{pas du json", content_type="application/json")
    assert r.status_code == 400


def test_get_cv_inexistant(client):
    u = client.post("/auth/register", json={
        "email": "nocv@x.com", "password": "x", "role": "candidat",
        "nom": "No", "prenom": "Cv"}).get_json()
    assert client.get(f"/cvs?candidat_id={u['id']}").get_json() is None


def test_upload_non_pdf_ne_crashe_pas(client):
    u = client.post("/auth/register", json={
        "email": "badfile@x.com", "password": "x", "role": "candidat",
        "nom": "Bad", "prenom": "File"}).get_json()
    r = client.post("/cvs", data={"candidat_id": str(u["id"]),
                                  "file": (io.BytesIO(b"ceci n'est pas un pdf"), "fake.pdf")},
                    content_type="multipart/form-data")
    assert r.status_code == 201 and isinstance(r.get_json()["skills"], list)


# --------------------------------------------------------------------------- #
# Pipeline IA (Lot B) — ignoré si dépendances absentes
# --------------------------------------------------------------------------- #
def _ai_available():
    from backend.ai import pipeline
    return pipeline.AVAILABLE


@pytest.mark.skipif(not _ai_available(), reason="pipeline IA non installé")
def test_upload_cv_extraction(client):
    import fitz
    doc = fitz.open(); page = doc.new_page()
    page.insert_text((72, 72), "Skills:\nPython, FastAPI, NLP\nExperience:\nDev backend\nEducation:\nMaster IA")
    pdf = doc.write()
    u = client.post("/auth/register", json={
        "email": "cvtest@x.com", "password": "x", "role": "candidat",
        "nom": "T", "prenom": "Cv"}).get_json()
    r = client.post("/cvs", data={"candidat_id": str(u["id"]),
                                   "file": (io.BytesIO(pdf), "cv.pdf")},
                    content_type="multipart/form-data")
    assert r.status_code == 201
    skills = r.get_json()["skills"]
    assert "Python" in skills and "NLP" in skills


@pytest.mark.skipif(not _ai_available(), reason="pipeline IA non installé")
def test_recherche_semantique_discrimine(client):
    from backend import reindex
    reindex.reindex()
    res = client.post("/search/candidats", json={"query": "data engineer python docker"}).get_json()
    assert isinstance(res, list)
    if len(res) >= 2:
        # résultats triés par score décroissant
        assert res[0]["score"] >= res[-1]["score"]


@pytest.mark.skipif(_ai_available(), reason="teste le fallback uniquement sans pipeline")
def test_matching_indisponible_renvoie_503(client):
    assert client.get("/matching/candidats?offre_id=1").status_code == 503
