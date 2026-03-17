#!/usr/bin/env python3
"""
Character Lock Visual Consistency Test -- Imagen 3.0 Image Generator
=====================================================================
Generates 3 images (one per scenario) using the same character-injected
prompts from simulate_character_lock.py and saves them as PNGs.

Reuses the project's existing genai_client.py for Vertex AI authentication
and calls Imagen 3.0 via the google-genai unified SDK.

Usage (from project root):
    python backend/scripts/generate_vertex_images.py

Output:
    backend/scripts/visual_tests/scenario_1_cyberpunk.png
    backend/scripts/visual_tests/scenario_2_tavern.png
    backend/scripts/visual_tests/scenario_3_space.png
"""

import io
import os
import sys
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Force UTF-8 stdout on Windows
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

# Use in-memory DB so character_lock doesn't need the real database
os.environ["AISPARK_DATABASE_URL"] = "sqlite:///:memory:"

# genai_client.py looks for vertex-key.json relative to cwd; ensure we run
# from backend/ so the key file is found.
os.chdir(BACKEND_DIR)

from google.genai import types                          # noqa: E402
from core.models import Base                            # noqa: E402
from core.database import engine                        # noqa: E402
from core.character_lock import (                       # noqa: E402
    character_manager,
    GenderType,
    AgeRange,
    BuildType,
)
from services.genai_client import get_genai_client, validate_vertex_config  # noqa: E402

# Create tables for the in-memory DB
Base.metadata.create_all(bind=engine)

# -- Console helpers ----------------------------------------------------------

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

OUTPUT_DIR = Path(__file__).resolve().parent / "visual_tests"
OUTPUT_DIR.mkdir(exist_ok=True)

IMAGEN_MODEL = "imagen-3.0-generate-001"


def print_status(label: str, msg: str) -> None:
    print(f"  {DIM}[{label}]{RESET} {msg}")


# -- 1. Pre-flight check -----------------------------------------------------

print(f"\n{BOLD}{CYAN}  Character Lock Visual Test -- Imagen 3.0{RESET}")
print(f"  {DIM}{'=' * 50}{RESET}")

if not validate_vertex_config():
    print(f"\n  {RED}ERROR: Vertex AI is not configured.{RESET}")
    print(f"  Ensure vertex-key.json exists in backend/ and config is set.")
    sys.exit(1)

print_status("OK", "Vertex AI configuration validated")

# -- 2. Build the same character as the simulator ----------------------------

character_data = {
    "name": "Kira Volkov",
    "description": (
        "A battle-scarred cybernetic mercenary with piercing heterochromatic eyes, "
        "a prosthetic left arm etched with circuitry tattoos, and an unmistakable "
        "silver streak through her jet-black hair."
    ),
    "entity_type": "person",
    "gender": "female",
    "age_range": "young adult (20-35)",
    "ethnicity": "Eastern European",
    "skin_tone": "pale olive",
    "face_shape": "angular",
    "eye_color": "heterochromatic (left ice-blue, right amber)",
    "eye_shape": "almond",
    "eyebrow_style": "sharp arched",
    "nose_shape": "straight, narrow bridge",
    "lip_shape": "full",
    "hair_color": "jet-black with a single silver streak",
    "hair_style": "asymmetric undercut",
    "hair_length": "chin-length on the longer side",
    "facial_hair": "clean-shaven",
    "height": "tall (5'10\")",
    "build": "athletic",
    "distinctive_features": [
        "cybernetic left arm with exposed circuitry and blue LED veins",
        "jagged scar across the right cheekbone",
        "small nose piercing (silver ring)",
        "faded Cyrillic tattoo behind left ear",
    ],
    "clothing_style": "tactical cyberpunk",
    "typical_outfit": (
        "a fitted black tactical vest over a dark-grey compression top, "
        "cargo pants with reinforced knee panels, and heavy combat boots"
    ),
    "accessories": [
        "fingerless gloves on the organic hand",
        "holographic wrist display on the cybernetic arm",
        "dog-tag necklace",
    ],
    "color_palette": ["black", "charcoal grey", "electric blue", "silver"],
    "personality_traits": ["stoic under fire", "dry sense of humour", "fiercely protective of allies"],
    "mannerisms": ["clenches cybernetic fist when anxious", "tilts head slightly before speaking", "smirks instead of smiling"],
    "voice_characteristics": "low, measured voice with a faint Slavic accent",
}

character = character_manager.create_character(character_data)
session_id = f"visual_{uuid.uuid4().hex[:8]}"
character_manager.lock_character_for_session(session_id, character.character_id)

print_status("OK", f"Character '{character.name}' created and locked (session={session_id})")

# -- 3. Scenarios ------------------------------------------------------------

SCENARIOS = [
    {
        "label": "Cyberpunk City",
        "filename": "scenario_1_cyberpunk.png",
        "prompt": (
            "walking through a rain-soaked neon-lit cyberpunk city at night, "
            "holographic billboards flickering overhead, puddles reflecting "
            "pink and blue light"
        ),
    },
    {
        "label": "Medieval Tavern",
        "filename": "scenario_2_tavern.png",
        "prompt": (
            "sitting at a worn wooden table inside a medieval tavern, "
            "firelight casting warm shadows, tankards and candles on the table, "
            "rowdy patrons in the background"
        ),
    },
    {
        "label": "Zero-Gravity Space Station",
        "filename": "scenario_3_space.png",
        "prompt": (
            "floating weightlessly inside a sleek zero-gravity space station, "
            "Earth visible through a panoramic viewport, soft white ambient "
            "lighting, equipment drifting in the background"
        ),
    },
]

# -- 4. Generate images ------------------------------------------------------

client = get_genai_client()
generated_files = []

for i, scenario in enumerate(SCENARIOS, start=1):
    # Build the character-injected prompt (same logic as character_lock)
    enhanced_prompt = character_manager.get_character_prompt_enhancement(
        session_id, scenario["prompt"]
    )

    print(f"\n  {BOLD}Scenario {i}: {scenario['label']}{RESET}")
    print(f"  {DIM}Prompt length: {len(enhanced_prompt)} chars{RESET}")
    print(f"  {DIM}Generating with {IMAGEN_MODEL}...{RESET}")

    try:
        response = client.models.generate_images(
            model=IMAGEN_MODEL,
            prompt=enhanced_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/png",
                aspect_ratio="16:9",
                safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            ),
        )

        if not response.generated_images:
            print(f"  {RED}WARNING: No images returned (possibly blocked by safety filter).{RESET}")
            continue

        image_bytes = response.generated_images[0].image.image_bytes
        output_path = OUTPUT_DIR / scenario["filename"]
        output_path.write_bytes(image_bytes)

        size_kb = len(image_bytes) / 1024
        print(f"  {GREEN}Saved: {output_path.relative_to(PROJECT_ROOT)} ({size_kb:.0f} KB){RESET}")
        generated_files.append(output_path)

    except Exception as e:
        print(f"  {RED}ERROR generating image: {e}{RESET}")
        # If the model isn't available, try the older model as fallback
        if "not found" in str(e).lower() or "404" in str(e):
            print(f"  {YELLOW}Trying fallback model: imagegeneration@006{RESET}")
            try:
                response = client.models.generate_images(
                    model="imagegeneration@006",
                    prompt=enhanced_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/png",
                    ),
                )
                if response.generated_images:
                    image_bytes = response.generated_images[0].image.image_bytes
                    output_path = OUTPUT_DIR / scenario["filename"]
                    output_path.write_bytes(image_bytes)
                    size_kb = len(image_bytes) / 1024
                    print(f"  {GREEN}Saved (fallback): {output_path.relative_to(PROJECT_ROOT)} ({size_kb:.0f} KB){RESET}")
                    generated_files.append(output_path)
            except Exception as e2:
                print(f"  {RED}Fallback also failed: {e2}{RESET}")

# -- 5. Summary --------------------------------------------------------------

print(f"\n  {DIM}{'=' * 50}{RESET}")
if generated_files:
    print(f"  {BOLD}{GREEN}Generated {len(generated_files)}/3 images:{RESET}")
    for f in generated_files:
        print(f"    {GREEN}{f.relative_to(PROJECT_ROOT)}{RESET}")
    print(f"\n  {BOLD}Open these files to visually verify character consistency")
    print(f"  across all three scenarios.{RESET}\n")
else:
    print(f"  {RED}No images were generated. Check your Vertex AI credentials")
    print(f"  and ensure the Imagen API is enabled for your project.{RESET}")
    print(f"\n  {YELLOW}Troubleshooting:{RESET}")
    print(f"  1. Ensure vertex-key.json is in backend/")
    print(f"  2. Enable 'Vertex AI API' in Google Cloud Console")
    print(f"  3. Enable 'Imagen API' for your project")
    print(f"  4. Check your project has Imagen 3.0 access (may need allowlisting)\n")
    sys.exit(1)
