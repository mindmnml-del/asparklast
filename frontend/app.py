"""
AISpark Studio - Complete Optimized Frontend
Main application with all components integrated
Compatible with Gemini 2.5 Flash API
"""

import streamlit as st
import time
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging for AISpark namespace
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AISpark - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aispark.frontend")

# Import components with error handling
try:
    from api_client import api_client, quick_health_check
    from components.auth_component import render_authentication_page, check_authentication, render_logout_button, render_user_profile
    from components.generation_component import render_generation_interface, render_recent_generations
    from components.history_component import render_history_interface
except ImportError as e:
    st.error(f"⚠️ Component import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="AISpark Studio v2.5 - Gemini Flash",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://aispark.studio/help',
        'Report a bug': 'https://aispark.studio/issues',
        'About': "AISpark Studio v2.5 - Powered by Gemini 2.5 Flash"
    }
)

# Custom CSS with Gemini 2.5 Flash branding
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .stButton > button {
        border-radius: 8px;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .status-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
    }
    
    .gemini-flash-badge {
        position: fixed;
        top: 50px;
        right: 10px;
        z-index: 999;
        background: linear-gradient(45deg, #4285f4, #34a853);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables with AISpark namespace"""
    defaults = {
        "aispark_token": None,
        "aispark_user": None,
        "aispark_current_page": "login",
        "aispark_error_message": None,
        "aispark_success_message": None,
        "aispark_generated_prompt": None,
        "aispark_backend_status": "unknown"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_notifications():
    """Display notifications"""
    if st.session_state.get("aispark_error_message"):
        st.error(st.session_state.aispark_error_message)
        st.session_state.aispark_error_message = None
    
    if st.session_state.get("aispark_success_message"):
        st.success(st.session_state.aispark_success_message)
        st.session_state.aispark_success_message = None

def check_backend_status():
    """Check backend status"""
    try:
        is_healthy = quick_health_check()
        st.session_state.aispark_backend_status = "healthy" if is_healthy else "unhealthy"
        return is_healthy
    except:
        st.session_state.aispark_backend_status = "disconnected"
        return False

def render_status_indicator():
    """Render status indicator"""
    status = st.session_state.get("aispark_backend_status", "unknown")
    
    if status == "healthy":
        indicator = "🟢 Backend Online"
        color = "#00cc44"
    elif status == "unhealthy":
        indicator = "🟡 Backend Issues"
        color = "#ffbb00"
    else:
        indicator = "🔴 Backend Offline"
        color = "#ff4444"
    
    st.markdown(f"""
    <div class="status-indicator" style="background-color: {color};">
        {indicator}
    </div>
    <div class="gemini-flash-badge">
        Gemini 2.5 Flash
    </div>
    """, unsafe_allow_html=True)

def render_sidebar_navigation(auth_data: Optional[Dict[str, Any]]):
    """Render sidebar navigation"""
    
    if not auth_data:
        return
    
    st.sidebar.markdown("### 🎨 AISpark Studio")
    st.sidebar.markdown("---")
    
    # User profile
    render_user_profile(auth_data["user"])
    
    # Navigation
    st.sidebar.markdown("### 🧭 Navigation")
    
    if st.sidebar.button("🚀 Prompt Generator", use_container_width=True, 
                        type="primary" if st.session_state.get("aispark_current_page") == "generate" else "secondary"):
        st.session_state.aispark_current_page = "generate"
        st.rerun()
    
    if st.sidebar.button("📚 My Prompts", use_container_width=True,
                        type="primary" if st.session_state.get("aispark_current_page") == "history" else "secondary"):
        st.session_state.aispark_current_page = "history"
        st.rerun()
    
    # Recent generations
    render_recent_generations()
    
    # Logout
    if render_logout_button():
        st.rerun()

def render_main_content(auth_data: Optional[Dict[str, Any]]):
    """Render main content"""
    
    if not auth_data:
        # Show authentication page
        result = render_authentication_page()
        if result:
            st.session_state.aispark_token = result["token"]
            st.session_state.aispark_user = result["user"]
            st.session_state.aispark_current_page = "generate"
            st.session_state.aispark_success_message = f"Welcome, {result['user'].get('email', 'User')}!"
            st.rerun()
        return
    
    # Show appropriate page
    current_page = st.session_state.get("aispark_current_page", "generate")
    
    if current_page == "generate":
        result = render_generation_interface(auth_data["token"], auth_data["user"])
        if result:
            st.session_state.aispark_success_message = "Prompt generated successfully!"
    
    elif current_page == "history":
        render_history_interface(auth_data["token"], auth_data["user"])
    
    else:
        st.session_state.aispark_current_page = "generate"
        st.rerun()

def main():
    """Main application function"""
    
    # Initialize
    init_session_state()
    
    # Check backend
    check_backend_status()
    
    # Render status
    render_status_indicator()
    
    # Show notifications
    show_notifications()
    
    # Check auth
    auth_data = check_authentication()
    
    # Render UI
    render_sidebar_navigation(auth_data)
    render_main_content(auth_data)
    
    # Footer
    st.markdown("---")
    st.markdown("**🎨 AISpark Studio v2.0** - Professional AI Prompt Generation Platform")

if __name__ == "__main__":
    main()
