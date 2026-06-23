"""Test E2E manuel du parcours utilisateur réel (UI Streamlit + API Flask).

NON collecté par pytest (nom sans préfixe test_). Nécessite Playwright + Chromium
et les deux serveurs lancés. Pilote un vrai navigateur sur les 3 rôles + la recherche IA.

Prérequis :
    pip install playwright && playwright install chromium
    python init_db.py && python -m backend.seed && python -m backend.reindex

Lancement (gère les serveurs automatiquement via le helper du skill webapp-testing,
ou lance Flask sur :5000 et Streamlit sur :8501 puis) :
    python tests/manual_ui_e2e.py

Les captures sont enregistrées dans un dossier temporaire (chemin affiché en fin de run).
"""
import json
import os
import sys
import tempfile
import urllib.request

from playwright.sync_api import sync_playwright

URL = os.environ.get("ATS_UI_URL", "http://localhost:8501")
API = os.environ.get("ATS_API_URL", "http://localhost:5000")
SHOT = tempfile.mkdtemp(prefix="ats_e2e_")
results = []


def step(name, ok):
    results.append(ok)
    print(f"[{'OK ' if ok else 'KO '}] {name}")


def warmup_model():
    """Précharge MiniLM côté Flask (1er appel ~30s) pour fiabiliser les clics UI."""
    try:
        req = urllib.request.Request(f"{API}/search/candidats",
                                     data=json.dumps({"query": "warmup"}).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=120).read()
        print("[OK ] modèle préchauffé")
    except Exception as e:
        print("[!! ] warmup:", str(e)[:120])


def login(page, email, pwd):
    page.get_by_label("Email").first.fill(email)
    page.get_by_label("Mot de passe").first.fill(pwd)
    page.get_by_role("button", name="Se connecter").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)


def logout(page):
    page.get_by_role("button", name="Se déconnecter").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)


def run():
    warmup_model()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(20000)
        page.goto(URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2500)
        step("page de connexion", "Se connecter" in page.content())

        login(page, "candidat@test.com", "1234")
        body = page.content()
        step("login candidat", "Espace candidat" in body)
        step("CV affiché", "Compétences détectées" in body)
        page.get_by_role("tab", name="Offres").click()
        page.wait_for_timeout(2000)
        step("offres listées", "Data Engineer" in page.content())
        logout(page)

        login(page, "rh@test.com", "1234")
        step("login recruteur", "Espace recruteur" in page.content())
        page.get_by_role("tab", name="Recherche IA").click()
        page.wait_for_timeout(1500)
        page.get_by_label("Ex : « data engineer Python et Docker »").first.fill("data engineer python docker")
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(4000)
        body = page.content()
        step("recherche IA -> candidat", ("Doe" in body) or ("correspondance" in body))
        logout(page)

        login(page, "admin@test.com", "1234")
        step("login admin", "Espace administrateur" in page.content())
        page.get_by_role("tab", name="Statistiques").click()
        page.wait_for_timeout(2000)
        step("stats admin", "Candidats" in page.content())
        page.screenshot(path=f"{SHOT}/admin.png")
        browser.close()

    print(f"\n=== {sum(results)}/{len(results)} étapes OK — captures: {SHOT} ===")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(run())
