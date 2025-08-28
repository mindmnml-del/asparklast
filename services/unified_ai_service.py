"""
Unified AI Service - Consolidated from all AI service variants
Combines: RAG, Diversity, Rate Limiting, Caching, Async Support, Self-Critique
Optimized for performance and maintainability
"""

import os
import json
import time
import asyncio
import logging
import random
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import settings, get_master_prompt_path, validate_api_key

# Set up logging
logger = logging.getLogger(__name__)

class UnifiedAIService:
    """
    Unified AI Service that consolidates all previous AI service functionality
    Features: Singleton pattern, async support, intelligent caching, RAG, diversity
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the service only once"""
        if self._initialized:
            return
            
        self._initialized = True
        
        # Core state
        self.model = None
        self.is_configured = False
        self.last_error = None
        self.master_prompt = ""
        
        # Performance tracking
        self.request_count = 0
        self.total_response_time = 0
        self.last_request_time = 0
        
        # Rate limiting
        self.request_queue = asyncio.Queue(maxsize=settings.max_concurrent_requests)
        self.rate_limiter_lock = asyncio.Lock()
        
        # Caching
        self.cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "size": 0}
        
        # Diversity tracking (prevent repetitive responses)
        self.recent_responses = []
        self.diversity_window = 10
        
        # RAG system
        self.knowledge_base = {}
        self.rag_ready = False
        
        # Auto-initialize if possible
        if validate_api_key():
            try:
                self._initialize()
            except Exception as e:
                logger.warning(f"Auto-initialization failed: {e}")
    
    def _initialize(self) -> bool:
        """Initialize the AI service with Google API"""
        try:
            if not validate_api_key():
                self.last_error = "Google API key not configured"
                return False
            
            # Configure Google AI
            genai.configure(api_key=settings.google_api_key)
            
            # Create model with optimized settings
            generation_config = {
                "temperature": settings.ai_temperature,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": settings.ai_max_tokens,
            }
            
            safety_settings = [
                {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
            ]
            
            self.model = genai.GenerativeModel(
                model_name=settings.ai_model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Load master prompt
            self._load_master_prompt()
            
            # Initialize RAG if enabled
            if settings.enable_rag:
                self._initialize_rag()
            
            self.is_configured = True
            self.last_error = None
            logger.info("✅ Unified AI Service initialized successfully")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"❌ AI Service initialization failed: {e}")
            return False
    
    def _load_master_prompt(self) -> None:
        """Load the master prompt from file"""
        try:
            master_path = get_master_prompt_path()
            if master_path.exists():
                with open(master_path, 'r', encoding='utf-8') as f:
                    self.master_prompt = f.read().strip()
                logger.info(f"✅ Master prompt loaded: {len(self.master_prompt)} characters")
            else:
                # Fallback master prompt
                self.master_prompt = self._get_fallback_master_prompt()
                logger.warning("⚠️ Master prompt file not found, using fallback")
        except Exception as e:
            self.master_prompt = self._get_fallback_master_prompt()
            logger.error(f"❌ Error loading master prompt: {e}")
    
    def _get_fallback_master_prompt(self) -> str:
        """Fallback master prompt if file not found"""
        return """
You are an expert AI prompt engineer specialized in creating high-quality prompts for image and video generation models.

Your task is to transform user requests into professional, detailed prompts that will produce exceptional visual content.

Key principles:
1. Be specific and descriptive
2. Include technical details (lighting, composition, style)
3. Structure prompts logically
4. Optimize for the target model
5. Ensure visual coherence

Create prompts that are:
- Technically precise
- Artistically compelling
- Optimized for the specified model
- Rich in visual detail
- Professional quality

Respond with a structured JSON containing:
{
  "structuredPrompt": {
    "subject": "main subject description",
    "setting": "environment and context",
    "lighting": "lighting setup and mood",
    "composition": "camera angle and framing",
    "styleAndMedium": "artistic style and medium",
    "technicalDetails": "technical specifications",
    "mood": "emotional tone and atmosphere"
  },
  "paragraphPrompt": "complete prompt as flowing text",
  "negativePrompt": "elements to avoid",
  "tool": "target generation tool",
  "type": "image or video"
}
"""
    
    def _initialize_rag(self) -> None:
        """Initialize RAG system with knowledge base"""
        try:
            kb_path = settings.knowledge_base_path
            if not Path(kb_path).exists():
                logger.warning(f"⚠️ Knowledge base path not found: {kb_path}")
                return
            
            # Load knowledge files
            knowledge_files = list(Path(kb_path).glob("*.txt")) + list(Path(kb_path).glob("*.md"))
            
            for file_path in knowledge_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.knowledge_base[file_path.name] = content
                except Exception as e:
                    logger.warning(f"⚠️ Could not load {file_path}: {e}")
            
            self.rag_ready = len(self.knowledge_base) > 0
            logger.info(f"✅ RAG initialized with {len(self.knowledge_base)} knowledge files")
            
        except Exception as e:
            logger.error(f"❌ RAG initialization failed: {e}")
            self.rag_ready = False
    
    def ensure_ready(self) -> bool:
        """Ensure the service is ready for use"""
        if not self.is_configured:
            return self._initialize()
        return True
    
    async def _apply_rate_limiting(self) -> None:
        """Apply rate limiting if enabled"""
        if not settings.rate_limit_enabled:
            return
        
        async with self.rate_limiter_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < settings.rate_limit_delay:
                wait_time = settings.rate_limit_delay - time_since_last
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()
    
    def _get_cache_key(self, request_data: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        if not settings.enable_cache:
            return None
        
        # Create hash from relevant request data
        cache_data = {
            "subject_action": request_data.get("subject_action", ""),
            "artistic_styles": sorted(request_data.get("artistic_styles", [])),
            "target_model": request_data.get("target_model", ""),
            "prompt_type": request_data.get("prompt_type", ""),
            "lighting": request_data.get("lighting", ""),
            "mood": request_data.get("mood", "")
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get response from cache if available"""
        if not cache_key or not settings.enable_cache:
            return None
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if cached_data["expires"] > datetime.now():
                self.cache_stats["hits"] += 1
                logger.info("✅ Cache hit")
                return cached_data["data"]
            else:
                # Remove expired entry
                del self.cache[cache_key]
                self.cache_stats["size"] -= 1
        
        self.cache_stats["misses"] += 1
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Save response to cache"""
        if not cache_key or not settings.enable_cache:
            return
        
        # Clean cache if too large
        if len(self.cache) >= settings.cache_max_size:
            # Remove oldest entries
            sorted_cache = sorted(
                self.cache.items(), 
                key=lambda x: x[1]["created"]
            )
            for old_key, _ in sorted_cache[:len(self.cache) // 4]:
                del self.cache[old_key]
                self.cache_stats["size"] -= 1
        
        self.cache[cache_key] = {
            "data": data,
            "created": datetime.now(),
            "expires": datetime.now() + timedelta(seconds=settings.cache_ttl)
        }
        self.cache_stats["size"] += 1
    
    def _apply_diversity(self, prompt: str) -> str:
        """Apply diversity techniques to avoid repetitive responses"""
        if not settings.enable_diversity:
            return prompt
        
        # Check for similarity with recent responses
        for recent_prompt in self.recent_responses:
            similarity = self._calculate_similarity(prompt, recent_prompt)
            if similarity > 0.8:  # Very similar
                # Add diversity elements
                diversity_additions = [
                    "with unique perspective",
                    "from an unusual angle", 
                    "with creative interpretation",
                    "featuring distinctive details",
                    "with original artistic flair"
                ]
                addition = random.choice(diversity_additions)
                prompt = f"{prompt}, {addition}"
                logger.info("✨ Applied diversity enhancement")
                break
        
        # Track this response
        self.recent_responses.append(prompt)
        if len(self.recent_responses) > self.diversity_window:
            self.recent_responses.pop(0)
        
        return prompt
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _enhance_with_rag(self, request_data: Dict[str, Any]) -> str:
        """Enhance prompt with RAG knowledge"""
        if not self.rag_ready or not settings.enable_rag:
            return ""
        
        # Extract relevant knowledge based on request
        styles = request_data.get("artistic_styles", [])
        subject = request_data.get("subject_action", "")
        
        relevant_knowledge = []
        
        for filename, content in self.knowledge_base.items():
            # Simple relevance check
            content_lower = content.lower()
            if any(style.lower() in content_lower for style in styles):
                relevant_knowledge.append(content[:500])  # First 500 chars
            elif any(word in content_lower for word in subject.lower().split()):
                relevant_knowledge.append(content[:300])  # First 300 chars
        
        if relevant_knowledge:
            rag_context = "\n\n".join(relevant_knowledge[:3])  # Max 3 pieces
            return f"\n\nRelevant knowledge context:\n{rag_context}"
        
        return ""
    
    async def generate_response(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response with all optimizations"""
        
        # Ensure service is ready
        if not self.ensure_ready():
            return {
                "error": True,
                "message": f"AI Service not available: {self.last_error}",
                "details": "Service initialization failed"
            }
        
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()
            
            # Check cache first
            cache_key = self._get_cache_key(request_data)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                return cached_response
            
            start_time = time.time()
            
            # Build enhanced prompt
            base_prompt = self._build_prompt(request_data)
            rag_context = self._enhance_with_rag(request_data)
            
            full_prompt = f"{self.master_prompt}\n\n{base_prompt}{rag_context}"
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt
            )
            
            # Process response
            result = self._process_response(response, request_data)
            
            # Apply diversity
            if "paragraphPrompt" in result:
                result["paragraphPrompt"] = self._apply_diversity(result["paragraphPrompt"])
            
            # Add metadata
            result["_metadata"] = {
                "response_time": time.time() - start_time,
                "cache_used": False,
                "rag_used": bool(rag_context),
                "diversity_applied": settings.enable_diversity,
                "model_used": settings.ai_model_name,
                "request_id": f"req_{int(time.time())}{random.randint(100, 999)}"
            }
            
            # Update stats
            self.request_count += 1
            self.total_response_time += result["_metadata"]["response_time"]
            
            # Cache result
            self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            return {
                "error": True,
                "message": "AI generation failed",
                "details": str(e)
            }
    
    def _build_prompt(self, request_data: Dict[str, Any]) -> str:
        """Build the prompt from request data"""
        
        prompt_parts = []
        
        # Core request
        prompt_parts.append(f"Create a {request_data.get('prompt_type', 'image')} prompt for: {request_data.get('subject_action', '')}")
        
        # Target model
        if target_model := request_data.get('target_model'):
            prompt_parts.append(f"Target model: {target_model}")
        
        # Environment and setting
        if environment := request_data.get('environment_setting'):
            prompt_parts.append(f"Environment: {environment}")
        
        # Technical details
        if lighting := request_data.get('lighting'):
            prompt_parts.append(f"Lighting: {lighting}")
        
        if mood := request_data.get('mood'):
            prompt_parts.append(f"Mood: {mood}")
        
        if color_palette := request_data.get('color_palette'):
            prompt_parts.append(f"Color palette: {color_palette}")
        
        if shot_type := request_data.get('shot_type'):
            prompt_parts.append(f"Shot type: {shot_type}")
        
        # Artistic styles
        if styles := request_data.get('artistic_styles'):
            prompt_parts.append(f"Artistic styles: {', '.join(styles)}")
        
        # Negative prompts
        if negative := request_data.get('negative_prompts'):
            prompt_parts.append(f"Avoid: {negative}")
        
        return "\n".join(prompt_parts)
    
    def _process_response(self, response, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the AI response into structured format"""
        
        try:
            response_text = response.text.strip()
            
            # Try to parse JSON response
            if response_text.startswith('{') and response_text.endswith('}'):
                try:
                    parsed = json.loads(response_text)
                    if "structuredPrompt" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    pass
            
            # Fallback: structure the response manually
            return {
                "structuredPrompt": {
                    "subject": request_data.get("subject_action", ""),
                    "setting": request_data.get("environment_setting", ""),
                    "lighting": request_data.get("lighting", ""),
                    "composition": request_data.get("shot_type", ""),
                    "styleAndMedium": ", ".join(request_data.get("artistic_styles", [])),
                    "mood": request_data.get("mood", ""),
                    "technicalDetails": response_text
                },
                "paragraphPrompt": response_text,
                "negativePrompt": request_data.get("negative_prompts", ""),
                "tool": request_data.get("target_model", "Universal"),
                "type": request_data.get("prompt_type", "image")
            }
            
        except Exception as e:
            logger.error(f"❌ Response processing failed: {e}")
            return {
                "error": True,
                "message": "Failed to process AI response",
                "details": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status and statistics"""
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "configured": self.is_configured,
            "model_name": settings.ai_model_name,
            "request_count": self.request_count,
            "avg_response_time": round(avg_response_time, 2),
            "cache_stats": self.cache_stats.copy(),
            "rag_ready": self.rag_ready,
            "knowledge_files": len(self.knowledge_base),
            "recent_responses_count": len(self.recent_responses),
            "rate_limiting": settings.rate_limit_enabled,
            "last_error": self.last_error
        }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear the response cache"""
        cache_size = len(self.cache)
        self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0, "size": 0}
        
        return {
            "message": f"Cache cleared. Removed {cache_size} entries.",
            "cache_stats": self.cache_stats.copy()
        }

# Global service instance
ai_service = UnifiedAIService()
