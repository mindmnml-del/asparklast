"""
Authentication Component for AISpark Studio
Handles login, registration, and user session management
"""

import streamlit as st
import time
from typing import Optional, Dict, Any
from .api_helper import api_client

# Prefix used in app.py for session variables
PREFIX = "aispark_"

def _get(key: str, default=None):
    return st.session_state.get(PREFIX + key, default)

def _set(key: str, value):
    st.session_state[PREFIX + key] = value

def render_login_form() -> Optional[Dict[str, Any]]:
    """Render login form and handle authentication"""
    st.markdown("#### 🔐 Sign In")
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email Address", placeholder="you@email.com", help="Enter your registered email address")
        password = st.text_input("Password", type="password", help="Enter your password")
        col1, col2 = st.columns([2, 1])
        with col1:
            login_button = st.form_submit_button("🚀 Sign In", use_container_width=True, type="primary")
        with col2:
            forgot_password = st.form_submit_button("🔑 Forgot?", use_container_width=True)
        if login_button:
            if not email or not password:
                st.error("Please enter both email and password")
                return None
            with st.spinner("🔍 Authenticating..."):
                result = api_client.login(email.strip().lower(), password)
                if result.get("error"):
                    if result.get("auth_error"):
                        st.error("❌ Invalid email or password")
                    elif result.get("connection_error"):
                        st.error("❌ Cannot connect to server. Please check if the backend is running.")
                    else:
                        st.error(f"❌ Login failed: {result.get('message', 'Unknown error')}")
                    return None
                token = result.get("access_token")
                if token:
                    user_info = api_client.get_current_user(token)
                    if not user_info.get("error"):
                        st.success("✅ Login successful!")
                        time.sleep(0.5)
                        return {"token": token, "user": user_info}
                st.error("❌ Failed to retrieve user information")
                return None
        if forgot_password:
            st.info("🔧 Password reset feature coming soon! Please contact support if you need help.")
    return None

def render_registration_form() -> Optional[str]:
    """Render registration form and handle user creation"""
    
    st.markdown("#### 📝 Create Account")
    
    with st.form("registration_form", clear_on_submit=True):
        email = st.text_input(
            "Email Address",
            placeholder="your@email.com",
            help="We'll never share your email with anyone else"
        )
        
        full_name = st.text_input(
            "Full Name (Optional)",
            placeholder="Your Name",
            help="This will be displayed in your profile"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            help="At least 8 characters with uppercase, lowercase, number, and special character"
        )
        
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            help="Re-enter your password"
        )
        
        # Password strength indicator
        if password:
            strength_score = calculate_password_strength(password)
            strength_color, strength_text = get_strength_display(strength_score)
            st.markdown(f"Password Strength: <span style='color: {strength_color}'>{strength_text}</span>", 
                       unsafe_allow_html=True)
        
        # Terms and conditions
        terms_accepted = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            help="You must accept the terms to create an account"
        )
        
        register_button = st.form_submit_button(
            "🎉 Create Account",
            use_container_width=True,
            type="primary"
        )
        
        if register_button:
            # Validation
            validation_errors = validate_registration_data(
                email, password, confirm_password, terms_accepted
            )
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"❌ {error}")
                return None
            
            with st.spinner("🛠️ Creating your account..."):
                result = api_client.register(
                    email.strip().lower(), 
                    password, 
                    full_name.strip() if full_name else ""
                )
                
                if result.get("error"):
                    if "already registered" in result.get("message", "").lower():
                        st.error("❌ An account with this email already exists. Please sign in instead.")
                    elif result.get("connection_error"):
                        st.error("❌ Cannot connect to server. Please check if the backend is running.")
                    else:
                        st.error(f"❌ Registration failed: {result.get('message', 'Unknown error')}")
                    return None
                else:
                    st.success("🎉 Account created successfully! Please sign in with your new credentials.")
                    time.sleep(2)
                    return "registration_success"
    
    return None

def validate_registration_data(
    email: str, 
    password: str, 
    confirm_password: str, 
    terms_accepted: bool
) -> list:
    """Validate registration form data"""
    errors = []
    
    # Email validation
    if not email:
        errors.append("Email is required")
    elif "@" not in email or "." not in email:
        errors.append("Please enter a valid email address")
    
    # Password validation
    if not password:
        errors.append("Password is required")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    elif password != confirm_password:
        errors.append("Passwords do not match")
    
    # Password strength validation
    strength_score = calculate_password_strength(password)
    if strength_score < 3:
        errors.append("Password is too weak. Please include uppercase, lowercase, numbers, and special characters")
    
    # Terms acceptance
    if not terms_accepted:
        errors.append("You must accept the Terms of Service to create an account")
    
    return errors

def calculate_password_strength(password: str) -> int:
    """Calculate password strength score (0-5)"""
    if not password:
        return 0
    
    score = 0
    
    # Length check
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    
    # Character variety checks
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
        score += 1
    
    return min(score, 5)

def get_strength_display(score: int) -> tuple:
    """Get color and text for password strength display"""
    if score <= 1:
        return "#ff4444", "Very Weak 🔴"
    elif score == 2:
        return "#ff8800", "Weak 🟠"
    elif score == 3:
        return "#ffbb00", "Fair 🟡"
    elif score == 4:
        return "#88dd00", "Good 🟢"
    else:
        return "#00cc44", "Strong 💚"

def render_user_profile(user_data: Dict[str, Any]) -> None:
    """Render user profile information"""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 Profile")
    
    # User basic info
    email = user_data.get("email", "Unknown")
    full_name = user_data.get("full_name", "")
    created_at = user_data.get("created_at", "")
    
    st.sidebar.markdown(f"**Email:** {email}")
    
    if full_name:
        st.sidebar.markdown(f"**Name:** {full_name}")
    
    if created_at:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%B %Y")
            st.sidebar.markdown(f"**Member since:** {date_str}")
        except:
            pass
    
    # Account status
    is_active = user_data.get("is_active", False)
    status_emoji = "✅" if is_active else "❌"
    status_text = "Active" if is_active else "Inactive"
    st.sidebar.markdown(f"**Status:** {status_emoji} {status_text}")

def render_logout_button() -> bool:
    """Render logout button and handle logout"""
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sign Out", use_container_width=True, type="secondary"):
        # Clear namespaced session state keys
        for key in list(st.session_state.keys()):
            if key.startswith(PREFIX):
                del st.session_state[key]
        st.sidebar.success("👋 Signed out successfully!")
        time.sleep(0.5)
        return True
    return False

def check_authentication() -> Optional[Dict[str, Any]]:
    """Check if user is authenticated and return user data (namespaced)"""
    token = _get("token")
    if not token:
        return None
    user_data = _get("user")
    if not user_data:
        user_result = api_client.get_current_user(token)
        if user_result.get("error"):
            # Invalidate token
            if PREFIX + "token" in st.session_state:
                del st.session_state[PREFIX + "token"]
            if PREFIX + "user" in st.session_state:
                del st.session_state[PREFIX + "user"]
            return None
        _set("user", user_result)
        user_data = user_result
    return {"token": token, "user": user_data}

def render_authentication_page() -> Optional[Dict[str, Any]]:
    """Main authentication page with tabs for login and registration (namespaced)"""
    st.markdown("""<div style='text-align: center; padding: 2rem 0;'>
        <h1>🎨 AISpark Studio</h1>
        <h3>Professional AI Prompt Generation Platform</h3>
        <p style='color: #666; font-size: 1.1rem;'>Create stunning prompts for AI image and video generation</p>
    </div>""", unsafe_allow_html=True)
    if not api_client.test_connection():
        st.error("""❌ Cannot connect to backend server.
Ensure the backend is running on http://127.0.0.1:8000.

Run (PowerShell):
```powershell
Set-Location 'd:\aispark 3\backend'
uvicorn main:app --host 127.0.0.1 --port 8000
```
""")
        return None
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
    with tab1:
        result = render_login_form()
        if result:
            _set("token", result["token"])
            _set("user", result["user"])
            _set("current_page", "generate")
            return result
    with tab2:
        registration_result = render_registration_form()
        if registration_result == "registration_success":
            st.balloons()
            st.rerun()  # Refresh to show login tab
    return None
