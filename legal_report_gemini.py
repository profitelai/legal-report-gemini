"""
Legal Evidence Report Generator / Générateur de Rapport de Preuves Juridiques
Bilingual: English + French | Bilingue : Anglais + Français

Usage:
  1. Add your AI Studio links, text files, and/or URLs in main() below.
  2. Run: python legal_report_gemini.py
  3. Output: Legal_Strategic_Report.md + Legal_Strategic_Report.pdf

Supported inputs:
  - Google AI Studio share links  (https://aistudio.google.com/app/prompts?state=...)
  - Any public URL
  - Local .txt files
"""

import os
import json
import time
import re
import requests
import markdown
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from typing import Optional
from dotenv import load_dotenv
from google import genai

# PDF via reportlab (pure Python, no system libs needed)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

load_dotenv()

API_KEY = os.getenv("ai_studio")

if not API_KEY:
    raise ValueError(
        "Missing ai_studio key in .env file.\n"
        "Add: ai_studio=your_key_here\n"
        "Get your key at: https://aistudio.google.com/app/apikey"
    )

client = genai.Client(api_key=API_KEY)

OUTPUT_MD = "Legal_Strategic_Report.md"
OUTPUT_PDF = "Legal_Strategic_Report.pdf"

SYSTEM_PROMPT = """
Tu es un Assistant en Stratégie de Dossier et Organisateur de Documents Juridiques.

Rédige le rapport UNIQUEMENT EN FRANÇAIS. N'indique jamais la langue dans les titres de section.

Ton rôle n'est PAS de donner des conseils juridiques.
Ton rôle est d'organiser les preuves, communications, chronologies, contradictions
et courbes d'escalade dans un format clair destiné à un avocat.

Utilise un ton strictement neutre et factuel.
Emploie des formulations comme : « potentiellement », « semble indiquer »,
« apparaît comme », « à vérifier par l'avocat ».
Ne formule jamais de conclusions juridiques.

Noms clés à surveiller en priorité :
Maurice, Constance, Nicole Fernbach, Mayer Schmukler, Deborah Schmukler,
Haim Sherrff, Yael Sherff, Cremisi, Haim Moryoussef, Rav Atlan, André Kalfon.

Le rapport doit inclure TOUTES les sections suivantes, avec exactement ces titres :

## 1. RÉSUMÉ EXÉCUTIF
- Aperçu factuel court de la situation.

## 2. CHRONOLOGIE DES ÉVÉNEMENTS
Tableau avec exactement ces colonnes (en français) :
Date | Heure | Source | Acteur Principal | Événement / Action | Note de Preuve

## 3. CONTRADICTIONS ET VIOLATIONS POTENTIELLES
- Là où une déclaration contredit une autre.
- Possibles manquements aux accords écrits.
- Se concentrer particulièrement sur les événements après le 17 décembre 2024.

## 4. COURBE D'ESCALADE
- Comment le ton a évolué : Coopératif → Tendu → Hostile / Conflit.

## 5. PERSONNES CLÉS
- Rôle de chaque personne basé UNIQUEMENT sur les preuves fournies.

## 6. INDEX DES PREUVES
- Liste de tous les messages, courriels, documents, dates et sources identifiés.

## 7. QUESTIONS POUR L'AVOCAT
- Questions factuelles que l'avocat devrait examiner.
"""


# ---------------------------------------------------------------------------
# Google AI Studio URL handler
# ---------------------------------------------------------------------------

def is_aistudio_url(url: str) -> bool:
    return "aistudio.google.com" in url


def extract_file_id_from_aistudio_url(url: str) -> Optional[str]:
    """Parse the file ID from an AI Studio share URL."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        state_raw = params.get("state", [""])[0]
        if not state_raw:
            return None
        state = json.loads(unquote(state_raw))
        ids = state.get("ids", [])
        return ids[0] if ids else None
    except Exception:
        return None


def parse_aistudio_json(data: dict) -> str:
    """Convert AI Studio JSON format into readable plain text."""
    result = ""

    # System instruction
    sys_instr = data.get("systemInstruction", {})
    if sys_instr:
        parts = sys_instr.get("parts", [])
        text = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict) and p.get("text"))
        if text:
            result += f"[SYSTEM INSTRUCTION]\n{text}\n\n"

    # Conversation turns
    contents = data.get("contents", data.get("messages", []))
    for item in contents:
        role = item.get("role", "unknown").upper()
        parts = item.get("parts", [])
        text = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict) and p.get("text"))
        if text:
            result += f"[{role}]\n{text}\n\n"

    # Fallback: if nothing parsed, return raw JSON as string
    if not result.strip():
        result = json.dumps(data, ensure_ascii=False, indent=2)

    return result


def extract_from_aistudio_url(url: str) -> str:
    """Download and parse a shared Google AI Studio session."""
    print(f"  [AI Studio] Detected AI Studio link.")

    file_id = extract_file_id_from_aistudio_url(url)
    if not file_id:
        return (
            "[ERROR] Could not extract file ID from AI Studio URL.\n"
            "Please copy the conversation manually into a .txt file.\n"
        )

    print(f"  [AI Studio] File ID: {file_id}")

    # Google Drive direct download URL
    download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; legal-report-tool/1.0)"
        }
        response = session.get(download_url, headers=headers, timeout=30, allow_redirects=True)

        # Detect Google login redirect
        if "accounts.google.com" in response.url:
            return (
                "[AI Studio session requires login — cannot auto-download]\n\n"
                "To fix this:\n"
                "1. Open the link in your browser while logged into Google.\n"
                "2. Select all text on the page (Ctrl+A / Cmd+A).\n"
                "3. Copy and paste it into gemini_session_1.txt (or session_2, etc.).\n"
                "4. Re-run the script.\n"
            )

        content_type = response.headers.get("Content-Type", "")

        # Try JSON first (AI Studio native format)
        if "json" in content_type or response.text.strip().startswith("{"):
            try:
                data = response.json()
                parsed = parse_aistudio_json(data)
                print(f"  [OK] AI Studio JSON parsed: {len(parsed):,} characters.")
                return parsed
            except json.JSONDecodeError:
                pass

        # Try HTML (some shared prompts render as HTML)
        if "html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
            clean = "\n".join(line.strip() for line in text.splitlines() if line.strip())
            print(f"  [OK] AI Studio HTML extracted: {len(clean):,} characters.")
            return clean

        # Plain text fallback
        print(f"  [OK] AI Studio raw text: {len(response.text):,} characters.")
        return response.text

    except requests.exceptions.ConnectionError:
        return "[ERROR] Network error — check your internet connection.\n"
    except Exception as e:
        return (
            f"[ERROR] Could not download AI Studio session.\n"
            f"Reason: {str(e)}\n\n"
            "To fix: copy the conversation text manually into gemini_session_1.txt\n"
        )


# ---------------------------------------------------------------------------
# Gemini share link handler (gemini.google.com/share/...)
# ---------------------------------------------------------------------------

def is_gemini_share_url(url: str) -> bool:
    return "gemini.google.com/share" in url


def extract_from_gemini_share(url: str) -> str:
    """
    Fetch a public Gemini shared conversation.
    Uses Playwright (headless browser) because the page is JavaScript-rendered.
    Falls back to requests + BeautifulSoup if Playwright is not installed.
    """
    print(f"  [Gemini Share] Detected shared Gemini conversation: {url}")

    # --- Try Playwright first (full JS rendering) ---
    try:
        from playwright.sync_api import sync_playwright

        print("  [Gemini Share] Launching headless browser...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)  # extra wait for dynamic content

            # Try to grab all visible message text
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        # Remove chrome/navigation elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "button"]):
            tag.decompose()

        # Gemini share pages use specific roles/classes — grab all text blocks
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        result = "\n".join(lines)

        if len(result) > 200:
            print(f"  [OK] Gemini Share extracted {len(result):,} characters.")
            return result
        else:
            print("  [WARN] Page loaded but content appears empty — may need login.")
            return _gemini_share_fallback(url)

    except ImportError:
        print("  [WARN] Playwright not installed. Falling back to basic fetch.")
        return _gemini_share_basic_fetch(url)

    except Exception as e:
        print(f"  [WARN] Headless browser error: {e}")
        return _gemini_share_basic_fetch(url)


def _gemini_share_basic_fetch(url: str) -> str:
    """Basic requests fallback — works if the page has server-side rendered content."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        result = "\n".join(lines)

        if len(result) > 300:
            print(f"  [OK] Basic fetch extracted {len(result):,} characters.")
            return result

        return _gemini_share_fallback(url)

    except Exception as e:
        print(f"  [ERROR] Basic fetch failed: {e}")
        return _gemini_share_fallback(url)


def _gemini_share_fallback(url: str) -> str:
    return (
        f"[Gemini Share — manual copy needed for: {url}]\n\n"
        "The conversation could not be downloaded automatically.\n"
        "To add it:\n"
        "  1. Open the link in your browser (Chrome or Firefox).\n"
        "  2. Wait for the conversation to fully load.\n"
        "  3. Press Ctrl+A (or Cmd+A on Mac) to select all.\n"
        "  4. Copy and paste into gemini_session_1.txt (or session_2, etc.).\n"
        "  5. Re-run the script.\n"
    )


# ---------------------------------------------------------------------------
# Generic URL and file readers
# ---------------------------------------------------------------------------

def read_text_file(path: str) -> str:
    if not os.path.exists(path):
        print(f"  [SKIP] File not found: {path}")
        return ""
    print(f"  [OK] Reading file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text_from_url(url: str) -> str:
    if is_aistudio_url(url):
        return extract_from_aistudio_url(url)

    if is_gemini_share_url(url):
        return extract_from_gemini_share(url)

    print(f"  [FETCH] URL: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
        extracted = "\n".join(clean_lines)
        print(f"  [OK] Extracted {len(extracted):,} characters from URL.")
        return extracted

    except Exception as e:
        print(f"  [ERROR] Could not fetch URL: {url}\n  Reason: {e}")
        return f"\n[ERROR extracting URL: {url}]\n{str(e)}\n"


def collect_sources(text_files: list = None, urls: list = None) -> str:
    combined = ""

    if text_files:
        for path in text_files:
            combined += f"\n\n{'='*60}\n"
            combined += f"SOURCE FILE: {path}\n"
            combined += f"{'='*60}\n"
            combined += read_text_file(path)

    if urls:
        for url in urls:
            combined += f"\n\n{'='*60}\n"
            combined += f"SOURCE URL: {url}\n"
            combined += f"{'='*60}\n"
            combined += extract_text_from_url(url)

    return combined


# ---------------------------------------------------------------------------
# Gemini analysis
# ---------------------------------------------------------------------------

def generate_report(raw_data: str) -> str:
    print("\nSending data to Gemini... (this may take 1-2 minutes for large files)")

    prompt = f"""
Analyse les données brutes suivantes et produis un rapport complet d'organisation
de preuves juridiques EN FRANÇAIS UNIQUEMENT.

Concentre-toi particulièrement sur les événements à partir du 17 décembre 2024.

Données brutes :

{raw_data}
"""

    # Try models from best to most available (free tier)
    models_to_try = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ]

    last_error = None
    for model_name in models_to_try:
        try:
            print(f"  Trying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "temperature": 0.2,
                }
            )
            print(f"  [OK] Used model: {model_name}")
            return response.text
        except Exception as e:
            err_str = str(e)
            # Skip on quota or model-not-found errors and try next
            if any(code in err_str for code in ["429", "404", "RESOURCE_EXHAUSTED", "NOT_FOUND"]):
                print(f"  [SKIP] {model_name} — {('quota exceeded' if '429' in err_str else 'not available')}, trying next...")
                last_error = e
                continue
            raise  # Re-raise unexpected errors immediately

    raise RuntimeError(
        "\nAll Gemini models are unavailable with your current API key.\n\n"
        "Most likely cause: the free-tier daily quota is used up for today.\n\n"
        "Solutions:\n"
        "  1. Get a fresh API key at https://aistudio.google.com/app/apikey\n"
        "     (free keys reset daily — a new key works immediately)\n"
        "  2. Or wait until tomorrow for the quota to reset.\n"
        "  3. Or enable billing for unlimited access.\n\n"
        "Once you have a new key, update the ai_studio= line in your .env file."
    )


# ---------------------------------------------------------------------------
# Output: Markdown + PDF
# ---------------------------------------------------------------------------

def save_markdown(report_text: str):
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n[SAVED] Markdown: {OUTPUT_MD}")


def save_pdf(report_text: str):
    """Generate a clean PDF using reportlab (no system libraries required)."""
    NAVY = colors.HexColor("#1a2e4a")
    LIGHT_GREY = colors.HexColor("#f7f7f7")
    GOLD = colors.HexColor("#f0c040")
    WARN_BG = colors.HexColor("#fff8e1")

    styles = getSampleStyleSheet()

    style_normal = ParagraphStyle(
        "normal", parent=styles["Normal"],
        fontSize=10, leading=14, spaceAfter=4,
    )
    style_h1 = ParagraphStyle(
        "h1", parent=styles["Heading1"],
        fontSize=16, textColor=NAVY, spaceBefore=18, spaceAfter=6,
        borderPad=4,
    )
    style_h2 = ParagraphStyle(
        "h2", parent=styles["Heading2"],
        fontSize=13, textColor=NAVY, spaceBefore=14, spaceAfter=4,
    )
    style_h3 = ParagraphStyle(
        "h3", parent=styles["Heading3"],
        fontSize=11, textColor=NAVY, spaceBefore=10, spaceAfter=4,
    )
    style_bullet = ParagraphStyle(
        "bullet", parent=style_normal,
        leftIndent=16, bulletIndent=6, spaceAfter=2,
    )
    style_disclaimer = ParagraphStyle(
        "disclaimer", parent=style_normal,
        fontSize=9, textColor=colors.HexColor("#555555"),
        backColor=WARN_BG, borderColor=GOLD,
        borderWidth=1, borderPad=6,
    )

    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title="Legal Strategic Report",
    )

    story = []

    # Disclaimer banner
    story.append(Paragraph(
        "<b>AVERTISSEMENT / DISCLAIMER:</b> Ce rapport est une organisation factuelle "
        "assistée par IA destinée à être examinée par un avocat qualifié. Il ne constitue "
        "pas un conseil juridique. / This report does not constitute legal advice.",
        style_disclaimer,
    ))
    story.append(Spacer(1, 0.4 * cm))

    # Paragraph styles for table cells
    cell_style = ParagraphStyle(
        "cell", parent=style_normal,
        fontSize=8, leading=11, spaceAfter=0,
    )
    cell_header_style = ParagraphStyle(
        "cell_header", parent=cell_style,
        textColor=colors.white, fontName="Helvetica-Bold",
    )

    # Parse markdown line by line into reportlab flowables
    current_table_rows = []
    in_table = False
    is_header_row = True

    def make_cell(text, is_header=False):
        """Wrap cell text in a Paragraph so it word-wraps inside the cell."""
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
        style = cell_header_style if is_header else cell_style
        return Paragraph(safe, style)

    def smart_col_widths(col_count, page_width):
        """Assign widths based on column position for the 6-col timeline table.
        Narrow for date/time/source, wider for actor/event/note."""
        if col_count == 6:
            # Date, Heure, Source, Acteur, Événement, Note
            return [
                1.5 * cm,   # Date
                1.2 * cm,   # Heure
                2.2 * cm,   # Source
                2.6 * cm,   # Acteur Principal
                4.0 * cm,   # Événement / Action
                4.0 * cm,   # Note de Preuve
            ]
        # Generic: give equal weight but make last two columns wider
        if col_count >= 3:
            narrow = page_width * 0.10
            wide   = (page_width - narrow * (col_count - 2)) / 2
            return [narrow] * (col_count - 2) + [wide, wide]
        return [page_width / col_count] * col_count

    def flush_table():
        nonlocal current_table_rows, in_table, is_header_row
        if current_table_rows:
            col_count = max(len(r) for r in current_table_rows)
            col_widths = smart_col_widths(col_count, doc.width)

            # Convert all plain-string rows into Paragraph rows
            para_rows = []
            for i, row in enumerate(current_table_rows):
                is_hdr = (i == 0)
                # Pad short rows to full column count
                padded = row + [""] * (col_count - len(row))
                para_rows.append([make_cell(c, is_header=is_hdr) for c in padded])

            tbl = Table(para_rows, colWidths=col_widths, repeatRows=1,
                        hAlign="LEFT")
            tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
                ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 5),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.3 * cm))
        current_table_rows = []
        in_table = False
        is_header_row = True

    def clean(text):
        # Strip bold/italic markdown markers for reportlab XML safety
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
        text = re.sub(r"`(.+?)`",       r"<font name='Courier'>\1</font>", text)
        return text

    for line in report_text.splitlines():
        stripped = line.strip()

        # Markdown table row
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            # Skip separator rows like |---|---|
            if all(re.match(r"^[-: ]+$", c) for c in cells):
                continue
            current_table_rows.append(cells)
            continue
        else:
            if in_table:
                flush_table()

        if not stripped:
            story.append(Spacer(1, 0.2 * cm))
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(clean(stripped[4:]), style_h3))
        elif stripped.startswith("## "):
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=NAVY, spaceAfter=2))
            story.append(Paragraph(clean(stripped[3:]), style_h2))
        elif stripped.startswith("# "):
            story.append(Paragraph(clean(stripped[2:]), style_h1))
            story.append(HRFlowable(width="100%", thickness=1.5,
                                    color=NAVY, spaceAfter=4))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            story.append(Paragraph("• " + clean(stripped[2:]), style_bullet))
        elif stripped.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor("#cccccc"),
                                    spaceBefore=8, spaceAfter=8))
        else:
            story.append(Paragraph(clean(stripped), style_normal))

    if in_table:
        flush_table()

    doc.build(story)
    print(f"[SAVED] PDF: {OUTPUT_PDF}")


# ---------------------------------------------------------------------------
# MAIN — Add your sources here
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Legal Evidence Report Generator")
    print("Générateur de Rapport de Preuves Juridiques")
    print("=" * 60)

    # -------------------------------------------------------
    # STEP 1: Add your Gemini share links here.
    # ÉTAPE 1 : Ajoutez vos liens Gemini partagés ici.
    # Format: https://gemini.google.com/share/XXXXXXXX
    # The script will auto-detect and extract them.
    # -------------------------------------------------------
    gemini_share_urls = [
        "https://gemini.google.com/share/fabc7c91d915",
        # Add more Gemini share links here:
        # "https://gemini.google.com/share/XXXXXXXX",
    ]

    # -------------------------------------------------------
    # STEP 2: Add your Google AI Studio share links here (if any).
    # ÉTAPE 2 : Ajoutez vos liens Google AI Studio ici.
    # -------------------------------------------------------
    aistudio_urls = [
        # "https://aistudio.google.com/app/prompts?state=...",
    ]

    # -------------------------------------------------------
    # STEP 2: Add your local text files here (optional).
    # ÉTAPE 2 : Ajoutez vos fichiers texte locaux ici.
    # -------------------------------------------------------
    text_files = [
        "mes_messages.txt",
        "gemini_session_1.txt",
        "gemini_session_2.txt",
        "gemini_session_3.txt",
    ]

    # -------------------------------------------------------
    # STEP 3: Add any other public URLs here (optional).
    # ÉTAPE 3 : Autres URLs publiques (optionnel).
    # -------------------------------------------------------
    other_urls = [
        # "https://example.com/document",
    ]

    all_urls = gemini_share_urls + aistudio_urls + other_urls

    print("\nCollecting sources / Collecte des sources...")
    raw_data = collect_sources(text_files=text_files, urls=all_urls)

    if not raw_data.strip():
        print(
            "\nNo data found. Add your AI Studio links, text files, or URLs in main()."
            "\nAucune donnée trouvée. Ajoutez vos liens, fichiers ou URLs dans main()."
        )
        return

    char_count = len(raw_data)
    print(f"\nTotal data collected: {char_count:,} characters / ~{char_count // 1000} KB")

    report = generate_report(raw_data)

    print("\nSaving outputs / Sauvegarde des fichiers...")
    save_markdown(report)
    save_pdf(report)

    print("\n" + "=" * 60)
    print("DONE / TERMINÉ")
    print(f"  Markdown : {OUTPUT_MD}")
    print(f"  PDF      : {OUTPUT_PDF}")
    print("=" * 60)


if __name__ == "__main__":
    main()
