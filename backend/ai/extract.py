"""Étape 1 du pipeline : extraction du texte d'un CV PDF (PyMuPDF).

cf. sujet §5.1 : CV PDF -> extraction texte (PyMuPDF).
"""


def extract_text(pdf_path):
    """Retourne le texte brut concaténé de toutes les pages du PDF.

    Lève ImportError si PyMuPDF n'est pas installé (géré en amont par le fallback).
    """
    import fitz  # PyMuPDF

    parts = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            # sort=True -> ordre de lecture haut->bas, plus robuste sur les CV multi-colonnes
            parts.append(page.get_text("text", sort=True))
    return "\n".join(parts).strip()
