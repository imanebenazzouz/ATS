"""Ce qui reste simulé en attendant le Lot C (LLM copilote).

Les données (users, CV, offres, candidatures) viennent désormais de l'API Flask
via `api_client.py`. Ne restent ici que les réponses LLM mockées et l'état local
du chat — le Lot C les remplacera par un vrai modèle + la persistance en base.
"""
import streamlit as st


def init_session_state():
    """Initialise l'état local non persisté (historique de chat en mémoire)."""
    if "chatbot_history" not in st.session_state:
        st.session_state.chatbot_history = {}  # user_id -> [{role, content}]


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
