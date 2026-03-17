# AISpark Studio - B2B Sandbox API Quickstart

## Overview

The Sandbox API provides external developers with access to AISpark Studio's
AI prompt generation and critic analysis engines via a simple REST API
authenticated with a static Bearer token.

**Base URL**: `http://localhost:8001/api/v1/sandbox`

## Authentication

All requests require an `Authorization` header with a Bearer token:

```
Authorization: Bearer YOUR_SANDBOX_API_KEY
```

The API key is configured server-side via the `AISPARK_SANDBOX_API_KEY`
environment variable.

## Setup (Server Admin)

1. Generate a secure key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Add to your `.env` file:
   ```
   AISPARK_SANDBOX_API_KEY=<generated-key>
   ```

3. Restart the backend server.

## Endpoints

### POST /generate

Generate an AI-enhanced prompt for image or video creation tools.

**Request Body** (JSON):

| Field             | Type   | Required | Default          | Description                            |
|-------------------|--------|----------|------------------|----------------------------------------|
| `prompt`          | string | Yes      | —                | User prompt (min 3 chars)              |
| `negative_prompt` | string | No       | `""`             | Things to avoid in generation          |
| `style`           | string | No       | `"professional"` | Generation style                       |
| `type`            | string | No       | `"image"`        | `"image"`, `"video"`, or `"universal"` |
| `tool`            | string | No       | `"Universal"`    | Target AI tool name                    |
| `diversity_enabled` | bool | No       | `true`           | Enable response diversity              |
| `rag_enabled`     | bool   | No       | `true`           | Enable RAG knowledge enhancement       |
| `auto_improve`    | bool   | No       | `false`          | Auto-improve via Spark Shield critic   |

**curl Example:**

```bash
curl -X POST http://localhost:8001/api/v1/sandbox/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SANDBOX_API_KEY" \
  -d '{
    "prompt": "A cyberpunk city at sunset with neon reflections",
    "type": "image",
    "style": "cinematic",
    "tool": "Midjourney"
  }'
```

**Success Response** (200):

```json
{
  "success": true,
  "data": {
    "structuredPrompt": {
      "subject": "...",
      "setting": "...",
      "lighting": "...",
      "composition": "...",
      "styleAndMedium": "...",
      "technicalDetails": "...",
      "mood": "..."
    },
    "paragraphPrompt": "A full paragraph prompt ready to paste...",
    "negativePrompt": "...",
    "tool": "Midjourney",
    "type": "image"
  }
}
```

### POST /critic/analyze

Analyze an existing prompt for quality scoring and improvement suggestions.

**Request Body** (JSON):

| Field             | Type   | Required | Default   | Description                       |
|-------------------|--------|----------|-----------|-----------------------------------|
| `prompt`          | string | Yes      | —         | Prompt to analyze (min 10 chars)  |
| `negative_prompt` | string | No       | `""`      | Negative prompt to include        |
| `analysis_type`   | string | No       | `"photo"` | `"photo"`, `"video"`, or `"both"` |

**curl Example:**

```bash
curl -X POST http://localhost:8001/api/v1/sandbox/critic/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SANDBOX_API_KEY" \
  -d '{
    "prompt": "A lone astronaut standing on a red desert planet, dual suns setting behind jagged mountains, long dramatic shadows",
    "analysis_type": "photo"
  }'
```

**Success Response** (200):

```json
{
  "success": true,
  "data": {
    "overall_score": 72,
    "category_scores": { "...": "..." },
    "assessment": "Strong visual concept...",
    "strengths": ["Clear subject-environment contrast", "..."],
    "weaknesses": ["Missing camera specifications", "..."],
    "top_suggestion": "Add technical camera details.",
    "improved_prompt": "..."
  }
}
```

## Error Responses

All errors return a consistent JSON structure:

```json
{
  "detail": {
    "error": "error_code",
    "message": "Human-readable explanation"
  }
}
```

| Error Code               | HTTP Status | Meaning                          |
|--------------------------|-------------|----------------------------------|
| `missing_credentials`    | 401         | No Authorization header sent     |
| `invalid_token`          | 401         | Bearer token does not match      |
| `sandbox_not_configured` | 503         | Server has no sandbox key set    |
| `generation_failed`      | 502         | AI service returned an error     |
| `analysis_failed`        | 502         | Critic service returned an error |
| `internal_error`         | 500         | Unexpected server error          |
