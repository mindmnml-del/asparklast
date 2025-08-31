import pytest
from unittest.mock import patch

from core.helios_personalities import HeliosPersonalitySystem, PersonalityType, PersonalityProfile

@pytest.fixture
def helios_system():
    """Fixture for a fresh HeliosPersonalitySystem instance for each test."""
    return HeliosPersonalitySystem()

class TestHeliosPersonalitySystem:
    """Tests for the HeliosPersonalitySystem class."""

    def test_initialization(self, helios_system):
        """Test that the system initializes with all six personalities."""
        assert len(helios_system.personalities) == 6
        for p_type in PersonalityType:
            assert p_type in helios_system.personalities
            assert isinstance(helios_system.personalities[p_type], PersonalityProfile)

    def test_analyze_request_technical(self, helios_system):
        """Test analysis of a technically-focused prompt."""
        prompt = "A photorealistic 8k render of a camera lens with precise lighting."
        analysis = helios_system.analyze_request(prompt)
        assert analysis["technical_complexity"] > 0
        assert analysis["emotional_intensity"] == 0
        assert analysis["industry_context"] == "photography"

    def test_analyze_request_emotional(self, helios_system):
        """Test analysis of an emotionally-focused prompt."""
        prompt = "An epic, dramatic and breathtaking cinematic story of a hero."
        analysis = helios_system.analyze_request(prompt)
        assert analysis["emotional_intensity"] > 0
        assert analysis["technical_complexity"] == 0
        assert analysis["industry_context"] == "cinematography"

    def test_analyze_request_experimental(self, helios_system):
        """Test analysis of a creative and experimental prompt."""
        prompt = "An unconventional, artistic and abstract painting."
        analysis = helios_system.analyze_request(prompt)
        assert analysis["creative_experimentation"] > 0
        assert analysis["industry_context"] == "digital_art"

    def test_personality_selection_prometheus(self, helios_system):
        """Test that a technical prompt selects Prometheus."""
        prompt = "A professional grade, technical photo of a product with 4k resolution."
        analysis = helios_system.analyze_request(prompt)
        primary, _, _ = helios_system.select_personality(analysis)
        assert primary == PersonalityType.PROMETHEUS

    def test_personality_selection_zeus(self, helios_system):
        """Test that a narrative prompt selects Zeus."""
        prompt = "Create a legendary and majestic story with a powerful and inspiring hero."
        analysis = helios_system.analyze_request(prompt)
        primary, _, _ = helios_system.select_personality(analysis)
        assert primary == PersonalityType.ZEUS

    def test_personality_selection_poseidon(self, helios_system):
        """Test that an atmospheric prompt selects Poseidon."""
        prompt = "An immersive, atmospheric scene with flowing mist and natural rain."
        analysis = helios_system.analyze_request(prompt)
        primary, _, _ = helios_system.select_personality(analysis)
        assert primary == PersonalityType.POSEIDON

    def test_personality_selection_default_athena(self, helios_system):
        """Test that a generic prompt defaults to Athena."""
        prompt = "A picture of a cat."
        analysis = helios_system.analyze_request(prompt)
        primary, _, reasoning = helios_system.select_personality(analysis)
        assert primary == PersonalityType.ATHENA
        assert "No specific creative indicators detected" in reasoning

    @patch('random.choice', return_value=PersonalityType.DIONYSUS)
    def test_personality_selection_tie_breaker(self, mock_random_choice, helios_system):
        """Test the tie-breaking logic, mocking random.choice."""
        prompt = "A bold, unconventional, and clean, precise image." # Dionysus vs Artemis
        analysis = helios_system.analyze_request(prompt)
        primary, _, _ = helios_system.select_personality(analysis)
        assert primary == PersonalityType.DIONYSUS
        mock_random_choice.assert_called_once()

    @patch('random.choice', return_value="with technical precision and professional-grade quality")
    def test_prompt_enhancement(self, mock_random_choice, helios_system):
        """Test the prompt enhancement functionality."""
        base_prompt = "A futuristic city"
        personality = PersonalityType.PROMETHEUS
        enhanced_prompt = helios_system.get_personality_prompt_enhancement(personality, base_prompt)

        assert base_prompt in enhanced_prompt
        assert "with technical precision and professional-grade quality" in enhanced_prompt
        mock_random_choice.assert_called_once()

    def test_signature_elements(self, helios_system):
        """Test retrieval of signature elements."""
        elements = helios_system.get_personality_signature_elements(PersonalityType.ARTEMIS)
        assert "Precise" in elements
        assert "Clean" in elements

    def test_context_generation(self, helios_system):
        """Test the generation of a personality context string."""
        context = helios_system.generate_personality_context(PersonalityType.ZEUS, [PersonalityType.POSEIDON])
        assert "Primary Personality: ⚡ Zeus" in context
        assert "Secondary Influences: Poseidon" in context

    def test_selection_stats(self, helios_system):
        """Test the statistics tracking for personality selections."""
        assert helios_system.get_selection_stats()["total_selections"] == 0

        prompt = "A technical photo."
        analysis = helios_system.analyze_request(prompt)
        helios_system.select_personality(analysis)

        stats = helios_system.get_selection_stats()
        assert stats["total_selections"] == 1
        assert stats["most_used"] == PersonalityType.PROMETHEUS
        assert stats["personality_usage"][PersonalityType.PROMETHEUS] == 1
