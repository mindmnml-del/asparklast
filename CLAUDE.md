# AISpark Studio - Claude Code Configuration

## Skills
Load skills from `~/.claude/skills/` directory. Each skill has a `SKILL.md` file with instructions.

### Key Skills for This Project
- `fastapi-pro` - FastAPI patterns and best practices
- `nextjs-best-practices` - Next.js App Router patterns
- `python-pro` - Python development patterns
- `rag-engineer` - RAG system implementation
- `database` - Database design and optimization
- `security-auditor` - Security audit practices
- `systematic-debugging` - Debugging methodology
- `git-pushing` - Git workflow

## Project Rules
- Do NOT modify existing working components (Vertex AI Search, RAG system, FastAPI backend)
- Only ADD new functionality, never change existing working code
- Service account configuration must remain unchanged
- Backend uses FastAPI + Python, Frontend uses Next.js + TypeScript + Tailwind

## Directory-Specific Context
- When working in `backend/`, read and follow `backend/CLAUDE.md`
- When working in `nextjs-frontend/`, read and follow `nextjs-frontend/CLAUDE.md`

## Validation Hooks
- Before completing any **backend** task, run: `bash .claude/hooks/backend-check.sh`
- Before completing any **frontend** task, run: `bash .claude/hooks/frontend-check.sh`
