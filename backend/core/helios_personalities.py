"""
Helios Master Prompt System - Six Creative Personalities
Dynamic personality selection and prompt enhancement
"""

import logging
import random
from enum import Enum
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


class PersonalityType(Enum):
    """Six Creative Personalities of Helios System"""
    PROMETHEUS = "prometheus"  # Technical Virtuoso
    ZEUS = "zeus"             # Epic Storyteller 
    POSEIDON = "poseidon"     # Atmospheric Artist
    ARTEMIS = "artemis"       # Precision Specialist
    DIONYSUS = "dionysus"     # Creative Rebel
    ATHENA = "athena"         # Strategic Harmonizer


@dataclass
class PersonalityProfile:
    """Profile for each creative personality"""
    name: str
    symbol: str
    title: str
    specialization: str
    traits: List[str]
    signature_elements: List[str]
    language_style: str
    strengths: List[str]
    
    def __str__(self) -> str:
        return f"{self.symbol} {self.name} - {self.title}"


class HeliosPersonalitySystem:
    """Helios Master Prompt System with Six Creative Personalities"""
    
    def __init__(self):
        self.personalities = self._initialize_personalities()
        self.selection_history = []
        self.master_prompt_loaded = False
        
    def _initialize_personalities(self) -> Dict[PersonalityType, PersonalityProfile]:
        """Initialize the six creative personalities"""
        return {
            PersonalityType.PROMETHEUS: PersonalityProfile(
                name="Prometheus",
                symbol="🔥",
                title="The Technical Virtuoso",
                specialization="Technical precision, complex compositions, professional workflows",
                traits=["analytical", "detail-oriented", "methodical", "perfectionist"],
                signature_elements=["Optimal", "Precision", "Technical specifications", "Professional grade"],
                language_style="Precise, technical vocabulary, specific measurements and settings",
                strengths=[
                    "Technical accuracy and professional standards",
                    "Complex lighting setups and camera specifications", 
                    "Photorealistic rendering and architectural visualization",
                    "Measurable quality metrics and industry standards"
                ]
            ),
            
            PersonalityType.ZEUS: PersonalityProfile(
                name="Zeus",
                symbol="⚡",
                title="The Epic Storyteller",
                specialization="Grand narratives, cinematic compositions, emotional storytelling",
                traits=["dramatic", "powerful", "narrative-driven", "emotionally intelligent"],
                signature_elements=["Epic", "Legendary", "Cinematic", "Breathtaking", "Majestic"],
                language_style="Dramatic, powerful adjectives, storytelling elements",
                strengths=[
                    "Epic, awe-inspiring scenes with strong emotional impact",
                    "Cinematic storytelling and character development",
                    "Dramatic lighting and powerful compositions",
                    "Hero's journey narratives and mythological themes"
                ]
            ),
            
            PersonalityType.POSEIDON: PersonalityProfile(
                name="Poseidon", 
                symbol="🌊",
                title="The Atmospheric Artist",
                specialization="Mood, atmosphere, environmental storytelling, natural elements",
                traits=["fluid", "intuitive", "atmospheric", "nature-connected"],
                signature_elements=["Atmospheric", "Flowing", "Immersive", "Natural", "Organic"],
                language_style="Flowing, atmospheric descriptions, natural metaphors",
                strengths=[
                    "Environmental mood and atmospheric conditions",
                    "Weather effects, natural lighting, and organic compositions",
                    "Immersive environments that tell stories through atmosphere",
                    "Emotional resonance through environmental design"
                ]
            ),
            
            PersonalityType.ARTEMIS: PersonalityProfile(
                name="Artemis",
                symbol="🌟", 
                title="The Precision Specialist",
                specialization="Clean aesthetics, minimalism, sharp focus, refined details",
                traits=["clean", "focused", "minimalist", "refined", "strategic"],
                signature_elements=["Precise", "Clean", "Refined", "Strategic", "Focused"],
                language_style="Clean, concise, purposeful language",
                strengths=[
                    "Clean, uncluttered compositions with perfect focus",
                    "Minimalist design and strategic use of negative space",
                    "Sharp, precise imagery with surgical attention to detail",
                    "Strategic decisions on what to include AND exclude"
                ]
            ),
            
            PersonalityType.DIONYSUS: PersonalityProfile(
                name="Dionysus",
                symbol="🎭",
                title="The Creative Rebel", 
                specialization="Unconventional creativity, bold experimentation, artistic risks",
                traits=["spontaneous", "experimental", "boundary-pushing", "artistic"],
                signature_elements=["Bold", "Experimental", "Unconventional", "Innovative", "Artistic"],
                language_style="Bold, experimental, unconventional terminology",
                strengths=[
                    "Creative risks and unconventional approaches",
                    "Artistic experimentation and bold creative choices",
                    "Breaking traditional rules for innovative results",
                    "Originality and pushing creative boundaries"
                ]
            ),
            
            PersonalityType.ATHENA: PersonalityProfile(
                name="Athena",
                symbol="🔮",
                title="The Strategic Harmonizer",
                specialization="Balance, harmony, strategic thinking, holistic integration", 
                traits=["strategic", "balanced", "wise", "integrative", "diplomatic"],
                signature_elements=["Harmonious", "Strategic", "Balanced", "Integrated", "Synergistic"],
                language_style="Balanced, strategic, integrative language",
                strengths=[
                    "Integration of all creative elements into harmonious wholes",
                    "Balancing competing creative demands",
                    "Strategically sound compositions with perfect balance", 
                    "Synergistic element interaction"
                ]
            )
        }
    
    def analyze_request(self, user_prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze user request to determine optimal personality selection"""
        analysis = {
            "technical_complexity": 0,
            "emotional_intensity": 0,
            "atmospheric_focus": 0,
            "precision_need": 0,
            "creative_experimentation": 0,
            "integration_complexity": 0,
            "keywords": [],
            "style_indicators": [],
            "industry_context": None
        }
        
        prompt_lower = user_prompt.lower()
        
        # Technical complexity indicators
        technical_keywords = [
            'camera', 'lens', 'aperture', 'iso', 'shutter', 'lighting', 'technical',
            'professional', 'specs', 'resolution', '4k', '8k', 'render', 'photorealistic'
        ]
        analysis["technical_complexity"] = sum(1 for kw in technical_keywords if kw in prompt_lower)
        
        # Emotional intensity indicators  
        emotional_keywords = [
            'epic', 'dramatic', 'powerful', 'emotional', 'story', 'narrative', 'cinematic',
            'breathtaking', 'awe', 'majestic', 'hero', 'legendary', 'inspiring'
        ]
        analysis["emotional_intensity"] = sum(1 for kw in emotional_keywords if kw in prompt_lower)
        
        # Atmospheric focus indicators
        atmospheric_keywords = [
            'atmosphere', 'mood', 'weather', 'fog', 'mist', 'rain', 'storm', 'natural',
            'organic', 'flowing', 'immersive', 'environment', 'ambient'
        ]
        analysis["atmospheric_focus"] = sum(1 for kw in atmospheric_keywords if kw in prompt_lower)
        
        # Precision need indicators
        precision_keywords = [
            'clean', 'minimal', 'precise', 'sharp', 'focused', 'clear', 'refined',
            'elegant', 'simple', 'uncluttered', 'strategic'
        ]
        analysis["precision_need"] = sum(1 for kw in precision_keywords if kw in prompt_lower)
        
        # Creative experimentation indicators
        experimental_keywords = [
            'experimental', 'bold', 'unconventional', 'innovative', 'artistic', 'creative',
            'unique', 'original', 'abstract', 'surreal', 'avant-garde'
        ]
        analysis["creative_experimentation"] = sum(1 for kw in experimental_keywords if kw in prompt_lower)
        
        # Integration complexity indicators
        integration_keywords = [
            'balance', 'harmony', 'integrated', 'combined', 'multiple', 'complex',
            'strategic', 'holistic', 'comprehensive', 'synergy'
        ]
        analysis["integration_complexity"] = sum(1 for kw in integration_keywords if kw in prompt_lower)
        
        # Extract style indicators
        style_patterns = [
            r'\b(photorealistic|realistic|photo)\b',
            r'\b(artistic|stylized|painted)\b',
            r'\b(minimal|minimalist|clean)\b', 
            r'\b(experimental|avant-garde|abstract)\b',
            r'\b(cinematic|film|movie)\b'
        ]
        
        for pattern in style_patterns:
            matches = re.findall(pattern, prompt_lower, re.IGNORECASE)
            analysis["style_indicators"].extend(matches)
        
        # Detect industry context
        if any(word in prompt_lower for word in ['photo', 'camera', 'photographer']):
            analysis["industry_context"] = "photography"
        elif any(word in prompt_lower for word in ['film', 'cinema', 'movie', 'scene']):
            analysis["industry_context"] = "cinematography"
        elif any(word in prompt_lower for word in ['game', 'character', 'level']):
            analysis["industry_context"] = "game_design"
        elif any(word in prompt_lower for word in ['architecture', 'building', 'interior']):
            analysis["industry_context"] = "architecture"
        elif any(word in prompt_lower for word in ['digital', 'art', 'painting', 'illustration']):
            analysis["industry_context"] = "digital_art"
        elif any(word in prompt_lower for word in ['fashion', 'model', 'clothing']):
            analysis["industry_context"] = "fashion"
        
        return analysis
    
    def select_personality(self, analysis: Dict[str, Any]) -> Tuple[PersonalityType, List[PersonalityType], str]:
        """Select optimal personality based on request analysis"""
        scores = {
            PersonalityType.PROMETHEUS: analysis["technical_complexity"],
            PersonalityType.ZEUS: analysis["emotional_intensity"],
            PersonalityType.POSEIDON: analysis["atmospheric_focus"], 
            PersonalityType.ARTEMIS: analysis["precision_need"],
            PersonalityType.DIONYSUS: analysis["creative_experimentation"],
            PersonalityType.ATHENA: analysis["integration_complexity"]
        }
        
        # Add context-based scoring
        if analysis.get("industry_context") == "photography":
            scores[PersonalityType.PROMETHEUS] += 2
        elif analysis.get("industry_context") == "cinematography":
            scores[PersonalityType.ZEUS] += 2
        elif analysis.get("industry_context") == "digital_art":
            scores[PersonalityType.DIONYSUS] += 1
        
        # Handle ties and low scores
        max_score = max(scores.values())
        if max_score == 0:
            # No clear indicators - use Athena as balanced default
            primary = PersonalityType.ATHENA
            reasoning = "No specific creative indicators detected, using strategic balance approach"
        else:
            # Get personalities with highest scores
            top_personalities = [p for p, s in scores.items() if s == max_score]
            
            if len(top_personalities) == 1:
                primary = top_personalities[0]
                reasoning = f"Clear {primary.value} indicators detected (score: {max_score})"
            else:
                # Multiple tied personalities - select strategically
                primary = self._resolve_tie(top_personalities, analysis)
                reasoning = f"Multiple high-scoring personalities, selected {primary.value} as primary"
        
        # Select secondary personalities for blending
        sorted_personalities = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        secondary = [p for p, s in sorted_personalities[1:3] if s > 0]
        
        # Update selection history
        self.selection_history.append({
            "primary": primary,
            "secondary": secondary,
            "scores": scores,
            "reasoning": reasoning
        })
        
        return primary, secondary, reasoning
    
    def _resolve_tie(self, tied_personalities: List[PersonalityType], analysis: Dict[str, Any]) -> PersonalityType:
        """Resolve ties between personalities using strategic logic"""
        # Strategic tie resolution based on context
        if PersonalityType.ATHENA in tied_personalities:
            return PersonalityType.ATHENA  # Balance is often the best approach
        elif PersonalityType.PROMETHEUS in tied_personalities and analysis.get("industry_context") in ["photography", "architecture"]:
            return PersonalityType.PROMETHEUS  # Technical excellence for technical fields
        elif PersonalityType.ZEUS in tied_personalities and "story" in str(analysis.get("style_indicators", [])).lower():
            return PersonalityType.ZEUS  # Storytelling when narrative is key
        else:
            return random.choice(tied_personalities)  # Random selection from remaining ties
    
    def get_personality_prompt_enhancement(self, personality: PersonalityType, base_prompt: str) -> str:
        """Get personality-specific prompt enhancements"""
        enhancements = {
            PersonalityType.PROMETHEUS: [
                "with technical precision and professional-grade quality",
                "featuring optimal lighting setup and camera specifications",
                "rendered with photorealistic accuracy and measurable quality metrics"
            ],
            PersonalityType.ZEUS: [
                "with epic scale and cinematic grandeur",
                "featuring dramatic composition and emotional storytelling",
                "creating a breathtaking and awe-inspiring visual narrative"
            ],
            PersonalityType.POSEIDON: [
                "with rich atmospheric mood and natural elements", 
                "featuring immersive environmental storytelling",
                "creating organic flow and emotional resonance through atmosphere"
            ],
            PersonalityType.ARTEMIS: [
                "with clean precision and refined elegance",
                "featuring strategic composition and minimal distraction",
                "creating sharp focus with purposeful simplicity"
            ],
            PersonalityType.DIONYSUS: [
                "with bold creativity and experimental innovation",
                "featuring unconventional approaches and artistic risk-taking",
                "creating original and boundary-pushing visual expression"
            ],
            PersonalityType.ATHENA: [
                "with strategic balance and harmonious integration",
                "featuring synergistic element interaction",
                "creating holistic composition with diplomatic balance"
            ]
        }
        
        enhancement = random.choice(enhancements[personality])
        return f"{base_prompt} {enhancement}"
    
    def get_personality_signature_elements(self, personality: PersonalityType) -> List[str]:
        """Get signature elements for a personality to include in prompts"""
        return self.personalities[personality].signature_elements
    
    def generate_personality_context(self, primary: PersonalityType, secondary: List[PersonalityType] = None) -> str:
        """Generate context string for personality-driven generation"""
        primary_profile = self.personalities[primary]
        
        context = f"Primary Personality: {primary_profile}\n"
        context += f"Specialization: {primary_profile.specialization}\n"
        context += f"Key Traits: {', '.join(primary_profile.traits)}\n"
        context += f"Signature Elements: {', '.join(primary_profile.signature_elements)}\n"
        
        if secondary:
            context += "\nSecondary Influences: "
            context += ", ".join([f"{self.personalities[p].name}" for p in secondary])
        
        return context
    
    def get_selection_stats(self) -> Dict[str, Any]:
        """Get personality selection statistics"""
        if not self.selection_history:
            return {"total_selections": 0, "personality_usage": {}, "avg_scores": {}}
        
        personality_count = {}
        total_scores = {}
        
        for selection in self.selection_history:
            primary = selection["primary"] 
            personality_count[primary] = personality_count.get(primary, 0) + 1
            
            for personality, score in selection["scores"].items():
                if personality not in total_scores:
                    total_scores[personality] = []
                total_scores[personality].append(score)
        
        avg_scores = {p: sum(scores)/len(scores) for p, scores in total_scores.items()}
        
        return {
            "total_selections": len(self.selection_history),
            "personality_usage": personality_count,
            "avg_scores": avg_scores,
            "most_used": max(personality_count, key=personality_count.get) if personality_count else None
        }


# Global Helios system instance
helios_system = HeliosPersonalitySystem()