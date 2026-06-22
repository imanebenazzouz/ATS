"""CSS du thème + helpers de rendu HTML (pills, badges, barres de progression, avatars)."""
import streamlit as st

PRIMARY = "#2d3a8c"
PRIMARY_LIGHT = "#4f5fc7"
ACCENT = "#6c63ff"
BG_SOFT = "#f4f6fb"


def inject_css():
    st.markdown(f"""
    <style>
    .stApp {{
        background: {BG_SOFT};
    }}
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {PRIMARY} 0%, #1a1a2e 100%);
    }}
    section[data-testid="stSidebar"] * {{
        color: #f0f0ff !important;
    }}
    section[data-testid="stSidebar"] button {{
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
    }}
    section[data-testid="stSidebar"] button p {{
        color: #f0f0ff !important;
    }}
    h1, h2, h3 {{
        color: #1a1a2e;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: white;
        border-radius: 8px 8px 0 0;
        padding: 8px 18px;
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background: {PRIMARY} !important;
        color: white !important;
    }}
    div[data-testid="stMetric"] {{
        background: white;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 2px 10px rgba(45,58,140,0.08);
        border: 1px solid #e8eaf6;
    }}
    div[data-testid="stExpander"] {{
        background: white;
        border-radius: 12px;
        border: 1px solid #e8eaf6;
    }}
    .ats-card {{
        background: white;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 2px 12px rgba(45,58,140,0.07);
        border: 1px solid #eceefc;
    }}
    .ats-card h4 {{
        margin: 0 0 4px 0;
        color: {PRIMARY};
    }}
    .ats-pill {{
        display: inline-block;
        background: #eef0fd;
        color: {PRIMARY};
        border-radius: 999px;
        padding: 3px 12px;
        margin: 2px 4px 2px 0;
        font-size: 0.82rem;
        font-weight: 600;
    }}
    .ats-badge {{
        display: inline-block;
        border-radius: 999px;
        padding: 3px 12px;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    .badge-active {{ background: #e3f9e9; color: #1c8a4b; }}
    .badge-pending {{ background: #fff4e0; color: #b8740a; }}
    .badge-rejected {{ background: #fde3e3; color: #c1342f; }}
    .ats-progress-track {{
        background: #eceefc;
        border-radius: 999px;
        height: 10px;
        width: 100%;
        overflow: hidden;
        margin: 6px 0 2px 0;
    }}
    .ats-progress-fill {{
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, {ACCENT}, {PRIMARY_LIGHT});
    }}
    .ats-avatar {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, {ACCENT}, {PRIMARY});
        color: white;
        font-weight: 700;
        margin-right: 10px;
    }}
    .ats-hero {{
        text-align: center;
        padding: 36px 0 8px 0;
    }}
    .ats-hero h1 {{
        font-size: 2.4rem;
        margin-bottom: 4px;
        background: linear-gradient(90deg, {PRIMARY}, {ACCENT});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .ats-hero p {{
        color: #666;
        font-size: 1rem;
    }}
    </style>
    """, unsafe_allow_html=True)


def skill_pills(skills):
    return "".join(f"<span class='ats-pill'>{s}</span>" for s in skills)


def status_badge(statut: str) -> str:
    mapping = {
        "active": ("badge-active", "Active"),
        "en attente": ("badge-pending", "En attente"),
        "acceptée": ("badge-active", "Acceptée"),
        "refusée": ("badge-rejected", "Refusée"),
        "pending": ("badge-pending", "En attente"),
    }
    cls, label = mapping.get(statut, ("badge-pending", statut.capitalize()))
    return f"<span class='ats-badge {cls}'>{label}</span>"


def progress_bar(score: float) -> str:
    pct = round(score * 100)
    return (f"<div class='ats-progress-track'><div class='ats-progress-fill' "
            f"style='width:{pct}%'></div></div><span style='font-size:0.85rem;color:#555'>{pct}% de correspondance</span>")


def avatar(prenom: str, nom: str) -> str:
    initials = (prenom[:1] + nom[:1]).upper()
    return f"<span class='ats-avatar'>{initials}</span>"
