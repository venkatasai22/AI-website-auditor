import os
import sqlite3
import re
import requests
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify, redirect, url_for
from bs4 import BeautifulSoup
import openai

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), "database.db")

# Initialize API keys from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_url TEXT NOT NULL,
            email TEXT,
            title TEXT,
            meta_description TEXT,
            h1_headings TEXT,
            word_count INTEGER,
            performance_score REAL,
            accessibility_score REAL,
            seo_score REAL,
            ai_summary TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    conn.close()


def normalize_url(url):
    if not url:
        return None
    url = url.strip()
    if not urlparse(url).scheme:
        url = "https://" + url
    return url


def extract_seo_data(html):
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "").strip()
    meta_desc = ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    if description_tag and description_tag.get("content"):
        meta_desc = description_tag["content"].strip()
    h1_tags = [h.text.strip() for h in soup.find_all("h1") if h.text.strip()]
    text = soup.get_text(separator=" ")
    words = re.findall(r"\w+", text)
    word_count = len(words)
    return {
        "title": title,
        "meta_description": meta_desc,
        "h1_headings": h1_tags,
        "word_count": word_count,
    }


def call_pagespeed(url):
    if not PAGESPEED_API_KEY:
        return {
            "performance": None,
            "accessibility": None,
            "seo": None,
            "warnings": "PAGESPEED_API_KEY not configured",
        }
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "key": PAGESPEED_API_KEY,
        "strategy": "mobile",
    }
    response = requests.get(endpoint, params=params, timeout=15)
    if response.status_code != 200:
        return {
            "performance": None,
            "accessibility": None,
            "seo": None,
            "warnings": f"Pagespeed API status {response.status_code}",
        }
    data = response.json()
    lighthouse = data.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})
    performance = categories.get("performance", {}).get("score")
    accessibility = categories.get("accessibility", {}).get("score")
    seo = categories.get("seo", {}).get("score")
    return {
        "performance": round(performance * 100, 2) if performance is not None else None,
        "accessibility": round(accessibility * 100, 2) if accessibility is not None else None,
        "seo": round(seo * 100, 2) if seo is not None else None,
        "warnings": None,
    }


def generate_ai_report(website_url, seo_data, pagespeed_data):
    if not OPENAI_API_KEY:
        return "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
    prompt = f"""
You are an AI Website Auditor. Analyze this website data and return a concise report.
Website: {website_url}

SEO extracted:
- title: {seo_data['title']}
- meta_description: {seo_data['meta_description']}
- h1_headings: {', '.join(seo_data['h1_headings'])}
- word_count: {seo_data['word_count']}

PageSpeed data:
- performance: {pagespeed_data.get('performance')}
- accessibility: {pagespeed_data.get('accessibility')}
- seo: {pagespeed_data.get('seo')}

Provide:
1) Top 3 SEO improvement suggestions.
2) Top 3 UX improvement suggestions.
3) Top 3 performance optimization tips.
4) Overall score out of 100 with short rationale.
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful technical website auditor assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/result")
def result():
    return render_template("result.html")


@app.route("/audit", methods=["POST"])
def audit():
    data = request.get_json() or {}
    website_url = normalize_url(data.get("website_url"))
    email = data.get("email", "")

    if not website_url:
        return jsonify({"error": "URL is required."}), 400

    try:
        response = requests.get(website_url, timeout=15, headers={"User-Agent": "AI-Website-Auditor/1.0"})
        response.raise_for_status()
    except Exception as exc:
        return jsonify({"error": f"Unable to fetch website: {exc}"}), 400

    seo_data = extract_seo_data(response.text)
    pagespeed_data = call_pagespeed(website_url)

    try:
        ai_summary = generate_ai_report(website_url, seo_data, pagespeed_data)
    except Exception as exc:
        ai_summary = f"AI report generation failed: {exc}"

    performance_score = pagespeed_data.get("performance")
    accessibility_score = pagespeed_data.get("accessibility")
    seo_page_speed_score = pagespeed_data.get("seo")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audits (website_url, email, title, meta_description, h1_headings, word_count, performance_score, accessibility_score, seo_score, ai_summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            website_url,
            email,
            seo_data["title"],
            seo_data["meta_description"],
            ", ".join(seo_data["h1_headings"]),
            seo_data["word_count"],
            performance_score,
            accessibility_score,
            seo_page_speed_score,
            ai_summary,
        ),
    )
    conn.commit()
    conn.close()

    report = {
        "website_url": website_url,
        "title": seo_data["title"],
        "meta_description": seo_data["meta_description"],
        "h1_headings": seo_data["h1_headings"],
        "word_count": seo_data["word_count"],
        "performance_score": performance_score,
        "accessibility_score": accessibility_score,
        "seo_score": seo_page_speed_score,
        "ai_summary": ai_summary,
    }

    return jsonify({"report": report})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
