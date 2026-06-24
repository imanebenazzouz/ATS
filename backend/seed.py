"""Peuple la base avec les comptes et offres de démonstration.

Reprend exactement les données qui étaient mockées dans `frontend/mock_data.py`
pour que la démo (comptes de test, offres, candidature) fonctionne à l'identique
une fois le front branché sur l'API. Idempotent : ne réinsère pas si déjà présent.

Usage :  python -m backend.seed   (après init_db.py)
"""
from werkzeug.security import generate_password_hash

from backend.db import dumps, get_connection

USERS = [
    ("candidat@test.com", "candidat", "Dupont", "Alice", None),
    ("rec@test.com", "recruteur", "Martin", "Bob", "TechCorp"),
    ("admin@ats.com", "admin", "Admin", "Super", None),
]

CV_JOHN = {
    "skills": ["Python", "Flask", "Docker", "NLP"],
    "experience": "2 ans backend developer chez XYZ",
    "education": "Master en Intelligence Artificielle",
    "date_upload": "2026-06-10",
}

OFFRES = [
    ("Data Engineer", "Tech", "Recherche data engineer pour pipeline ML.",
     ["Python", "Docker", "SQL"], "2026-06-05"),
    ("Développeur Backend", "Tech", "Développement d'API REST avec Flask.",
     ["Python", "Flask", "PostgreSQL"], "2026-06-12"),
    ("Chargé(e) de marketing digital", "Marketing",
     "Pilotage des campagnes d'acquisition et gestion des réseaux sociaux.",
     ["SEO", "Google Ads", "Réseaux sociaux"], "2026-06-14"),
    ("Contrôleur de gestion", "Finance", "Suivi budgétaire et reporting financier mensuel.",
     ["Excel", "SAP", "Comptabilité"], "2026-06-16"),
    ("UI/UX Designer", "Design",
     "Conception des interfaces et tests utilisateurs pour l'app mobile.",
     ["Figma", "UX Research", "Prototypage"], "2026-06-17"),
    ("Chargé(e) de recrutement", "Ressources Humaines",
     "Sourcing et suivi des candidatures pour les équipes tech.",
     ["Sourcing", "Entretiens", "ATS"], "2026-06-18"),
    ("Business Developer", "Vente", "Prospection et développement du portefeuille clients B2B.",
     ["Prospection", "Négociation", "CRM"], "2026-06-19"),
]


def seed():
    conn = get_connection()

    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        print("Base déjà peuplée — rien à faire.")
        conn.close()
        return

    pwd = generate_password_hash("1234")
    for email, role, nom, prenom, entreprise in USERS:
        conn.execute(
            """INSERT INTO users (email, password_hash, role, nom, prenom, entreprise)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (email, pwd, role, nom, prenom, entreprise),
        )

    candidat_id = conn.execute("SELECT id FROM users WHERE email = 'candidat@test.com'").fetchone()[0]
    recruteur_id = conn.execute("SELECT id FROM users WHERE email = 'rec@test.com'").fetchone()[0]

    conn.execute(
        """INSERT INTO cvs (candidat_id, fichier_path, skills, experience, education, date_upload)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (candidat_id, "cv_john_doe.pdf", dumps(CV_JOHN["skills"]),
         CV_JOHN["experience"], CV_JOHN["education"], CV_JOHN["date_upload"]),
    )

    for titre, domaine, description, comps, date_pub in OFFRES:
        conn.execute(
            """INSERT INTO offres (recruteur_id, titre, domaine, description,
                                   competences_requises, statut, date_publication)
               VALUES (?, ?, ?, ?, ?, 'active', ?)""",
            (recruteur_id, titre, domaine, description, dumps(comps), date_pub),
        )

    # candidature de démo : John -> Data Engineer
    offre_de = conn.execute("SELECT id FROM offres WHERE titre = 'Data Engineer'").fetchone()[0]
    conn.execute(
        """INSERT INTO candidatures (candidat_id, offre_id, date, statut, score_matching)
           VALUES (?, ?, '2026-06-15', 'en_attente', 0.82)""",
        (candidat_id, offre_de),
    )

    conn.commit()
    conn.close()
    print("Données de démonstration insérées.")


if __name__ == "__main__":
    seed()
