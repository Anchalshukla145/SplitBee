import streamlit as st
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db
from modules.auth import login_user, create_user, seed_demo_user, logout_user

# ---------------------------------------------------------------------------
# Initialize database and seed demo user
# ---------------------------------------------------------------------------
init_db()
seed_demo_user()

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SplitBee — Shared Expenses",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# Load custom CSS
# ---------------------------------------------------------------------------
css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State defaults
# ---------------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None

# ---------------------------------------------------------------------------
# Login / Register Page
# ---------------------------------------------------------------------------
if not st.session_state.logged_in:

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0 1rem 0;">
            <span style="font-size: 4rem;">🐝</span>
            <h1 style="margin: 0; font-size: 2.5rem;
                background: linear-gradient(135deg, #F59E0B, #D97706);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                SplitBee
            </h1>
            <p style="color: #9CA3AF; font-size: 1.1rem; margin-top: 0.5rem;">
                Smart Shared Expense Management
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        tab_login, tab_register = st.tabs(["Login", "Register"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.form_submit_button("Login", use_container_width=True):
                    if not username or not password:
                        st.error("Enter both username and password.")
                    else:
                        user = login_user(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user["id"]
                            st.session_state.username = user["username"]
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

        with tab_register:
            with st.form("register_form"):
                new_user = st.text_input("Username", key="reg_user")
                new_pass = st.text_input("Password", type="password", key="reg_pass")
                confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if new_pass != confirm:
                        st.error("Passwords do not match.")
                    else:
                        ok, result = create_user(new_user, new_pass)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.user_id = result
                            st.session_state.username = new_user.strip()
                            st.rerun()
                        else:
                            st.error(result)

# ---------------------------------------------------------------------------
# Main Application (Logged In)
# ---------------------------------------------------------------------------
else:
    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <span style="font-size: 2.5rem;">🐝</span>
        <h2 style="margin: 0.3rem 0 0; font-size: 1.4rem;
            background: linear-gradient(135deg, #F59E0B, #D97706);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            SplitBee
        </h2>
        <p style="color: #9CA3AF; font-size: 0.85rem; margin: 0.2rem 0;">
            👤 <strong>{st.session_state.username}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    pages_list = [
        "Dashboard",
        "Groups",
        "Expenses",
        "Import CSV",
        "Balances",
        "Settlements",
        "Approvals",
        "Reports",
    ]
    default_idx = pages_list.index(st.session_state.current_page) if st.session_state.current_page in pages_list else 0

    page = st.sidebar.radio(
        "Navigation",
        pages_list,
        index=default_idx,
        label_visibility="collapsed"
    )

    if page != st.session_state.current_page:
        st.session_state.current_page = page
        st.rerun()

    st.sidebar.markdown("---")

    if st.sidebar.button("Logout", use_container_width=True):
        logout_user(st)
        st.rerun()

    # Route to views
    if st.session_state.current_page == "Dashboard":
        from views.dashboard_view import render
        render()
    elif st.session_state.current_page == "Groups":
        from views.groups_view import render
        render()
    elif st.session_state.current_page == "Expenses":
        from views.expenses_view import render
        render()
    elif st.session_state.current_page == "Import CSV":
        from views.import_view import render
        render()
    elif st.session_state.current_page == "Balances":
        from views.balances_view import render
        render()
    elif st.session_state.current_page == "Settlements":
        from views.settlements_view import render
        render()
    elif st.session_state.current_page == "Approvals":
        from views.approval_view import render
        render()
    elif st.session_state.current_page == "Reports":
        from views.reports_view import render
        render()