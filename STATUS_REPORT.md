# AISpark Studio — Full-Stack Architecture & Execution Audit

**Date:** 2026-03-01
**Audit Type:** Read-Only Deep Scan (production-code-audit, systematic-debugging, nextjs-app-router-patterns)
**Scope:** Entire codebase — FastAPI backend, Next.js frontend, Streamlit frontend, database, services
**Files Scanned:** 139+ source files across all directories

---

## 1. Executive Summary

AISpark Studio is an AI-powered prompt generation platform built on **FastAPI (Python)** with **Vertex AI Search RAG**, a **6-personality Helios system**, and a **Character Lock** consistency engine. The backend is **production-ready** with 40+ endpoints, 64/64 passing tests, and robust service architecture. The **Next.js frontend remains a boilerplate shell** with zero backend integration — this is the primary development blocker.

---

## 2. What Works Perfectly

### 2.1 FastAPI Backend
| Component | File | Size | Status |
|---|---|---|---|
| API Server (40+ endpoints) | `backend/main.py` | 730 lines | Working |
| Centralized Config | `backend/config.py` | — | Working |
| Pydantic Schemas | `backend/core/schemas.py` | — | Working |
| CRUD Operations | `backend/core/crud.py` | — | Working |

### 2.2 AI & RAG Pipeline
| Component | File | Size | Status |
|---|---|---|---|
| Unified AI Service | `backend/services/unified_ai_service.py` | 31KB | Working (Gemini 2.5-flash) |
| Vertex AI Search | `backend/services/vertex_search_service.py` | 19KB | Working (34 docs, vertex_first) |
| Prompt Critic | `backend/services/unified_critic_service.py` | 7KB | Working |

### 2.3 Creative Systems
| Component | File | Size | Status |
|---|---|---|---|
| Helios 6 Personalities | `backend/core/helios_personalities.py` | 19KB | Working (Prometheus, Zeus, Poseidon, Artemis, Dionysus, Athena) |
| Character Lock System | `backend/core/character_lock.py` | 17KB | Working (20+ visual attributes, session locking) |

### 2.4 Auth & Database
| Component | File | Status |
|---|---|---|
| JWT OAuth2 + Credits | `backend/core/auth.py` | Working |
| SQLAlchemy Models (5 tables) | `backend/core/models.py` | Working |
| SQLite WAL Mode | `backend/core/database.py` | Working |

### 2.5 Supporting Services
| Component | File | Status |
|---|---|---|
| Cache Layer (Redis + fallback) | `backend/services/cache_service.py` | Designed but **disabled** (`ENABLE_CACHE=false`) |
| Export (JSON/CSV/TXT) | `backend/services/export_service.py` | Working |
| Health Check | `backend/utils/health_check.py` | Working |

### 2.6 Testing
- **Location:** `backend/tests/`
- **Result:** 64/64 tests passing (100%)
- **Coverage:** Unit (character_lock, helios), API endpoints, Vertex Search integration

### 2.7 Streamlit Frontend (Legacy)
- **Location:** `frontend/`
- **Status:** Fully functional — auth, generation, history, knowledge base integration
- **API Client:** `frontend/api_client.py` — complete HTTP bridge to FastAPI

---

## 3. What Is Broken / Stuck

### 3.1 Next.js Frontend — Empty Shell (CRITICAL)
- **Location:** `nextjs-frontend/`
- **Current state:** Default `create-next-app` boilerplate, no custom development
- **Files:** Only `app/layout.tsx`, `app/page.tsx` (template), `globals.css`, `favicon.ico`

**Missing entirely:**
| Component | Status |
|---|---|
| `/app/api/` routes | Not created |
| Custom pages/components | Not created |
| HTTP client (axios, SWR, React Query) | Not installed |
| State management (Zustand, Redux, Jotai) | Not installed |
| UI library (shadcn/ui, Radix, MUI) | Not installed |
| Form handling (React Hook Form) | Not installed |
| `.env.local` for backend URL | Not created |
| API integration with FastAPI | Not implemented |
| Auth flow (JWT cookie/header) | Not implemented |

**TypeScript check:** `npx tsc --noEmit` — **0 errors** (trivially passing — no custom code)

### 3.2 RAG Pipeline — Hardcoded Query (HIGH)
- **File:** `backend/services/unified_ai_service.py`, line ~440
- **Problem:** Search query is hardcoded to `["video", "generation", "prompt", "technique", "style"]`
- **Impact:** Same 3 documents returned regardless of user input — RAG context is **not dynamic**
- **See:** `docs/SYSTEM_AUDIT_REPORT.md` Strategy 1 for fix

### 3.3 Helios Not Connected to RAG (MEDIUM)
- **Problem:** Personality selection happens independently from Vertex Search queries
- **Impact:** A "Prometheus" (technical) request retrieves same docs as a "Zeus" (narrative) request
- **See:** `docs/SYSTEM_AUDIT_REPORT.md` Strategy 2 for fix

### 3.4 Dual Cache Problem (MEDIUM)
- **Problem:** `UnifiedAIService` has its own `self.cache` dict (line 63) separate from `CacheService`
- **Impact:** Cache inconsistency — a prompt cached in one layer may be evicted from the other
- **Note:** `CacheService` is also disabled via env config

### 3.5 Empty Knowledge Base Fallback (MEDIUM)
- **Directory:** `knowledge_base/`
- **Problem:** Directory is empty — local RAG fallback will never return content
- **Impact:** If Vertex Search fails, zero knowledge augmentation

### 3.6 SQLite StaticPool Bottleneck (MEDIUM)
- **File:** `backend/core/database.py`
- **Problem:** `StaticPool` uses single connection for all threads
- **Impact:** Serialization bottleneck under concurrent async requests

### 3.7 Security Items (LOW-MEDIUM)
| Issue | Severity | File |
|---|---|---|
| CORS `allow_origins=["*"]` | Medium | `backend/main.py` |
| `secret_key` has hardcoded default | Medium | `backend/config.py` |
| Debug `print()` in production code | Low | `unified_ai_service.py:661` |
| Inconsistent import paths | Low | Various |

---

## 4. Database Schema Overview

```
users (8 cols)
├── id, email (unique), full_name, hashed_password
├── is_active, credits
└── created_at, updated_at

generated_prompts (6 cols)
├── id, title, raw_response (JSON blob)
├── is_favorite, owner_id (FK → users)
└── created_at

feedback (6 cols)
├── id, liked, comment
├── prompt_id (FK → generated_prompts)
├── user_id (FK → users)
└── created_at

api_usage (7 cols)          ⚠️ Missing index on created_at
├── id, user_id (FK), endpoint, method
├── response_time_ms, status_code, error_message
└── created_at

system_metrics (6 cols)     ⚠️ Missing index on metric_name + recorded_at
├── id, metric_name, metric_value, metric_type
├── tags (JSON)
└── recorded_at
```

---

## 5. Architecture Diagram (Current State)

```
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  Streamlit Frontend  │────▶│   FastAPI Backend     │────▶│  Vertex AI Search │
│  (frontend/app.py)   │ HTTP│   (backend/main.py)   │     │  (34 docs, RAG)   │
│  Port: 8503          │     │   Port: 8001          │     │  Discovery Engine  │
└─────────────────────┘     └──────────────────────┘     └──────────────────┘
                                     │          │
                                     │          ▼
                                     │    ┌──────────────┐
                                     │    │  Google AI    │
                                     │    │  Gemini 2.5   │
                                     │    │  Flash        │
                                     │    └──────────────┘
                                     ▼
                              ┌──────────────┐
                              │  SQLite DB    │
                              │  (WAL Mode)   │
                              └──────────────┘

┌─────────────────────┐
│  Next.js Frontend    │
│  (nextjs-frontend/)  │────▶  ❌ NO BACKEND INTEGRATION
│  Port: 3000          │
└─────────────────────┘
```

---

## 6. Prioritized Atomic Action Plan

### Phase 1: Next.js Frontend Bridge (CRITICAL — Unblocks everything)

| Step | Action | Command / Detail |
|---|---|---|
| 1.1 | Install core dependencies | `cd nextjs-frontend && npm install axios swr zustand` |
| 1.2 | Install UI framework | `npx shadcn@latest init` |
| 1.3 | Create `.env.local` | `NEXT_PUBLIC_API_URL=http://localhost:8001` |
| 1.4 | Create TypeScript API client | `lib/api-client.ts` — typed wrapper for all FastAPI endpoints |
| 1.5 | Implement auth flow | JWT token storage, login/register pages, auth context |
| 1.6 | Build main dashboard page | `app/dashboard/page.tsx` — prompt generation + history |
| 1.7 | Build generation form | Integrate with `/generate` and `/helios/auto-generate` |
| 1.8 | Build prompt history | Fetch from `/prompts` with pagination |
| 1.9 | Build character manager | CRUD UI for Character Lock System |
| 1.10 | Build Helios personality selector | Visual personality picker + stats |

### Phase 2: RAG Pipeline Optimization (HIGH)

| Step | Action | File |
|---|---|---|
| 2.1 | Dynamic query construction from user input | `unified_ai_service.py` — replace hardcoded search terms |
| 2.2 | Connect Helios personality keywords to RAG queries | `unified_ai_service.py` — inject personality context |
| 2.3 | Add relevance threshold filtering | `unified_ai_service.py` — filter low-score results |
| 2.4 | Populate `knowledge_base/` or remove fallback | Decision needed |

### Phase 3: Operational Hardening (MEDIUM)

| Step | Action | File |
|---|---|---|
| 3.1 | Consolidate dual cache into single CacheService | `unified_ai_service.py` + `cache_service.py` |
| 3.2 | Enable cache service | Set `AISPARK_ENABLE_CACHE=true` in `.env` |
| 3.3 | Add missing DB indexes | `api_usage.created_at`, `system_metrics.metric_name` |
| 3.4 | Restrict CORS origins | Replace `["*"]` with specific frontend URLs |
| 3.5 | Enforce secret_key via env validation | Remove hardcoded default in `config.py` |
| 3.6 | Remove debug print() | `unified_ai_service.py:661` |
| 3.7 | Configure Alembic for migrations | Add `alembic.ini` + migration scripts |

### Phase 4: Production Scaling (FUTURE)

| Step | Action |
|---|---|
| 4.1 | Migrate SQLite → PostgreSQL |
| 4.2 | Switch from StaticPool to connection pooling |
| 4.3 | Enable Redis cache with proper configuration |
| 4.4 | Add real-time streaming (WebSocket/SSE) for generation |
| 4.5 | Implement rate limiting at API gateway level |

---

## 7. File Reference Map

### Working Files
| File | Purpose | Status |
|---|---|---|
| `backend/main.py` | FastAPI app, 40+ endpoints | Working |
| `backend/config.py` | Centralized settings | Working |
| `backend/core/models.py` | SQLAlchemy models (5 tables) | Working |
| `backend/core/schemas.py` | Pydantic validation | Working |
| `backend/core/auth.py` | JWT authentication | Working |
| `backend/core/crud.py` | Database CRUD | Working |
| `backend/core/character_lock.py` | Character consistency (17KB) | Working |
| `backend/core/helios_personalities.py` | 6 personalities (19KB) | Working |
| `backend/services/unified_ai_service.py` | AI generation + RAG (31KB) | Working (with noted issues) |
| `backend/services/vertex_search_service.py` | Vertex AI Search (19KB) | Working |
| `backend/services/unified_critic_service.py` | Prompt analysis (7KB) | Working |
| `backend/services/cache_service.py` | Cache layer (16KB) | Disabled |
| `backend/services/export_service.py` | Export JSON/CSV/TXT (6KB) | Working |
| `frontend/app.py` | Streamlit UI | Working (legacy) |
| `frontend/api_client.py` | API client bridge | Working |

### Boilerplate (Needs Development)
| File | Purpose | Status |
|---|---|---|
| `nextjs-frontend/app/page.tsx` | Home page | Template only |
| `nextjs-frontend/app/layout.tsx` | Root layout | Minimal |
| `nextjs-frontend/next.config.ts` | Config | Empty |

### Documentation
| File | Purpose |
|---|---|
| `IMPLEMENTATION_PLAN.md` | Feature roadmap |
| `DEVELOPMENT_ROADMAP.md` | Phase completion status |
| `docs/SYSTEM_AUDIT_REPORT.md` | Previous architecture audit (2026-02-27) |

---

**End of Report**

*Generated by Claude Code — Read-only audit, no source files modified.*
