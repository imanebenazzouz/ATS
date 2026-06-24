"""LLM copilote (Lot C) — explication des matchs, chatbot, bonus recherche web.

Le LLM n'est PAS le moteur de matching (qui reste basé sur la similarité cosinus
du Lot B) : il sert uniquement à expliquer/reformuler/résumer, comme précisé dans
le sujet (§8 "Le LLM n'est pas le moteur principal").
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

# Fallback en cascade : si un modèle gratuit OpenRouter est temporairement
# rate-limité (fréquent sur le tier free), on retombe sur le suivant.
CHAT_MODELS = [
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-20b:free",
]


def _call_llm(prompt: str) -> str:
    last_error = None
    for model in CHAT_MODELS:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            last_error = exc
            continue
    raise last_error


def explain_match(candidat_skills, candidat_experience, offre_titre, offre_competences, score) -> str:
    """Sujet §8.1 : explication textuelle d'un score de matching CV <-> offre."""
    prompt = f"""Tu es un copilote RH. Explique en 3-4 lignes pourquoi ce candidat correspond
(ou pas) à cette offre, à partir des données ci-dessous. Reste factuel et concis.

Offre : {offre_titre}
Compétences requises : {", ".join(offre_competences) or "non précisées"}

Candidat — compétences détectées : {", ".join(candidat_skills) or "non précisées"}
Candidat — expérience : {candidat_experience or "non précisée"}

Score de matching calculé (similarité cosinus) : {round((score or 0) * 100)}%

Réponse :"""
    return _call_llm(prompt)


def web_search(question: str, max_results: int = 3) -> str:
    """Bonus sujet §9 : recherche externe pour enrichir le chatbot hors périmètre RH."""
    try:
        from ddgs import DDGS
        results = DDGS().text(question, max_results=max_results)
        return "\n\n".join(f"{r['title']} : {r['body']} (source: {r['href']})" for r in results)
    except Exception:
        return ""


def needs_web_search(question: str) -> bool:
    """Heuristique simple : questions sur le marché de l'emploi / hors périmètre ATS."""
    keywords = ["salaire", "marché", "tendance", "actualité", "entreprise", "secteur"]
    return any(k in question.lower() for k in keywords)


def chat_reply(question: str, role: str) -> str:
    """Sujet §8 : copilote conversationnel candidat/recruteur."""
    web_context = web_search(question) if needs_web_search(question) else ""

    if role == "candidat":
        system = ("Tu es un copilote carrière qui conseille un candidat sur sa recherche d'emploi : "
                   "CV, lettre de motivation, mise en valeur de compétences, préparation d'entretien.")
    else:
        system = ("Tu es un copilote RH qui aide un recruteur à affiner sa recherche de candidats "
                   "et sa stratégie de recrutement.")

    prompt = f"""{system}

{"Contexte web (à utiliser seulement si pertinent) :" + chr(10) + web_context if web_context else ""}

Question : {question}

Réponse concise et actionnable :"""
    return _call_llm(prompt)
