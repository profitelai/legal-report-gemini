# Legal Evidence Report Generator

An AI-powered tool that fetches Gemini conversation links, combines them, and generates a structured **PDF report** for your lawyer — in French, with a chronological timeline, contradictions, escalation curve, and evidence index.

---

## What it does

1. Fetches any number of shared Gemini conversation links automatically
2. Combines them with any local text files you provide
3. Sends everything to the Gemini AI for structured legal analysis
4. Exports a clean **PDF** and **Markdown** report ready to hand to your lawyer

---

## Requirements

- Python 3.9 or higher
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## Installation (one time only)

### Step 1 — Clone the project

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

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key

### Step 4 — Create your `.env` file

Copy the example file and add your key:

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder:

```
ai_studio=YOUR_GEMINI_KEY_HERE
```

---

## How to use it

### Step 1 — Add your Gemini conversation links

Open `legal_report_gemini.py` in any text editor.

Find the `gemini_share_urls` list and paste your links:

```python
gemini_share_urls = [
    "https://gemini.google.com/share/YOUR_FIRST_LINK",
    "https://gemini.google.com/share/YOUR_SECOND_LINK",
    "https://gemini.google.com/share/YOUR_THIRD_LINK",
    # Add as many as you need
]
```

**How to get a Gemini share link:**
- Open your conversation on [gemini.google.com](https://gemini.google.com)
- Click the **Share** button
- Copy the link that appears

### Step 2 — Run the tool

```bash
python3 legal_report_gemini.py
```

### Step 3 — Get your report

Two files will be created in the same folder:

| File | Description |
|---|---|
| `Legal_Strategic_Report.pdf` | Send this to your lawyer |
| `Legal_Strategic_Report.md` | Plain text version |

---

## What the report contains

The PDF is organized in chronological order with these sections:

1. **Résumé Exécutif** — Short factual overview
2. **Chronologie des Événements** — Timeline table: Date, Time, Source, Actor, Event, Evidence Note
3. **Contradictions et Violations Potentielles** — Where statements conflict or agreements were breached
4. **Courbe d'Escalade** — How tone shifted from cooperative to hostile
5. **Personnes Clés** — Each person's role based on the evidence
6. **Index des Preuves** — Full list of all documents, messages, and sources
7. **Questions pour l'Avocat** — Factual questions the lawyer should review

---

## If a conversation won't download automatically

Some Gemini links require a logged-in session. If the tool can't fetch a link automatically:

1. Open the link in Chrome while logged into your Google account
2. Press `Ctrl+A` (Windows) or `Cmd+A` (Mac) to select all
3. Copy and paste the text into `gemini_session_1.txt`
4. Add it to the `text_files` list in `main()`:
   ```python
   text_files = ["gemini_session_1.txt"]
   ```
5. Re-run the script

---

## If the API quota is exceeded

The tool automatically tries multiple Gemini models in order:
`gemini-2.5-pro` → `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-2.0-flash-lite`

If all are exhausted (free daily quota), get a new free key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) and update your `.env` file. Free keys reset daily.

---

## Supported input types

| Type | Example |
|---|---|
| Gemini share link | `https://gemini.google.com/share/XXXXXXXX` |
| Google AI Studio link | `https://aistudio.google.com/app/prompts?state=...` |
| Local text file | `mes_messages.txt`, `gemini_session_1.txt` |
| Any public URL | Any webpage with readable content |

---

## Project structure

```
legal-report-gemini/
├── legal_report_gemini.py   # Main script
├── requirements.txt         # Python dependencies
├── .env.example             # API key template
├── .gitignore               # Excludes .env and report files
└── README.md                # This file
```

---

## Disclaimer

This tool organizes evidence for review by a qualified lawyer. It does not constitute legal advice.

---

*Built with [Google Gemini API](https://ai.google.dev/) and [ReportLab](https://www.reportlab.com/).*
