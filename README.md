# Legal Evidence Report Generator — AI-Powered PDF for Lawyers

> Generate a structured **legal evidence report PDF** from your Gemini AI conversations in minutes.
> Organize your case timeline, contradictions, and key actors — ready to hand directly to your lawyer.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Gemini AI](https://img.shields.io/badge/Powered%20by-Gemini%20AI-orange)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![PDF Output](https://img.shields.io/badge/Output-PDF%20%2B%20Markdown-red)](DEMO_Report.pdf)

---

## What Is This Tool?

**Legal Evidence Report Generator** is an open-source Python tool that:

- Automatically fetches your **shared Gemini AI conversations** via link
- Combines multiple sessions into a single unified evidence base
- Uses **Gemini AI** to analyze, organize, and structure all information
- Exports a **professional PDF legal evidence report** and Markdown file

The output is a lawyer-ready document organized with:
- Chronological timeline of events
- Identified contradictions and potential agreement violations
- Behavioral escalation curve (cooperative → hostile)
- Index of all evidence and sources
- Questions suggested for legal review

**Languages:** French (default) — ideal for Quebec / Canadian law practice.

---

## Demo Report

See a real sample output generated from Gemini conversations:

- [DEMO_Report.md](DEMO_Report.md) — view directly on GitHub
- [DEMO_Report.pdf](DEMO_Report.pdf) — download the formatted PDF

---

## Who Is This For?

| Use Case | Description |
|---|---|
| **Individuals preparing a legal case** | Organize months of messages, emails, and conversations into one clear document |
| **Lawyers and paralegals** | Receive structured, AI-analyzed evidence from clients in PDF format |
| **Mediators and arbitrators** | Review a neutral chronological timeline with flagged contradictions |
| **Anyone documenting a dispute** | Non-violence agreements, custody, business, harassment, property — any case |

---

## Key Features

- **Automatic Gemini link extraction** — paste a `gemini.google.com/share/` link, the tool fetches it automatically using a headless browser
- **Multi-session combining** — add 2, 5, or 20 links and they are all merged before analysis
- **Smart PDF layout** — chronological table with auto-wrapping text, no overlap, clean columns
- **AI model fallback** — tries `gemini-2.5-pro` → `gemini-2.5-flash` → `gemini-2.0-flash` automatically if quota is exceeded
- **No private data committed** — `.env` and all personal files are gitignored by default
- **Works offline with text files** — if a link can't be fetched, paste the conversation into a `.txt` file

---

## Installation

### Requirements

- Python 3.9 or higher
- Free [Gemini API key](https://aistudio.google.com/app/apikey) (Google account required)

### Step 1 — Clone

```bash
git clone https://github.com/profitelai/legal-report-gemini.git
cd legal-report-gemini
```

### Step 2 — Install dependencies

```bash
pip3 install -r requirements.txt
python3 -m playwright install chromium
```

### Step 3 — Get a free Gemini API key

1. Visit [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key

### Step 4 — Configure your `.env` file

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder:

```
ai_studio=YOUR_GEMINI_API_KEY_HERE
```

---

## How to Run

### Step 1 — Add your Gemini conversation links

Open `legal_report_gemini.py` and paste your links:

```python
gemini_share_urls = [
    "https://gemini.google.com/share/YOUR_FIRST_LINK",
    "https://gemini.google.com/share/YOUR_SECOND_LINK",
    # Add as many as needed
]
```

**How to get a Gemini share link:**
1. Open your conversation at [gemini.google.com](https://gemini.google.com)
2. Click the **Share** button (top right)
3. Copy the link

### Step 2 — Run

```bash
python3 legal_report_gemini.py
```

### Step 3 — Get your legal evidence report

Two files are created automatically:

```
Legal_Strategic_Report.pdf   ← Send this to your lawyer
Legal_Strategic_Report.md    ← Plain text version
```

---

## Report Structure

The generated PDF legal evidence report contains these sections, in order:

| Section | Description |
|---|---|
| **1. Résumé Exécutif** | Short factual overview of the situation |
| **2. Chronologie des Événements** | Timeline: Date, Time, Source, Actor, Event, Evidence Note |
| **3. Contradictions et Violations Potentielles** | Where statements conflict or agreements appear breached |
| **4. Courbe d'Escalade** | Tone progression: Cooperative → Tense → Hostile |
| **5. Personnes Clés** | Each actor's role based only on provided evidence |
| **6. Index des Preuves** | Full list of documents, messages, and sources |
| **7. Questions pour l'Avocat** | Suggested factual questions for legal review |

---

## Supported Input Types

| Source | Format |
|---|---|
| Gemini shared conversation | `https://gemini.google.com/share/XXXXXXXX` |
| Google AI Studio prompt | `https://aistudio.google.com/app/prompts?state=...` |
| Manual copy-paste | `.txt` file (any name) |
| Public web page | Any readable URL |

---

## Frequently Asked Questions

**Can I use this for any type of legal case?**
Yes. The tool works for any dispute: custody, harassment, business contracts, property, mediation agreements, etc.

**Is my data sent to Google?**
The text from your conversations is sent to the Gemini API for analysis. Review [Google's privacy policy](https://policies.google.com/privacy) before use. Do not commit your `.env` file.

**The report says "potential" and "appears to" everywhere — why?**
This tool does not give legal advice. Neutral language is intentional so a qualified lawyer can make the final assessment.

**What if a Gemini link won't download?**
Some private links require a logged-in browser session. In that case:
1. Open the link in Chrome
2. Press `Ctrl+A` / `Cmd+A` to select all text
3. Paste into `gemini_session_1.txt`
4. Add the filename to the `text_files` list and re-run

**What if I get a quota error?**
The tool automatically tries multiple models. If all free-tier models are exhausted, get a new free key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) (resets daily).

**Can I run this in French only?**
Yes — the default output is French. The AI prompt is configured for French legal terminology.

---

## Project Structure

```
legal-report-gemini/
├── legal_report_gemini.py   # Main script
├── requirements.txt         # Python dependencies
├── .env.example             # API key template (safe to share)
├── .gitignore               # Excludes .env, reports, personal files
├── DEMO_Report.md           # Sample output (Markdown)
├── DEMO_Report.pdf          # Sample output (PDF)
└── README.md                # This file
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `google-genai` | Gemini AI API client |
| `playwright` | Headless browser to fetch Gemini share pages |
| `beautifulsoup4` | HTML parsing |
| `reportlab` | PDF generation (no system libraries needed) |
| `markdown` | Markdown processing |
| `python-dotenv` | `.env` file loading |
| `requests` | HTTP requests |

---

## Disclaimer

This tool organizes and structures evidence for review by a qualified lawyer.
**It does not constitute legal advice.**
Always consult a licensed attorney for legal matters.

---

## License

MIT License — free to use, modify, and distribute.

---

*Built with [Google Gemini API](https://ai.google.dev/) · [ReportLab](https://www.reportlab.com/) · [Playwright](https://playwright.dev/)*
