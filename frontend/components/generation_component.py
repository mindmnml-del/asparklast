"""
Prompt Generation Component for AISpark Studio
Handles the main AI prompt generation interface
"""

import streamlit as st
import json
import time
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

def render_generation_interface(token: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Main prompt generation interface"""
    
    st.title("🚀 AI Prompt Generator")
    st.markdown("Transform your ideas into professional AI prompts")
    
    # Main generation form
    with st.container():
        # Create two columns: main form and tips
        col_main, col_tips = st.columns([2.5, 1])
        
        with col_main:
            result = render_generation_form(token)
            if result:
                return result
        
        with col_tips:
            render_generation_tips()
    
    # Show generated results if available
    if st.session_state.get("aispark_generated_prompt"):
        render_prompt_result(st.session_state["aispark_generated_prompt"], token)
    
    return None

def render_generation_form(token: str) -> Optional[Dict[str, Any]]:
    """Render the main generation form"""
    
    st.markdown("### 🎨 Create Your Prompt")
    
    with st.form("generation_form", clear_on_submit=False):
        insp = st.session_state.get("aispark_inspiration", {})
        # Core input
        subject_action = st.text_area(
            "✨ Describe what you want to create",
            placeholder="A majestic dragon soaring through crystal mountains at sunset, breathing colorful magical fire...",
            height=120,
            help="Be as descriptive as possible. Include details about the subject, action, and setting.",
            key="subject_input",
            value=insp.get("subject", "")
        )
        
        # Primary settings row
        col1, col2 = st.columns(2)
        
        with col1:
            target_model = st.selectbox(
                "🎯 Target AI Model",
                [
                    "Universal", "Midjourney", "DALL-E", "Stable Diffusion", 
                    "Leonardo", "Firefly", "Runway", "Pika"
                ],
                help="Choose the AI model you'll use to generate the content"
            )
            
            prompt_type = st.selectbox(
                "📱 Content Type",
                ["image", "video"],
                help="Type of content to generate"
            )
            theme_profile = st.selectbox(
                "🎭 Theme Profile",
                [
                    "Auto", "Fantasy", "Sci-Fi", "Portrait", "Landscape",
                    "Cyberpunk", "Historical", "Wildlife", "Abstract",
                    "Cinematic Action", "Music Video"
                ],
                help="Choose a thematic style for smarter inspiration and defaults"
            )
        
        with col2:
            artistic_styles = st.multiselect(
                "🎨 Artistic Styles",
                [
                    "Fantasy", "Sci-Fi", "Realistic", "Photorealistic",
                    "Anime", "Cartoon", "Cinematic", "Abstract", 
                    "Impressionist", "Digital Art", "Oil Painting", 
                    "Watercolor", "Sketch", "3D Render", "Cyberpunk",
                    "Steampunk", "Art Nouveau", "Baroque", "Minimalist"
                ],
                help="Select artistic styles to influence the output",
                default=insp.get("styles", [])
            )
            
            shot_type = st.selectbox(
                "📷 Camera/Shot Type",
                [
                    "Default", "Close-up", "Medium shot", "Wide shot", 
                    "Extreme close-up", "Full body", "Portrait",
                    "Bird's eye view", "Low angle", "High angle",
                    "Dutch angle", "Over the shoulder"
                ],
                help="Camera perspective and framing"
            )
        
        # Advanced options
        with st.expander("🎛️ Advanced Options", expanded=False):
            
            col_tech1, col_tech2 = st.columns(2)
            
            with col_tech1:
                lighting = st.text_input(
                    "💡 Lighting Setup",
                    placeholder="Golden hour, dramatic backlighting, soft ambient...",
                    help="Describe the lighting conditions and mood",
                    value=insp.get("lighting", "")
                )
                
                mood = st.text_input(
                    "🎭 Mood & Atmosphere",
                    placeholder="Epic, mysterious, peaceful, dramatic...",
                    help="Emotional tone and feeling of the image",
                    value=insp.get("mood", "")
                )
                
                color_palette = st.text_input(
                    "🎨 Color Palette",
                    placeholder="Warm oranges and purples, cool blues...",
                    help="Preferred color scheme and palette"
                )
            
            with col_tech2:
                environment_setting = st.text_input(
                    "🌍 Environment/Setting",
                    placeholder="Ancient temple, futuristic city, enchanted forest...",
                    help="Background environment and setting details",
                    value=insp.get("environment", "")
                )
                
                negative_prompts = st.text_input(
                    "🚫 Negative Prompts",
                    placeholder="blurry, low quality, distorted, watermark...",
                    help="Things to avoid in the generation"
                )
                
                use_rag = st.checkbox(
                    "🧠 Use Knowledge Enhancement (RAG)",
                    value=True,
                    help="Enhance prompts with knowledge base information"
                )
        
        # Generation controls
        st.markdown("---")
        
        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
        
        with col_btn1:
            generate_button = st.form_submit_button(
                "✨ Generate Prompt",
                use_container_width=True,
                type="primary"
            )
        
        with col_btn2:
            clear_button = st.form_submit_button(
                "🗑️ Clear Form",
                use_container_width=True
            )
        
        with col_btn3:
            inspire_button = st.form_submit_button(
                "🎲 Inspire Me",
                use_container_width=True
            )
        
        # Handle form submissions
        if clear_button:
            clear_form()
            st.rerun()

        if inspire_button:
            fill_random_inspiration(
                prompt_type=prompt_type,
                theme=None if theme_profile == "Auto" else theme_profile,
                available_styles=[
                    "Fantasy", "Sci-Fi", "Realistic", "Photorealistic",
                    "Anime", "Cartoon", "Cinematic", "Abstract", 
                    "Impressionist", "Digital Art", "Oil Painting", 
                    "Watercolor", "Sketch", "3D Render", "Cyberpunk",
                    "Steampunk", "Art Nouveau", "Baroque", "Minimalist"
                ]
            )
            st.rerun()
        
        if generate_button:
            return handle_generation_request(token, {
                "subject_action": subject_action,
                "target_model": target_model,
                "prompt_type": prompt_type,
                "artistic_styles": artistic_styles,
                "shot_type": shot_type,
                "lighting": lighting,
                "mood": mood,
                "color_palette": color_palette,
                "environment_setting": environment_setting,
                "negative_prompts": negative_prompts,
                "use_rag": use_rag
            })
    
    return None

def handle_generation_request(token: str, form_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle the prompt generation request"""
    
    # Validation
    if not form_data.get("subject_action", "").strip():
        st.error("❌ Please describe what you want to create")
        return None
    
    # Prepare request data
    request_data = {
        "subject_action": form_data["subject_action"].strip(),
        "target_model": form_data["target_model"],
        "prompt_type": form_data["prompt_type"],
        "artistic_styles": form_data["artistic_styles"],
        "shot_type": form_data["shot_type"] if form_data["shot_type"] != "Default" else "",
        "lighting": form_data["lighting"].strip() if form_data["lighting"] else "",
        "mood": form_data["mood"].strip() if form_data["mood"] else "",
        "color_palette": form_data["color_palette"].strip() if form_data["color_palette"] else "",
        "environment_setting": form_data["environment_setting"].strip() if form_data["environment_setting"] else "",
        "negative_prompts": form_data["negative_prompts"].strip() if form_data["negative_prompts"] else "",
        "use_rag": form_data["use_rag"]
    }
    
    # Show generation progress
    with st.spinner("🤖 Generating your professional prompt..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate progress steps
        steps = [
            "🔍 Analyzing your request...",
            "🧠 Enhancing with knowledge base...", 
            "🎨 Optimizing for target model...",
            "✨ Generating final prompt..."
        ]
        
        for i, step in enumerate(steps):
            status_text.text(step)
            progress_bar.progress((i + 1) / len(steps))
            time.sleep(0.5)
        
        # Make API request
        from .api_helper import api_client
        result = api_client.generate_prompt(request_data, token)
        
        progress_bar.progress(1.0)
        status_text.text("✅ Generation complete!")
        time.sleep(0.5)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
    
    if result.get("error"):
        st.error(f"❌ Generation failed: {result.get('message', 'Unknown error')}")
        return None
    
    st.success("🎉 Prompt generated successfully!")
    st.session_state["aispark_generated_prompt"] = result
    return result

def render_generation_tips():
    """Render tips and guidance for better prompts"""
    
    st.markdown("### 💡 Pro Tips")
    
    st.info("""
    **For amazing results:**
    
    ✨ **Be specific** - Include details about materials, textures, colors
    
    🎯 **Set the scene** - Describe the environment and atmosphere
    
    📸 **Add technical details** - Mention lighting, camera angles, quality
    
    🎨 **Choose styles** - Select artistic styles that match your vision
    
    🚫 **Use negatives** - Specify what you want to avoid
    """)
    
    # Example prompts
    with st.expander("📖 Example Prompts"):
        st.markdown("""
        **Fantasy Example:**
        *"A mystical elven archer with silver hair, standing in an enchanted forest clearing, dappled sunlight filtering through ancient trees, wearing intricate leather armor with glowing runes, bow drawn and ready, photorealistic, cinematic lighting, 4K"*
        
        **Sci-Fi Example:**
        *"Futuristic cyberpunk cityscape at night, neon lights reflecting on wet streets, flying cars between towering skyscrapers, holographic advertisements, dramatic perspective, high contrast, digital art style"*
        
        **Portrait Example:**
        *"Professional headshot of a confident businesswoman, soft studio lighting, neutral background, sharp focus, natural smile, high resolution, corporate photography style"*
        """)
    
    # Model-specific tips
    with st.expander("🎯 Model-Specific Tips"):
        st.markdown("""
        **Midjourney:**
        - Use artistic language
        - Mention famous artists
        - Add aspect ratios (--ar 16:9)
        - Include quality parameters
        
        **DALL-E:**
        - Clear, simple descriptions
        - Avoid technical jargon
        - Focus on visual elements
        
        **Stable Diffusion:**
        - Technical photography terms
        - Specific camera settings
        - Detailed style descriptions
        """)

def render_prompt_result(result: Dict[str, Any], token: str):
    """Display the generated prompt results"""
    
    st.markdown("---")
    st.markdown("## 🎯 Your Generated Prompt")
    
    raw_response = result.get("raw_response", {})
    
    # Main prompt display (robust to shape differences)
    paragraph = None
    if isinstance(raw_response, dict) and "paragraphPrompt" in raw_response:
        paragraph = raw_response["paragraphPrompt"]
    elif "paragraphPrompt" in result:
        # Fallback: some responses may return paragraphPrompt at the top level
        paragraph = result["paragraphPrompt"]

    if paragraph:
        st.markdown("### 📝 Complete Prompt")
        st.code(paragraph, language="text")
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("📋 Copy Prompt", use_container_width=True):
                st.success("✅ Prompt copied to clipboard!")
        
        with col2:
            if st.button("💾 Save to Favorites", use_container_width=True):
                handle_favorite_toggle(result, token)
        
        with col3:
            if st.button("🔍 Analyze Quality", use_container_width=True):
                analyze_prompt_quality(prompt_text, token)
    
    # Negative prompt
    if isinstance(raw_response, dict) and raw_response.get("negativePrompt"):
        st.markdown("### 🚫 Negative Prompt")
        st.code(raw_response["negativePrompt"], language="text")
    
    # Structured breakdown
    if isinstance(raw_response, dict) and "structuredPrompt" in raw_response:
        with st.expander("📋 Structured Breakdown", expanded=False):
            structured = raw_response["structuredPrompt"]
            
            for key, value in structured.items():
                if value:
                    clean_key = key.replace("_", " ").replace("And", " & ").title()
                    st.markdown(f"**{clean_key}:** {value}")
    
    # Generation metadata
    if isinstance(raw_response, dict) and "_metadata" in raw_response:
        with st.expander("📊 Generation Info", expanded=False):
            metadata = raw_response["_metadata"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                if "response_time" in metadata:
                    st.metric("⏱️ Generation Time", f"{metadata['response_time']:.2f}s")
                if "model_used" in metadata:
                    st.metric("🤖 AI Model", metadata["model_used"])
            
            with col2:
                if "rag_used" in metadata:
                    rag_status = "✅ Enhanced" if metadata["rag_used"] else "➖ Standard"
                    st.metric("🧠 Knowledge Enhancement", rag_status)
                if "cache_used" in metadata:
                    cache_status = "⚡ Cached" if metadata["cache_used"] else "🆕 Fresh"
                    st.metric("💾 Cache Status", cache_status)

    # Debug info for visibility when shapes differ
    with st.expander("🔎 Raw Result (debug)", expanded=False):
        try:
            st.json(result)
        except Exception:
            st.write(result)

def handle_favorite_toggle(result: Dict[str, Any], token: str):
    """Handle favorite toggle for a prompt"""
    
    prompt_id = result.get("id")
    if not prompt_id:
        st.warning("Cannot save to favorites - prompt not saved to database")
        return
    
    from .api_helper import api_client
    
    # Toggle favorite status
    toggle_result = api_client.toggle_favorite(prompt_id, True, token)
    
    if toggle_result.get("error"):
        st.error(f"Failed to save to favorites: {toggle_result.get('message')}")
    else:
        st.success("✅ Saved to favorites!")

def analyze_prompt_quality(prompt: str, token: str):
    """Analyze prompt quality using critic service"""
    
    with st.spinner("🔍 Analyzing prompt quality..."):
        from .api_helper import api_client
        
        analysis = api_client.analyze_prompt(prompt, "", "photo", token)
        
        if analysis.get("error"):
            st.error(f"Analysis failed: {analysis.get('message')}")
            return
        
        # Display analysis results
        st.markdown("#### 📊 Quality Analysis")
        
        overall_score = analysis.get("overall_score", 0)
        
        # Score display with color coding
        if overall_score >= 85:
            score_color = "#00cc44"
            score_emoji = "🌟"
        elif overall_score >= 70:
            score_color = "#88dd00"
            score_emoji = "⭐"
        elif overall_score >= 50:
            score_color = "#ffbb00"
            score_emoji = "🟡"
        else:
            score_color = "#ff4444"
            score_emoji = "🔴"
        
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; border-radius: 8px; background-color: {score_color}20; border: 2px solid {score_color};'>
            <h2 style='color: {score_color}; margin: 0;'>{score_emoji} {overall_score}/100</h2>
            <p style='margin: 0;'>{analysis.get('assessment', 'Quality analysis complete')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Strengths and weaknesses
        col1, col2 = st.columns(2)
        
        with col1:
            if analysis.get("strengths"):
                st.markdown("**✅ Strengths:**")
                for strength in analysis["strengths"]:
                    st.markdown(f"• {strength}")
        
        with col2:
            if analysis.get("weaknesses"):
                st.markdown("**⚠️ Areas to improve:**")
                for weakness in analysis["weaknesses"]:
                    st.markdown(f"• {weakness}")
        
        # Top suggestion
        if analysis.get("top_suggestion"):
            st.info(f"💡 **Top Suggestion:** {analysis['top_suggestion']}")

def clear_form():
    """Clear all form inputs"""
    # Clear session state for form fields
    if "aispark_generated_prompt" in st.session_state:
        del st.session_state["aispark_generated_prompt"]

def _smart_inspiration(prompt_type: str, available_styles: List[str], theme: Optional[str] = None) -> Dict[str, Any]:
    """Generate a rich, varied inspiration using procedural composition, with optional theme guidance."""
    subjects = [
        "ancient dragon", "neon samurai", "cybernetic jaguar", "clockwork automaton",
        "starship captain", "desert wanderer", "underwater goddess", "forest guardian",
        "time-traveling archaeologist", "lunar botanist", "storm sorcerer", "quantum hacker",
        "bioluminescent whale", "glass golem", "celestial messenger", "runic blacksmith",
        "steampunk airship", "sentient orchard", "AI painter", "voyaging lighthouse"
    ]
    actions = [
        "emerging from", "descending into", "soaring above", "weaving through",
        "standing amid", "conjuring", "resting beside", "discovering",
        "dancing within", "guarding", "transforming", "awakening in"
    ]
    environments = [
        "crystalline caverns", "rain-soaked neon alleyways", "ancient temple ruins",
        "floating islands at dusk", "submerged coral city", "glacier-lit fjords",
        "bioluminescent jungle", "abandoned observatory", "clockwork cathedral",
        "windswept desert monoliths", "orbital shipyards", "misty bamboo forest"
    ]
    moods = [
        "epic and awe-inspiring", "mysterious and tense", "serene and contemplative",
        "whimsical and playful", "elegant and refined", "ominous and foreboding",
        "triumphant and radiant", "nostalgic and dreamy"
    ]
    lightings = [
        "golden hour backlight", "cinematic rim lighting", "soft volumetric rays",
        "noir high-contrast", "bioluminescent glow", "moonlit reflections",
        "subsurface scattering highlights", "haze with god rays", "studio softbox key"
    ]
    THEME_BANKS = {
            "Fantasy": {
                "subjects": ["ancient dragon", "forest druid", "phoenix knight", "elf archer", "rune golem"],
                "environments": ["enchanted grove", "crystalline caverns", "floating isles", "ancient temple ruins"],
                "moods": ["epic and awe-inspiring", "mystical and serene", "ominous and arcane"],
                "lightings": ["golden hour backlight", "moonlit glow", "volumetric god rays"],
                "style_pairs": [["Fantasy", "Cinematic"], ["Art Nouveau", "Impressionist"]]
            },
            "Sci-Fi": {
                "subjects": ["starship captain", "quantum hacker", "android courier", "exo-suit explorer", "lunar botanist"],
                "environments": ["orbital shipyards", "neon megacity", "alien mesa", "sterile research lab"],
                "moods": ["futuristic and sleek", "mysterious and tense", "optimistic and bright"],
                "lightings": ["neon rim light", "noir high-contrast", "soft volumetric rays"],
                "style_pairs": [["Sci-Fi", "Cinematic"], ["Cyberpunk", "Digital Art"]]
            },
            "Portrait": {
                "subjects": ["renaissance noble", "modern dancer", "astronaut portrait", "artisan blacksmith", "CEO headshot"],
                "environments": ["studio backdrop", "moody workshop", "sunlit window", "minimalist set"],
                "moods": ["elegant and refined", "confident and calm", "intimate and soft"],
                "lightings": ["studio softbox key", "rembrandt lighting", "butterfly lighting"],
                "style_pairs": [["Photorealistic", "Cinematic"], ["Realistic", "Minimalist"]]
            },
            "Landscape": {
                "subjects": ["glacier valley", "desert canyon", "alpine lake", "mossy waterfall", "volcanic shore"],
                "environments": ["windswept monoliths", "misty bamboo forest", "starlit ridgeline", "foggy marsh"],
                "moods": ["serene and contemplative", "dramatic and wild", "nostalgic and dreamy"],
                "lightings": ["golden hour backlight", "blue hour glow", "moonlit reflections"],
                "style_pairs": [["Realistic", "Photorealistic"], ["Impressionist", "Watercolor"]]
            },
            "Cyberpunk": {
                "subjects": ["neon ronin", "augmented courier", "street netrunner", "synth detective"],
                "environments": ["rain-soaked neon alleyways", "holographic market", "elevated maglev station"],
                "moods": ["gritty and tense", "nocturnal and electric"],
                "lightings": ["neon rim light", "reflective neon bounce", "noir high-contrast"],
                "style_pairs": [["Cyberpunk", "Digital Art"], ["Cinematic", "3D Render"]]
            },
            "Historical": {
                "subjects": ["roman centurion", "medieval cartographer", "renaissance painter", "samurai retainer"],
                "environments": ["forum basilica", "castle scriptorium", "seaside palazzo", "edo street"],
                "moods": ["elegant and formal", "stoic and dignified", "scholarly and quiet"],
                "lightings": ["soft window light", "candlelit chiaroscuro", "diffused daylight"],
                "style_pairs": [["Oil Painting", "Baroque"], ["Art Nouveau", "Impressionist"]]
            },
            "Wildlife": {
                "subjects": ["bioluminescent whale", "snow leopard", "scarlet macaw", "desert fox", "great horned owl"],
                "environments": ["glacier-lit fjords", "tropical canopy", "dune sea", "ancient redwoods"],
                "moods": ["majestic and calm", "alert and focused", "playful and curious"],
                "lightings": ["moonlit reflections", "soft morning haze", "golden rim light"],
                "style_pairs": [["Photorealistic", "Realistic"], ["Cinematic", "Minimalist"]]
            },
            "Abstract": {
                "subjects": ["fractured geometry", "fluid aurora", "glass tessellation", "chromatic vortex"],
                "environments": ["infinite void", "gallery plinth", "floating planes", "liquid horizon"],
                "moods": ["whimsical and playful", "mysterious and tense", "elegant and refined"],
                "lightings": ["studio gradient", "subsurface glow", "haze with god rays"],
                "style_pairs": [["Abstract", "Minimalist"], ["Digital Art", "Impressionist"]]
            },
            "Cinematic Action": {
                "subjects": ["stunt rider", "rooftop chaser", "spy operative", "storm chaser"],
                "environments": ["rainy night city", "cargo ship deck", "desert highway", "forest ravine"],
                "moods": ["intense and kinetic", "urgent and high-stakes"],
                "lightings": ["noir high-contrast", "backlit spray", "sparks and embers"],
                "style_pairs": [["Cinematic", "Realistic"], ["Photorealistic", "3D Render"]]
            },
            "Music Video": {
                "subjects": ["indie vocalist", "hip-hop dancer", "synthwave duo", "string quartet"],
                "environments": ["LED tunnel", "abandoned theater", "warehouse stage", "desert salt flats"],
                "moods": ["stylish and expressive", "vibrant and rhythmic", "dreamy and ethereal"],
                "lightings": ["neon key/fill", "strobe accents", "colored haze"],
                "style_pairs": [["Cinematic", "Digital Art"], ["Abstract", "Minimalist"]]
            },
        }

    # Default cohesive style pairs
    style_pairs = [
        ["Fantasy", "Cinematic"], ["Sci-Fi", "Cinematic"], ["Realistic", "Photorealistic"],
        ["Cyberpunk", "Digital Art"], ["Anime", "Cartoon"], ["3D Render", "Photorealistic"],
        ["Art Nouveau", "Impressionist"], ["Steampunk", "Baroque"], ["Minimalist", "Abstract"]
    ]

    # If a theme is provided, override where applicable
    if theme in THEME_BANKS:
        bank = THEME_BANKS[theme]
        subjects = bank.get("subjects", subjects)
        environments = bank.get("environments", environments)
        moods = bank.get("moods", moods)
        lightings = bank.get("lightings", lightings)
        style_pairs = bank.get("style_pairs", style_pairs)
    # Prefer cohesive style pairs
    # Filter to available styles
    def pick_styles():
        pair = random.choice(style_pairs)
        return [s for s in pair if s in available_styles] or random.sample(available_styles, k=min(2, len(available_styles)))

    subject = random.choice(subjects)
    action = random.choice(actions)
    environment = random.choice(environments)
    mood = random.choice(moods)
    lighting = random.choice(lightings)
    styles = pick_styles()

    sentence = f"{subject} {action} {environment}"
    details = f"{mood}, {lighting}"
    subject_line = f"{sentence}, richly detailed textures, natural imperfections"

    # Tailor a bit by prompt type
    if prompt_type == "video":
        subject_line += ", cinematic motion cues, dynamic composition"
    else:
        subject_line += ", finely tuned composition, high fidelity"

    return {
        "subject": subject_line,
        "styles": styles,
        "lighting": lighting,
        "mood": mood.title(),
        "environment": environment
    }

def fill_random_inspiration(prompt_type: str = "image", theme: Optional[str] = None, available_styles: Optional[List[str]] = None):
    """Smartly fill form with diverse inspiration; avoids recent repeats."""
    if available_styles is None:
        available_styles = [
            "Fantasy", "Sci-Fi", "Realistic", "Photorealistic",
            "Anime", "Cartoon", "Cinematic", "Abstract", 
            "Impressionist", "Digital Art", "Oil Painting", 
            "Watercolor", "Sketch", "3D Render", "Cyberpunk",
            "Steampunk", "Art Nouveau", "Baroque", "Minimalist"
        ]

    history_key = "aispark_inspiration_history"
    history = st.session_state.get(history_key, [])

    # Try a few times to avoid immediate repeats
    candidate = None
    for _ in range(10):
        cand = _smart_inspiration(prompt_type, available_styles, theme)
        if cand not in history[-5:]:
            candidate = cand
            break
    if candidate is None:
        candidate = cand  # fallback

    st.session_state[history_key] = (history + [candidate])[-20:]
    st.session_state["aispark_inspiration"] = candidate
    st.success("🎲 Smart inspiration applied! You can tweak fields or generate again.")

def render_recent_generations():
    """Show recent generations in sidebar"""
    
    st.sidebar.markdown("### 🕒 Recent Generations")
    
    if st.session_state.get("aispark_generated_prompt"):
        with st.sidebar.expander("Last Generated", expanded=True):
            result = st.session_state["aispark_generated_prompt"]
            raw_response = result.get("raw_response", {})
            
            if "paragraphPrompt" in raw_response:
                prompt_preview = raw_response["paragraphPrompt"][:100]
                if len(raw_response["paragraphPrompt"]) > 100:
                    prompt_preview += "..."
                
                st.markdown(f"*{prompt_preview}*")
                
                if st.button("📋 Copy Last Prompt", use_container_width=True):
                    st.success("Copied!")
    else:
        st.sidebar.info("Your recent prompts will appear here")
