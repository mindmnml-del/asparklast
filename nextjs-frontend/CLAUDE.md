# Frontend - Claude Code Context

## Stack
- Next.js 15 (App Router), TypeScript, Tailwind CSS v4
- React Server Components by default; use `"use client"` only when needed

## Rules
- **NEVER** modify backend files (`backend/` directory)
- **NEVER** change `next.config.ts` or `package.json` unless explicitly approved
- Use App Router conventions: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`
- All API calls go through the FastAPI backend at `http://localhost:8001`
- Prefer Server Components; only use Client Components for interactivity (forms, state, effects)

## Validation
- Before completing any task, run: `bash .claude/hooks/frontend-check.sh` from the project root
- All code must pass `npm run lint` with zero errors
