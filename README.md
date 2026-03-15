<<<<<<< HEAD
# AI Website Auditor

A full-stack web app (Flask + Vanilla JS) that analyzes a website and returns SEO, UX, and performance suggestions using Google PageSpeed Insights + OpenAI.

## Project structure

```
/ai-website-auditor
  /templates
    index.html
    result.html
  /static
    style.css
    script.js
  app.py
  requirements.txt
  database.db (created automatically)
```

## Setup

1. Create and activate a Python virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables (Windows PowerShell example):

```powershell
$env:OPENAI_API_KEY="your_openai_key"
$env:PAGESPEED_API_KEY="your_pagespeed_key"
```

4. Run the app:

```bash
python app.py
```

5. Open http://localhost:5000.

## Notes

- The app stores audit entries in `database.db`.
- If `PAGESPEED_API_KEY` is missing, performance scores will return `null` and the app continues.
- If `OPENAI_API_KEY` is missing, AI summary will show a helpful message.

## How it works

- User submits URL + email on landing page.
- Backend fetches HTML and extracts title, meta description, H1 headings, and word count.
- It calls Google PageSpeed Insights (mobile strategy) for performance metrics.
- It sends combined data to OpenAI for audit recommendations.
- Results are saved in SQLite and sent to frontend.
- Frontend displays audit in a result dashboard.
=======
# AI-website-auditor
>>>>>>> 003a06de1ed12ed0317d387b8c22ed083b334dca
