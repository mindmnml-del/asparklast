"""
History Component for AISpark Studio
Handles prompt history, favorites, and management
"""

import streamlit as st
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

def render_history_interface(token: str, user_data: Dict[str, Any]) -> None:
    """Main prompt history interface"""
    
    st.title("📚 My Prompt Library")
    st.markdown("Browse, manage, and organize your generated prompts")
    
    # Load user's prompts
    prompts = load_user_prompts(token)
    
    if prompts is None:
        st.error("❌ Failed to load your prompts. Please try again.")
        return
    
    if not prompts:
        render_empty_state()
        return
    
    # History controls and filters
    render_history_controls(prompts, token)
    
    # Display prompts
    render_prompt_list(prompts, token)

def load_user_prompts(token: str) -> Optional[List[Dict]]:
    """Load user's prompt history from API"""
    
    from .api_helper import api_client
    
    with st.spinner("📖 Loading your prompt library..."):
        result = api_client.get_prompts(token, 0, 50, False)
        # API may return a list (success) or dict (error)
        if isinstance(result, dict) and result.get("error"):
            return None
        if isinstance(result, list):
            return result
        return []

def render_empty_state():
    """Show empty state when user has no prompts"""
    
    st.markdown("""
    <div style='text-align: center; padding: 3rem; color: #666;'>
        <h2>📝 No prompts yet</h2>
        <p>Start creating amazing AI prompts to build your library!</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🚀 Create First Prompt", use_container_width=True, type="primary"):
            st.session_state["aispark_current_page"] = "generate"
            st.rerun()

def render_history_controls(prompts: List[Dict], token: str):
    """Render filtering and search controls"""
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search prompts",
            placeholder="Search by content, style, or description...",
            key="search_input"
        )
    
    with col2:
        filter_type = st.selectbox(
            "📋 Filter",
            ["All Prompts", "Favorites Only", "Recent"],
            key="filter_type"
        )
    
    with col3:
        sort_order = st.selectbox(
            "🔄 Sort by",
            ["Newest First", "Oldest First", "Favorites"],
            key="sort_order"
        )
    
    with col4:
        # Export controls
        render_export_controls(token)
    
    # Show statistics
    render_library_stats(prompts)

def render_library_stats(prompts: List[Dict]):
    """Show statistics about user's prompt library"""
    
    total_prompts = len(prompts)
    favorites_count = sum(1 for p in prompts if p.get("is_favorite"))
    
    # Display stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📝 Total Prompts", total_prompts)
    
    with col2:
        st.metric("⭐ Favorites", favorites_count)
    
    with col3:
        if total_prompts > 0:
            fav_percentage = (favorites_count / total_prompts) * 100
            st.metric("📊 Favorite Rate", f"{fav_percentage:.1f}%")

def render_prompt_list(prompts: List[Dict], token: str):
    """Render the list of prompts"""
    
    st.markdown("---")
    
    for prompt in prompts:
        render_prompt_card(prompt, token)
        st.markdown("---")

def render_prompt_card(prompt: Dict, token: str):
    """Render individual prompt card"""
    
    prompt_id = prompt.get("id")
    title = prompt.get("title", "Untitled Prompt")
    created_at = prompt.get("created_at", "")
    is_favorite = prompt.get("is_favorite", False)
    
    # Format creation date
    time_str = "Unknown"
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = created_at
    
    # Card layout
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        st.markdown(f"### {title}")
        st.caption(f"📅 Created: {time_str}")
        
        # Show preview of prompt content
        raw_response = prompt.get("raw_response", {})
        if "paragraphPrompt" in raw_response:
            preview = raw_response["paragraphPrompt"][:150]
            if len(raw_response["paragraphPrompt"]) > 150:
                preview += "..."
            st.markdown(f"*{preview}*")
    
    with col2:
        # Favorite toggle
        favorite_emoji = "⭐" if is_favorite else "☆"
        if st.button(favorite_emoji, key=f"fav_{prompt_id}", help="Toggle favorite"):
            toggle_favorite(prompt_id, not is_favorite, token)
            st.rerun()
    
    with col3:
        # View button
        if st.button("👁️ View", key=f"view_{prompt_id}", use_container_width=True):
            show_prompt_details(prompt, token)
    
    with col4:
        # Copy button
        if st.button("📋 Copy", key=f"copy_{prompt_id}", use_container_width=True):
            copy_prompt_to_clipboard(prompt)

def show_prompt_details(prompt: Dict, token: str):
    """Show detailed view of a prompt"""
    
    title = prompt.get("title", "Untitled Prompt")
    raw_response = prompt.get("raw_response", {})
    
    with st.expander(f"📖 {title} - Details", expanded=True):
        
        if "paragraphPrompt" in raw_response:
            st.markdown("#### 📝 Complete Prompt")
            st.code(raw_response["paragraphPrompt"], language="text")
        
        if raw_response.get("negativePrompt"):
            st.markdown("#### 🚫 Negative Prompt")
            st.code(raw_response["negativePrompt"], language="text")
        
        # Structured breakdown
        if "structuredPrompt" in raw_response:
            st.markdown("#### 📋 Breakdown")
            structured = raw_response["structuredPrompt"]
            
            for key, value in structured.items():
                if value:
                    clean_key = key.replace("_", " ").title()
                    st.markdown(f"**{clean_key}:** {value}")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Copy Prompt", key=f"detail_copy_{prompt['id']}", use_container_width=True):
                copy_prompt_to_clipboard(prompt)
        
        with col2:
            if st.button("🔄 Use as Template", key=f"detail_template_{prompt['id']}", use_container_width=True):
                use_as_template(prompt)

def toggle_favorite(prompt_id: int, is_favorite: bool, token: str):
    """Toggle favorite status of a prompt"""
    
    from .api_helper import api_client
    
    result = api_client.toggle_favorite(prompt_id, is_favorite, token)
    
    if result.get("error"):
        st.error(f"Failed to update favorite: {result.get('message')}")
    else:
        status = "added to" if is_favorite else "removed from"
        st.success(f"✅ Prompt {status} favorites!")

def copy_prompt_to_clipboard(prompt: Dict):
    """Copy prompt to clipboard"""
    
    raw_response = prompt.get("raw_response", {})
    prompt_text = raw_response.get("paragraphPrompt", "No prompt text available")
    
    st.success("✅ Prompt copied to clipboard!")
    st.code(prompt_text, language="text")

def use_as_template(prompt: Dict):
    """Use this prompt as a template for new generation"""
    
    raw_response = prompt.get("raw_response", {})
    structured = raw_response.get("structuredPrompt", {})
    
    if not structured:
        st.warning("Cannot use as template - no structured data available")
        return
    
    # Store template data in session state
    st.session_state["template_data"] = {
        "subject_action": structured.get("subject", ""),
        "lighting": structured.get("lighting", ""),
        "mood": structured.get("mood", ""),
        "environment_setting": structured.get("setting", "")
    }
    
    # Switch to generation page
    st.session_state["aispark_current_page"] = "generate"
    st.success("🔄 Template loaded! Switched to generator.")
    time.sleep(1)
    st.rerun()

def render_export_controls(token: str):
    """Render export functionality controls"""
    
    export_format = st.selectbox(
        "💾 Export",
        ["Choose format...", "JSON", "CSV", "TXT"],
        key="export_format",
        help="Export your prompts to file"
    )
    
    if export_format != "Choose format...":
        favorites_only = st.checkbox(
            "⭐ Favorites only",
            key="export_favorites_only",
            help="Export only favorite prompts"
        )
        
        if st.button("📥 Download", key="export_download", use_container_width=True):
            perform_export(token, export_format.lower(), favorites_only)

def perform_export(token: str, format: str, favorites_only: bool = False):
    """Perform the export operation"""
    
    from .api_helper import api_client
    
    with st.spinner(f"📦 Preparing {format.upper()} export..."):
        try:
            content = api_client.export_prompts(format, token, 0, 1000, favorites_only)
            
            if content.startswith("Authentication failed"):
                st.error("❌ Authentication failed. Please login again.")
                return
            
            if content.startswith("No prompts found"):
                st.warning("⚠️ No prompts found to export.")
                return
            
            if content.startswith("Export failed") or content.startswith("Export error"):
                st.error(f"❌ {content}")
                return
            
            # Determine file extension and MIME type
            if format == "json":
                mime_type = "application/json"
                file_ext = "json"
            elif format == "csv":
                mime_type = "text/csv"
                file_ext = "csv"
            else:  # txt
                mime_type = "text/plain"
                file_ext = "txt"
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_favorites" if favorites_only else ""
            filename = f"aispark_prompts{suffix}_{timestamp}.{file_ext}"
            
            # Create download button
            st.download_button(
                label=f"📄 Download {filename}",
                data=content,
                file_name=filename,
                mime=mime_type,
                help=f"Download your prompts as {format.upper()} file"
            )
            
            st.success(f"✅ Export ready! Click the download button above to save your {format.upper()} file.")
            
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
