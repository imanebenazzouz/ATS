"""Accès SQLite partagé pour l'API Flask.

La base `ats.db` est créée à la racine du projet par `init_db.py`.
On expose une connexion configurée (Row factory + foreign keys) et quelques
helpers de (dé)sérialisation JSON pour les colonnes liste (skills, compétences).
"""
import json
import os
import sqlite3

# Racine du projet = dossier parent de backend/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Chemin de la base, surchargeable via ATS_DB_PATH (pratique pour les tests).
DB_PATH = os.environ.get("ATS_DB_PATH", os.path.join(ROOT, "ats.db"))


def get_connection():
    """Connexion SQLite avec lignes accessibles par nom de colonne."""
    conn = sqlite3.connect(os.environ.get("ATS_DB_PATH", DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def dumps(value):
    """Sérialise une liste Python en JSON pour le stockage (None -> None)."""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def loads(value):
    """Désérialise une colonne JSON en liste Python (None/'' -> [])."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []
