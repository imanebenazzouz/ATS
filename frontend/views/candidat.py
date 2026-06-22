"""Espace candidat : CV, offres, candidatures, chatbot."""
import streamlit as st
from datetime import datetime
from theme import skill_pills, status_badge, progress_bar
from views.chatbot import render_chatbot


def page_candidat(user):
    st.title(f"Espace candidat — {user['prenom']} {user['nom']}")
    tab_cv, tab_offres, tab_candidatures, tab_chat = st.tabs(
        ["Mon CV", "Offres", "Mes candidatures", "Chatbot LLM"]
    )

    with tab_cv:
        _render_cv_tab(user)

    with tab_offres:
        _render_offres_tab(user)

    with tab_candidatures:
        _render_candidatures_tab(user)

    with tab_chat:
        render_chatbot(user)


def _render_cv_tab(user):
    mon_cv = next((c for c in st.session_state.cvs if c["candidat_id"] == user["id"]), None)
    uploaded = st.file_uploader("Uploader mon CV (PDF)", type="pdf")
    if uploaded and st.button("Analyser le CV", type="primary"):
        st.session_state.cvs = [c for c in st.session_state.cvs if c["candidat_id"] != user["id"]]
        st.session_state.cvs.append({
            "id": len(st.session_state.cvs) + 1, "candidat_id": user["id"], "fichier": uploaded.name,
            "skills": ["Python", "NLP", "Docker"], "experience": "Expérience extraite (simulation)",
            "education": "Formation extraite (simulation)",
            "date_upload": datetime.now().strftime("%Y-%m-%d"),
        })
        st.success("CV analysé : extraction → chunking → embeddings → stockage (simulé)")
        st.rerun()

    if mon_cv:
        st.markdown(f"""
        <div class="ats-card">
            <h4>{mon_cv['fichier']}</h4>
            <p style="color:#888; margin-top:0;">Uploadé le {mon_cv['date_upload']}</p>
            <p><strong>Compétences détectées</strong></p>
            {skill_pills(mon_cv['skills'])}
            <p style="margin-top:14px;"><strong>Expérience</strong><br>{mon_cv['experience']}</p>
            <p><strong>Formation</strong><br>{mon_cv['education']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Aucun CV indexé pour le moment.")


def _render_offres_tab(user):
    for offre in st.session_state.offres:
        if offre["statut"] != "active":
            continue
        st.markdown(f"""
        <div class="ats-card">
            <h4>{offre['titre']}</h4>
            <p style="color:#888; margin-top:0;">{offre['entreprise']} — publié le {offre['date_publication']}</p>
            <p>{offre['description']}</p>
            {skill_pills(offre['competences_requises'])}
        </div>
        """, unsafe_allow_html=True)
        deja_postule = any(c["candidat_id"] == user["id"] and c["offre_id"] == offre["id"]
                            for c in st.session_state.candidatures)
        if deja_postule:
            st.success("Déjà postulé")
        elif st.button("Postuler", key=f"postuler_{offre['id']}", type="primary"):
            mon_cv = next((c for c in st.session_state.cvs if c["candidat_id"] == user["id"]), None)
            score = 0.0
            if mon_cv:
                communes = set(mon_cv["skills"]) & set(offre["competences_requises"])
                score = round(len(communes) / max(len(offre["competences_requises"]), 1), 2)
            st.session_state.candidatures.append({
                "id": st.session_state.next_candidature_id, "candidat_id": user["id"],
                "offre_id": offre["id"], "date": datetime.now().strftime("%Y-%m-%d"),
                "statut": "en attente", "score_matching": score,
            })
            st.session_state.next_candidature_id += 1
            st.success("Candidature envoyée !")
            st.rerun()


def _render_candidatures_tab(user):
    mes_candidatures = [c for c in st.session_state.candidatures if c["candidat_id"] == user["id"]]
    if not mes_candidatures:
        st.info("Aucune candidature pour le moment.")
    for c in mes_candidatures:
        offre = next(o for o in st.session_state.offres if o["id"] == c["offre_id"])
        st.markdown(f"""
        <div class="ats-card">
            <h4>{offre['titre']} <span style="font-weight:400; color:#888;">— {offre['entreprise']}</span></h4>
            {status_badge(c['statut'])}
            {progress_bar(c['score_matching'])}
        </div>
        """, unsafe_allow_html=True)
