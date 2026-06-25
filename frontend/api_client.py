"""Client HTTP vers l'API Flask (Lot A).

Toutes les vues passent par ces fonctions au lieu de lire/écrire `st.session_state`.
L'URL de base est configurable via la variable d'environnement ATS_API_URL
(par défaut http://127.0.0.1:5000).
"""
import os

import requests

BASE_URL = os.environ.get("ATS_API_URL", "http://127.0.0.1:5000")
TIMEOUT = 15


def _url(path):
    return f"{BASE_URL}{path}"


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
def login(email, password):
    """Retourne le dict user si OK, sinon None."""
    r = requests.post(_url("/auth/login"), json={"email": email, "password": password}, timeout=TIMEOUT)
    return r.json() if r.status_code == 200 else None


def register(nom, prenom, email, password, role, entreprise=None):
    """Retourne (user, error). user=None si échec, error=message ou None."""
    r = requests.post(_url("/auth/register"), json={
        "nom": nom, "prenom": prenom, "email": email,
        "password": password, "role": role, "entreprise": entreprise,
    }, timeout=TIMEOUT)
    if r.status_code == 201:
        return r.json(), None
    return None, r.json().get("error", "Erreur inconnue.")


# --------------------------------------------------------------------------- #
# Users
# --------------------------------------------------------------------------- #
def get_user(user_id):
    r = requests.get(_url(f"/users/{user_id}"), timeout=TIMEOUT)
    return r.json() if r.status_code == 200 else None


def list_users():
    return requests.get(_url("/users"), timeout=TIMEOUT).json()


def update_user_role(user_id, role):
    requests.put(_url(f"/users/{user_id}/role"), json={"role": role}, timeout=TIMEOUT)


def delete_user(user_id):
    requests.delete(_url(f"/users/{user_id}"), timeout=TIMEOUT)


# --------------------------------------------------------------------------- #
# Offres
# --------------------------------------------------------------------------- #
def list_offres(statut=None, recruteur_id=None):
    params = {}
    if statut:
        params["statut"] = statut
    if recruteur_id:
        params["recruteur_id"] = recruteur_id
    return requests.get(_url("/offres"), params=params, timeout=TIMEOUT).json()


def create_offre(recruteur_id, titre, domaine, description, competences_requises):
    requests.post(_url("/offres"), json={
        "recruteur_id": recruteur_id, "titre": titre, "domaine": domaine,
        "description": description, "competences_requises": competences_requises,
    }, timeout=TIMEOUT)


def set_offre_statut(offre_id, statut):
    requests.put(_url(f"/offres/{offre_id}"), json={"statut": statut}, timeout=TIMEOUT)


def delete_offre(offre_id):
    requests.delete(_url(f"/offres/{offre_id}"), timeout=TIMEOUT)


# --------------------------------------------------------------------------- #
# CV
# --------------------------------------------------------------------------- #
def get_cv(candidat_id):
    """Retourne le CV courant du candidat, ou None."""
    return requests.get(_url("/cvs"), params={"candidat_id": candidat_id}, timeout=TIMEOUT).json()


def upload_cv(candidat_id, uploaded_file):
    """Envoie le PDF (objet UploadedFile Streamlit) à l'API."""
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
    r = requests.post(_url("/cvs"), data={"candidat_id": candidat_id}, files=files, timeout=TIMEOUT)
    return r.json()


# --------------------------------------------------------------------------- #
# Candidatures
# --------------------------------------------------------------------------- #
def list_candidatures(candidat_id=None, offre_id=None):
    params = {}
    if candidat_id:
        params["candidat_id"] = candidat_id
    if offre_id:
        params["offre_id"] = offre_id
    return requests.get(_url("/candidatures"), params=params, timeout=TIMEOUT).json()


def create_candidature(candidat_id, offre_id):
    """Retourne (candidature, error)."""
    r = requests.post(_url("/candidatures"), json={
        "candidat_id": candidat_id, "offre_id": offre_id,
    }, timeout=TIMEOUT)
    if r.status_code == 201:
        return r.json(), None
    return None, r.json().get("error", "Erreur inconnue.")


def respond_candidature(cand_id, statut, message_recruteur=None):
    requests.put(_url(f"/candidatures/{cand_id}"), json={
        "statut": statut, "message_recruteur": message_recruteur,
    }, timeout=TIMEOUT)


# --------------------------------------------------------------------------- #
# Messagerie
# --------------------------------------------------------------------------- #
def get_messages(candidature_id):
    r = requests.get(_url(f"/candidatures/{candidature_id}/messages"), timeout=TIMEOUT)
    return r.json() if r.status_code == 200 else []


def send_message(candidature_id, expediteur_id, contenu):
    r = requests.post(_url(f"/candidatures/{candidature_id}/messages"), json={
        "expediteur_id": expediteur_id, "contenu": contenu,
    }, timeout=TIMEOUT)
    return r.status_code == 201, r.json().get("error") if r.status_code != 201 else None


# --------------------------------------------------------------------------- #
# Matching sémantique (Lot B)
# --------------------------------------------------------------------------- #
def search_candidats(query):
    """Recherche RH en langage naturel. Retourne (resultats, error)."""
    r = requests.post(_url("/search/candidats"), json={"query": query}, timeout=TIMEOUT)
    if r.status_code == 200:
        return r.json(), None
    return None, r.json().get("error", "Erreur inconnue.")


def matching_candidats(offre_id):
    """Candidats classés pour une offre (offre -> CV). Retourne (resultats, error)."""
    r = requests.get(_url("/matching/candidats"), params={"offre_id": offre_id}, timeout=TIMEOUT)
    if r.status_code == 200:
        return r.json(), None
    return None, r.json().get("error", "Erreur inconnue.")


def matching_offres(candidat_id):
    """Offres recommandées pour un candidat (CV -> offres). Retourne (resultats, error)."""
    r = requests.get(_url("/matching/offres"), params={"candidat_id": candidat_id}, timeout=TIMEOUT)
    if r.status_code == 200:
        return r.json(), None
    return None, r.json().get("error", "Erreur inconnue.")


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #
def get_stats():
    return requests.get(_url("/stats"), timeout=TIMEOUT).json()
