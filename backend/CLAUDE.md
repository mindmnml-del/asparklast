# Backend - Claude Code Context

## Stack
- Python 3.11+, FastAPI, SQLAlchemy, Pydantic
- SQLite database (production path to PostgreSQL)

## Rules
- **NEVER** modify existing Vertex AI Search or RAG pipeline logic
- **NEVER** change `services/vertex_search_service.py` or `services/unified_ai_service.py` unless explicitly approved
- **NEVER** alter service account configuration or authentication setup
- Only **ADD** new functionality — do not refactor or rewrite existing working code
- Follow existing patterns in `core/models.py` and `core/schemas.py` for new models/schemas
- All external I/O (Vertex AI calls, DB operations) must have try/except error handling

## Validation
- Before completing any task, run: `bash .claude/hooks/backend-check.sh` from the project root
- All new code must pass `python -m pytest tests/ -v`
