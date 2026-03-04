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
from google.genai import types as genai_types
from services.genai_client import (
    get_genai_async_client,
    get_genai_client,
    build_safety_settings,
    validate_vertex_config,
)

from config import settings, get_master_prompt_path, validate_api_key
from core.helios_personalities import helios_system, PersonalityType

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
        self.async_client = None
        self.generation_config = None
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
        """Initialize the AI service with Vertex AI via google-genai"""
        try:
            if not validate_api_key():
                self.last_error = "No valid credentials configured"
                return False

            # Get shared async client (Vertex AI)
            self.async_client = get_genai_async_client()

            # Build generation config (used per-call)
            self.generation_config = genai_types.GenerateContentConfig(
                temperature=settings.ai_temperature,
                top_p=0.95,
                top_k=64,
                max_output_tokens=settings.ai_max_tokens,
                safety_settings=build_safety_settings(),
            )

            # Load master prompt
            self._load_master_prompt()

            # Initialize RAG if enabled
            if settings.enable_rag:
                self._initialize_rag()

            self.is_configured = True
            self.last_error = None
            logger.info("Unified AI Service initialized successfully (Vertex AI)")
            return True

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"AI Service initialization failed: {e}")
            return False
    
    def _load_master_prompt(self) -> None:
        """Load the Helios master prompt from file"""
        try:
            master_path = get_master_prompt_path()
            if master_path.exists():
                with open(master_path, 'r', encoding='utf-8') as f:
                    self.master_prompt = f.read().strip()
                logger.info(f"✅ Helios Master Prompt loaded: {len(self.master_prompt)} characters")
            else:
                # Fallback master prompt
                self.master_prompt = self._get_fallback_master_prompt()
                logger.warning("⚠️ Helios master prompt file not found, using fallback")
        except Exception as e:
            self.master_prompt = self._get_fallback_master_prompt()
            logger.error(f"❌ Error loading Helios master prompt: {e}")
    
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
        user_text = request_data.get("prompt", "") or request_data.get("subject_action", "")
        cache_data = {
            "subject_action": user_text,
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
    
    def _enhance_with_rag(self, request_data: Dict[str, Any],
                          helios_keywords: Optional[List[str]] = None) -> str:
        """Enhance prompt with RAG knowledge using Vertex Search"""
        if not settings.enable_rag:
            return ""

        try:
            # Import vertex search service
            from services.vertex_search_service import vertex_search_service

            # Dynamically extract search terms from the user's request
            search_terms = self._extract_search_terms(request_data, helios_keywords=helios_keywords)

            if not search_terms:
                return ""

            search_query = " ".join(search_terms)
            logger.debug(f"RAG search query: {search_query}")

            # Check if vertex search is available
            if not vertex_search_service.is_available():
                logger.warning("⚠️ Vertex credentials missing or service unavailable, skipping RAG. "
                             "Generation will continue without knowledge base context.")
                return ""
            
            # Perform search using asyncio
            import asyncio
            try:
                # If we're already in an async context, use the existing loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, but can't await here
                    # Fall back to local knowledge base approach
                    return self._fallback_local_rag(request_data)
                else:
                    search_result = loop.run_until_complete(
                        vertex_search_service.search(search_query, max_results=3)
                    )
            except RuntimeError:
                # No event loop or can't run in current context
                search_result = asyncio.run(
                    vertex_search_service.search(search_query, max_results=3)
                )
            
            if search_result.get("error") or not search_result.get("results"):
                logger.debug("No relevant knowledge found in Vertex Search")
                return ""
            
            # Extract relevant content from search results
            relevant_knowledge = []
            for result in search_result["results"][:3]:  # Max 3 results
                doc = result.get("document", {})
                content = doc.get("content", "") or doc.get("snippet", "")
                if content:
                    # Limit content length
                    content = content[:400] + "..." if len(content) > 400 else content
                    relevant_knowledge.append(content)
            
            if relevant_knowledge:
                rag_context = "\n\n".join(relevant_knowledge)
                logger.info(f"RAG enhanced with {len(relevant_knowledge)} knowledge pieces from Vertex Search")
                return f"\n\nRelevant knowledge context:\n{rag_context}"
            
            return ""
            
        except Exception as e:
            logger.error(f"Error in Vertex Search RAG: {e}")
            # Fall back to local knowledge base if available
            return self._fallback_local_rag(request_data)
    
    def _fallback_local_rag(self, request_data: Dict[str, Any]) -> str:
        """Fallback to local knowledge base RAG"""
        if not self.rag_ready:
            return ""
        
        # Original local RAG logic as fallback
        styles = request_data.get("artistic_styles", [])
        subject = request_data.get("prompt", "") or request_data.get("subject_action", "")

        relevant_knowledge = []
        
        for filename, content in self.knowledge_base.items():
            content_lower = content.lower()
            if any(style.lower() in content_lower for style in styles):
                relevant_knowledge.append(content[:500])
            elif any(word in content_lower for word in subject.lower().split()):
                relevant_knowledge.append(content[:300])
        
        if relevant_knowledge:
            rag_context = "\n\n".join(relevant_knowledge[:3])
            return f"\n\nRelevant knowledge context:\n{rag_context}"
        
        return ""

    def _select_helios_personality(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze request and select Helios personality for RAG enrichment.
        Returns a dict with personality info, or None if analysis fails."""
        try:
            user_prompt = (
                request_data.get("prompt", "") or request_data.get("subject_action", "")
            ).strip()
            if not user_prompt:
                return None

            context = {}
            for field in ("artistic_styles", "mood", "lighting", "shot_type",
                          "environment_setting", "prompt_type", "target_model"):
                value = request_data.get(field)
                if value:
                    context[field] = value

            analysis = helios_system.analyze_request(user_prompt, context)
            primary, secondary, reasoning = helios_system.select_personality(analysis)
            signature_elements = helios_system.get_personality_signature_elements(primary)

            result = {
                "primary_name": primary.value,
                "secondary_names": [p.value for p in secondary],
                "reasoning": reasoning,
                "signature_elements": signature_elements,
            }
            logger.info(f"Helios personality selected: {primary.value} (reasoning: {reasoning})")
            return result
        except Exception as e:
            logger.warning(f"Helios personality selection failed: {e}. Continuing without personality enrichment.")
            return None

    def _extract_search_terms(self, request_data: Dict[str, Any],
                              helios_keywords: Optional[List[str]] = None) -> List[str]:
        """Extract dynamic search terms from the user's request data for RAG queries"""
        terms = []

        # Primary: user's subject/action description (supports both schema keys)
        subject = (request_data.get("prompt", "") or request_data.get("subject_action", "")).strip()
        if subject:
            # Split into meaningful words, filter out very short ones
            words = [w for w in subject.split() if len(w) > 2]
            terms.extend(words[:5])  # Cap at 5 words from subject

        # Secondary: artistic styles
        styles = request_data.get("artistic_styles", [])
        if styles:
            terms.extend(styles[:3])

        # Tertiary: other relevant fields
        for field in ("lighting", "mood", "environment_setting", "shot_type"):
            value = request_data.get(field, "")
            if value and isinstance(value, str) and value.strip():
                words = [w for w in value.strip().split() if len(w) > 2]
                terms.extend(words[:3])

        # Prompt type context
        prompt_type = request_data.get("prompt_type", "")
        if prompt_type:
            terms.append(prompt_type)

        # Helios personality signature keywords (enrichment from personality system)
        if helios_keywords:
            terms.extend(helios_keywords[:3])

        # Deduplicate while preserving order
        seen = set()
        unique_terms = []
        for term in terms:
            lower = term.lower()
            if lower not in seen:
                seen.add(lower)
                unique_terms.append(term)

        return unique_terms[:10]  # Cap at 10 terms for a focused query

    async def _enhance_with_rag_async(self, request_data: Dict[str, Any], user_token: str = None,
                                      helios_keywords: Optional[List[str]] = None) -> str:
        """Async version of RAG enhancement using Vertex Search with proper auth context"""
        if not settings.enable_rag:
            return ""

        try:
            # Dynamically extract search terms from the actual user request
            search_terms = self._extract_search_terms(request_data, helios_keywords=helios_keywords)

            if not search_terms:
                logger.debug("No search terms extracted from request, skipping RAG")
                return ""

            search_query = " ".join(search_terms)

            # If Georgian text detected, translate key terms to English for better search
            if any(ord(c) >= 0x10D0 and ord(c) <= 0x10FF for c in search_query):
                georgian_to_english = {
                    "ვიდეო": "video", "ფოტო": "photo", "პრომპტ": "prompt",
                    "აპლიკაცია": "application", "ლოგო": "logo", "გენერაცია": "generation",
                    "ტექნიკა": "technique", "სტილი": "style", "ეფექტი": "effect",
                    "ანიმაცია": "animation", "პორტრეტი": "portrait", "პეიზაჟი": "landscape"
                }
                english_terms = []
                for term in search_terms:
                    english_term = georgian_to_english.get(term, term)
                    english_terms.append(english_term)
                search_query = " ".join(english_terms)

            logger.info(f"🔍 RAG async search query: {search_query}")
            
            # Use Discovery Engine with service account credentials
            logger.info("🔍 Using Discovery Engine with service account...")
            from services.vertex_search_service import vertex_search_service
            
            if vertex_search_service.is_available():
                logger.info("🔍 Vertex Search service is available, performing search...")
                search_result = await vertex_search_service.search(search_query, max_results=3)
                
                if not search_result.get("error") and search_result.get("results"):
                    logger.info(f"🔍 Direct Vertex Search found {len(search_result['results'])} results")
                    
                    # Extract relevant content from search results
                    relevant_knowledge = []
                    for i, result in enumerate(search_result["results"][:3]):  # Max 3 results
                        doc = result.get("document", {})
                        content_field = doc.get("content")
                        snippet_field = doc.get("snippet", "")
                        
                        logger.info(f"🔍 Document {i+1}: content='{content_field[:50] if content_field else 'None'}...', snippet='{snippet_field[:50]}...'")
                        
                        content = content_field or snippet_field
                        if content:
                            # Limit content length and clean up HTML entities
                            content = content.replace("&#39;", "'").replace("&quot;", '"')
                            content = content[:400] + "..." if len(content) > 400 else content
                            relevant_knowledge.append(content)
                            logger.info(f"✅ Added content from document {i+1}: {len(content)} characters")
                        else:
                            logger.warning(f"⚠️ Document {i+1} has no content or snippet")
                    
                    if relevant_knowledge:
                        rag_context = "\n\n".join(relevant_knowledge)
                        logger.info(f"✅ RAG enhanced with {len(relevant_knowledge)} knowledge pieces from direct Vertex Search")
                        return f"\n\nRelevant knowledge context:\n{rag_context}"
                    else:
                        logger.warning("⚠️ No usable content found in search results")
                else:
                    logger.info(f"🔍 Direct Vertex Search error or no results: {search_result.get('message', 'No results')}")
            else:
                logger.warning("⚠️ Vertex credentials missing or service unavailable, skipping RAG enhancement. "
                             "Generation will continue without knowledge base context.")

            return ""

        except Exception as e:
            logger.error(f"Error in Vertex Search RAG: {e}. Continuing generation without RAG.")
            return ""
    
    async def generate_response(self, request_data: Dict[str, Any], user_token: str = None) -> Dict[str, Any]:
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

            # Helios personality analysis for RAG enrichment
            helios_info = self._select_helios_personality(request_data)
            helios_keywords = helios_info.get("signature_elements") if helios_info else None

            logger.info("About to call RAG async function...")
            # Use Vertex Search RAG with user authentication token + Helios keywords
            rag_context = await self._enhance_with_rag_async(
                request_data, user_token, helios_keywords=helios_keywords
            )
            logger.info(f"RAG function returned {len(rag_context)} characters")
            
            full_prompt = f"{self.master_prompt}\n\n{base_prompt}{rag_context}"
            
            # Generate response (native async via Vertex AI)
            response = await self.async_client.models.generate_content(
                model=settings.ai_model_name,
                contents=full_prompt,
                config=self.generation_config,
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

            # Add Helios personality metadata if available
            if helios_info:
                result["_metadata"]["helios"] = {
                    "primary_personality": helios_info["primary_name"],
                    "secondary_personalities": helios_info["secondary_names"],
                    "selection_reasoning": helios_info["reasoning"],
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
        user_text = request_data.get('prompt', '') or request_data.get('subject_action', '')
        prompt_parts.append(f"Create a {request_data.get('prompt_type', 'image')} prompt for: {user_text}")
        
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
        
        # ROBUST response parsing for Google Generative AI
        response_text = ""
        
        try:
            # Method 1: Direct text access
            if hasattr(response, 'text'):
                response_text = response.text.strip()
                logger.debug("Used direct text access")
        except Exception as e1:
            logger.debug(f"Direct text failed: {e1}")
            try:
                # Method 2: Candidates approach
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts_text = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                parts_text.append(part.text)
                        response_text = "".join(parts_text).strip()
                        logger.debug("Used candidates parts approach")
            except Exception as e2:
                logger.debug(f"Candidates approach failed: {e2}")
                try:
                    # Method 3: Alternative parts access
                    if hasattr(response, 'parts') and response.parts:
                        parts_text = []
                        for part in response.parts:
                            if hasattr(part, 'text'):
                                parts_text.append(part.text)
                        response_text = "".join(parts_text).strip()
                        logger.debug("Used direct parts approach")
                except Exception as e3:
                    logger.error(f"All parsing methods failed: {e1}, {e2}, {e3}")
                    response_text = "Error: Unable to parse AI response - please try again"
        
        # Validate we got actual text content
        if not response_text or response_text.startswith("<google"):
            response_text = "Error: AI response parsing failed - please regenerate"
        
        logger.info(f"Final parsed text length: {len(response_text)} characters")
        print(f"DEBUG: PARSED RESPONSE TEXT: {response_text[:200]}...")
        
        try:
            
            # Try to parse JSON response
            if response_text.startswith('{') and response_text.endswith('}'):
                try:
                    parsed = json.loads(response_text)
                    if "structuredPrompt" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    pass
            
            # Fallback: structure the response manually
            user_text = request_data.get("prompt", "") or request_data.get("subject_action", "")
            return {
                "structuredPrompt": {
                    "subject": user_text,
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

    def extract_character_traits(self, prompt: str) -> Dict[str, Any]:
        """Extract visual/character traits from a prompt using Gemini.

        Returns a dict with CharacterSheet-compatible keys plus
        'is_character' (bool) indicating if a visual subject was found.
        """
        extraction_config = genai_types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.9,
            max_output_tokens=1024,
        )

        extraction_prompt = f"""Analyze the following creative prompt and extract visual subject traits.

PROMPT: "{prompt}"

Determine what type of visual subject this describes:
- "person" for humans or humanoid characters
- "creature" for animals, monsters, aliens
- "environment" for scenes, landscapes, architecture
- "object" for items, vehicles, artifacts

If the prompt does NOT describe any identifiable visual subject (e.g. abstract concepts, actions only), set "is_character" to false and return minimal data.

Return ONLY a valid JSON object with these keys:
{{
  "is_character": true,
  "entity_type": "person",
  "name": "descriptive name for this subject",
  "description": "brief description",
  "gender": "male|female|non-binary|unspecified",
  "age_range": "child (5-12)|teenager (13-19)|young adult (20-35)|middle-aged (36-55)|senior (55+)",
  "ethnicity": "",
  "skin_tone": "",
  "eye_color": "",
  "hair_color": "",
  "hair_style": "",
  "height": "",
  "build": "slim|athletic|average|muscular|curvy|heavy-set",
  "distinctive_features": [],
  "clothing_style": "",
  "typical_outfit": "",
  "accessories": [],
  "color_palette": [],
  "lighting": "",
  "atmosphere": "",
  "time_of_day": "",
  "architecture_style": ""
}}

Rules:
- For person/creature: fill physical traits, leave environment fields empty.
- For environment: fill lighting/atmosphere/time_of_day/architecture_style, leave physical traits empty.
- Only include traits explicitly mentioned or strongly implied in the prompt.
- Leave fields as empty string "" or empty array [] if not mentioned.
- Return ONLY the JSON, no markdown fences, no explanation."""

        try:
            client = get_genai_client()
            response = client.models.generate_content(
                model=settings.ai_model_name,
                contents=extraction_prompt,
                config=extraction_config,
            )

            text = response.text.strip()
            # Strip markdown fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()
            if text.startswith("json"):
                text = text[4:].strip()

            return json.loads(text)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response as JSON: {e}")
            return {"is_character": False, "error": "Failed to parse AI response"}
        except Exception as e:
            logger.error(f"Character extraction failed: {e}")
            return {"is_character": False, "error": str(e)}

# Global service instance
ai_service = UnifiedAIService()
