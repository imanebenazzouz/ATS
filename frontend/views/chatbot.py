"""Chatbot LLM partagé entre les vues candidat et recruteur."""
import html

import streamlit as st

import api_client as api
from mock_data import mock_llm_chat_reply

esc = html.escape


def render_chatbot(user):
    history = st.session_state.chatbot_history.setdefault(user["id"], [])
    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    question = st.chat_input("Pose ta question au copilote LLM...")
    if question:
        history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        reply = mock_llm_chat_reply(question, user["role"])
        history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)


def render_messagerie(candidature_id, current_user_id, key_suffix=""):
    """Messagerie privée recruteur <-> candidat pour une candidature acceptée."""
    messages = api.get_messages(candidature_id)

    with st.container(border=True):
        if not messages:
            st.caption("Aucun message pour le moment. Commencez la conversation.")
        for msg in messages:
            is_me = msg["expediteur_id"] == current_user_id
            align = "right" if is_me else "left"
            bg = "#eef0ff" if is_me else "#f1f5f9"
            color = "#4338ca" if is_me else "#334155"
            label = "Vous" if is_me else f"{esc(msg['prenom'])} {esc(msg['nom'])}"
            st.markdown(
                f"<div style='text-align:{align};margin:6px 0'>"
                f"<span style='font-size:0.75rem;color:#94a3b8'>{label} — {esc(msg['date_envoi'][:16])}</span><br>"
                f"<span style='display:inline-block;background:{bg};color:{color};padding:8px 14px;"
                f"border-radius:12px;max-width:80%;text-align:left'>{esc(msg['contenu'])}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with st.form(f"msg_form_{candidature_id}_{key_suffix}", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        texte = col1.text_input("Votre message", label_visibility="collapsed",
                                placeholder="Écrivez votre message…")
        envoyer = col2.form_submit_button("Envoyer", use_container_width=True, type="primary")
    if envoyer:
        if not texte.strip():
            st.warning("Le message ne peut pas être vide.")
        else:
            ok, err = api.send_message(candidature_id, current_user_id, texte.strip())
            if ok:
                st.rerun()
            else:
                st.error(err or "Erreur lors de l'envoi.")
