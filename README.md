<p align="center"><img src="docs/assets/banner.png" alt="AISpark Studio Banner" width="100%"></p>

# AISpark Studio

> AI-powered creative prompt generation platform with RAG, 6 Helios personalities, and visual character consistency.

[![CI](https://github.com/mindmnml-del/asparklast/actions/workflows/ci.yml/badge.svg)](https://github.com/mindmnml-del/asparklast/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15.5-000000?style=flat&logo=nextdotjs&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-Vertex_AI-4285F4?style=flat&logo=googlecloud&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

---

## Overview

AISpark Studio is a full-stack creative AI platform that generates high-quality prompts for image, video, and text generation. It combines a **FastAPI** backend with a **Next.js** frontend, powered by **Google Vertex AI Search** as a RAG (Retrieval-Augmented Generation) knowledge base and **Gemini 2.5-flash** as the generation model.

---

## Key Features

| Feature | Description |
|---|---|
| **Helios Personalities** | 6 distinct creative AI personalities (Prometheus, Athena, Hermes, Apollo, Artemis, Hephaestus) that shape generation style |
| **Character Lock System** | Visual consistency tracking across generations — maintains 20+ character attributes for coherent multi-prompt workflows |
| **Vertex AI Search RAG** | 34-document knowledge base via Google Discovery Engine, queried at generation time |
| **Self-Critique Pipeline** | Generated prompts are automatically analyzed and refined before delivery |
| **Multi-format Export** | Structured JSON, plain text, and tool-specific output formats |
| **JWT Authentication** | Secure user accounts with token-based auth and role separation |

---

## Architecture

```
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  Next.js Frontend │────▶│   FastAPI Backend     │────▶│  Vertex AI Search │
│  (App Router)     │HTTP │   (40+ endpoints)     │     │  (34 docs, RAG)   │
│  Port: 3000       │     │   Port: 8001          │     │  Discovery Engine  │
└──────────────────┘     └──────────────────────┘     └──────────────────┘
                                    │          │
                                    ▼          ▼
                             ┌──────────┐  ┌──────────────┐
                             │ SQLite DB │  │ Gemini 2.5   │
                             │ 5 tables │  │ Flash        │
                             └──────────┘  └──────────────┘
```

### Backend Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── config.py                  # Centralized settings (pydantic-settings)
├── core/
│   ├── models.py              # SQLAlchemy ORM models
│   ├── schemas.py             # Pydantic request/response schemas
│   ├── crud.py                # Database operations
│   ├── auth.py                # JWT authentication
│   ├── character_lock.py      # Character consistency system
│   └── helios_personalities.py # 6 Helios creative personalities
├── services/
│   ├── unified_ai_service.py  # Primary AI generation pipeline
│   ├── vertex_search_service.py # Google Vertex AI Search (RAG)
│   ├── unified_critic_service.py # Self-critique & refinement
│   ├── cache_service.py       # Response caching layer
│   └── export_service.py      # Multi-format export
├── api/
│   ├── v1/                    # API v1 routes
│   └── v2/                    # API v2 routes (B2B, admin)
└── tests/
    ├── test_api_endpoints.py
    ├── test_vertex_search.py
    └── unit/
```

---

## Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **Google Cloud** project with:
  - Vertex AI Search enabled (Discovery Engine)
  - Service account with `discoveryengine.viewer` role
  - Gemini API access
- **Google AI Studio** API key (for Gemini)

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/mindmnml-del/asparklast.git
cd asparklast
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials (see Environment Variables section)

# Start the backend server
uvicorn main:app --reload --port 8001
```

Backend will be available at `http://localhost:8001`
API docs at `http://localhost:8001/docs`

### 3. Frontend Setup

```bash
cd nextjs-frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8001

# Start the development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

---

## Environment Variables

Create `backend/.env` based on `backend/.env.example`:

```env
# Google AI
AISPARK_GOOGLE_API_KEY=your_google_ai_studio_key

# Security (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
AISPARK_SECRET_KEY=your_secret_key

# Database
AISPARK_DATABASE_URL=sqlite:///./aispark_studio.db

# AI Model
AISPARK_AI_MODEL_NAME=gemini-2.5-flash
AISPARK_AI_TEMPERATURE=0.8
AISPARK_AI_MAX_TOKENS=2048

# RAG Mode: vertex_first | local_first | vertex_only | local_only
AISPARK_RAG_MODE=vertex_first

# Vertex AI Search
AISPARK_VERTEX_SEARCH_ENABLED=true
AISPARK_VERTEX_PROJECT_ID=your_gcp_project_id
AISPARK_VERTEX_LOCATION=global
AISPARK_VERTEX_DATA_STORE_ID=your_data_store_id
AISPARK_VERTEX_ENGINE_ID=your_engine_id
AISPARK_VERTEX_GEN_LOCATION=us-central1

# Google Cloud Auth
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
GOOGLE_CLOUD_PROJECT=your_gcp_project_id

# CORS
AISPARK_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_api_endpoints.py -v
python -m pytest tests/test_vertex_search.py -v
python -m pytest tests/unit/ -v

# Run with coverage report
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

### Frontend Tests

```bash
cd nextjs-frontend

# Lint check
npm run lint

# End-to-end tests (requires running backend)
npm run test:e2e

# E2E with UI
npm run test:e2e:ui
```

---

## API Reference

Once the backend is running, full interactive docs are available at:

- **Swagger UI:** `http://localhost:8001/docs`
- **ReDoc:** `http://localhost:8001/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/token` | Obtain JWT token |
| `POST` | `/generate` | Generate AI prompt |
| `GET` | `/prompts` | List saved prompts |
| `GET` | `/health` | Service health check |
| `GET` | `/characters` | List character sheets |
| `POST` | `/characters` | Create character sheet |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.115+, Python 3.11+, SQLAlchemy 2.0, Uvicorn |
| Frontend | Next.js 15.5, React 19, Tailwind CSS v4, Zustand, TanStack Query |
| AI / RAG | Google Gemini 2.5-flash, Vertex AI Search (Discovery Engine) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Database | SQLite (development) → PostgreSQL (production path) |
| Testing | pytest, pytest-asyncio, Playwright |

---

## Project Structure (Root)

```
aispark-studio/
├── backend/               # FastAPI application
├── nextjs-frontend/       # Next.js 15 frontend
├── knowledge_base/        # Local RAG document fallback
├── docs/                  # Internal documentation
├── CLAUDE.md              # Claude Code configuration
└── README.md
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
