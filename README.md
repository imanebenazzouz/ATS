# ATS Intelligent — SaaS RH + Copilote LLM

Projet S6 BUT Informatique. Plateforme ATS (Applicant Tracking System) intégrant matching
sémantique CV ↔ offres et un copilote LLM.

## État actuel

- **Frontend Streamlit** : fonctionnel, branché sur l'API.
- **Backend Flask + SQLite** : auth (mots de passe hashés) et CRUD offres / CV / candidatures /
  utilisateurs / stats.
- **Pipeline IA (Lot B)** : extraction PDF (PyMuPDF) → chunking sémantique → embeddings
  `all-MiniLM-L6-v2` → stockage des vecteurs → matching bidirectionnel par similarité cosinus
  (FAISS). Score réel des candidatures + recherche RH en langage naturel. Fallback automatique
  sur un score d'intersection si les dépendances du pipeline ne sont pas installées.
- **À venir** : copilote LLM réel — explications de matching et chatbot (Lot C, aujourd'hui simulé).

## Structure

```
init_db.py          → crée le schéma SQLite (ats.db)
backend/
  app.py            → API Flask (auth + CRUD + matching)
  db.py             → connexion SQLite + helpers JSON
  seed.py           → données de démonstration
  reindex.py        → (re)calcule chunks + embeddings du contenu existant
  ai/               → pipeline IA (Lot B)
    extract.py      → extraction PDF (PyMuPDF)
    chunking.py     → découpage sémantique par sections
    embeddings.py   → encodage MiniLM (all-MiniLM-L6-v2)
    matching.py     → FAISS + similarité cosinus
    pipeline.py     → orchestration + fallback si deps absentes
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
python -m backend.reindex      # embeddings du contenu seedé (Lot B, optionnel)
python -m backend.app          # http://127.0.0.1:5000

# 3. Frontend (terminal 2)
pip install -r frontend/requirements.txt
cd frontend && streamlit run app.py
```

> Le pipeline IA télécharge le modèle `all-MiniLM-L6-v2` au premier lancement
> (~90 Mo). Sans `backend/requirements.txt` installé, l'app fonctionne quand même
> (score d'intersection en fallback, recherche IA désactivée).

L'URL de l'API est configurable côté front via la variable d'environnement `ATS_API_URL`.

Comptes de démo (mot de passe `1234`) : `candidat@test.com`, `rh@test.com`, `admin@test.com`.
