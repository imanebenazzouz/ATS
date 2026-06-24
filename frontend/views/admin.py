"""Espace admin : utilisateurs, modération des offres, statistiques."""
import html

import streamlit as st

import api_client as api
from theme import avatar, status_badge

esc = html.escape
ROLES = ["candidat", "recruteur", "admin"]


def page_admin(user):
    st.title("Espace administrateur")
    tab_users, tab_offres, tab_stats = st.tabs(
        ["👥 Utilisateurs", "🛡️ Modération", "📊 Statistiques"]
    )
    with tab_users:
        _render_users_tab(user)
    with tab_offres:
        _render_offres_tab()
    with tab_stats:
        _render_stats_tab()


def _confirm_delete(label, key, on_confirm):
    """Bouton de suppression avec confirmation (popover) pour éviter les clics accidentels."""
    with st.popover(label, use_container_width=True):
        st.write("Confirmer la suppression ? Cette action est définitive.")
        if st.button("Oui, supprimer", key=key, type="primary"):
            on_confirm()
            st.rerun()


def _render_users_tab(current_user):
    users = api.list_users()
    st.caption(f"{len(users)} utilisateur(s)")
    for u in users:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.markdown(f"{avatar(u['prenom'], u['nom'])}**{esc(u['prenom'])} {esc(u['nom'])}**  \n"
                        f"<span style='color:#64748b;font-size:0.85rem'>{esc(u['email'])}</span>",
                        unsafe_allow_html=True)
            new_role = c2.selectbox("Rôle", ROLES, index=ROLES.index(u["role"]),
                                    key=f"role_{u['id']}", label_visibility="collapsed")
            if new_role != u["role"]:
                api.update_user_role(u["id"], new_role)
                st.toast(f"Rôle de {u['prenom']} → {new_role}", icon="🔁")
                st.rerun()
            if u["id"] == current_user["id"]:
                c3.caption("(toi)")
            else:
                with c3:
                    _confirm_delete("🗑️", f"del_u_{u['id']}",
                                    lambda uid=u["id"]: (api.delete_user(uid),
                                                         st.toast("Utilisateur supprimé", icon="🗑️")))


def _render_offres_tab():
    offres = api.list_offres()
    st.caption(f"{len(offres)} offre(s)")
    if not offres:
        st.info("Aucune offre.")
    for offre in offres:
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.markdown(f"**{esc(offre['titre'])}** — {esc(offre['entreprise'] or '')} "
                        f"{status_badge(offre['statut'])}", unsafe_allow_html=True)
            if offre["statut"] != "active":
                if c2.button("Valider", key=f"val_{offre['id']}", type="primary"):
                    api.set_offre_statut(offre["id"], "active")
                    st.toast("Offre validée", icon="✅")
                    st.rerun()
            else:
                if c2.button("Désactiver", key=f"off_{offre['id']}"):
                    api.set_offre_statut(offre["id"], "inactive")
                    st.toast("Offre désactivée", icon="⏸️")
                    st.rerun()
            with c3:
                _confirm_delete("🗑️", f"del_o_{offre['id']}",
                                lambda oid=offre["id"]: (api.delete_offre(oid),
                                                         st.toast("Offre supprimée", icon="🗑️")))


def _render_stats_tab():
    s = api.get_stats()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Candidats", s["nb_candidats"])
    c2.metric("Recruteurs", s["nb_recruteurs"])
    c3.metric("Offres", s["nb_offres"])
    c4.metric("Candidatures", s["nb_candidatures"])
    c5.metric("Score moyen", f"{s['score_moyen_matching']*100:.0f}%")
    if st.button("🔄 Rafraîchir"):
        st.rerun()
