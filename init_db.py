import sqlite3
import os

DB_PATH = os.environ.get("ATS_DB_PATH", os.path.join(os.path.dirname(__file__), "ats.db"))


def init_db(db_path=None):
    db_path = db_path or os.environ.get("ATS_DB_PATH", DB_PATH)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        PRAGMA foreign_keys = ON;

        -- Utilisateurs (Candidat, Recruteur, Admin)
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            role            TEXT NOT NULL CHECK(role IN ('candidat', 'recruteur', 'admin')),
            nom             TEXT NOT NULL,
            prenom          TEXT NOT NULL,
            entreprise      TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- CV des candidats
        -- texte_brut = sortie de l'extraction PDF (Lot B). skills/experience/education
        -- sont remplis pour l'instant par des valeurs placeholder ; le pipeline IA (Lot B)
        -- les renseignera à partir du chunking sémantique.
        CREATE TABLE IF NOT EXISTS cvs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            candidat_id     INTEGER NOT NULL,
            fichier_path    TEXT NOT NULL,
            texte_brut      TEXT,
            skills          TEXT,          -- JSON: liste de compétences
            experience      TEXT,
            education       TEXT,
            date_upload     DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidat_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Offres publiées par les recruteurs
        CREATE TABLE IF NOT EXISTS offres (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            recruteur_id        INTEGER NOT NULL,
            titre               TEXT NOT NULL,
            domaine             TEXT,
            description         TEXT,
            competences_requises TEXT,     -- JSON: liste de compétences
            statut              TEXT DEFAULT 'active' CHECK(statut IN ('active', 'inactive')),
            date_publication    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recruteur_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Chunks sémantiques (CV ou Offre) — rempli par le pipeline IA (Lot B)
        CREATE TABLE IF NOT EXISTS chunks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cv_id           INTEGER,
            offre_id        INTEGER,
            source          TEXT NOT NULL CHECK(source IN ('cv', 'offre')),
            type_section    TEXT NOT NULL,
            contenu         TEXT NOT NULL,
            embedding       BLOB,
            FOREIGN KEY (cv_id)    REFERENCES cvs(id)    ON DELETE CASCADE,
            FOREIGN KEY (offre_id) REFERENCES offres(id) ON DELETE CASCADE
        );

        -- Candidatures
        CREATE TABLE IF NOT EXISTS candidatures (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            candidat_id     INTEGER NOT NULL,
            offre_id        INTEGER NOT NULL,
            date            DATETIME DEFAULT CURRENT_TIMESTAMP,
            statut          TEXT DEFAULT 'en attente' CHECK(statut IN ('en attente', 'acceptée', 'refusée')),
            score_matching  REAL,
            message_recruteur TEXT,
            date_reponse    TEXT,
            FOREIGN KEY (candidat_id) REFERENCES users(id)   ON DELETE CASCADE,
            FOREIGN KEY (offre_id)    REFERENCES offres(id)  ON DELETE CASCADE,
            UNIQUE (candidat_id, offre_id)
        );

        -- Résultats de matching IA (rempli par le Lot B / Lot C)
        CREATE TABLE IF NOT EXISTS matching_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            candidat_id     INTEGER NOT NULL,
            offre_id        INTEGER NOT NULL,
            score           REAL NOT NULL,
            explication_llm TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidat_id) REFERENCES users(id)   ON DELETE CASCADE,
            FOREIGN KEY (offre_id)    REFERENCES offres(id)  ON DELETE CASCADE
        );

        -- Sessions chatbot (Candidat ou Recruteur)
        CREATE TABLE IF NOT EXISTS chatbot_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            role_user       TEXT NOT NULL CHECK(role_user IN ('candidat', 'recruteur')),
            date_creation   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Messages LLM dans une session chatbot
        CREATE TABLE IF NOT EXISTS conseils_llm (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER NOT NULL,
            question        TEXT NOT NULL,
            reponse_llm     TEXT NOT NULL,
            timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chatbot_sessions(id) ON DELETE CASCADE
        );

        -- Statistiques globales (générées par l'admin)
        CREATE TABLE IF NOT EXISTS statistiques (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nb_candidats        INTEGER DEFAULT 0,
            nb_recruteurs       INTEGER DEFAULT 0,
            nb_offres           INTEGER DEFAULT 0,
            nb_candidatures     INTEGER DEFAULT 0,
            score_moyen_matching REAL DEFAULT 0.0,
            date_calcul         DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print(f"Base de données initialisée : {db_path}")


if __name__ == "__main__":
    init_db()
