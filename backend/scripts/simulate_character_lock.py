#!/usr/bin/env python3
"""
Character Lock Sandbox -- Visual Consistency Demonstration
==========================================================
Standalone script that showcases the 79-field Character Lock injection
and consistency engine without requiring a running backend or real DB.

Usage (from project root):
    python backend/scripts/simulate_character_lock.py
"""

import io
import os
import sys
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Force UTF-8 stdout on Windows to support box-drawing characters
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Bootstrap: add backend/ to sys.path and point DB to an in-memory SQLite
# so all core imports resolve without a running server.
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Force an ephemeral in-memory database (read by config -> database at import)
os.environ["AISPARK_DATABASE_URL"] = "sqlite:///:memory:"

# Suppress noisy SQLAlchemy SQL echo for a clean demo
os.environ.setdefault("AISPARK_DEBUG_MODE", "false")

# Now safe to import core modules
from core.models import Base                           # noqa: E402
from core.database import engine                       # noqa: E402
from core.character_lock import (                      # noqa: E402
    character_manager,
    CharacterSheet,
    GenderType,
    AgeRange,
    BuildType,
)

# Create tables in the in-memory DB so the manager can persist characters
Base.metadata.create_all(bind=engine)

# -- Console formatting helpers ----------------------------------------------

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

DIVIDER = f"{DIM}{'=' * 80}{RESET}"
THIN_DIV = f"{DIM}{'-' * 80}{RESET}"


def banner(text: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(DIVIDER)


def section(text: str) -> None:
    print(f"\n{THIN_DIV}")
    print(f"  {BOLD}{YELLOW}{text}{RESET}")
    print(THIN_DIV)


def kv(key: str, value: str) -> None:
    print(f"  {DIM}{key}:{RESET} {value}")


def _wrap(text: str, width: int = 70) -> list:
    """Naive word-wrap for console output."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)
    return lines


# -- 1. Build a richly detailed character ------------------------------------

banner("CHARACTER LOCK SANDBOX -- Visual Consistency Demo")

character_data = {
    # Identity
    "name": "Kira Volkov",
    "description": (
        "A battle-scarred cybernetic mercenary with piercing heterochromatic eyes, "
        "a prosthetic left arm etched with circuitry tattoos, and an unmistakable "
        "silver streak through her jet-black hair."
    ),
    "entity_type": "person",

    # Physical
    "gender": "female",
    "age_range": "young adult (20-35)",
    "ethnicity": "Eastern European",
    "skin_tone": "pale olive",

    # Facial features
    "face_shape": "angular",
    "eye_color": "heterochromatic (left ice-blue, right amber)",
    "eye_shape": "almond",
    "eyebrow_style": "sharp arched",
    "nose_shape": "straight, narrow bridge",
    "lip_shape": "full",

    # Hair
    "hair_color": "jet-black with a single silver streak",
    "hair_style": "asymmetric undercut",
    "hair_length": "chin-length on the longer side",
    "facial_hair": "clean-shaven",

    # Body
    "height": "tall (5'10\")",
    "build": "athletic",
    "distinctive_features": [
        "cybernetic left arm with exposed circuitry and blue LED veins",
        "jagged scar across the right cheekbone",
        "small nose piercing (silver ring)",
        "faded Cyrillic tattoo behind left ear",
    ],

    # Style & Clothing
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

    # Personality & mannerisms (behavioural consistency)
    "personality_traits": [
        "stoic under fire",
        "dry sense of humour",
        "fiercely protective of allies",
    ],
    "mannerisms": [
        "clenches cybernetic fist when anxious",
        "tilts head slightly before speaking",
        "smirks instead of smiling",
    ],
    "voice_characteristics": "low, measured voice with a faint Slavic accent",
}

section("Step 1 -- Creating Character Sheet")
character = character_manager.create_character(character_data)

filled_fields = sum(
    1
    for attr in vars(character)
    if not attr.startswith("_")
    and getattr(character, attr) not in (None, "", [], 0, False)
)
total_fields = len([a for a in vars(character) if not a.startswith("_")])

kv("Character ID", character.character_id)
kv("Name", character.name)
kv("Fields populated", f"{filled_fields} / {total_fields}")

issues = character.validate()
kv("Validation issues", ", ".join(issues) if issues else "None")

print(f"\n  {BOLD}Generated prompt text:{RESET}")
prompt_text = character.to_prompt_text()
for line in _wrap(prompt_text, width=74):
    print(f"  {DIM}{line}{RESET}")

# -- 2. Lock character to a session ------------------------------------------

session_id = f"sandbox_{uuid.uuid4().hex[:8]}"

section("Step 2 -- Locking Character to Session")
locked = character_manager.lock_character_for_session(session_id, character.character_id)
kv("Session ID", session_id)
kv("Lock status", f"{GREEN}LOCKED{RESET}" if locked else f"{RED}FAILED{RESET}")

# -- 3. Define three diverse base prompts ------------------------------------

BASE_PROMPTS = [
    {
        "label": "Cyberpunk City",
        "prompt": (
            "walking through a rain-soaked neon-lit cyberpunk city at night, "
            "holographic billboards flickering overhead, puddles reflecting "
            "pink and blue light"
        ),
    },
    {
        "label": "Medieval Tavern",
        "prompt": (
            "sitting at a worn wooden table inside a medieval tavern, "
            "firelight casting warm shadows, tankards and candles on the table, "
            "rowdy patrons in the background"
        ),
    },
    {
        "label": "Zero-Gravity Space Station",
        "prompt": (
            "floating weightlessly inside a sleek zero-gravity space station, "
            "Earth visible through a panoramic viewport, soft white ambient "
            "lighting, equipment drifting in the background"
        ),
    },
]

# -- 4. Inject character context and display Before / After -------------------

section("Step 3 -- Prompt Injection: Before & After")

for i, scenario in enumerate(BASE_PROMPTS, start=1):
    print(f"\n{BOLD}{MAGENTA}  +-- Scenario {i}: {scenario['label']}{RESET}")

    # BEFORE (raw prompt)
    print(f"  |")
    print(f"  |  {BOLD}BEFORE (base prompt):{RESET}")
    for line in _wrap(scenario["prompt"], width=70):
        print(f"  |  {DIM}{line}{RESET}")

    # AFTER (character-injected prompt)
    enhanced = character_manager.get_character_prompt_enhancement(
        session_id, scenario["prompt"]
    )
    print(f"  |")
    print(f"  |  {BOLD}{GREEN}AFTER (character-injected):{RESET}")
    for line in _wrap(enhanced, width=70):
        print(f"  |  {GREEN}{line}{RESET}")

    print(f"  |")
    print(f"  +{'-' * 78}")

# -- 5. Summary stats --------------------------------------------------------

section("Character Lock Manager Stats")
stats = character_manager.get_stats()
for k, v in stats.items():
    kv(k.replace("_", " ").title(), str(v))

print(f"\n{BOLD}{CYAN}  [OK] Sandbox complete -- all 3 scenarios rendered successfully.{RESET}\n")
