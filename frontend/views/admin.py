"""Espace admin : utilisateurs, modération des offres, statistiques."""
import streamlit as st
from theme import status_badge, avatar


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
    for u in st.session_state.users:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.markdown(f"{avatar(u['prenom'], u['nom'])}**{u['prenom']} {u['nom']}**  \n"
                          f"<span style='color:#888;font-size:0.85rem'>{u['email']}</span>",
                          unsafe_allow_html=True)
            new_role = col2.selectbox("Rôle", ["candidat", "recruteur", "admin"],
                                       index=["candidat", "recruteur", "admin"].index(u["role"]),
                                       key=f"role_{u['id']}", label_visibility="collapsed")
            if new_role != u["role"]:
                u["role"] = new_role
                st.rerun()
            if u["id"] != current_user["id"] and col3.button("Supprimer", key=f"del_user_{u['id']}"):
                st.session_state.users.remove(u)
                st.rerun()


def _render_offres_tab():
    for offre in st.session_state.offres:
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.markdown(f"**{offre['titre']}** — {offre['entreprise']} {status_badge(offre['statut'])}",
                          unsafe_allow_html=True)
            if offre["statut"] != "active" and col2.button("Valider", key=f"valider_{offre['id']}"):
                offre["statut"] = "active"
                st.rerun()
            if col3.button("Supprimer", key=f"del_offre_{offre['id']}"):
                st.session_state.offres.remove(offre)
                st.rerun()


def _render_stats_tab():
    nb_candidats = sum(1 for u in st.session_state.users if u["role"] == "candidat")
    nb_recruteurs = sum(1 for u in st.session_state.users if u["role"] == "recruteur")
    nb_offres = len(st.session_state.offres)
    nb_candidatures = len(st.session_state.candidatures)
    score_moyen = (sum(c["score_matching"] for c in st.session_state.candidatures) / nb_candidatures
                   if nb_candidatures else 0)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Candidats", nb_candidats)
    col2.metric("Recruteurs", nb_recruteurs)
    col3.metric("Offres publiées", nb_offres)
    col4.metric("Candidatures", nb_candidatures)
    col5.metric("Score moyen", f"{score_moyen*100:.0f}%")
