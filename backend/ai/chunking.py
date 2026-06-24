"""Étape 2 du pipeline : chunking structuré (sémantique) par sections.

cf. sujet §5.2 : on ne fait pas un simple découpage texte, mais une segmentation
par sections détectées via regex de titres (Skills / Experience / Education...).
Chaque chunk = {type_section, contenu}.
"""
import re

# Titres de section reconnus -> type canonique
SECTION_PATTERNS = [
    (re.compile(r"comp[ée]tences?|skills?|technologies?|stack", re.I), "skills"),
    (re.compile(r"exp[ée]riences?|parcours|emplois?", re.I), "experience"),
    (re.compile(r"[ée]ducation|formations?|dipl[ôo]mes?|scolarit[ée]", re.I), "education"),
    (re.compile(r"projets?|projects?|r[ée]alisations?", re.I), "projets"),
    (re.compile(r"langues?|languages?", re.I), "langues"),
    (re.compile(r"certifications?", re.I), "certifications"),
    (re.compile(r"profil|summary|r[ée]sum[ée]|about", re.I), "profil"),
]


def _match_section(line):
    """Retourne le type de section si la ligne est un titre, sinon None.

    Un titre est une ligne courte (<= 45 car., <= 4 mots) contenant un mot-clé de
    section — ce qui couvre « Compétences techniques », « Expériences professionnelles »,
    « Projets & side projects », etc. (et pas seulement le mot-clé seul).
    """
    stripped = line.strip().rstrip(":").strip()
    if not stripped or len(stripped) > 45 or len(stripped.split()) > 4:
        return None
    for pattern, type_section in SECTION_PATTERNS:
        if pattern.search(stripped):
            return type_section
    return None


def _split_inline(line):
    """Gère 'Skills: Python, Flask' -> (type, 'Python, Flask'). Sinon None."""
    if ":" not in line:
        return None
    head, _, tail = line.partition(":")
    head, tail = head.strip(), tail.strip()
    for pattern, type_section in SECTION_PATTERNS:
        if pattern.fullmatch(head):
            return type_section, tail
    return None


def chunk_text(text):
    """Découpe le texte en chunks par section.

    Retourne une liste de dicts {type_section, contenu}. Si aucun titre n'est
    détecté, retourne un unique chunk de type 'divers' avec tout le texte.
    """
    lines = [l for l in text.splitlines()]
    sections = []           # (type_section, [lignes de contenu])
    current = []            # le texte avant le premier titre va dans 'profil'
    sections.append(("profil", current))

    for line in lines:
        inline = _split_inline(line)
        if inline:
            type_section, content = inline
            current = [content] if content else []
            sections.append((type_section, current))
            continue
        section_type = _match_section(line)
        if section_type:
            current = []
            sections.append((section_type, current))
        elif current is not None and line.strip():
            current.append(line.strip())
        # texte avant le premier titre -> ignoré (en-tête / identité)

    chunks = []
    for type_section, content_lines in sections:
        contenu = " ".join(content_lines).strip()
        if contenu:
            chunks.append({"type_section": type_section, "contenu": contenu})

    # Aucun titre reconnu -> tout le texte est du 'divers' (et non du 'profil')
    if len(chunks) == 1 and chunks[0]["type_section"] == "profil":
        chunks[0]["type_section"] = "divers"

    if not chunks:
        cleaned = " ".join(l.strip() for l in lines if l.strip())
        if cleaned:
            chunks.append({"type_section": "divers", "contenu": cleaned})
    return chunks


def extract_skills(chunks):
    """Liste de compétences à partir du/des chunk(s) 'skills' (pour la fiche CV du front).

    Gère les formats du type « Langages : JavaScript, Python | Frameworks : React, ... » :
    on découpe sur les séparateurs et on retire les préfixes de label (« Langages : »).
    """
    contenu = " ".join(c["contenu"] for c in chunks if c["type_section"] == "skills")
    if not contenu:
        return []
    skills, seen = [], set()
    for token in re.split(r"[,;/\n•|]+", contenu):
        token = re.sub(r"^[A-Za-zÀ-ÿ &.]{2,22}\s*:\s*", "", token.strip()).strip()
        key = token.lower()
        if token and 1 < len(token) <= 30 and key not in seen:
            seen.add(key)
            skills.append(token)
    return skills[:20]


def section_text(chunks, type_section):
    """Concatène les chunks d'un type donné (ex: 'experience') en une chaîne."""
    return " ".join(c["contenu"] for c in chunks if c["type_section"] == type_section).strip()
