"""Page de connexion / inscription."""
import streamlit as st


def page_login():
    st.markdown("""
    <div class="ats-hero">
        <h1>ATS Intelligent</h1>
        <p>SaaS RH + Copilote LLM — maquette frontend (données mockées)</p>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        tab_login, tab_register = st.tabs(["Se connecter", "Créer un compte"])

        with tab_login:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Mot de passe", type="password", key="login_password")
            st.caption("Comptes de démo : candidat@test.com / rh@test.com / admin@test.com — mdp `1234`")
            if st.button("Se connecter", use_container_width=True, type="primary"):
                user = next((u for u in st.session_state.users
                             if u["email"] == email and u["password"] == password), None)
                if user:
                    st.session_state.current_user_id = user["id"]
                    st.rerun()
                else:
                    st.error("Email ou mot de passe incorrect.")

        with tab_register:
            nom = st.text_input("Nom", key="reg_nom")
            prenom = st.text_input("Prénom", key="reg_prenom")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Mot de passe", type="password", key="reg_password")
            role = st.selectbox("Rôle", ["candidat", "recruteur"], key="reg_role")
            entreprise = st.text_input("Entreprise", key="reg_entreprise") if role == "recruteur" else None
            if st.button("Créer le compte", use_container_width=True, type="primary"):
                if any(u["email"] == new_email for u in st.session_state.users):
                    st.error("Cet email est déjà utilisé.")
                else:
                    st.session_state.users.append({
                        "id": st.session_state.next_user_id, "email": new_email, "password": new_password,
                        "role": role, "nom": nom, "prenom": prenom, "entreprise": entreprise,
                    })
                    st.session_state.next_user_id += 1
                    st.success("Compte créé ! Connecte-toi.")
