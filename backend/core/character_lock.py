"""
Character Lock System for AISpark Studio
Ensures visual consistency across video generation sequences
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class GenderType(Enum):
    """Character gender options"""
    MALE = "male"
    FEMALE = "female" 
    NON_BINARY = "non-binary"
    UNSPECIFIED = "unspecified"


class AgeRange(Enum):
    """Character age range categories"""
    CHILD = "child (5-12)"
    TEENAGER = "teenager (13-19)"
    YOUNG_ADULT = "young adult (20-35)"
    MIDDLE_AGED = "middle-aged (36-55)"
    SENIOR = "senior (55+)"


class BuildType(Enum):
    """Character build/body type"""
    SLIM = "slim"
    ATHLETIC = "athletic"
    AVERAGE = "average"
    MUSCULAR = "muscular"
    CURVY = "curvy"
    HEAVY_SET = "heavy-set"


@dataclass
class CharacterSheet:
    """
    Complete character specification for visual consistency
    Used to maintain the same character across multiple video generations
    """
    
    # Basic Identity
    name: str = "Unnamed Character"
    character_id: str = ""
    description: str = ""
    
    # Physical Characteristics
    gender: GenderType = GenderType.UNSPECIFIED
    age_range: AgeRange = AgeRange.YOUNG_ADULT
    ethnicity: str = ""
    skin_tone: str = ""
    
    # Facial Features
    face_shape: str = ""  # oval, round, square, heart, oblong
    eye_color: str = ""   # blue, brown, green, hazel, amber
    eye_shape: str = ""   # almond, round, hooded, upturned
    eyebrow_style: str = ""  # thick, thin, arched, straight
    nose_shape: str = ""  # straight, button, aquiline, broad
    lip_shape: str = ""   # full, thin, heart-shaped, wide
    
    # Hair
    hair_color: str = ""  # natural colors or fantasy
    hair_style: str = ""  # long, short, curly, straight, wavy
    hair_length: str = "" # shoulder-length, waist-length, pixie, etc.
    facial_hair: str = "" # beard, mustache, goatee, clean-shaven
    
    # Body Characteristics  
    height: str = ""      # tall, average, short, petite
    build: BuildType = BuildType.AVERAGE
    distinctive_features: List[str] = field(default_factory=list)  # scars, tattoos, etc.
    
    # Style & Clothing
    clothing_style: str = ""      # casual, formal, bohemian, gothic, etc.
    typical_outfit: str = ""      # specific outfit description
    accessories: List[str] = field(default_factory=list)  # jewelry, glasses, etc.
    color_palette: List[str] = field(default_factory=list)  # preferred colors
    
    # Personality Traits (for behavioral consistency)
    personality_traits: List[str] = field(default_factory=list)
    mannerisms: List[str] = field(default_factory=list)
    voice_characteristics: str = ""  # if applicable for audio
    
    # Entity Classification
    entity_type: str = "person"  # "person" | "environment" | "object" | "creature"

    # Environment-specific fields (used when entity_type != "person")
    lighting: str = ""
    atmosphere: str = ""
    time_of_day: str = ""
    architecture_style: str = ""

    # Technical Metadata
    created_by: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    reference_images: List[str] = field(default_factory=list)  # paths to reference images
    
    # Usage Statistics
    times_used: int = 0
    last_used: Optional[datetime] = None
    successful_generations: int = 0
    
    def to_prompt_text(self) -> str:
        """Convert character sheet to detailed prompt text for AI generation"""
        if self.entity_type == "environment":
            return self._environment_prompt_text()

        prompt_parts = []

        # Basic description
        if self.description:
            prompt_parts.append(self.description)
        
        # Physical characteristics
        physical_desc = []
        if self.gender != GenderType.UNSPECIFIED:
            physical_desc.append(f"{self.gender.value}")
        if self.age_range:
            physical_desc.append(f"{self.age_range.value}")
        if self.ethnicity:
            physical_desc.append(f"{self.ethnicity} ethnicity")
        if self.skin_tone:
            physical_desc.append(f"{self.skin_tone} skin")
        
        if physical_desc:
            prompt_parts.append(", ".join(physical_desc))
        
        # Facial features
        face_desc = []
        if self.face_shape:
            face_desc.append(f"{self.face_shape} face")
        if self.eye_color and self.eye_shape:
            face_desc.append(f"{self.eye_shape} {self.eye_color} eyes")
        elif self.eye_color:
            face_desc.append(f"{self.eye_color} eyes")
        if self.nose_shape:
            face_desc.append(f"{self.nose_shape} nose")
        if self.lip_shape:
            face_desc.append(f"{self.lip_shape} lips")
        
        if face_desc:
            prompt_parts.append(", ".join(face_desc))
        
        # Hair description
        hair_desc = []
        if self.hair_color:
            hair_desc.append(f"{self.hair_color} hair")
        if self.hair_style:
            hair_desc.append(f"{self.hair_style}")
        if self.hair_length:
            hair_desc.append(f"{self.hair_length}")
        if self.facial_hair and self.facial_hair != "clean-shaven":
            hair_desc.append(f"with {self.facial_hair}")
        
        if hair_desc:
            prompt_parts.append(" ".join(hair_desc))
        
        # Body and build
        if self.height or self.build != BuildType.AVERAGE:
            body_desc = []
            if self.height:
                body_desc.append(f"{self.height} height")
            if self.build != BuildType.AVERAGE:
                body_desc.append(f"{self.build.value} build")
            prompt_parts.append(", ".join(body_desc))
        
        # Distinctive features
        if self.distinctive_features:
            prompt_parts.append(f"distinctive features: {', '.join(self.distinctive_features)}")
        
        # Clothing and style
        if self.typical_outfit:
            prompt_parts.append(f"wearing {self.typical_outfit}")
        elif self.clothing_style:
            prompt_parts.append(f"dressed in {self.clothing_style} style")
        
        if self.accessories:
            prompt_parts.append(f"accessories: {', '.join(self.accessories)}")
        
        return ". ".join(prompt_parts) + "."

    def _environment_prompt_text(self) -> str:
        """Build prompt text for environment entity type"""
        parts = []
        if self.description:
            parts.append(self.description)
        if self.architecture_style:
            parts.append(f"{self.architecture_style} architecture")
        if self.lighting:
            parts.append(f"{self.lighting} lighting")
        if self.atmosphere:
            parts.append(f"{self.atmosphere} atmosphere")
        if self.time_of_day:
            parts.append(f"time of day: {self.time_of_day}")
        if self.color_palette:
            parts.append(f"color palette: {', '.join(self.color_palette)}")
        if self.distinctive_features:
            parts.append(f"details: {', '.join(self.distinctive_features)}")
        return ". ".join(parts) + "." if parts else "An environment."

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, list):
                data[key] = value.copy()
            else:
                data[key] = value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterSheet':
        """Create CharacterSheet from dictionary"""
        # Handle enum conversions
        if 'gender' in data and isinstance(data['gender'], str):
            data['gender'] = GenderType(data['gender'])
        if 'age_range' in data and isinstance(data['age_range'], str):
            data['age_range'] = AgeRange(data['age_range'])
        if 'build' in data and isinstance(data['build'], str):
            data['build'] = BuildType(data['build'])
        
        # Handle datetime conversions
        for date_field in ['created_at', 'updated_at', 'last_used']:
            if date_field in data and isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except (ValueError, TypeError):
                    data[date_field] = datetime.now()
        
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate character sheet and return list of issues"""
        issues = []
        
        if not self.name or self.name == "Unnamed Character":
            issues.append("Character needs a name")
        
        if not self.description:
            issues.append("Character needs a basic description")
        
        if not self.character_id:
            issues.append("Character needs a unique ID")
        
        # Check for minimum viable character definition
        essential_features = [
            self.gender != GenderType.UNSPECIFIED,
            bool(self.age_range),
            bool(self.skin_tone or self.ethnicity),
            bool(self.hair_color or self.hair_style),
            bool(self.eye_color)
        ]
        
        if sum(essential_features) < 3:
            issues.append("Character needs more physical characteristics defined")
        
        return issues
    
    def update_usage_stats(self, successful: bool = True):
        """Update usage statistics"""
        self.times_used += 1
        self.last_used = datetime.now()
        if successful:
            self.successful_generations += 1
        self.updated_at = datetime.now()


# Fields stored as dedicated DB columns (queried/filtered/indexed)
_STRUCTURED_FIELDS = {
    "character_id", "name", "description", "entity_type",
    "gender", "age_range", "build", "created_by",
    "created_at", "updated_at", "version",
    "times_used", "last_used", "successful_generations",
}


class CharacterLockManager:
    """
    Manages character consistency and locks for video generation.
    Storage backed by SQLAlchemy (Character model in core.models).
    """

    def __init__(self):
        self.characters: Dict[str, CharacterSheet] = {}
        self.active_locks: Dict[str, str] = {}  # session_id -> character_id
        self._db_loaded = False
        self._legacy_storage_path = Path("characters")

    # ── DB session management ──────────────────────────────────────────

    def _get_session(self):
        """Get a new DB session. Imported lazily to avoid circular imports."""
        from core.database import SessionLocal
        return SessionLocal()

    def _ensure_db_loaded(self):
        """Load characters from DB on first access, then migrate legacy JSON."""
        if self._db_loaded:
            return

        try:
            self._load_from_db()
            self._migrate_legacy_json()
        except Exception as e:
            logger.error(f"Failed to load characters from DB: {e}")
        finally:
            self._db_loaded = True

    def _load_from_db(self):
        """Load all characters from the database into memory."""
        from core.models import Character

        db = self._get_session()
        try:
            rows = db.query(Character).all()
            for row in rows:
                sheet = self._row_to_sheet(row)
                self.characters[sheet.character_id] = sheet
            logger.info(f"Loaded {len(rows)} characters from database")
        finally:
            db.close()

    def _migrate_legacy_json(self):
        """Migrate characters from legacy JSON files to the database."""
        if not self._legacy_storage_path.exists():
            return

        json_files = list(self._legacy_storage_path.glob("*.json"))
        if not json_files:
            return

        migrated = 0
        db = self._get_session()
        try:
            from core.models import Character

            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    char_id = data.get("character_id", "")
                    if char_id and char_id not in self.characters:
                        sheet = CharacterSheet.from_dict(data)
                        row_data = self._sheet_to_row_dict(sheet)
                        row = Character(**row_data)
                        db.add(row)
                        self.characters[sheet.character_id] = sheet
                        migrated += 1
                except Exception as e:
                    logger.error(f"Failed to migrate {json_file}: {e}")

            if migrated > 0:
                db.commit()
                logger.info(f"Migrated {migrated} characters from JSON to database")

                # Rename legacy directory to prevent re-migration
                migrated_path = Path("characters_migrated")
                try:
                    self._legacy_storage_path.rename(migrated_path)
                    logger.info(f"Renamed '{self._legacy_storage_path}' to '{migrated_path}'")
                except Exception as e:
                    logger.warning(
                        f"Could not rename legacy characters dir: {e}. "
                        f"Please manually remove '{self._legacy_storage_path}' to prevent re-migration."
                    )
        except Exception as e:
            db.rollback()
            logger.error(f"JSON migration failed: {e}")
        finally:
            db.close()

    # ── Row ↔ CharacterSheet conversion ────────────────────────────────

    @staticmethod
    def _row_to_sheet(row) -> CharacterSheet:
        """Convert a Character DB row to a CharacterSheet dataclass."""
        attrs = row.attributes or {}

        data = {
            "character_id": row.character_id,
            "name": row.name or "Unnamed Character",
            "description": row.description or "",
            "entity_type": row.entity_type or "person",
            "gender": row.gender or "unspecified",
            "age_range": row.age_range or "young adult (20-35)",
            "build": row.build or "average",
            "created_by": row.created_by,
            "created_at": row.created_at or datetime.now(),
            "updated_at": row.updated_at or datetime.now(),
            "version": row.version or "1.0",
            "times_used": row.times_used or 0,
            "last_used": row.last_used,
            "successful_generations": row.successful_generations or 0,
        }
        # Merge in all attribute fields
        data.update(attrs)

        return CharacterSheet.from_dict(data)

    @staticmethod
    def _sheet_to_row_dict(sheet: CharacterSheet) -> dict:
        """Convert a CharacterSheet to a dict for creating/updating a Character row."""
        full_dict = sheet.to_dict()

        structured = {}
        attributes = {}

        for key, value in full_dict.items():
            if key in _STRUCTURED_FIELDS:
                structured[key] = value
            else:
                attributes[key] = value

        # Handle datetime fields — store as datetime objects, not ISO strings
        for dt_field in ("created_at", "updated_at", "last_used"):
            if dt_field in structured and isinstance(structured[dt_field], str):
                try:
                    structured[dt_field] = datetime.fromisoformat(structured[dt_field])
                except (ValueError, TypeError):
                    structured[dt_field] = None

        # Handle enum values — store as strings for DB
        for enum_field in ("gender", "age_range", "build"):
            if enum_field in structured and hasattr(structured[enum_field], 'value'):
                structured[enum_field] = structured[enum_field].value

        structured["attributes"] = attributes
        return structured

    # ── DB write helpers ───────────────────────────────────────────────

    def _save_to_db(self, character: CharacterSheet):
        """Save or update a character in the database."""
        from core.models import Character

        db = self._get_session()
        try:
            row_data = self._sheet_to_row_dict(character)
            existing = db.query(Character).filter(
                Character.character_id == character.character_id
            ).first()

            if existing:
                for key, value in row_data.items():
                    setattr(existing, key, value)
            else:
                row = Character(**row_data)
                db.add(row)

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save character {character.character_id}: {e}")
        finally:
            db.close()

    def _delete_from_db(self, character_id: str):
        """Delete a character from the database."""
        from core.models import Character

        db = self._get_session()
        try:
            db.query(Character).filter(
                Character.character_id == character_id
            ).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete character {character_id}: {e}")
        finally:
            db.close()

    # ── Public API (identical signatures to original) ──────────────────

    def create_character(self, character_data: Dict[str, Any]) -> CharacterSheet:
        """Create a new character from data"""
        self._ensure_db_loaded()

        character = CharacterSheet.from_dict(character_data)

        # Generate ID if not provided
        if not character.character_id:
            import uuid
            character.character_id = f"char_{uuid.uuid4().hex[:12]}"

        # Validate character
        issues = character.validate()
        if issues:
            logger.warning(f"Character {character.name} has validation issues: {issues}")

        # Save to database first, then update in-memory cache
        self._save_to_db(character)
        self.characters[character.character_id] = character

        logger.info(f"Created character: {character.name} ({character.character_id})")
        return character

    def get_character(self, character_id: str) -> Optional[CharacterSheet]:
        """Get character by ID"""
        self._ensure_db_loaded()
        return self.characters.get(character_id)

    def get_all_characters(self) -> List[CharacterSheet]:
        """Get all characters"""
        self._ensure_db_loaded()
        return list(self.characters.values())

    def update_character(self, character_id: str, updates: Dict[str, Any]) -> Optional[CharacterSheet]:
        """Update existing character"""
        self._ensure_db_loaded()

        if character_id not in self.characters:
            return None

        character = self.characters[character_id]

        # Apply updates
        for key, value in updates.items():
            if hasattr(character, key):
                setattr(character, key, value)

        character.updated_at = datetime.now()

        # Persist to database
        self._save_to_db(character)

        logger.info(f"Updated character: {character.name} ({character_id})")
        return character

    def delete_character(self, character_id: str) -> bool:
        """Delete character"""
        self._ensure_db_loaded()

        if character_id not in self.characters:
            return False

        character = self.characters.pop(character_id)

        # Remove from database
        self._delete_from_db(character_id)

        # Remove any active locks
        self.release_character_lock(character_id)

        logger.info(f"Deleted character: {character.name} ({character_id})")
        return True

    def lock_character_for_session(self, session_id: str, character_id: str) -> bool:
        """Lock character for consistency in a generation session"""
        self._ensure_db_loaded()

        if character_id not in self.characters:
            return False

        # Release any existing lock for this session
        if session_id in self.active_locks:
            old_char_id = self.active_locks[session_id]
            logger.info(f"Releasing previous character lock: {old_char_id}")

        self.active_locks[session_id] = character_id

        character = self.characters[character_id]
        character.update_usage_stats()

        logger.info(f"Locked character {character.name} for session {session_id}")
        return True

    def get_session_character(self, session_id: str) -> Optional[CharacterSheet]:
        """Get the character locked for a session"""
        self._ensure_db_loaded()

        if session_id not in self.active_locks:
            return None

        character_id = self.active_locks[session_id]
        return self.characters.get(character_id)

    def release_character_lock(self, character_id: str) -> bool:
        """Release character lock"""
        sessions_to_remove = [
            session_id for session_id, char_id in self.active_locks.items()
            if char_id == character_id
        ]

        for session_id in sessions_to_remove:
            del self.active_locks[session_id]

        if sessions_to_remove:
            logger.info(f"Released character lock for character {character_id}")
            return True
        return False

    def release_session_lock(self, session_id: str) -> bool:
        """Release lock for a specific session"""
        if session_id in self.active_locks:
            character_id = self.active_locks.pop(session_id)
            logger.info(f"Released session {session_id} lock on character {character_id}")
            return True
        return False

    def get_character_prompt_enhancement(self, session_id: str, base_prompt: str) -> str:
        """Enhance prompt with character consistency"""
        character = self.get_session_character(session_id)
        if not character:
            return base_prompt

        character_prompt = character.to_prompt_text()

        # Combine character description with base prompt
        if "character" in base_prompt.lower() or "person" in base_prompt.lower():
            # Replace generic character references
            enhanced_prompt = f"{character_prompt} {base_prompt}"
        else:
            # Add character as the subject
            enhanced_prompt = f"Character: {character_prompt}. Scene: {base_prompt}"

        logger.info(f"Enhanced prompt with character {character.name}")
        return enhanced_prompt

    def get_stats(self) -> Dict[str, Any]:
        """Get character lock manager statistics"""
        self._ensure_db_loaded()

        total_usage = sum(char.times_used for char in self.characters.values())
        successful_generations = sum(char.successful_generations for char in self.characters.values())

        return {
            "total_characters": len(self.characters),
            "active_locks": len(self.active_locks),
            "total_usage": total_usage,
            "successful_generations": successful_generations,
            "success_rate": successful_generations / max(total_usage, 1) * 100,
            "most_used_character": max(
                self.characters.values(),
                key=lambda c: c.times_used,
                default=None
            ).name if self.characters else None
        }


# Global character lock manager instance
character_manager = CharacterLockManager()