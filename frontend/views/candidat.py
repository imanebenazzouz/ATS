"""Espace candidat : CV, offres (avec matching), suivi, chatbot."""
import html

import streamlit as st

import api_client as api
from theme import card, match_chip, progress_bar, reco_badge, skill_pills, status_badge
from views.chatbot import render_chatbot

esc = html.escape


def page_candidat(user):
    st.title(f"Espace candidat — {user['prenom']} {user['nom']}")
    cv = api.get_cv(user["id"])
    if not cv:
        st.info("👋 Bienvenue ! Upload ton **CV** dans l'onglet « Mon CV » pour activer "
                "le matching et trier les offres par pertinence.")

    tab_cv, tab_offres, tab_suivi, tab_chat = st.tabs(
        ["📄 Mon CV", "💼 Offres", "📨 Suivi", "💬 Chatbot LLM"]
    )
    with tab_cv:
        _render_cv_tab(user, cv)
    with tab_offres:
        _render_offres_tab(user, cv)
    with tab_suivi:
        _render_suivi_tab(user)
    with tab_chat:
        render_chatbot(user)


def _render_cv_tab(user, mon_cv):
    with st.form("upload_cv", clear_on_submit=True):
        uploaded = st.file_uploader("Choisis ton CV au format PDF", type="pdf")
        submitted = st.form_submit_button("Analyser mon CV", type="primary", use_container_width=True)
    if submitted:
        if not uploaded:
            st.warning("Sélectionne d'abord un fichier PDF.")
        else:
            with st.spinner("Analyse du CV : extraction → chunking → embeddings…"):
                api.upload_cv(user["id"], uploaded)
            st.toast("CV analysé ✅ — le matching est à jour", icon="✅")
            st.rerun()

    st.divider()
    if not mon_cv:
        st.info("Aucun CV indexé pour le moment.")
        return

    blocs = ""
    if mon_cv.get("experience"):
        blocs += f"<p style='margin-top:14px'><strong>Expérience</strong><br>{esc(mon_cv['experience'])}</p>"
    if mon_cv.get("education"):
        blocs += f"<p><strong>Formation</strong><br>{esc(mon_cv['education'])}</p>"
    st.markdown(card(
        f"<h4>📄 {esc(mon_cv['fichier'])}</h4>"
        f"<p style='color:#94a3b8;margin-top:0'>Uploadé le {esc(mon_cv['date_upload'])} · "
        f"le matching se recalcule automatiquement</p>"
        f"<p><strong>Compétences détectées</strong></p>{skill_pills(mon_cv['skills'])}{blocs}"
    ), unsafe_allow_html=True)


def _render_offres_tab(user, cv):
    offres = api.list_offres(statut="active")
    postulees = {c["offre_id"] for c in api.list_candidatures(candidat_id=user["id"])}

    # Matching automatique CV -> offres : score par offre, tri meilleur d'abord
    score_map = {}
    if cv:
        reco, _ = api.matching_offres(user["id"])
        score_map = {r["offre_id"]: r["score"] for r in (reco or [])}
    else:
        st.info("📄 Upload ton CV pour voir ton **% de correspondance** sur chaque offre.")

    # Filtres
    domaines = ["Tous"] + sorted({o["domaine"] for o in offres if o["domaine"]})
    c1, c2 = st.columns([1, 2])
    dom = c1.selectbox("Domaine", domaines)
    q = c2.text_input("🔎 Rechercher (titre, compétence…)")
    if dom != "Tous":
        offres = [o for o in offres if o["domaine"] == dom]
    if q:
        t = q.lower()
        offres = [o for o in offres if t in o["titre"].lower()
                  or any(t in c.lower() for c in o["competences_requises"])]

    if cv:
        offres = sorted(offres, key=lambda o: -score_map.get(o["id"], 0))
        st.caption(f"{len(offres)} offre(s) — triées par pertinence (matching automatique)")
    else:
        st.caption(f"{len(offres)} offre(s)")
    if not offres:
        st.info("Aucune offre ne correspond à ces critères.")

    # top-3 recommandées (parmi celles non postulées, score significatif)
    reco_ids = {o["id"] for o in offres
                if cv and score_map.get(o["id"], 0) >= 0.15 and o["id"] not in postulees}
    reco_ids = set(list(sorted(reco_ids, key=lambda i: -score_map.get(i, 0)))[:3])

    for offre in offres:
        sc = score_map.get(offre["id"])
        is_reco = offre["id"] in reco_ids
        chip = match_chip(sc) if cv and sc is not None else ""
        ribbon = reco_badge() if is_reco else ""
        st.markdown(card(
            f"<h4>{esc(offre['titre'])} "
            f"<span class='ats-badge badge-pending'>{esc(offre['domaine'] or '')}</span> {chip} {ribbon}</h4>"
            f"<p style='color:#94a3b8;margin-top:0'>{esc(offre['entreprise'] or '')} — publié le {esc(offre['date_publication'])}</p>"
            f"<p>{esc(offre['description'] or '')}</p>{skill_pills(offre['competences_requises'])}",
            extra_class="reco" if is_reco else "",
        ), unsafe_allow_html=True)
        if offre["id"] in postulees:
            st.success("✓ Déjà postulé", icon="✅")
        elif st.button("Postuler", key=f"post_{offre['id']}", type="primary"):
            _, err = api.create_candidature(user["id"], offre["id"])
            st.toast(err or "Candidature envoyée 🎉", icon="⚠️" if err else "🎉")
            st.rerun()


def _render_suivi_tab(user):
    cands = api.list_candidatures(candidat_id=user["id"])
    if not cands:
        st.info("Tu n'as pas encore postulé. Va dans l'onglet « Offres » 💼")
        return
    st.caption(f"{len(cands)} candidature(s)")
    offres = {o["id"]: o for o in api.list_offres()}
    for c in sorted(cands, key=lambda c: c["date"], reverse=True):
        offre = offres.get(c["offre_id"])
        if not offre:
            continue
        reponse = ""
        if c["statut"] != "en_attente":
            msg = f" : « {esc(c['message_recruteur'])} »" if c.get("message_recruteur") else ""
            reponse = (f"<p style='margin-top:10px;color:#475569'>Réponse du recruteur le "
                       f"{esc(c.get('date_reponse') or '—')}{msg}</p>")
        st.markdown(card(
            f"<h4>{esc(offre['titre'])} <span style='font-weight:400;color:#94a3b8'>— {esc(offre['entreprise'] or '')}</span></h4>"
            f"<p style='color:#94a3b8;margin-top:0'>Envoyée le {esc(c['date'])}</p>"
            f"{status_badge(c['statut'])}{progress_bar(c['score_matching'])}{reponse}"
        ), unsafe_allow_html=True)
