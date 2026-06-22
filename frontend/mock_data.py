"""Données mockées en session_state — remplace le backend Flask en attendant qu'il soit codé."""
import streamlit as st
from datetime import datetime


def init_mock_data():
    if "users" in st.session_state:
        return

    st.session_state.users = [
        {"id": 1, "email": "candidat@test.com", "password": "1234", "role": "candidat",
         "nom": "Doe", "prenom": "John", "entreprise": None},
        {"id": 2, "email": "rh@test.com", "password": "1234", "role": "recruteur",
         "nom": "Martin", "prenom": "Alice", "entreprise": "TechCorp"},
        {"id": 3, "email": "admin@test.com", "password": "1234", "role": "admin",
         "nom": "Admin", "prenom": "Super", "entreprise": None},
    ]
    st.session_state.next_user_id = 4

    st.session_state.cvs = [
        {"id": 1, "candidat_id": 1, "fichier": "cv_john_doe.pdf",
         "skills": ["Python", "Flask", "Docker", "NLP"],
         "experience": "2 ans backend developer chez XYZ",
         "education": "Master en Intelligence Artificielle",
         "date_upload": "2026-06-10"},
    ]

    st.session_state.offres = [
        {"id": 1, "recruteur_id": 2, "titre": "Data Engineer", "entreprise": "TechCorp",
         "description": "Recherche data engineer pour pipeline ML.",
         "competences_requises": ["Python", "Docker", "SQL"],
         "statut": "active", "date_publication": "2026-06-05"},
        {"id": 2, "recruteur_id": 2, "titre": "Développeur Backend", "entreprise": "TechCorp",
         "description": "Développement d'API REST avec Flask.",
         "competences_requises": ["Python", "Flask", "PostgreSQL"],
         "statut": "active", "date_publication": "2026-06-12"},
    ]
    st.session_state.next_offre_id = 3

    st.session_state.candidatures = [
        {"id": 1, "candidat_id": 1, "offre_id": 1, "date": "2026-06-15",
         "statut": "en attente", "score_matching": 0.82},
    ]
    st.session_state.next_candidature_id = 2

    st.session_state.chatbot_history = {}  # user_id -> [{role, content}]


def get_user(user_id):
    return next(u for u in st.session_state.users if u["id"] == user_id)


def mock_llm_explanation(candidat_skills, offre_competences):
    communes = set(candidat_skills) & set(offre_competences)
    lignes = [f"- {c} (match élevé)" for c in communes]
    manquantes = set(offre_competences) - set(candidat_skills)
    if manquantes:
        lignes.append(f"- Compétences manquantes : {', '.join(manquantes)}")
    score = len(communes) / max(len(offre_competences), 1)
    niveau = "fort" if score > 0.6 else "moyen" if score > 0.3 else "faible"
    return f"Ce candidat correspond de manière {niveau} au poste :\n" + "\n".join(lignes)


def mock_llm_chat_reply(question: str, role: str) -> str:
    if role == "candidat":
        return (f"(Réponse simulée du LLM copilote) D'après ton CV, je te conseille de mettre en avant "
                f"tes compétences techniques en lien avec : « {question} ». Pense à quantifier ton expérience.")
    return (f"(Réponse simulée du LLM copilote) Pour ta recherche « {question} », je te recommande "
            f"de filtrer les candidats par compétences techniques précises plutôt que par intitulé de poste.")
