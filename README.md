# ATS Intelligent — SaaS RH + Copilote LLM

Projet S6 BUT Informatique. Plateforme ATS (Applicant Tracking System) intégrant matching
sémantique CV ↔ offres et un copilote LLM.

## État actuel

- **Frontend Streamlit** : fonctionnel, branché sur l'API.
- **Backend Flask + SQLite** : auth (mots de passe hashés) et CRUD offres / CV / candidatures /
  utilisateurs / stats.
- **À venir** : pipeline IA réel — extraction PDF, chunking, embeddings MiniLM, FAISS, similarité
  cosinus (Lot B) et copilote LLM (explications, chatbot) (Lot C). Pour l'instant le score de
  matching est une intersection de compétences et les réponses LLM sont simulées.

## Structure

```
init_db.py          → crée le schéma SQLite (ats.db)
backend/
  app.py            → API Flask (auth + CRUD)
  db.py             → connexion SQLite + helpers JSON
  seed.py           → données de démonstration
frontend/
  app.py            → point d'entrée, routeur selon le rôle
  api_client.py     → client HTTP vers l'API Flask
  theme.py          → CSS + helpers d'affichage
  mock_data.py      → réponses LLM simulées (en attendant le Lot C)
  views/            → une vue par rôle + le chatbot
```

## Démarrage

```bash
# 1. Base de données
python init_db.py
python -m backend.seed

# 2. Backend (terminal 1, à la racine)
pip install -r backend/requirements.txt
python -m backend.app          # http://127.0.0.1:5000

# 3. Frontend (terminal 2)
pip install -r frontend/requirements.txt
cd frontend && streamlit run app.py
```

L'URL de l'API est configurable côté front via la variable d'environnement `ATS_API_URL`.

Comptes de démo (mot de passe `1234`) : `candidat@test.com`, `rh@test.com`, `admin@test.com`.
