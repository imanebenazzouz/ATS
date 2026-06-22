"""Espace recruteur : offres, résultats de matching, chatbot."""
import streamlit as st
from datetime import datetime
from theme import skill_pills, status_badge, progress_bar, avatar
from mock_data import get_user, mock_llm_explanation
from views.chatbot import render_chatbot


def page_recruteur(user):
    st.title(f"Espace recruteur — {user['entreprise']}")
    tab_offres, tab_candidats, tab_chat = st.tabs(
        ["Mes offres", "Résultats de matching", "Chatbot LLM"]
    )

    with tab_offres:
        _render_offres_tab(user)

    with tab_candidats:
        _render_matching_tab(user)

    with tab_chat:
        render_chatbot(user)


def _render_offres_tab(user):
    with st.expander("Publier une nouvelle offre"):
        titre = st.text_input("Titre du poste", key="offre_titre")
        domaine = st.selectbox(
            "Domaine", ["Tech", "Marketing", "Finance", "Design", "Ressources Humaines", "Vente"],
            key="offre_domaine",
        )
        description = st.text_area("Description", key="offre_description")
        competences = st.text_input("Compétences requises (séparées par des virgules)", key="offre_competences")
        if st.button("Publier l'offre", type="primary"):
            st.session_state.offres.append({
                "id": st.session_state.next_offre_id, "recruteur_id": user["id"],
                "titre": titre, "entreprise": user["entreprise"], "domaine": domaine, "description": description,
                "competences_requises": [c.strip() for c in competences.split(",") if c.strip()],
                "statut": "active", "date_publication": datetime.now().strftime("%Y-%m-%d"),
            })
            st.session_state.next_offre_id += 1
            st.success("Offre publiée !")
            st.rerun()

    mes_offres = [o for o in st.session_state.offres if o["recruteur_id"] == user["id"]]
    for offre in mes_offres:
        st.markdown(f"""
        <div class="ats-card">
            <h4>{offre['titre']} {status_badge(offre['statut'])}</h4>
            <p style="color:#888; margin-top:0;">{offre['domaine']}</p>
            <p>{offre['description']}</p>
            {skill_pills(offre['competences_requises'])}
        </div>
        """, unsafe_allow_html=True)


def _render_matching_tab(user):
    mes_offres = [o for o in st.session_state.offres if o["recruteur_id"] == user["id"]]
    offre_choisie = st.selectbox(
        "Choisir une offre", mes_offres, format_func=lambda o: o["titre"]
    ) if mes_offres else None

    if not offre_choisie:
        return

    candidatures = [c for c in st.session_state.candidatures if c["offre_id"] == offre_choisie["id"]]
    if not candidatures:
        st.info("Aucune candidature pour cette offre.")
    for c in sorted(candidatures, key=lambda c: -c["score_matching"]):
        candidat = get_user(c["candidat_id"])
        cv = next((cv for cv in st.session_state.cvs if cv["candidat_id"] == candidat["id"]), None)
        st.markdown(f"""
        <div class="ats-card">
            <h4>{avatar(candidat['prenom'], candidat['nom'])}{candidat['prenom']} {candidat['nom']} {status_badge(c['statut'])}</h4>
            {progress_bar(c['score_matching'])}
        </div>
        """, unsafe_allow_html=True)
        if cv:
            with st.expander("Voir l'explication du LLM"):
                st.write(mock_llm_explanation(cv["skills"], offre_choisie["competences_requises"]))

        if c["statut"] == "en attente":
            with st.form(key=f"reponse_form_{c['id']}"):
                message = st.text_input("Message au candidat (optionnel)", key=f"msg_{c['id']}")
                col1, col2 = st.columns(2)
                accepter = col1.form_submit_button("Accepter", type="primary", use_container_width=True)
                refuser = col2.form_submit_button("Refuser", use_container_width=True)
                if accepter or refuser:
                    c["statut"] = "acceptée" if accepter else "refusée"
                    c["message_recruteur"] = message
                    c["date_reponse"] = datetime.now().strftime("%Y-%m-%d")
                    st.rerun()
        else:
            st.caption(f"Réponse envoyée le {c.get('date_reponse', '—')}"
                       + (f" : « {c['message_recruteur']} »" if c.get("message_recruteur") else ""))
