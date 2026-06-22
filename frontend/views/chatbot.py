"""Chatbot LLM partagé entre les vues candidat et recruteur."""
import streamlit as st
from mock_data import mock_llm_chat_reply


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
