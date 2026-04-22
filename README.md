# 🌿 MyHealthHub

> **PDAI Assignment 3 · Mara Rüsen · ESADE Business School · 2026**

A personal health dashboard prototype for a fictional user **Celina Becker (35, Berlin)**, combining upcoming appointments, private-insurance finances, a full medical record history, and interactive analytics — all searchable through an AI chatbot that knows her data.

This is an **evolution** of my Assignment 2 project (DanceFinder), applying the same Streamlit + Claude + persistence stack to a completely new domain: **personal health data aggregation** instead of external service discovery.

---

## ✨ Features

| # | Feature | Detail |
|---|---|---|
| 1 | 📅 **Appointments** | 6 upcoming visits, email reminders that persist in SQLite |
| 2 | 💶 **Finances** | Private-insurance tariff, claims, reimbursements, **AI receipt scanner (upload/camera/example)** — protected by Face ID |
| 3 | 📋 **Records** | 10 historical visits — view **by specialty** OR as a **chronological timeline** |
| 4 | 📊 **Insights** | 4 interactive Plotly charts: spending trends, specialty donut, preventive-care gauge, reimbursement rates |
| 5 | 🔒 **Face ID auth** | Simulated biometric gate in front of sensitive financial data |
| 6 | 💬 **HealthBuddy** | Claude-powered chatbot with **full context** of Celina's data, persists history in SQLite |
| 7 | 🎨 **Warm theme** | Cream `#FFFBF5` + mint `#8FBC8F` |

---

## 🏗️ Tech Stack

- **Frontend:** Streamlit (multipage)
- **Charts:** Plotly (interactive)
- **AI:** Anthropic Claude (`claude-sonnet-4-6`) with a keyword-matching **demo-mode fallback** when no API key is set
- **Persistence:** SQLite (reminders, claim submissions, chat history)
- **Mock data:** JSON files in `data/`

---

## 📁 Project Structure

```
Assigment 3/
├── app.py                         ← Home dashboard
├── pages/
│   ├── 1_📅_Appointments.py
│   ├── 2_💶_Finances.py           (Face-ID-gated)
│   ├── 3_📋_Records.py            (Specialty OR Timeline view)
│   └── 4_📊_Insights.py           (4 interactive charts)
├── data/
│   ├── celina.json
│   ├── appointments.json
│   ├── records.json
│   ├── finances.json
│   └── myhealthhub.db             ← SQLite (gitignored, auto-created)
├── utils/
│   ├── data_loader.py
│   ├── auth.py                    ← Face ID simulation
│   ├── chatbot.py                 ← Claude + fallback + history
│   └── database.py                ← SQLite layer
├── .streamlit/
│   ├── config.toml                ← Warm mint theme
│   └── secrets.toml.example
├── requirements.txt
└── README.md
```

---

## 🚀 Run locally

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. (Optional) Add your Claude API key
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then edit the file and paste your key

# 3. Launch
streamlit run app.py
```

The app opens at `http://localhost:8501`.

**Without API key:** the chatbot runs in demo mode with pre-written answers to common questions.

---

## 🔄 Evolution from Assignment 2 (DanceFinder)

| Layer | DanceFinder (Assignment 2) | MyHealthHub (Assignment 3) |
|---|---|---|
| **Domain** | External discovery (dance classes in BCN) | Personal data aggregation (own health) |
| **Data source** | Web-scraped `classes.json` + `studios.json` | Mock JSON for fictional user Celina |
| **AI pattern** | Search-only chatbot (Claude + Cohere rerank) | **Context-aware assistant** — entire user record loaded as system prompt |
| **UI pattern** | List + map + filter bar | **KPI dashboard** + card grid + timeline |
| **Persistence** | SQLite for community ratings | SQLite for **reminders, claim submissions, chat history** |
| **New capability** | — | **Privacy-first UX** (Face ID auth gate for sensitive sections) |
| **Analytics** | — | **4 interactive Plotly charts** on spending, visits, preventive care |
| **Theme** | Dark | Warm cream + mint (healthcare-appropriate) |

---

## 🔐 Privacy note

All data is **fake**, locally stored. Face ID is a UX simulation — no real biometrics.

---

## 💡 Try these chatbot queries

- *"When is my next appointment?"*
- *"What did my last blood test show?"*
- *"How much have I paid out of pocket this year?"*
- *"What vaccinations am I up to date on?"*
- *"Am I allergic to anything?"*
- *"What's my insurance tariff?"*
