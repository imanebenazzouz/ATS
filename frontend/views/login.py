"""Page de connexion / inscription."""
import streamlit as st

import api_client as api


def page_login():
    st.markdown("""
    <div class="ats-hero">
        <h1>ATS Intelligent</h1>
        <p>SaaS RH + Copilote LLM</p>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        tab_login, tab_register = st.tabs(["Se connecter", "Créer un compte"])
        with tab_login:
            _render_login()
        with tab_register:
            _render_register()


def _render_login():
    with st.form("login", clear_on_submit=False):
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        st.caption("Comptes de démo : candidat@test.com / rec@test.com / admin@ats.com — mdp `1234`")
        ok = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
    if ok:
        user = api.login(email.strip(), password)
        if user:
            st.session_state.current_user_id = user["id"]
            st.rerun()
        else:
            st.error("Email ou mot de passe incorrect.")


def _render_register():
    with st.form("register", clear_on_submit=False):
        col1, col2 = st.columns(2)
        nom = col1.text_input("Nom")
        prenom = col2.text_input("Prénom")
        new_email = st.text_input("Email")
        new_password = st.text_input("Mot de passe", type="password")
        ok = st.form_submit_button("Créer le compte", use_container_width=True, type="primary")
    if ok:
        if not all([nom.strip(), prenom.strip(), new_email.strip(), new_password]):
            st.warning("Merci de remplir tous les champs obligatoires.")
        elif len(new_password) < 4:
            st.warning("Le mot de passe doit faire au moins 4 caractères.")
        else:
            user, error = api.register(nom.strip(), prenom.strip(), new_email.strip(),
                                       new_password, "candidat", None)
            if user:
                st.success("Compte créé ! Connecte-toi via l'onglet « Se connecter ».")
            else:
                st.error(error)
