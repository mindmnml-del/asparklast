"""
Unit tests for Helios Personality System
Tests the HeliosPersonalitySystem functionality and personality management
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

# Import the system under test
from core.helios_personalities import HeliosPersonalitySystem, PersonalityType


class TestHeliosPersonalitySystem:
    """Test suite for HeliosPersonalitySystem"""
    
    def setup_method(self):
        """Setup test fixtures before each test method"""
        self.helios = HeliosPersonalitySystem()
    
    def test_initialization(self):
        """Test that HeliosPersonalitySystem initializes correctly"""
        assert self.helios is not None
        assert hasattr(self.helios, 'personalities')
        assert len(self.helios.personalities) == 6  # Should have 6 personalities
    
    def test_personality_types_available(self):
        """Test that all personality types are available"""
        personality_types = list(PersonalityType)
        assert len(personality_types) == 6
        
        expected_types = ["prometheus", "zeus", "poseidon", "artemis", "dionysus", "athena"]
        for personality_type in personality_types:
            assert personality_type.value in expected_types
    
    def test_analyze_request_basic(self):
        """Test basic request analysis functionality"""
        test_prompt = "Help me write a technical documentation"
        
        analysis = self.helios.analyze_request(test_prompt)
        
        assert analysis is not None
        # Check for actual analysis keys from the implementation
        assert "technical_complexity" in analysis
        assert "emotional_intensity" in analysis
        assert "atmospheric_focus" in analysis
        assert "precision_need" in analysis
        assert "creative_experimentation" in analysis
        assert "integration_complexity" in analysis
    
    def test_select_personality(self):
        """Test personality selection based on analysis"""
        # Create a mock analysis that matches actual implementation keys
        mock_analysis = {
            "technical_complexity": 0.9,
            "emotional_intensity": 0.2,
            "atmospheric_focus": 0.1,
            "precision_need": 0.8,
            "creative_experimentation": 0.2,
            "integration_complexity": 0.3
        }
        
        primary, secondary, reasoning = self.helios.select_personality(mock_analysis)
        
        assert primary in PersonalityType
        assert isinstance(secondary, list)
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
    
    def test_get_personality_prompt_enhancement(self):
        """Test prompt enhancement for different personalities"""
        base_prompt = "Explain quantum computing"
        
        for personality in PersonalityType:
            enhanced_prompt = self.helios.get_personality_prompt_enhancement(
                personality, base_prompt
            )
            
            assert isinstance(enhanced_prompt, str)
            assert len(enhanced_prompt) > len(base_prompt)
            assert base_prompt in enhanced_prompt
    
    def test_generate_personality_context(self):
        """Test personality context generation"""
        primary_personality = PersonalityType.PROMETHEUS
        secondary_personalities = [PersonalityType.ATHENA]
        
        context = self.helios.generate_personality_context(
            primary_personality, secondary_personalities
        )
        
        assert isinstance(context, str)
        assert len(context) > 0
        assert "PROMETHEUS" in context.upper()
    
    def test_get_selection_stats(self):
        """Test selection statistics functionality"""
        stats = self.helios.get_selection_stats()
        
        assert isinstance(stats, dict)
        # Should have basic stat structure even if no selections made yet
        assert "total_selections" in stats
    
    def test_analyze_request_with_context(self):
        """Test request analysis with context"""
        test_prompt = "Write a story about space exploration"
        context = {"user_preference": "detailed", "session_history": []}
        
        analysis = self.helios.analyze_request(test_prompt, context)
        
        assert analysis is not None
        assert "emotional_intensity" in analysis
        # Story prompt should have high emotional intensity
        assert analysis["emotional_intensity"] > 0.5
    
    def test_personality_profiles_complete(self):
        """Test that all personality profiles are properly initialized"""
        for personality_type in PersonalityType:
            profile = self.helios.personalities[personality_type]
            
            assert hasattr(profile, 'name')
            assert hasattr(profile, 'title')  # Use 'title' instead of 'description'
            assert hasattr(profile, 'traits')
            assert isinstance(profile.name, str)
            assert isinstance(profile.title, str)
            assert len(profile.name) > 0
    
    def test_get_personality_signature_elements(self):
        """Test personality signature elements retrieval"""
        for personality_type in PersonalityType:
            elements = self.helios.get_personality_signature_elements(personality_type)
            
            assert isinstance(elements, list)
            # Should have some signature elements
            if len(elements) > 0:
                assert all(isinstance(elem, str) for elem in elements)
    
    def test_analyze_request_returns_proper_structure(self):
        """Test that analyze_request returns all expected keys"""
        test_prompt = "Create a beautiful landscape"
        analysis = self.helios.analyze_request(test_prompt)
        
        expected_keys = [
            "technical_complexity",
            "emotional_intensity", 
            "atmospheric_focus",
            "precision_need",
            "creative_experimentation",
            "integration_complexity"
        ]
        
        for key in expected_keys:
            assert key in analysis
            assert isinstance(analysis[key], (int, float))
    
    def test_personality_selection_with_real_analysis(self):
        """Test personality selection using real analysis output"""
        test_prompt = "Help me create technical documentation"
        analysis = self.helios.analyze_request(test_prompt)
        
        primary, secondary, reasoning = self.helios.select_personality(analysis)
        
        assert primary in PersonalityType
        assert isinstance(secondary, list)
        assert isinstance(reasoning, str)
        # Technical documentation should likely select PROMETHEUS (technical)
        # but we don't force this since the algorithm might evolve


class TestPersonalityType:
    """Test suite for PersonalityType enum"""
    
    def test_personality_type_values(self):
        """Test that personality types have expected values"""
        expected_values = {
            "prometheus", "zeus", "poseidon", 
            "artemis", "dionysus", "athena"
        }
        
        actual_values = {pt.value for pt in PersonalityType}
        assert actual_values == expected_values
    
    def test_personality_type_uniqueness(self):
        """Test that all personality types are unique"""
        values = [pt.value for pt in PersonalityType]
        assert len(values) == len(set(values))
    
    def test_all_personality_types_accessible(self):
        """Test that all personality types can be accessed"""
        assert PersonalityType.PROMETHEUS.value == "prometheus"
        assert PersonalityType.ZEUS.value == "zeus"
        assert PersonalityType.POSEIDON.value == "poseidon"
        assert PersonalityType.ARTEMIS.value == "artemis"
        assert PersonalityType.DIONYSUS.value == "dionysus"
        assert PersonalityType.ATHENA.value == "athena"


if __name__ == "__main__":
    pytest.main([__file__])
