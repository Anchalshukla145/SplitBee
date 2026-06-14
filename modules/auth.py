"""
Authentication module for SplitBee.
Handles login, registration, password hashing, and session management.
"""
import hashlib
from database.db import fetch_one, execute


def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(username, password):
    """
    Register a new user.
    Returns (True, user_id) on success, (False, error_message) on failure.
    """
    username = username.strip()
    if not username:
        return False, "Username cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."

    existing = fetch_one("SELECT id FROM users WHERE username = ?", (username,))
    if existing:
        return False, f"Username '{username}' is already taken."

    pw_hash = hash_password(password)
    user_id = execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, pw_hash)
    )
    return True, user_id


def login_user(username, password):
    """
    Authenticate a user. Returns user dict on success, None on failure.
    """
    user = fetch_one("SELECT * FROM users WHERE username = ?", (username.strip(),))
    if user is None:
        return None
    if user["password_hash"] != hash_password(password):
        return None
    return user


def verify_user(user_id):
    """Check if a user_id exists. Returns user dict or None."""
    return fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))


def get_current_user(st):
    """Get the current logged-in user from session state."""
    if not st.session_state.get("logged_in"):
        return None
    return {
        "id": st.session_state.get("user_id"),
        "username": st.session_state.get("username"),
    }


def get_all_users():
    """Return list of all users."""
    from database.db import fetch_all
    return fetch_all("SELECT id, username, created_at FROM users ORDER BY username")


def logout_user(st):
    """Clear session state."""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None


def seed_demo_user():
    """Create demo user admin/admin123 if it doesn't exist."""
    existing = fetch_one("SELECT id FROM users WHERE username = ?", ("admin",))
    if not existing:
        execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", hash_password("admin123"))
        )
