"""
Admin Authentication Module

Simple authentication for protecting Settings pages.
Admin credentials are stored in .streamlit/secrets.toml

Author: Wong Xin Ping
Date: 26 January 2026
"""

import streamlit as st
import hashlib
import os


def get_admin_credentials():
    """Get admin credentials from secrets.toml or environment variables"""
    # Default credentials (should be changed in production)
    default_username = "admin"
    default_password = "Tertiary@888"

    # Try to get from secrets.toml or environment
    try:
        username = st.secrets.get("ADMIN_USERNAME", os.environ.get("ADMIN_USERNAME", default_username))
        password = st.secrets.get("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD", default_password))
    except Exception:
        username = os.environ.get("ADMIN_USERNAME", default_username)
        password = os.environ.get("ADMIN_PASSWORD", default_password)

    return username, password


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('admin_authenticated', False)


def logout():
    """Log out the admin user"""
    st.session_state['admin_authenticated'] = False
    st.session_state['admin_username'] = None


def login_page():
    """Display login page and handle authentication"""
    st.markdown("### Admin Login")
    st.caption("Enter admin credentials to access settings")

    with st.form("admin_login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            admin_username, admin_password = get_admin_credentials()

            if username == admin_username and password == admin_password:
                st.session_state['admin_authenticated'] = True
                st.session_state['admin_username'] = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    st.markdown("---")
    st.caption("Default credentials: admin / Tertiary@888")
    st.caption("To change credentials, add ADMIN_USERNAME and ADMIN_PASSWORD to .streamlit/secrets.toml")


def require_auth(page_function):
    """Decorator/wrapper to require authentication for a page"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_page()
            return None
        return page_function(*args, **kwargs)
    return wrapper


def show_logout_button():
    """Show logout button in sidebar or page"""
    if is_authenticated():
        username = st.session_state.get('admin_username', 'Admin')
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"Logged in as: **{username}**")
        with col2:
            if st.button("Logout", key="logout_btn", use_container_width=True):
                logout()
                st.rerun()
