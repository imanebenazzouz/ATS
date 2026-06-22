"""
ATS Intelligent — Frontend Streamlit
Point d'entrée : applique le thème, route vers la bonne vue selon le rôle.
Les données proviennent de l'API Flask (voir api_client.py) ; seul l'historique
de chat reste local (mock_data.py, en attendant le Lot C).
"""
import requests
import streamlit as st

import api_client as api
from mock_data import init_session_state
from theme import avatar, inject_css
from views.admin import page_admin
from views.candidat import page_candidat
from views.login import page_login
from views.recruteur import page_recruteur

st.set_page_config(page_title="ATS Intelligent", layout="wide")
inject_css()
init_session_state()

if "current_user_id" not in st.session_state:
    page_login()
else:
    try:
        current_user = api.get_user(st.session_state.current_user_id)
    except requests.RequestException:
        st.error("Impossible de joindre l'API. Lance le backend : `python -m backend.app`")
        st.stop()

    if not current_user:
        del st.session_state.current_user_id
        st.rerun()

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
