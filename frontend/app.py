"""
ATS Intelligent — Frontend Streamlit (maquette avec données mockées)
Point d'entrée : initialise les données, applique le thème, route vers la bonne vue selon le rôle.
Aucun backend Flask pour l'instant — tout est simulé en session_state (voir mock_data.py).
"""
import streamlit as st

from theme import inject_css, avatar
from mock_data import init_mock_data, get_user
from views.login import page_login
from views.candidat import page_candidat
from views.recruteur import page_recruteur
from views.admin import page_admin

st.set_page_config(page_title="ATS Intelligent", layout="wide")
inject_css()
init_mock_data()

if "current_user_id" not in st.session_state:
    page_login()
else:
    current_user = get_user(st.session_state.current_user_id)

    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding: 12px 0 20px 0;">
            {avatar(current_user['prenom'], current_user['nom'])}
            <div style="margin-top:8px; font-weight:700;">{current_user['prenom']} {current_user['nom']}</div>
            <div style="opacity:0.7; font-size:0.85rem; text-transform:uppercase;">{current_user['role']}</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        if st.button("Se déconnecter", use_container_width=True):
            del st.session_state.current_user_id
            st.rerun()

    PAGES_BY_ROLE = {
        "candidat": page_candidat,
        "recruteur": page_recruteur,
        "admin": page_admin,
    }
    PAGES_BY_ROLE[current_user["role"]](current_user)
