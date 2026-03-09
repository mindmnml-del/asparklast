"""
Unit tests for Character Lock System
Test character creation, validation, and consistency management
"""

import pytest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.character_lock import (
    CharacterSheet,
    CharacterLockManager,
    GenderType,
    AgeRange,
    BuildType
)
from core.models import Base


class TestCharacterSheet:
    """Test CharacterSheet functionality"""

    def test_character_creation_defaults(self):
        """Test character creation with default values"""
        character = CharacterSheet()
        
        assert character.name == "Unnamed Character"
        assert character.gender == GenderType.UNSPECIFIED
        assert character.age_range == AgeRange.YOUNG_ADULT
        assert character.build == BuildType.AVERAGE
        assert isinstance(character.created_at, datetime)
        assert character.times_used == 0

    def test_character_creation_with_data(self):
        """Test character creation with specific data"""
        character = CharacterSheet(
            name="Test Hero",
            gender=GenderType.FEMALE,
            age_range=AgeRange.YOUNG_ADULT,
            ethnicity="Caucasian",
            eye_color="blue",
            hair_color="blonde"
        )
        
        assert character.name == "Test Hero"
        assert character.gender == GenderType.FEMALE
        assert character.age_range == AgeRange.YOUNG_ADULT
        assert character.ethnicity == "Caucasian"
        assert character.eye_color == "blue"
        assert character.hair_color == "blonde"

    def test_character_validation_minimal(self):
        """Test character validation with minimal data"""
        character = CharacterSheet(
            name="Valid Character",
            character_id="test_char_123",
            description="A test character",
            gender=GenderType.MALE,
            skin_tone="fair",
            hair_color="brown",
            eye_color="green"
        )
        
        issues = character.validate()
        assert len(issues) == 0  # Should be valid

    def test_character_validation_incomplete(self):
        """Test character validation with incomplete data"""
        character = CharacterSheet()  # Default values
        
        issues = character.validate()
        assert len(issues) > 0
        assert "Character needs a name" in issues
        assert "Character needs a unique ID" in issues
        assert "Character needs a basic description" in issues

    def test_character_prompt_generation(self):
        """Test conversion to prompt text"""
        character = CharacterSheet(
            name="Epic Hero",
            description="A brave warrior",
            gender=GenderType.MALE,
            age_range=AgeRange.YOUNG_ADULT,
            ethnicity="Nordic",
            skin_tone="fair",
            face_shape="angular",
            eye_color="blue",
            eye_shape="piercing",
            hair_color="blonde",
            hair_style="long",
            height="tall",
            build=BuildType.MUSCULAR,
            typical_outfit="leather armor and cloak"
        )
        
        prompt = character.to_prompt_text()
        
        # Check that all major attributes are included
        assert "brave warrior" in prompt
        assert "male" in prompt
        assert "young adult" in prompt
        assert "Nordic ethnicity" in prompt
        assert "fair skin" in prompt
        assert "angular face" in prompt
        assert "piercing blue eyes" in prompt
        assert "blonde hair" in prompt
        assert "long" in prompt
        assert "tall height" in prompt
        assert "muscular build" in prompt
        assert "wearing leather armor and cloak" in prompt

    def test_character_serialization(self):
        """Test dictionary conversion and back"""
        character = CharacterSheet(
            name="Serialization Test",
            gender=GenderType.FEMALE,
            age_range=AgeRange.TEENAGER,
            build=BuildType.ATHLETIC,
            distinctive_features=["scar on left cheek", "tattoo on arm"],
            personality_traits=["brave", "impulsive"]
        )
        
        # Convert to dict
        data = character.to_dict()
        
        # Check enum conversion
        assert data["gender"] == "female"
        assert data["age_range"] == "teenager (13-19)"
        assert data["build"] == "athletic"
        assert isinstance(data["created_at"], str)
        
        # Convert back from dict
        restored = CharacterSheet.from_dict(data)
        
        assert restored.name == character.name
        assert restored.gender == character.gender
        assert restored.age_range == character.age_range
        assert restored.build == character.build
        assert restored.distinctive_features == character.distinctive_features

    def test_character_usage_stats(self):
        """Test usage statistics tracking"""
        character = CharacterSheet(name="Stats Test")
        
        assert character.times_used == 0
        assert character.successful_generations == 0
        assert character.last_used is None
        
        # Update stats - successful
        character.update_usage_stats(successful=True)
        
        assert character.times_used == 1
        assert character.successful_generations == 1
        assert character.last_used is not None
        
        # Update stats - failed
        character.update_usage_stats(successful=False)
        
        assert character.times_used == 2
        assert character.successful_generations == 1  # No change
        assert character.last_used is not None


class TestCharacterLockManager:
    """Test CharacterLockManager functionality"""

    @pytest.fixture
    def temp_manager(self):
        """Create a temporary character manager backed by in-memory SQLite"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=test_engine)
        TestSession = sessionmaker(bind=test_engine)

        manager = CharacterLockManager()
        manager._db_loaded = True  # Skip lazy loading from real DB
        manager.characters.clear()
        manager.active_locks.clear()
        manager._get_session = lambda: TestSession()  # Override session factory

        yield manager

        Base.metadata.drop_all(bind=test_engine)

    def test_create_character(self, temp_manager):
        """Test character creation through manager"""
        character_data = {
            "name": "Manager Test",
            "description": "A test character created through manager",
            "gender": "female",
            "age_range": "young adult (20-35)",
            "eye_color": "brown",
            "hair_color": "black"
        }
        
        character = temp_manager.create_character(character_data)
        
        assert character.name == "Manager Test"
        assert character.character_id.startswith("char_")
        assert len(character.character_id) == 17  # "char_" + 12 hex chars
        assert character.gender == GenderType.FEMALE
        assert character in temp_manager.characters.values()

    def test_character_retrieval(self, temp_manager):
        """Test character retrieval methods"""
        # Create test character
        character_data = {"name": "Retrieval Test", "description": "Test"}
        character = temp_manager.create_character(character_data)
        
        # Test get by ID
        retrieved = temp_manager.get_character(character.character_id)
        assert retrieved == character
        
        # Test get all
        all_chars = temp_manager.get_all_characters()
        assert len(all_chars) == 1
        assert character in all_chars
        
        # Test non-existent character
        missing = temp_manager.get_character("nonexistent_id")
        assert missing is None

    def test_character_update(self, temp_manager):
        """Test character updating"""
        # Create character
        character_data = {"name": "Update Test", "description": "Original"}
        character = temp_manager.create_character(character_data)
        original_updated_at = character.updated_at
        
        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)
        
        # Update character
        updates = {
            "description": "Updated description",
            "eye_color": "green",
            "personality_traits": ["updated", "trait"]
        }
        
        updated_char = temp_manager.update_character(character.character_id, updates)
        
        assert updated_char is not None
        assert updated_char.description == "Updated description"
        assert updated_char.eye_color == "green"
        assert updated_char.personality_traits == ["updated", "trait"]
        assert updated_char.updated_at >= original_updated_at

    def test_character_deletion(self, temp_manager):
        """Test character deletion"""
        # Create character
        character_data = {"name": "Delete Test", "description": "To be deleted"}
        character = temp_manager.create_character(character_data)
        char_id = character.character_id
        
        assert char_id in temp_manager.characters
        
        # Delete character
        success = temp_manager.delete_character(char_id)
        
        assert success is True
        assert char_id not in temp_manager.characters
        
        # Try to delete non-existent character
        success = temp_manager.delete_character("nonexistent")
        assert success is False

    def test_character_locking(self, temp_manager):
        """Test character locking for sessions"""
        # Create character
        character_data = {"name": "Lock Test", "description": "For locking"}
        character = temp_manager.create_character(character_data)
        char_id = character.character_id
        session_id = "test_session_123"
        
        # Lock character
        success = temp_manager.lock_character_for_session(session_id, char_id)
        assert success is True
        
        # Check session character
        locked_char = temp_manager.get_session_character(session_id)
        assert locked_char == character
        
        # Check that usage stats were updated
        assert character.times_used == 1
        assert character.last_used is not None

    def test_session_lock_management(self, temp_manager):
        """Test session lock management"""
        # Create two characters
        char1_data = {"name": "Character 1", "description": "First"}
        char2_data = {"name": "Character 2", "description": "Second"}
        char1 = temp_manager.create_character(char1_data)
        char2 = temp_manager.create_character(char2_data)
        
        session_id = "test_session"
        
        # Lock first character
        temp_manager.lock_character_for_session(session_id, char1.character_id)
        assert temp_manager.get_session_character(session_id) == char1
        
        # Lock second character (should replace first)
        temp_manager.lock_character_for_session(session_id, char2.character_id)
        assert temp_manager.get_session_character(session_id) == char2
        
        # Release session lock
        success = temp_manager.release_session_lock(session_id)
        assert success is True
        assert temp_manager.get_session_character(session_id) is None

    def test_prompt_enhancement(self, temp_manager):
        """Test prompt enhancement with character consistency"""
        # Create character
        character_data = {
            "name": "Enhancement Test",
            "description": "A mystical wizard",
            "gender": "male",
            "age_range": "middle-aged (36-55)",
            "hair_color": "silver",
            "eye_color": "violet",
            "typical_outfit": "flowing robes"
        }
        character = temp_manager.create_character(character_data)
        session_id = "enhancement_session"
        
        # Lock character for session
        temp_manager.lock_character_for_session(session_id, character.character_id)
        
        # Test prompt enhancement
        base_prompt = "casting a powerful spell in ancient library"
        enhanced = temp_manager.get_character_prompt_enhancement(session_id, base_prompt)
        
        assert "mystical wizard" in enhanced
        assert "silver hair" in enhanced
        assert "violet eyes" in enhanced
        assert "flowing robes" in enhanced
        assert "casting a powerful spell" in enhanced
        
        # Test with no locked character
        no_char_enhanced = temp_manager.get_character_prompt_enhancement("no_session", base_prompt)
        assert no_char_enhanced == base_prompt

    def test_character_persistence(self, temp_manager):
        """Test character saving to database"""
        from core.models import Character

        # Create character
        character_data = {
            "name": "Persistence Test",
            "description": "Should persist in database",
            "eye_color": "amber",
            "distinctive_features": ["birthmark on forehead"]
        }

        character = temp_manager.create_character(character_data)
        char_id = character.character_id

        # Verify it was saved to DB by querying directly
        db = temp_manager._get_session()
        try:
            row = db.query(Character).filter(Character.character_id == char_id).first()
            assert row is not None
            assert row.name == "Persistence Test"
            assert row.description == "Should persist in database"
            assert row.attributes.get("eye_color") == "amber"
            assert row.attributes.get("distinctive_features") == ["birthmark on forehead"]
        finally:
            db.close()

    def test_manager_statistics(self, temp_manager):
        """Test character manager statistics"""
        # Initially empty
        stats = temp_manager.get_stats()
        assert stats["total_characters"] == 0
        assert stats["active_locks"] == 0
        assert stats["total_usage"] == 0
        
        # Create and use characters
        char1_data = {"name": "Stats Char 1", "description": "First"}
        char2_data = {"name": "Stats Char 2", "description": "Second"}
        
        char1 = temp_manager.create_character(char1_data)
        char2 = temp_manager.create_character(char2_data)
        
        # Use characters
        temp_manager.lock_character_for_session("session1", char1.character_id)
        temp_manager.lock_character_for_session("session2", char2.character_id)
        
        # Additional usage
        char1.update_usage_stats(successful=True)
        char1.update_usage_stats(successful=False)
        char2.update_usage_stats(successful=True)
        
        stats = temp_manager.get_stats()
        
        assert stats["total_characters"] == 2
        assert stats["active_locks"] == 2
        assert stats["total_usage"] == 5  # 2 from locks + 3 manual updates  
        assert stats["successful_generations"] == 4  # 2 from locks + 2 manual successful
        assert stats["success_rate"] == 80.0  # 4/5 * 100
        assert stats["most_used_character"] in ["Stats Char 1", "Stats Char 2"]