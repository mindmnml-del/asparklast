"""
Shared Google Gen AI client for Vertex AI text generation.
Uses service account credentials from vertex-key.json.
Singleton pattern - shared by UnifiedAIService and UnifiedCriticService.
"""

import logging
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from google.oauth2.service_account import Credentials

from config import settings

logger = logging.getLogger(__name__)

_client: Optional[genai.Client] = None


def _resolve_credentials() -> Optional[Credentials]:
    """
    Load service account credentials using the same cascade
    as vertex_search_service.py for consistency.
    """
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    # Priority 1: settings.google_application_credentials
    if settings.google_application_credentials:
        sa_path = Path(settings.google_application_credentials)
        if sa_path.exists():
            creds = Credentials.from_service_account_file(str(sa_path), scopes=scopes)
            logger.info(f"GenAI client: loaded credentials from {sa_path}")
            return creds

    # Priority 2: known key file names in working directory
    for candidate in ["vertex-key.json", "streamlit-vertex-key.json"]:
        p = Path(candidate)
        if p.exists():
            creds = Credentials.from_service_account_file(str(p), scopes=scopes)
            logger.info(f"GenAI client: loaded credentials from {p}")
            return creds

    logger.warning("GenAI client: no service account key file found, falling back to ADC")
    return None


def get_genai_client() -> genai.Client:
    """Return the shared Gen AI client (lazy singleton)."""
    global _client
    if _client is None:
        credentials = _resolve_credentials()
        project = settings.vertex_project_id or settings.google_cloud_project
        location = settings.vertex_gen_location

        _client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
            credentials=credentials,
        )
        logger.info(
            f"GenAI client initialized: project={project}, location={location}"
        )
    return _client


def get_genai_async_client():
    """Return the async interface of the shared Gen AI client."""
    return get_genai_client().aio


def build_safety_settings() -> list:
    """Build standard safety settings for generation."""
    return [
        types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="BLOCK_MEDIUM_AND_ABOVE",
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="BLOCK_MEDIUM_AND_ABOVE",
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="BLOCK_MEDIUM_AND_ABOVE",
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_MEDIUM_AND_ABOVE",
        ),
    ]


def validate_vertex_config() -> bool:
    """Check if Vertex AI generation is properly configured."""
    project = settings.vertex_project_id or settings.google_cloud_project
    if not project:
        return False
    # Check that at least one credential source exists
    if settings.google_application_credentials:
        if Path(settings.google_application_credentials).exists():
            return True
    for candidate in ["vertex-key.json", "streamlit-vertex-key.json"]:
        if Path(candidate).exists():
            return True
    return False
