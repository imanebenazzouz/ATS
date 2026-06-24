"""CSS du thème + helpers de rendu HTML (pills, badges, barres de progression, avatars).

Toutes les couleurs de texte sont explicites pour rester lisibles quel que soit le
thème clair/sombre du navigateur (sinon Streamlit met le texte en clair -> invisible
sur les cartes blanches).
"""
import html

import streamlit as st

# Palette
PRIMARY = "#4f46e5"        # indigo
PRIMARY_DARK = "#4338ca"
ACCENT = "#7c3aed"         # violet
INK = "#1e293b"            # texte principal
MUTED = "#64748b"          # texte secondaire
BG = "#f5f7fb"
CARD = "#ffffff"
BORDER = "#e6e8f0"


def inject_css():
    st.markdown(f"""
    <style>
    /* ---------- Base : couleurs de texte explicites (anti texte-blanc-sur-blanc) ---------- */
    .stApp {{ background: {BG}; }}
    .stApp, .stApp p, .stApp li, .stApp label, .stMarkdown,
    div[data-testid="stMarkdownContainer"] {{ color: {INK}; }}
    h1, h2, h3, h4, h5 {{ color: #111827 !important; }}
    .stApp a {{ color: {PRIMARY}; }}

    /* ---------- Sidebar (fond sombre -> texte clair) ---------- */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {PRIMARY_DARK} 0%, #1e1b4b 100%);
    }}
    section[data-testid="stSidebar"] * {{ color: #eef2ff !important; }}
    section[data-testid="stSidebar"] button {{
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.35) !important;
        border-radius: 10px !important;
    }}
    section[data-testid="stSidebar"] button:hover {{
        background: rgba(255,255,255,0.22) !important;
    }}

    /* ---------- Titres de page ---------- */
    .main h1 {{
        font-weight: 800; letter-spacing: -0.02em;
        background: linear-gradient(90deg, {PRIMARY_DARK}, {ACCENT});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}

    /* ---------- Onglets ---------- */
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: none; }}
    .stTabs [data-baseweb="tab"] {{
        background: #ffffff; color: {INK} !important;
        border: 1px solid {BORDER}; border-radius: 10px;
        padding: 8px 18px; font-weight: 600;
    }}
    .stTabs [data-baseweb="tab"]:hover {{ border-color: {PRIMARY}; }}
    .stTabs [aria-selected="true"] {{
        background: {PRIMARY} !important; border-color: {PRIMARY} !important;
    }}
    .stTabs [aria-selected="true"] * {{ color: #ffffff !important; }}

    /* ---------- Cartes custom ---------- */
    .ats-card {{
        background: {CARD}; color: {INK};
        border-radius: 16px; padding: 20px 24px; margin-bottom: 16px;
        box-shadow: 0 4px 16px rgba(30,41,59,0.06); border: 1px solid {BORDER};
    }}
    .ats-card p {{ color: #334155; margin: 6px 0; }}
    .ats-card strong {{ color: {INK}; }}
    .ats-card h4 {{ margin: 0 0 6px 0; color: {PRIMARY_DARK}; font-weight: 700; }}

    /* ---------- Pills / badges ---------- */
    .ats-pill {{
        display: inline-block; background: #eef0ff; color: {PRIMARY_DARK} !important;
        border-radius: 999px; padding: 4px 12px; margin: 2px 4px 2px 0;
        font-size: 0.82rem; font-weight: 600;
    }}
    .ats-badge {{
        display: inline-block; border-radius: 999px; padding: 3px 12px;
        font-size: 0.74rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;
    }}
    .badge-active   {{ background: #dcfce7; color: #15803d !important; }}
    .badge-pending  {{ background: #fef3c7; color: #b45309 !important; }}
    .badge-rejected {{ background: #fee2e2; color: #b91c1c !important; }}

    /* ---------- Barre de progression (matching) ---------- */
    .ats-progress-track {{
        background: #eceefc; border-radius: 999px; height: 10px; width: 100%;
        overflow: hidden; margin: 8px 0 4px 0;
    }}
    .ats-progress-fill {{
        height: 100%; border-radius: 999px;
        background: linear-gradient(90deg, {ACCENT}, {PRIMARY});
    }}

    /* ---------- Avatar ---------- */
    .ats-avatar {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 38px; height: 38px; border-radius: 50%;
        background: linear-gradient(135deg, {ACCENT}, {PRIMARY});
        color: #fff !important; font-weight: 700; margin-right: 10px; vertical-align: middle;
    }}

    /* ---------- Hero (login) ---------- */
    .ats-hero {{ text-align: center; padding: 30px 0 6px 0; }}
    .ats-hero h1 {{
        font-size: 2.4rem; font-weight: 800; margin-bottom: 4px;
        background: linear-gradient(90deg, {PRIMARY_DARK}, {ACCENT});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .ats-hero p {{ color: {MUTED}; font-size: 1.02rem; }}

    /* ---------- Widgets Streamlit : fonds clairs, texte lisible ---------- */
    div[data-testid="stMetric"] {{
        background: {CARD}; border-radius: 14px; padding: 16px 18px;
        box-shadow: 0 4px 16px rgba(30,41,59,0.06); border: 1px solid {BORDER};
    }}
    div[data-testid="stMetric"] * {{ color: {INK} !important; }}
    div[data-testid="stMetricValue"] {{ color: {PRIMARY_DARK} !important; }}

    div[data-testid="stExpander"] {{
        background: {CARD}; border-radius: 14px; border: 1px solid {BORDER};
    }}
    div[data-testid="stExpander"] summary, div[data-testid="stExpander"] p {{ color: {INK} !important; }}

    /* Champs de saisie */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
        background: #ffffff !important; color: {INK} !important;
        border-radius: 10px !important;
    }}
    .stTextInput label, .stTextArea label, .stSelectbox label, .stFileUploader label {{
        color: {INK} !important; font-weight: 600;
    }}

    /* Uploader de fichier */
    div[data-testid="stFileUploaderDropzone"], section[data-testid="stFileUploaderDropzone"] {{
        background: #ffffff !important; border: 1px dashed {PRIMARY} !important; border-radius: 12px !important;
    }}
    div[data-testid="stFileUploader"] * {{ color: {INK} !important; }}

    /* Conteneurs bordés (st.container border=True) */
    div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px; }}

    /* Boutons primaires */
    .stButton button[kind="primary"] {{
        background: {PRIMARY} !important; border: none !important; border-radius: 10px !important;
        font-weight: 600;
    }}
    .stButton button[kind="primary"]:hover {{ background: {PRIMARY_DARK} !important; }}

    /* Captions */
    .stCaption, div[data-testid="stCaptionContainer"] {{ color: {MUTED} !important; }}
    </style>
    """, unsafe_allow_html=True)


def compact(html_str: str) -> str:
    """Aplati un bloc HTML multi-lignes en une seule ligne.

    Streamlit (markdown) casse le rendu d'un bloc HTML dès qu'il contient une ligne
    vide (ex. quand skill_pills est vide) et réaffiche alors les balises en texte brut.
    En supprimant retours à la ligne et lignes vides, le rendu reste fiable.
    """
    return " ".join(line.strip() for line in html_str.splitlines() if line.strip())


def card(inner_html: str) -> str:
    """Enveloppe un contenu HTML dans une carte (rendu fiable, une seule ligne)."""
    return compact(f"<div class='ats-card'>{inner_html}</div>")


def skill_pills(skills):
    if not skills:
        return "<span style='color:#94a3b8;font-size:0.85rem'>—</span>"
    return "".join(f"<span class='ats-pill'>{html.escape(str(s))}</span>" for s in skills)


def status_badge(statut: str) -> str:
    mapping = {
        "active": ("badge-active", "Active"),
        "en attente": ("badge-pending", "En attente"),
        "acceptée": ("badge-active", "Acceptée"),
        "refusée": ("badge-rejected", "Refusée"),
        "pending": ("badge-pending", "En attente"),
        "inactive": ("badge-rejected", "Inactive"),
    }
    cls, label = mapping.get(statut, ("badge-pending", html.escape(str(statut)).capitalize()))
    return f"<span class='ats-badge {cls}'>{label}</span>"


def progress_bar(score: float) -> str:
    pct = round((score or 0) * 100)
    return (f"<div class='ats-progress-track'><div class='ats-progress-fill' "
            f"style='width:{pct}%'></div></div>"
            f"<span style='font-size:0.85rem;color:{MUTED}'>{pct}% de correspondance</span>")


def avatar(prenom: str, nom: str) -> str:
    initials = html.escape((prenom[:1] + nom[:1]).upper())
    return f"<span class='ats-avatar'>{initials}</span>"
