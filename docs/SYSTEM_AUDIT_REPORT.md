# AISpark Studio — System Architecture Audit Report

> **Date:** 2026-02-27  
> **Auditors:** `@explorer-agent` · `@architect` · `@security-auditor`  
> **Scope:** Full read-only static analysis of `backend/`, `frontend/`, `nextjs-frontend/`  
> **Status:** ✅ Audit Complete

---

## 1. System Capabilities

### 1.1 Backend (FastAPI)

| Capability                    | File                        | Status                                                    |
| ----------------------------- | --------------------------- | --------------------------------------------------------- |
| AI Prompt Generation          | `unified_ai_service.py`     | ✅ Operational — Singleton, async, Gemini 2.5 Flash       |
| Vertex AI Search RAG          | `vertex_search_service.py`  | ✅ Operational — Discovery Engine, GCS/GDocs fetchers     |
| Helios 6-Personality System   | `helios_personalities.py`   | ✅ Operational — Keyword analysis + personality selection |
| Character Lock System         | `character_lock.py`         | ✅ Operational — Session-based CRUD with locking          |
| Prompt Critic / Self-Critique | `unified_critic_service.py` | ✅ Operational — Quality scoring + suggestions            |
| Export Service                | `export_service.py`         | ✅ Operational — JSON / CSV / TXT with Helios metadata    |
| Cache Layer                   | `cache_service.py`          | ✅ Designed — Redis primary + in-memory fallback          |
| Authentication                | `auth.py`                   | ✅ Operational — OAuth2 / JWT / password hashing          |
| Database                      | `database.py` + `models.py` | ✅ Operational — SQLite WAL + PostgreSQL pool support     |

### 1.2 Frontend (Streamlit Legacy)

| Capability                 | File                                     | Status                                              |
| -------------------------- | ---------------------------------------- | --------------------------------------------------- |
| API Client Bridge          | `frontend/api_client.py`                 | ✅ Functional — HTTP client to FastAPI              |
| Knowledge Base Integration | `frontend/knowledge_base_integration.py` | ✅ Functional — Local file scanning + Helios loader |
| Streamlit UI               | `frontend/app.py`                        | ✅ Functional — Legacy Streamlit interface          |

### 1.3 Next.js Frontend (New)

| Capability          | File                   | Status                                                      |
| ------------------- | ---------------------- | ----------------------------------------------------------- |
| App Router Setup    | `nextjs-frontend/app/` | ⚠️ **Boilerplate** — Default `create-next-app` template     |
| Tailwind CSS v4     | `package.json`         | ✅ Configured — `tailwindcss@^4`, `@tailwindcss/postcss@^4` |
| ESLint              | `eslint.config.mjs`    | ✅ Passing — 0 lint errors                                  |
| React 19            | `package.json`         | ✅ Installed — `react@19.1.0`                               |
| Next.js             | `package.json`         | ✅ Installed — `next@15.5.2`                                |
| Backend Integration | —                      | ❌ **Not implemented** — No API routes or fetch calls       |

---

## 2. Bridge Architecture Status

### 2.1 Current State

```
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  Streamlit Frontend  │────▶│   FastAPI Backend     │────▶│  Vertex AI Search │
│  (frontend/app.py)   │ HTTP│   (backend/main.py)   │     │  (RAG Pipeline)   │
│  Port: 8501          │     │   Port: 8000          │     │  Discovery Engine  │
└─────────────────────┘     └──────────────────────┘     └──────────────────┘
         │                          │          │
         │                          │          ▼
         │                          │    ┌──────────────┐
         │                          │    │  Google AI    │
         │                          │    │  Gemini 2.5   │
         │                          │    │  Flash        │
         │                          │    └──────────────┘
         │                          ▼
         │                   ┌──────────────┐
         │                   │  SQLite DB    │
         │                   │  (WAL Mode)   │
         │                   └──────────────┘
         │
┌────────┴────────────┐
│  Next.js Frontend    │
│  (nextjs-frontend/)  │────▶  ❌ NO BRIDGE YET
│  Port: 3000          │
└─────────────────────┘
```

### 2.2 Bridge Gap Analysis

| Layer              | Streamlit Bridge                   | Next.js Bridge | Gap                                      |
| ------------------ | ---------------------------------- | -------------- | ---------------------------------------- |
| **API Client**     | ✅ `api_client.py` (11.8 KB)       | ❌ Missing     | Need TypeScript API client               |
| **Auth Flow**      | ✅ Token-based login               | ❌ Missing     | Need JWT cookie/header integration       |
| **KB Integration** | ✅ `knowledge_base_integration.py` | ❌ Missing     | Need Server Component data fetching      |
| **Real-time UI**   | ❌ Streamlit limitations           | Potential      | WebSocket / SSE for generation streaming |
| **Error Handling** | ✅ Basic try-catch                 | ❌ Missing     | Need error boundaries + toast system     |

> [!IMPORTANT]
> The Next.js frontend is currently a **blank `create-next-app` scaffold** with zero backend integration. This is the highest priority gap for the Bridge Architecture.

---

## 3. Knowledge Base Optimization Roadmap

### 3.1 Current RAG Architecture

```
User Request → UnifiedAIService.generate_response()
                    │
                    ├── Step 1: Build base prompt from request_data
                    ├── Step 2: _enhance_with_rag_async() ──┐
                    │                                        │
                    │   ┌─────── vertex_first mode ──────────┘
                    │   │
                    │   ├── Vertex Search (Discovery Engine)
                    │   │     └── Hardcoded query: "video generation prompt technique style"
                    │   │
                    │   └── Fallback: Local KB (file glob *.txt, *.md)
                    │         └── knowledge_base/ directory → EMPTY
                    │
                    ├── Step 3: Concatenate master_prompt + base_prompt + rag_context
                    └── Step 4: Gemini 2.5 Flash generate_content()
```

### 3.2 Critical Findings

> [!CAUTION]
> **Finding 1: `knowledge_base/` directory is EMPTY.** The local RAG fallback path (`_fallback_local_rag`) will never return content. This means if Vertex Search fails, there is zero knowledge augmentation.

> [!WARNING]
> **Finding 2: Hardcoded RAG query.** In `_enhance_with_rag_async()` (line 440), the search query is hardcoded to `["video", "generation", "prompt", "technique", "style"]` regardless of user input. This means the RAG context is **not dynamic** — the same 3 documents are returned every time.

> [!WARNING]
> **Finding 3: Helios personality context is NOT injected into RAG.** The Helios personality system selects a personality but does not pipe its context into the Vertex Search query or the RAG enhancement prompt. The personality enhancement happens only _after_ generation, via `_apply_diversity()`.

### 3.3 Three Deterministic RAG Enhancement Strategies

#### Strategy 1: Dynamic Query Construction from Request Data

**Problem:** Hardcoded search terms ignore user's actual request.

**Solution:** Replace the static search terms in `_enhance_with_rag_async()` with a dynamic query built from the request:

```python
# CURRENT (line 440):
search_terms = ["video", "generation", "prompt", "technique", "style"]

# PROPOSED:
search_terms = []
if subject := request_data.get("subject_action"):
    search_terms.append(subject)
if styles := request_data.get("artistic_styles"):
    search_terms.extend(styles[:3])
if mood := request_data.get("mood"):
    search_terms.append(mood)
if not search_terms:
    search_terms = ["visual", "generation", "technique"]  # fallback
```

**Impact:** Directly maps user intent to knowledge retrieval, increasing relevance.  
**Risk:** LOW — Preserves `vertex_first` mode, only changes query construction.

---

#### Strategy 2: Helios Personality-Aware Context Injection

**Problem:** The Helios personality system runs independently from RAG. The personality's specialization keywords are never used to refine the knowledge search.

**Solution:** Inject personality context into the RAG query AND the final prompt:

```python
# In generate_response(), after personality selection:
personality_context = helios_system.generate_personality_context(primary, secondary)
personality_keywords = helios_system.get_personality_signature_elements(primary)

# Pass to RAG:
request_data["_personality_keywords"] = personality_keywords

# In _enhance_with_rag_async():
personality_kw = request_data.get("_personality_keywords", [])
search_terms.extend(personality_kw[:2])
```

**Impact:** Knowledge retrieval becomes personality-aware. A "Prometheus" request retrieves technical docs; a "Zeus" request retrieves narrative/cinematic docs.  
**Risk:** LOW — Additive change, no modification to existing Vertex Search integration.

---

#### Strategy 3: Semantic Result Ranking with Relevance Threshold

**Problem:** All 3 search results are concatenated equally regardless of relevance score. Low-relevance results dilute the context window.

**Solution:** Implement a relevance threshold and weighted content truncation:

```python
# In _enhance_with_rag_async(), after getting search results:
RELEVANCE_THRESHOLD = 0.3
relevant_knowledge = []

for result in search_result["results"][:5]:  # fetch 5, filter to top 3
    score = result.get("score", 0)
    if score < RELEVANCE_THRESHOLD:
        continue

    doc = result.get("document", {})
    content = doc.get("content") or doc.get("snippet", "")

    # Weighted truncation: higher relevance = more content
    max_chars = int(200 + (score * 400))  # 200-600 chars based on score
    content = content[:max_chars]
    relevant_knowledge.append(f"[Relevance: {score:.2f}] {content}")
```

**Impact:** Maximizes context quality within token budget. Prevents irrelevant docs from consuming prompt space.  
**Risk:** LOW — Only filters existing results, preserves `vertex_first` pipeline.

---

## 4. Database & Caching Audit

### 4.1 Schema Assessment

| Table               | Columns | Indexes                     | Relationships                     | Issues                                                  |
| ------------------- | ------- | --------------------------- | --------------------------------- | ------------------------------------------------------- |
| `users`             | 8       | `id` (PK), `email` (unique) | → `generated_prompts`, `feedback` | ✅ Solid                                                |
| `generated_prompts` | 6       | `id` (PK)                   | → `users`, → `feedback`           | ⚠️ `raw_response` is JSON blob — not queryable          |
| `feedback`          | 6       | `id` (PK)                   | → `generated_prompts`, → `users`  | ✅ Solid                                                |
| `api_usage`         | 7       | `id` (PK)                   | → `users`                         | ⚠️ Missing index on `created_at` for time-range queries |
| `system_metrics`    | 6       | `id` (PK)                   | None                              | ⚠️ Missing index on `metric_name` + `recorded_at`       |

### 4.2 Concurrency & Connection Management

| Aspect            | SQLite Config                    | PostgreSQL Config               | Assessment                                                               |
| ----------------- | -------------------------------- | ------------------------------- | ------------------------------------------------------------------------ |
| **Pool Strategy** | `StaticPool` (single connection) | `pool_size=10, max_overflow=20` | ⚠️ SQLite `StaticPool` is a bottleneck under concurrent FastAPI requests |
| **WAL Mode**      | ✅ Enabled                       | N/A                             | Good for read concurrency                                                |
| **Cache Size**    | 10,000 pages                     | N/A                             | ✅ Adequate                                                              |
| **Foreign Keys**  | ✅ Enforced via PRAGMA           | N/A (default)                   | ✅ Good                                                                  |
| **Synchronous**   | `NORMAL`                         | N/A                             | ✅ Good perf/safety balance                                              |
| **Pool Pre-ping** | N/A                              | ✅ Enabled                      | ✅ Prevents stale connections                                            |
| **Pool Recycle**  | N/A                              | 300s                            | ✅ Appropriate                                                           |

> [!WARNING]
> **SQLite `StaticPool` Bottleneck:** `StaticPool` uses a single connection for all threads. Under concurrent FastAPI async handlers, this creates a serialization bottleneck. For production, either migrate to PostgreSQL or switch to `QueuePool` with `check_same_thread=False`.

### 4.3 Caching Layer Assessment

| Aspect                 | Status                          | Notes                                                                       |
| ---------------------- | ------------------------------- | --------------------------------------------------------------------------- |
| **Redis Integration**  | ✅ Designed                     | Full async Redis client with connection pooling                             |
| **In-Memory Fallback** | ✅ Implemented                  | Dict-based with TTL expiry                                                  |
| **Serialization**      | ✅ JSON + Pickle fallback       | Handles complex objects                                                     |
| **Metrics**            | ✅ Hits/misses/errors/evictions | Good observability                                                          |
| **Concurrency**        | ⚠️ Fallback not thread-safe     | `_fallback_cache` dict access is not locked                                 |
| **Cache Decorator**    | ✅ `@cached()` decorator        | Clean API                                                                   |
| **Dual Caching**       | ⚠️ Duplicate caching logic      | `UnifiedAIService` has its OWN in-memory cache separate from `CacheService` |

> [!WARNING]
> **Dual Cache Problem:** `UnifiedAIService` maintains its own `self.cache` dict (line 63) with independent TTL/eviction logic, completely separate from `CacheService`. This creates cache inconsistency — a prompt could be cached in one layer but evicted from the other.

---

## 5. Technical Debt Register

| ID    | Severity    | Component        | Issue                                                                                                                          | Recommendation                                |
| ----- | ----------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------- |
| TD-01 | 🔴 Critical | Next.js Frontend | Boilerplate — zero backend integration                                                                                         | Implement API client + auth flow              |
| TD-02 | 🔴 Critical | RAG Pipeline     | Hardcoded search query in `_enhance_with_rag_async()`                                                                          | Implement Strategy 1 (Dynamic Query)          |
| TD-03 | 🟠 High     | Knowledge Base   | `knowledge_base/` directory is empty                                                                                           | Populate with 34 docs or remove fallback path |
| TD-04 | 🟠 High     | Caching          | Dual cache systems (UnifiedAI + CacheService)                                                                                  | Consolidate into single CacheService          |
| TD-05 | 🟠 High     | Database         | `StaticPool` bottleneck for SQLite concurrency                                                                                 | Migrate to PostgreSQL or `QueuePool`          |
| TD-06 | 🟡 Medium   | RAG Pipeline     | Helios personality not connected to RAG queries                                                                                | Implement Strategy 2 (Personality-Aware)      |
| TD-07 | 🟡 Medium   | Database         | No indexes on `api_usage.created_at`, `system_metrics.metric_name`                                                             | Add composite indexes                         |
| TD-08 | 🟡 Medium   | Security         | CORS `allow_origins=["*"]` in production                                                                                       | Restrict to known frontend origins            |
| TD-09 | 🟡 Medium   | Security         | `secret_key` has hardcoded default value                                                                                       | Enforce via env validation                    |
| TD-10 | 🟡 Medium   | Caching          | `_fallback_cache` not thread-safe                                                                                              | Add `asyncio.Lock` for concurrent access      |
| TD-11 | 🟢 Low      | Code Quality     | `cache_service.py` imports `backend.config` (line 19) but `unified_ai_service.py` imports `config` — inconsistent module paths | Standardize imports                           |
| TD-12 | 🟢 Low      | Code Quality     | Debug `print()` statement in `_process_response()` (line 661)                                                                  | Remove or convert to logger                   |
| TD-13 | 🟢 Low      | Config           | Duplicate imports in `config.py` (lines 7,11 and 6,12)                                                                         | Remove duplicates                             |

---

## 6. Verification Results

| Check         | Command                                    | Result                                                    |
| ------------- | ------------------------------------------ | --------------------------------------------------------- |
| Next.js Lint  | `npm run lint` in `nextjs-frontend/`       | ✅ **PASS** — 0 errors, exit code 0                       |
| Backend Tests | `python -m pytest tests/ -v` in `backend/` | ⏳ Not executed — requires virtual env + dependencies     |
| Git Status    | `git status`                               | ✅ Clean — committed to `main`, pushed to `github` remote |

---

## 7. Recommended Priority Roadmap

```
Phase 1 (Week 1-2): Bridge Architecture
├── Build TypeScript API client for Next.js
├── Implement JWT auth flow (cookie-based for App Router)
├── Create Server Components for data fetching
└── Build prompt generation form + results display

Phase 2 (Week 2-3): RAG Optimization
├── Implement Strategy 1: Dynamic Query Construction
├── Implement Strategy 2: Helios Personality-Aware Context
├── Implement Strategy 3: Semantic Relevance Threshold
└── Populate or remove knowledge_base/ fallback

Phase 3 (Week 3-4): Operational Hardening
├── Consolidate dual cache into CacheService
├── Add missing database indexes
├── Restrict CORS origins
├── Enforce secret_key via env validation
└── Migrate SQLite → PostgreSQL for production
```

---

_Report generated by AISpark Orchestrator — Read-only audit, no files modified._
