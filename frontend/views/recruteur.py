"""Espace recruteur : offres, résultats de matching, recherche IA, chatbot."""
import html

import streamlit as st

import api_client as api
from theme import avatar, card, match_chip, progress_bar, skill_pills, status_badge
from views.chatbot import render_chatbot

esc = html.escape
DOMAINES = ["Tech", "Marketing", "Finance", "Design", "Ressources Humaines", "Vente"]


def page_recruteur(user):
    st.title(f"Espace recruteur — {user['entreprise']}")
    tab_offres, tab_match, tab_search, tab_chat = st.tabs(
        ["💼 Mes offres", "🎯 Matching", "🤖 Recherche IA", "💬 Chatbot LLM"]
    )
    with tab_offres:
        _render_offres_tab(user)
    with tab_match:
        _render_matching_tab(user)
    with tab_search:
        _render_search_tab()
    with tab_chat:
        render_chatbot(user)


def _render_offres_tab(user):
    with st.expander("➕ Publier une nouvelle offre"):
        with st.form("new_offre", clear_on_submit=True):
            titre = st.text_input("Titre du poste *")
            domaine = st.selectbox("Domaine", DOMAINES)
            description = st.text_area("Description")
            competences = st.text_input("Compétences requises (séparées par des virgules)")
            ok = st.form_submit_button("Publier l'offre", type="primary", use_container_width=True)
        if ok:
            if not titre.strip():
                st.warning("Le titre est obligatoire.")
            else:
                api.create_offre(user["id"], titre.strip(), domaine, description.strip(),
                                 [c.strip() for c in competences.split(",") if c.strip()])
                st.toast("Offre publiée ✅", icon="✅")
                st.rerun()

    offres = api.list_offres(recruteur_id=user["id"])
    st.caption(f"{len(offres)} offre(s) publiée(s)")
    if not offres:
        st.info("Tu n'as pas encore publié d'offre.")
    for offre in sorted(offres, key=lambda o: o["date_publication"], reverse=True):  # récentes en haut
        st.markdown(card(
            f"<h4>{esc(offre['titre'])} {status_badge(offre['statut'])}</h4>"
            f"<p style='color:#94a3b8;margin-top:0'>{esc(offre['domaine'] or '')} — publié le {esc(offre['date_publication'])}</p>"
            f"<p>{esc(offre['description'] or '')}</p>{skill_pills(offre['competences_requises'])}"
        ), unsafe_allow_html=True)


def _render_matching_tab(user):
    offres = api.list_offres(recruteur_id=user["id"])
    if not offres:
        st.info("Publie d'abord une offre pour voir les candidats.")
        return
    offre = st.selectbox("Offre à analyser", offres, format_func=lambda o: o["titre"])
    if not offre:
        return

    cands = api.list_candidatures(offre_id=offre["id"])
    st.caption(f"{len(cands)} candidature(s) — score de matching calculé automatiquement (cosinus), meilleur en haut")
    if not cands:
        st.info("Aucune candidature pour cette offre.")
        return

    for c in sorted(cands, key=lambda c: -(c["score_matching"] or 0)):  # meilleur score en haut
        candidat = api.get_user(c["candidat_id"])
        cv = api.get_cv(c["candidat_id"])
        st.markdown(card(
            f"<h4>{avatar(candidat['prenom'], candidat['nom'])}{esc(candidat['prenom'])} {esc(candidat['nom'])} "
            f"{match_chip(c['score_matching'])} {status_badge(c['statut'])}</h4>{progress_bar(c['score_matching'])}"
        ), unsafe_allow_html=True)
        if cv:
            with st.expander("🤖 Explication du matching (LLM)"):
                cache_key = f"explain_{c['candidat_id']}_{offre['id']}"
                if cache_key not in st.session_state:
                    if st.button("Générer l'explication", key=f"btn_{cache_key}"):
                        with st.spinner("Le copilote analyse le profil..."):
                            explication, error = api.explain_match(c["candidat_id"], offre["id"])
                        st.session_state[cache_key] = explication or f"Erreur : {error}"
                        st.rerun()
                else:
                    st.write(st.session_state[cache_key])

        if c["statut"] == "en attente":
            with st.form(f"rep_{c['id']}", clear_on_submit=True):
                message = st.text_input("Message au candidat (optionnel)")
                col1, col2 = st.columns(2)
                acc = col1.form_submit_button("✅ Accepter", type="primary", use_container_width=True)
                ref = col2.form_submit_button("✕ Refuser", use_container_width=True)
                if acc or ref:
                    api.respond_candidature(c["id"], "acceptée" if acc else "refusée", message.strip())
                    st.toast("Réponse envoyée", icon="📨")
                    st.rerun()
        else:
            msg = f" : « {esc(c['message_recruteur'])} »" if c.get("message_recruteur") else ""
            st.caption(f"Réponse envoyée le {c.get('date_reponse') or '—'}{msg}")
        st.divider()


def _render_search_tab():
    st.caption("Décris le profil recherché en langage naturel — l'IA classe les candidats par pertinence sémantique.")
    query = st.text_input("Ex : « data engineer Python et Docker »", key="search_ia")
    if not query:
        return
    with st.spinner("Recherche sémantique…"):
        results, err = api.search_candidats(query)
    if err:
        st.warning(err)
        return
    if not results:
        st.info("Aucun candidat indexé ne correspond.")
        return
    st.caption(f"{len(results)} candidat(s) trouvé(s) — parmi **tous** les candidats inscrits (pas seulement ceux qui ont postulé)")
    for r in results:
        st.markdown(card(
            f"<h4>{avatar(r.get('prenom') or '', r.get('nom') or '')}{esc(r.get('prenom') or '')} {esc(r.get('nom') or '')} "
            f"{match_chip(r['score'])}</h4>{progress_bar(r['score'])}"
        ), unsafe_allow_html=True)
