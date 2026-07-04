# PlacementIQ

**A Multi-Agent AI Placement Preparation Coach**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq_Llama_3.3_70B-F55036?style=for-the-badge)
![Gemini](https://img.shields.io/badge/LLM-Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-16A34A?style=for-the-badge)
![Docker](https://img.shields.io/badge/Deploy-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

> PlacementIQ takes one resume and runs it through **three specialist AI agents, orchestrated in sequence** — Resume Agent → Skill-Gap Agent → Interview Agent — to produce a single readiness report and hand the candidate straight into a live, role-specific mock interview.

---

## 📑 Table of Contents

- [Why Multi-Agent](#-why-multi-agent)
- [System Architecture](#️-system-architecture)
- [Agent Responsibilities](#-agent-responsibilities)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Deployment](#-deployment)
- [API Reference](#-api-reference)
- [Prompt Engineering Notes](#-prompt-engineering-notes)
- [Roadmap](#️-roadmap)

---

## 🎯 Why Multi-Agent

Most placement-prep tools are a single prompt wrapped in a chat UI. PlacementIQ instead runs a **pipeline of specialist agents**, each with its own prompt, model, and responsibility, coordinated by an Orchestrator:

| Capability | Typical Single-Agent Bot | **PlacementIQ** |
|---|---|---|
| Resume review | Generic feedback | Structured scoring + extracted skills + role suggestion (Gemini, multimodal-ready) |
| Skill assessment | None | Deterministic gap analysis against a role's required-skill matrix |
| Interview prep | Static question list | RAG-retrieved, role-specific questions from a vector store |
| Interview delivery | N/A | Adaptive, multi-turn mock interview with follow-up questions (Groq / Llama 3.3 70B) |
| Personalization | None | Every downstream agent consumes the previous agent's structured output |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    📄 CANDIDATE RESUME (PDF/TXT)             │
└──────────────────────────────┬────────────────────────────────┘
                               │
              ╔════════════════▼═════════════════════╗
              ║   🧠 AGENT 1 · RESUME AGENT (Gemini)  ║
              ║   Extracts skills, scores resume,     ║
              ║   suggests a target role              ║
              ╚════════════════╤═════════════════════╝
                               │ structured JSON
              ╔════════════════▼═════════════════════╗
              ║  📊 AGENT 2 · SKILL-GAP AGENT          ║
              ║  Compares extracted skills against    ║
              ║  the target role's skill matrix       ║
              ╚════════════════╤═════════════════════╝
                               │ readiness score + gaps
              ╔════════════════▼═════════════════════╗
              ║ 🎤 AGENT 3 · INTERVIEW AGENT (Groq)    ║
              ║ RAG-seeds first question from ChromaDB║
              ║ then runs an adaptive multi-turn       ║
              ║ mock interview + final scoring         ║
              ╚═══════════════════════════════════════╝
                               │
                    ⚖️ ORCHESTRATOR ties all three
                    agents into one /pipeline/full-report call
```

---

## 🔍 Agent Responsibilities

| Agent | Model | Input | Output |
|---|---|---|---|
| **Resume Agent** | Gemini 2.0 Flash | Raw resume text (parsed from PDF/TXT) | Score, strengths, weaknesses, extracted skills, suggested role |
| **Skill-Gap Agent** | Deterministic (no LLM call — fast, explainable, zero hallucination risk) | Extracted skills + target role | Matched skills, missing skills, readiness % |
| **Interview Agent** | Groq — Llama 3.3 70B | Role + RAG-retrieved question bank (ChromaDB) | Adaptive Q&A turns + final communication/technical/confidence scores |
| **Orchestrator** | — | Resume text | Chains the above three end-to-end for the `/pipeline/full-report` route |

---

## 🛠️ Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI (Python) | Async, typed, auto-generated OpenAPI docs |
| LLM — reasoning/chat | Groq (Llama 3.3 70B) | Very low latency, ideal for a live back-and-forth mock interview |
| LLM — document understanding | Google Gemini | Strong structured-output + PDF/multimodal parsing |
| Vector DB | ChromaDB | Lightweight, embeddable, zero external infra — retrieves role-specific interview questions |
| Frontend | HTML / CSS / JavaScript (vanilla SPA) | No build step, fast to ship, easy to containerize |
| Deployment | Docker + Docker Compose, Nginx reverse proxy | Meets the "Docker" deployment requirement directly; portable to any host |

---

## 📁 Project Structure

```
placementiq/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── resume_agent.py       Gemini-based resume analysis
│   │   │   ├── skillgap_agent.py     Deterministic skill matching
│   │   │   ├── interview_agent.py    Groq-based adaptive interview
│   │   │   └── orchestrator.py       Chains all three agents
│   │   ├── rag/
│   │   │   └── vector_store.py       ChromaDB + custom hashing embedding fn
│   │   ├── routers/                  FastAPI route handlers
│   │   ├── core/config.py            Env-driven settings
│   │   └── main.py                   App entrypoint
│   ├── data/question_bank.json       Seed interview question bank
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── index.html / style.css / app.js
│   ├── Dockerfile
│   └── nginx.conf                    Proxies /api/* to the backend container
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

**1 · Clone & configure**
```bash
git clone <your-repo-url> && cd placementiq
cp backend/.env.example backend/.env
# Edit backend/.env with your GROQ_API_KEY and GEMINI_API_KEY
```

**2 · Run with Docker Compose (recommended)**
```bash
docker compose up --build
```
Visit **http://localhost** — the frontend is served by Nginx and proxies API calls to the backend automatically.

**3 · Or run locally without Docker**
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend — in a second terminal
cd frontend
python3 -m http.server 5500
# then edit app.js: set API_BASE = "http://localhost:8000"
```

---

## ☁️ Deployment

To get a public **Live Project Link**:

1. Push this repo to GitHub.
2. Create a free account on [Render](https://render.com) (or Railway).
3. **New → Web Service → Docker**, point it at `backend/Dockerfile`, add `GROQ_API_KEY` and `GEMINI_API_KEY` as environment variables.
4. **New → Static Site** (or a second Docker web service) for `frontend/`, and set its Nginx proxy target to the backend's public Render URL instead of `backend:8000`.
5. Copy the resulting public URL — that's your Live Project Link.

*(Docker itself already satisfies the "use Docker" deployment requirement even before pushing to a host — `docker compose up --build` is a complete, reproducible deployment.)*

---

## 📡 API Reference

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/health` | Liveness check |
| `POST` | `/api/resume/analyze` | Run only the Resume Agent |
| `POST` | `/api/skillgap/analyze` | Run only the Skill-Gap Agent |
| `POST` | `/api/interview/start` | Start a mock interview for a role |
| `POST` | `/api/interview/continue` | Send a candidate answer, get the next question |
| `POST` | `/api/interview/score` | Score a finished interview transcript |
| `POST` | `/api/pipeline/full-report` | **Orchestrator** — runs all three agents end-to-end |

Full interactive docs are auto-generated by FastAPI at `/docs` once the backend is running.

---

## ✍️ Prompt Engineering Notes

- **Structured-output constraints**: both the Resume Agent and the Interview scoring call are prompted to return *only* raw JSON matching an explicit schema, with a fallback parser in case a model wraps the response in markdown fences.
- **Role-conditioning**: the Interview Agent's system prompt is templated per target role so the same agent code serves any role without retraining or branching logic.
- **RAG grounding**: interview questions are retrieved from ChromaDB rather than generated fresh each time, which keeps question quality consistent and lets the question bank be extended with real, college-specific questions without touching any prompt.
- **Separation of concerns**: the Skill-Gap Agent deliberately makes **no LLM call at all** — it's a deterministic set comparison. This was a conscious design choice to avoid hallucinated skill-matching and to keep that step fast and explainable in a demo.

---

## 🗺️ Roadmap

| Stage | Status | Description |
|---|---|---|
| 1 | ✅ Done | Resume Agent + Gemini structured extraction |
| 2 | ✅ Done | Skill-Gap Agent + role skill matrices |
| 3 | ✅ Done | ChromaDB RAG question bank + Groq adaptive interview |
| 4 | ✅ Done | Orchestrator + full-pipeline API + dashboard UI |
| 5 | 🔲 Planned | College-specific question bank ingestion via PDF upload |
| 6 | 🔲 Planned | Persistent candidate history + progress tracking |

---

Built as an individual project — Prompt Engineering · LLM APIs (Groq, Gemini) · Vector DB (ChromaDB) · FastAPI · Docker.
