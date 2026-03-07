"""
Unified Critic Service - Consolidated critic functionality
Provides prompt quality analysis and improvement suggestions
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from google.genai import types as genai_types
from services.genai_client import get_genai_client, validate_vertex_config

from config import settings

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Types of analysis available"""
    PHOTO = "photo"
    VIDEO = "video"
    BOTH = "both"

class UnifiedCriticService:
    """
    Unified Critic Service for prompt quality analysis
    Consolidates basic and enhanced critic functionality
    """
    
    def __init__(self):
        self.client = None
        self.critic_config = None
        self.is_configured = False
        self.cache = {}
        self.analysis_count = 0
        self.total_score = 0

        # Auto-initialize if possible
        if validate_vertex_config():
            try:
                self._initialize()
            except Exception as e:
                logger.warning(f"Critic service auto-init failed: {e}")

    def _initialize(self) -> bool:
        """Initialize the critic service with Vertex AI"""
        try:
            if not validate_vertex_config():
                return False

            self.client = get_genai_client()

            # Critic uses a faster model with lower temperature
            self.critic_config = genai_types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.9,
                max_output_tokens=1024,
            )

            self.is_configured = True
            logger.info("Unified Critic Service initialized (Vertex AI)")
            return True

        except Exception as e:
            logger.error(f"Critic service initialization failed: {e}")
            return False
    
    def analyze_prompt(
        self, 
        prompt: str, 
        negative_prompt: str = "", 
        analysis_type: AnalysisType = AnalysisType.PHOTO
    ) -> Dict[str, Any]:
        """Analyze prompt quality"""
        
        if not self.is_configured:
            if not self._initialize():
                return self._error_response("Critic service not available")
        
        try:
            cache_key = hashlib.md5(f"{prompt}{negative_prompt}{analysis_type.value}".encode()).hexdigest()
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                if time.time() - cached["timestamp"] < settings.cache_ttl:
                    return cached["data"]
            
            analysis_prompt = self._build_analysis_prompt(prompt, negative_prompt, analysis_type)
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=analysis_prompt,
                config=self.critic_config,
            )
            result = self._parse_analysis_response(response.text, analysis_type)
            
            self.cache[cache_key] = {"data": result, "timestamp": time.time()}
            self.analysis_count += 1
            if "overall_score" in result:
                self.total_score += result["overall_score"]
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return self._error_response(f"Analysis failed: {str(e)}")
    
    def _build_analysis_prompt(self, prompt: str, negative_prompt: str, analysis_type: AnalysisType) -> str:
        """Build analysis prompt based on type"""
        categories = self._get_categories(analysis_type)

        if analysis_type == AnalysisType.VIDEO:
            category_guide = (
                "- TEMPORAL_COHERENCE: Logical time progression, scene continuity, consistent pacing cues\n"
                "- MOTION_CLARITY: Explicit motion descriptions, direction, speed, subject movement\n"
                "- NARRATIVE_FLOW: Story arc across shots, cause-and-effect, emotional progression\n"
                "- TECHNICAL_SPECS: Frame rate, resolution, aspect ratio, codec-relevant details\n"
                "- CINEMATIC_QUALITY: Camera movement, depth of field, color grading, filmic language"
            )
        else:
            category_guide = (
                "- CONCEPT_CONFLICT: Clear subject-vs-environment tension, visual contrast, thematic intent\n"
                "- HIERARCHY_COMPOSITION: Foreground/mid/background layering, focal guidance, rule of thirds\n"
                "- ATMOSPHERE_SPECIFICITY: Concrete lighting, weather, time-of-day, sensory detail\n"
                "- TECHNICAL_PRECISION: Camera/lens specs, render settings, resolution, format accuracy\n"
                "- NARRATIVE_DYNAMICS: Story implication, character intent, emotional subtext, viewer engagement"
            )

        return f"""You are a strict prompt-quality grader. Analyze this {analysis_type.value} prompt:

PROMPT: "{prompt}"
NEGATIVE: "{negative_prompt}"

Score each category (0-20):
{categories}

GRADING RUBRIC (apply strictly per category):
0-5 POOR: Missing or contradictory elements, no usable detail for this category.
6-10 BASIC: Generic or vague, recognizable intent but lacks specificity or has flaws.
11-15 GOOD: Solid professional-level detail, clear intent, minor gaps only.
16-20 EXCEPTIONAL: Masterclass detail, precise and evocative, no meaningful improvement possible.

CATEGORY GUIDE:
{category_guide}

SCORING RULES:
- Use the full 0-20 range. Most prompts score 8-14 per category.
- Reserve 16+ for truly exceptional detail. A score of 20 means flawless.
- overall_score = SUM of all 5 category scores (Total 0-100 scale).
- Be critical. Vague prompts must score below 10.

Return ONLY valid JSON:
{{"overall_score": 0, "category_scores": {{"CAT": 0}}, "assessment": "1-2 sentences", "strengths": ["str"], "weaknesses": ["weak"], "top_suggestion": "suggestion", "improved_prompt": "enhanced version"}}"""
    
    def _get_categories(self, analysis_type: AnalysisType) -> str:
        """Get scoring categories based on analysis type"""
        if analysis_type == AnalysisType.VIDEO:
            return "1. TEMPORAL_COHERENCE\n2. MOTION_CLARITY\n3. NARRATIVE_FLOW\n4. TECHNICAL_SPECS\n5. CINEMATIC_QUALITY"
        else:
            return "1. CONCEPT_CONFLICT\n2. HIERARCHY_COMPOSITION\n3. ATMOSPHERE_SPECIFICITY\n4. TECHNICAL_PRECISION\n5. NARRATIVE_DYNAMICS"
    
    def _parse_analysis_response(self, response_text: str, analysis_type: AnalysisType) -> Dict[str, Any]:
        """Parse analysis response"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                result = json.loads(json_text)
                
                required_fields = ["overall_score", "category_scores", "assessment"]
                if all(field in result for field in required_fields):
                    return result
            
            return self._fallback_response()
            
        except Exception:
            return self._fallback_response()
    
    def _fallback_response(self) -> Dict[str, Any]:
        """Fallback response when parsing fails"""
        return {
            "overall_score": 75,
            "category_scores": {"general": 75},
            "assessment": "Basic analysis",
            "strengths": ["Structure present"],
            "weaknesses": ["Could be more detailed"],
            "top_suggestion": "Add more specific details",
            "improved_prompt": "Enhanced version needed"
        }
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "error": True,
            "message": message,
            "overall_score": 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        avg_score = self.total_score / max(self.analysis_count, 1)
        return {
            "configured": self.is_configured,
            "analysis_count": self.analysis_count,
            "average_score": round(avg_score, 1),
            "cache_size": len(self.cache)
        }

# Global instance
critic_service = UnifiedCriticService()
