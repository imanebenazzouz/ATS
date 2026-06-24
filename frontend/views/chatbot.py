"""Chatbot LLM (Lot C) — partagé entre les vues candidat et recruteur.

Branché sur l'API Flask : historique persisté en base (chatbot_sessions /
conseils_llm), réponse générée par un vrai LLM (backend/llm.py).
"""
import streamlit as st

import api_client as api


def render_chatbot(user):
    history = api.chatbot_history(user["id"])
    for msg in history:
        with st.chat_message("user"):
            st.write(msg["question"])
        with st.chat_message("assistant"):
            st.write(msg["reponse"])

    question = st.chat_input("Pose ta question au copilote LLM...")
    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Le copilote réfléchit..."):
                reponse, error = api.chatbot_message(user["id"], user["role"], question)
            st.write(reponse or f"Erreur : {error}")
        st.rerun()
