# AISpark Studio — Frontend Vision Document

**Date:** 2026-03-01
**Source:** Multi-Agent Brainstorming Session (UX Designer + Next.js Architect + Product Strategist)
**Status:** Approved for Implementation

---

## 1. Design Philosophy: "The Pantheon Interface"

AISpark Studio is a **creative instrument**, not a form-based tool. The 6 Helios personalities are creative collaborators with opinions, not dropdown options. Every UX decision must pass this test: *"Does this make the tool feel like a creative partner or a configuration panel?"*

---

## 2. Technology Decisions (Final)

| Concern | Decision | Rationale |
|---|---|---|
| State Management | **Zustand** (client state) + **TanStack Query v5** (server state) | Zustand for auth/personality/generation state; TanStack Query for all API data with mutation lifecycle hooks |
| UI Components | **shadcn/ui** (Radix + Tailwind) | Owned source code, modifiable for personality theming |
| Icons | **Lucide React** | shadcn default, tree-shakeable |
| Styling | **Tailwind CSS v4** + CSS custom properties | Per-personality color tokens via `data-personality` attribute |
| Data Fetching | **TanStack Query v5** | `useMutation` with AbortController for 25-31s generation calls |
| Auth Token | **Browser cookie** (`aispark_token`) | Non-httpOnly for client read, SameSite=Strict, 24h TTL |
| i18n | **next-intl** (V2) | Georgian + English; use translation keys from day one |
| Typography | **Geist Sans** (UI), **Geist Mono** (code), consider serif for AI output | Serif for generated prompts elevates perceived quality |

### Installation Commands

```bash
cd nextjs-frontend

# Core
npm install @tanstack/react-query @tanstack/react-query-devtools zustand

# shadcn/ui
npx shadcn@latest init
npx shadcn@latest add button card dialog dropdown-menu input label progress select separator skeleton tabs textarea toast badge scroll-area

# Utilities
npm install clsx tailwind-merge class-variance-authority lucide-react
```

---

## 3. App Router File Structure

```
nextjs-frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── layout.tsx                  # Centered card, no sidebar
│   │
│   ├── (dashboard)/
│   │   ├── layout.tsx                  # Sidebar + Topbar + QueryClientProvider
│   │   ├── page.tsx                    # → redirects to /generate
│   │   ├── generate/page.tsx           # Main generation workspace
│   │   ├── helios/
│   │   │   ├── page.tsx                # Personality selector + stats
│   │   │   └── [personality]/page.tsx  # Per-personality detail
│   │   ├── characters/
│   │   │   ├── page.tsx                # Character gallery
│   │   │   ├── new/page.tsx            # Create character form
│   │   │   └── [id]/page.tsx           # Character detail + lock/unlock
│   │   ├── history/page.tsx            # Prompt history + export
│   │   ├── search/page.tsx             # Vertex AI search
│   │   └── settings/page.tsx           # Account + credits
│   │
│   ├── api/auth/session/route.ts       # Cookie set/clear handler
│   ├── globals.css                     # Tailwind + personality tokens
│   ├── layout.tsx                      # Root: fonts, theme script
│   └── not-found.tsx
│
├── components/
│   ├── ui/                             # shadcn/ui primitives
│   ├── features/
│   │   ├── generation/
│   │   │   ├── GenerationForm.tsx
│   │   │   ├── GenerationResult.tsx
│   │   │   └── GenerationProgress.tsx  # Phased loading (25-31s)
│   │   ├── helios/
│   │   │   ├── PersonalityCard.tsx
│   │   │   └── PersonalitySelector.tsx
│   │   ├── characters/
│   │   │   ├── CharacterCard.tsx
│   │   │   ├── CharacterForm.tsx
│   │   │   └── LockBadge.tsx
│   │   ├── critic/
│   │   │   ├── CriticPanel.tsx
│   │   │   └── ScoreRing.tsx
│   │   └── history/
│   │       ├── PromptHistoryList.tsx
│   │       └── ExportButton.tsx
│   ├── layouts/
│   │   ├── Sidebar.tsx
│   │   └── Topbar.tsx
│   └── shared/
│       ├── ThemeProvider.tsx            # Personality-aware CSS vars
│       ├── CreditsDisplay.tsx
│       └── ErrorBoundary.tsx
│
├── lib/
│   ├── api/
│   │   ├── client.ts                   # Base fetch + auth + 402 handling
│   │   ├── auth.ts
│   │   ├── generation.ts
│   │   ├── helios.ts
│   │   ├── characters.ts
│   │   ├── prompts.ts
│   │   ├── search.ts
│   │   └── critic.ts
│   ├── types/api.ts                    # Manually typed from backend schemas.py
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── personalityStore.ts
│   │   └── generationStore.ts          # AbortController + elapsed timer
│   ├── hooks/
│   │   ├── useGeneration.ts
│   │   ├── useHelios.ts
│   │   ├── useCharacters.ts
│   │   └── useCredits.ts
│   └── utils/
│       ├── personality-tokens.ts
│       └── format.ts
│
└── middleware.ts                        # JWT cookie check → redirect
```

---

## 4. Layout Architecture: "Observatory Layout"

```
┌──────────────────────────────────────────────────────────────────────┐
│  TOPBAR: [Logo] [Credits Orb ⬡ 47] [Search]       [Notifications] [Avatar] │
├──────────────┬──────────────────────────────────┬────────────────────┤
│              │                                  │                    │
│  LEFT NAV    │         MAIN CANVAS              │  CONTEXT RAIL      │
│  (72px icon  │         (fluid width)            │  (320px,           │
│  → 240px     │                                  │   collapsible,     │
│  on hover)   │                                  │   glassmorphic)    │
│              │                                  │                    │
│  ⚡ Generate  │                                  │  Active Personality│
│  🎭 Helios   │                                  │  Locked Character  │
│  🔒 Characters│                                  │  Last Prompt       │
│  📚 History  │                                  │  Critic Score      │
│  🔍 Search   │                                  │  Credits Used      │
│  📤 Export   │                                  │                    │
│  ⚙️ Settings │                                  │                    │
│              │                                  │                    │
└──────────────┴──────────────────────────────────┴────────────────────┘
```

**Context Rail** (right panel) persists across navigation, showing active session state. It solves context loss when navigating between pages. Semi-transparent glassmorphic surface.

**Mobile**: Single column + bottom tab bar (Generate, Library, Settings). Context Rail becomes swipe-up bottom sheet.

---

## 5. Personality Color System

Each Helios personality drives the entire app's accent colors via CSS custom properties:

| Personality | Primary | Secondary | Glow | Character |
|---|---|---|---|---|
| Prometheus | `#f97316` (Orange) | `#fb923c` | `rgba(249,115,22,0.15)` | Angular, fiery |
| Zeus | `#eab308` (Gold) | `#facc15` | `rgba(234,179,8,0.15)` | Regal, radial |
| Poseidon | `#0ea5e9` (Ocean) | `#38bdf8` | `rgba(14,165,233,0.15)` | Fluid, wave |
| Artemis | `#10b981` (Emerald) | `#34d399` | `rgba(16,185,129,0.15)` | Precise, minimal |
| Dionysus | `#d946ef` (Fuchsia) | `#e879f9` | `rgba(217,70,239,0.15)` | Chaotic, explosive |
| Athena | `#8b5cf6` (Violet) | `#a78bfa` | `rgba(139,92,246,0.15)` | Balanced, wise |

**Implementation**: `<html data-personality="zeus">` drives CSS variables. `ThemeProvider.tsx` updates this attribute from `personalityStore`. All brand colors reference `var(--personality-primary)`.

**Dark mode base**: `#0A0B0E` deepest → `#111318` surfaces → `#1A1D26` elevated cards. Not pure black.

---

## 6. Core UX Flows

### 6.1 Personality Selection — "The Pantheon Chamber"

Not a dropdown. A **hexagonal constellation** of 6 animated sigil nodes on `/helios`. Each personality has a unique procedural animation (flame for Prometheus, waves for Poseidon, etc.).

**Interaction**: Hover → 110% scale + personality brief tooltip. Click → golden ring animation, background gradient shifts to personality color. "Let Helios Decide" auto-suggest mode calls `/helios/analyze` and animates selection.

**On Generate page**: Compact 6-icon horizontal row inheriting the same visual language.

### 6.2 Prompt Generation — "The Studio" (Single-Page, Multi-Phase)

```
PHASE 1: INPUT           PHASE 2: CONFIGURE        PHASE 3: GENERATING
─────────────────        ──────────────────        ───────────────────
Large textarea      →    Personality active    →   Narrative loading
(placeholder text)       Character lock toggle     (phased messages)
                         RAG mode toggle

PHASE 4: RESULTS         PHASE 5: REFINE
────────────────         ───────────────
Generated prompt    →    Critic score panel
Quality score ring       Enhancement suggestions
Copy/Export actions      "Try with Artemis?" cross-personality
```

**Phase 3 Loading (25-31s)** — No spinner. Narrative progress messages:

| Elapsed | Message |
|---|---|
| 0-3s | "Initializing Helios personality..." |
| 3-8s | "Searching Vertex AI knowledge base..." |
| 8-15s | "Analyzing prompt structure..." |
| 15-22s | "Generating creative variations..." |
| 22-28s | "Applying personality signature..." |
| 28-35s | "Finalizing and quality-checking..." |

Progress bar fills to 95% max (never 100% until actually complete). Cancel button available via `AbortController`.

### 6.3 Character Lock — "The Character Codex"

**Character Sheet**: Tabbed dossier with 5 groups (Physical, Wardrobe, Expression, Motion, Meta) — not a flat 20-field form.

**Lock UX**: Lock action shows confirmation modal → padlock closes animation → golden border traces card → "LOCKED TO SESSION" badge. The locked character appears in Context Rail as a "Consistency Anchor."

**Live Preview**: Shows the exact text that will be injected into prompts, bridging form inputs to AI output.

### 6.4 Credits — "The Sparks System"

Rename "credits" to **"Sparks"** — linguistic framing matters.

**Credits Orb** in topbar: persistent arc indicator, color transitions green → amber → red.
**Pre-generation cost preview**: "Generate — 1 Spark" on the button.
**402 handling**: Non-blocking banner (not modal), "Your prompt is saved", three pricing tiers.

---

## 7. State Architecture

### Zustand Stores (Client State)

```typescript
// authStore: user, isAuthenticated, setUser, clearAuth
// personalityStore: activePersonality, setPersonality
// generationStore: isGenerating, abortController, elapsedSeconds, start/cancel/finish
```

### TanStack Query (Server State)

```typescript
// Query keys: ['characters', 'list'], ['prompts', { page }], ['helios', 'stats']
// Mutations: useGeneration(), useCreateCharacter(), useLockCharacter()
// staleTime: 60s, retry: 1, refetchOnWindowFocus: false
```

### Local State (Component)

Form values, dialog toggles, tab selections, sidebar collapse.

---

## 8. Authentication Flow

```
Login page → POST /auth/token (form-encoded, field: username=email)
           → Set cookie: aispark_token=JWT; path=/; max-age=86400; SameSite=Strict
           → Fetch GET /users/me → populate authStore
           → Redirect to /generate

middleware.ts → Check aispark_token cookie
             → No token + protected route → redirect /login
             → Has token + /login → redirect /generate

401 from API → Clear cookie → redirect /login
```

---

## 9. API Client Architecture

**Pattern**: Function-based modules per resource in `lib/api/`. Base `client.ts` handles auth injection, 401 redirect, 402 credits error.

```typescript
// lib/api/client.ts
async function request<T>(path: string, init?: RequestInit, signal?: AbortSignal): Promise<T>
// Reads aispark_token cookie, injects Bearer header
// 401 → clearAuth + redirect
// 402 → throw ApiError with isCreditsError=true
```

**Types**: Manually written in `lib/types/api.ts` from backend `schemas.py`. No OpenAPI codegen — schema is small enough and codegen adds build complexity.

---

## 10. User Personas

| Persona | Profile | Key Need | Killer Feature |
|---|---|---|---|
| **Solo Creator** (60%) | Freelance video editor, YouTube/TikTok | Fast generation, consistency across scenes | Character Lock saves 20 min/project |
| **Studio Producer** (25%, highest LTV) | Creative agency coordinator | Reproducible results, team sharing, audit trail | Character Lock + Export + Collections |
| **Curious Experimenter** (15%) | Hobbyist, student | Instant value, no friction | Personality comparison "wow moment" |

---

## 11. Conversion Funnel

```
Landing Page (personality comparison demo, no sign-up wall)
    ↓ "Try it free" — 3 anonymous generations
First Generation (default to Zeus personality for maximum drama)
    ↓ "Aha moment": critique score explains WHY the prompt works
Account Creation (triggered by "Save this prompt", not before)
    ↓ Google OAuth primary, email secondary
First Session (50 free Sparks, onboarding checklist)
    ↓ Milestone-triggered upgrade ("You've saved 10 prompts — ready for unlimited?")
Upgrade (not triggered by depletion, triggered by value perception)
```

---

## 12. Feature Prioritization

### MVP (Sprint 1-2) — Ship First

| # | Feature | FastAPI Endpoint | Priority |
|---|---|---|---|
| 1 | Generation page + personality selector | `/generate`, `/helios/auto-generate`, `/helios/personalities` | CRITICAL |
| 2 | Character Lock toggle in generation | `/characters/list`, `/characters/{id}/lock`, `/characters/session/current` | CRITICAL |
| 3 | Prompt history (list, copy, delete) | `/prompts`, `/prompts/{id}` | CRITICAL |
| 4 | Credit balance display (topbar) | `/users/me` → credits field | CRITICAL |
| 5 | Auth flow (login/register) | `/auth/token`, `/auth/register` | CRITICAL |
| 6 | Export (single prompt) | `/prompts/export/{format}` | HIGH |

### V2 (Sprint 3-4) — Retention

| # | Feature | Endpoint |
|---|---|---|
| 7 | Full Character Management UI (20-attribute form) | `/characters/*` CRUD |
| 8 | Critic score display + suggestions | `/critic/analyze` |
| 9 | Personality comparison view (1 input → 6 outputs) | `/helios/enhance` x6 |
| 10 | Dashboard with usage stats | `/helios/stats`, `/critic/stats` |
| 11 | Collections / Favorites | Client-side + `/prompts` filtering |
| 12 | Payment/upgrade flow | New endpoint needed |

### V3 — Scale

| # | Feature |
|---|---|
| 13 | Community gallery (opt-in sharing) |
| 14 | Team workspaces |
| 15 | Prompt versioning / diff view |
| 16 | API access for developers |
| 17 | Georgian language support (next-intl) |
| 18 | Mobile PWA |

---

## 13. Implementation Checklist (Sprint 1 — Atomic Steps)

```
[ ] 1.  npm install dependencies (TanStack Query, Zustand, shadcn, Lucide)
[ ] 2.  npx shadcn@latest init + add core components
[ ] 3.  Create globals.css with personality color tokens
[ ] 4.  Create ThemeProvider.tsx
[ ] 5.  Create lib/api/client.ts (base fetch + auth + error handling)
[ ] 6.  Create lib/types/api.ts (TypeScript types from schemas.py)
[ ] 7.  Create lib/stores/ (authStore, personalityStore, generationStore)
[ ] 8.  Create middleware.ts (JWT cookie guard)
[ ] 9.  Create (auth) route group + login/register pages
[ ] 10. Create (dashboard) layout with Sidebar + Topbar + QueryClientProvider
[ ] 11. Create CreditsDisplay.tsx in Topbar
[ ] 12. Create PersonalitySelector.tsx (6-card grid)
[ ] 13. Create GenerationForm.tsx
[ ] 14. Create GenerationProgress.tsx (phased loading)
[ ] 15. Create GenerationResult.tsx
[ ] 16. Create /generate page (combines form + selector + progress + result)
[ ] 17. Create CharacterCard.tsx + LockBadge.tsx
[ ] 18. Create Character Lock toggle in generation flow
[ ] 19. Create PromptHistoryList.tsx
[ ] 20. Create /history page
[ ] 21. Create ExportButton.tsx
[ ] 22. Create .env.local (NEXT_PUBLIC_API_URL=http://localhost:8001)
[ ] 23. Run npx tsc --noEmit — verify 0 errors
[ ] 24. Run npm run lint — verify 0 errors
[ ] 25. Manual test: login → generate → view history → export
```

---

## 14. Critical Implementation Notes

- **FastAPI OAuth2** uses `username` field (not `email`) — login fetch must send `username=email_value` as form-encoded
- **CORS**: Backend allows `["*"]` — no changes needed for development
- **Tailwind v4**: Uses CSS `@theme` block, NOT `tailwind.config.js` for token definitions
- **Route groups**: `(auth)` and `(dashboard)` are invisible in URLs — `/login` not `/(auth)/login`
- **AbortController + React 19 StrictMode**: Double-invokes effects in dev — ensure `startGeneration` creates fresh controller each time
- **Credits 402**: Surface as modal dialog, distinct from all other API errors

---

*Generated by Multi-Agent Brainstorming: Lead UX Designer + Next.js Architect + Product Strategist*
*Orchestrated via @multi-agent-brainstorming @ui-ux-pro-max @nextjs-app-router-patterns @frontend-design*
