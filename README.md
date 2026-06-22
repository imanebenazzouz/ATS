# ATS Intelligent — SaaS RH + Copilote LLM

Projet S6 BUT Informatique. Plateforme ATS (Applicant Tracking System) intégrant matching
sémantique CV ↔ offres et un copilote LLM.

## État actuel

Frontend Streamlit fonctionnel avec données mockées (voir `frontend/mock_data.py`).
Le backend Flask + pipeline IA (extraction PDF, chunking, embeddings MiniLM, FAISS,
LLM copilote) reste à implémenter.

## Structure

```
frontend/
  app.py          → point d'entrée, routeur selon le rôle (candidat/recruteur/admin)
  theme.py        → CSS + helpers d'affichage
  mock_data.py    → données simulées en attendant le backend
  views/          → une vue par rôle + le chatbot
```

## Lancer le frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Comptes de démo (mot de passe `1234`) : `candidat@test.com`, `rh@test.com`, `admin@test.com`.
