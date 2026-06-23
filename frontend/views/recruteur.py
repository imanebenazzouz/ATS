"""Espace recruteur : offres, résultats de matching, chatbot."""
import html

import streamlit as st

import api_client as api
from mock_data import mock_llm_explanation
from theme import avatar, progress_bar, skill_pills, status_badge
from views.chatbot import render_chatbot

esc = html.escape


def page_recruteur(user):
    st.title(f"Espace recruteur — {user['entreprise']}")
    tab_offres, tab_candidats, tab_search, tab_chat = st.tabs(
        ["Mes offres", "Résultats de matching", "Recherche IA", "Chatbot LLM"]
    )

    with tab_offres:
        _render_offres_tab(user)

    with tab_candidats:
        _render_matching_tab(user)

    with tab_search:
        _render_search_tab()

    with tab_chat:
        render_chatbot(user)


def _render_search_tab():
    st.caption("Recherche sémantique : décris le profil recherché en langage naturel.")
    query = st.text_input("Ex : « data engineer Python et Docker »", key="search_ia")
    if not query:
        return
    resultats, error = api.search_candidats(query)
    if error:
        st.warning(error)
        return
    if not resultats:
        st.info("Aucun candidat indexé pour le moment.")
    for r in resultats:
        st.markdown(f"""
        <div class="ats-card">
            <h4>{avatar(r.get('prenom') or '', r.get('nom') or '')}{esc(r.get('prenom') or '')} {esc(r.get('nom') or '')}</h4>
            {progress_bar(r['score'])}
        </div>
        """, unsafe_allow_html=True)


def _render_offres_tab(user):
    with st.expander("Publier une nouvelle offre"):
        titre = st.text_input("Titre du poste", key="offre_titre")
        domaine = st.selectbox(
            "Domaine", ["Tech", "Marketing", "Finance", "Design", "Ressources Humaines", "Vente"],
            key="offre_domaine",
        )
        description = st.text_area("Description", key="offre_description")
        competences = st.text_input("Compétences requises (séparées par des virgules)", key="offre_competences")
        if st.button("Publier l'offre", type="primary"):
            api.create_offre(
                user["id"], titre, domaine, description,
                [c.strip() for c in competences.split(",") if c.strip()],
            )
            st.success("Offre publiée !")
            st.rerun()

    mes_offres = api.list_offres(recruteur_id=user["id"])
    for offre in mes_offres:
        st.markdown(f"""
        <div class="ats-card">
            <h4>{esc(offre['titre'])} {status_badge(offre['statut'])}</h4>
            <p style="color:#888; margin-top:0;">{esc(offre['domaine'] or '')}</p>
            <p>{esc(offre['description'] or '')}</p>
            {skill_pills(offre['competences_requises'])}
        </div>
        """, unsafe_allow_html=True)


def _render_matching_tab(user):
    mes_offres = api.list_offres(recruteur_id=user["id"])
    offre_choisie = st.selectbox(
        "Choisir une offre", mes_offres, format_func=lambda o: o["titre"]
    ) if mes_offres else None

    if not offre_choisie:
        return

    candidatures = api.list_candidatures(offre_id=offre_choisie["id"])
    if not candidatures:
        st.info("Aucune candidature pour cette offre.")
    for c in sorted(candidatures, key=lambda c: -c["score_matching"]):
        candidat = api.get_user(c["candidat_id"])
        cv = api.get_cv(c["candidat_id"])
        st.markdown(f"""
        <div class="ats-card">
            <h4>{avatar(candidat['prenom'], candidat['nom'])}{esc(candidat['prenom'])} {esc(candidat['nom'])} {status_badge(c['statut'])}</h4>
            {progress_bar(c['score_matching'])}
        </div>
        """, unsafe_allow_html=True)
        if cv:
            with st.expander("Voir l'explication du LLM"):
                st.write(mock_llm_explanation(cv["skills"], offre_choisie["competences_requises"]))

        if c["statut"] == "en attente":
            with st.form(key=f"reponse_form_{c['id']}"):
                message = st.text_input("Message au candidat (optionnel)", key=f"msg_{c['id']}")
                col1, col2 = st.columns(2)
                accepter = col1.form_submit_button("Accepter", type="primary", use_container_width=True)
                refuser = col2.form_submit_button("Refuser", use_container_width=True)
                if accepter or refuser:
                    api.respond_candidature(c["id"], "acceptée" if accepter else "refusée", message)
                    st.rerun()
        else:
            st.caption(f"Réponse envoyée le {c.get('date_reponse') or '—'}"
                       + (f" : « {c['message_recruteur']} »" if c.get("message_recruteur") else ""))
