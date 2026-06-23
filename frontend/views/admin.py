"""Espace admin : utilisateurs, modération des offres, statistiques."""
import html

import streamlit as st

import api_client as api
from theme import avatar, status_badge

esc = html.escape


def page_admin(user):
    st.title("Espace administrateur")
    tab_users, tab_offres, tab_stats = st.tabs(["Utilisateurs", "Modérer les offres", "Statistiques"])

    with tab_users:
        _render_users_tab(user)

    with tab_offres:
        _render_offres_tab()

    with tab_stats:
        _render_stats_tab()


def _render_users_tab(current_user):
    for u in api.list_users():
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.markdown(f"{avatar(u['prenom'], u['nom'])}**{esc(u['prenom'])} {esc(u['nom'])}**  \n"
                          f"<span style='color:#888;font-size:0.85rem'>{esc(u['email'])}</span>",
                          unsafe_allow_html=True)
            new_role = col2.selectbox("Rôle", ["candidat", "recruteur", "admin"],
                                       index=["candidat", "recruteur", "admin"].index(u["role"]),
                                       key=f"role_{u['id']}", label_visibility="collapsed")
            if new_role != u["role"]:
                api.update_user_role(u["id"], new_role)
                st.rerun()
            if u["id"] != current_user["id"] and col3.button("Supprimer", key=f"del_user_{u['id']}"):
                api.delete_user(u["id"])
                st.rerun()


def _render_offres_tab():
    for offre in api.list_offres():
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.markdown(f"**{esc(offre['titre'])}** — {esc(offre['entreprise'] or '')} {status_badge(offre['statut'])}",
                          unsafe_allow_html=True)
            if offre["statut"] != "active" and col2.button("Valider", key=f"valider_{offre['id']}"):
                api.set_offre_statut(offre["id"], "active")
                st.rerun()
            if col3.button("Supprimer", key=f"del_offre_{offre['id']}"):
                api.delete_offre(offre["id"])
                st.rerun()


def _render_stats_tab():
    s = api.get_stats()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Candidats", s["nb_candidats"])
    col2.metric("Recruteurs", s["nb_recruteurs"])
    col3.metric("Offres publiées", s["nb_offres"])
    col4.metric("Candidatures", s["nb_candidatures"])
    col5.metric("Score moyen", f"{s['score_moyen_matching']*100:.0f}%")
