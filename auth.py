"""
auth.py — Password hashing and session-based auth for Streamlit.
No JWT needed — we use st.session_state to hold the logged-in user id.
"""
import streamlit as st
from passlib.context import CryptContext
from db import get_session, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    db = get_session()
    try:
        if db.query(User).filter(User.username == username).first():
            return False, "Username already taken."
        if db.query(User).filter(User.email == email).first():
            return False, "Email already registered."
        user = User(username=username, email=email, hashed_password=hash_password(password))
        db.add(user)
        db.commit()
        return True, "Account created! Please sign in."
    except Exception as e:
        db.rollback()
        return False, f"Error: {e}"
    finally:
        db.close()


def login_user(username: str, password: str) -> tuple[bool, str]:
    db = get_session()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            return False, "Invalid username or password."
        # Store in session
        st.session_state["user_id"]   = user.id
        st.session_state["username"]  = user.username
        st.session_state["logged_in"] = True
        return True, "Welcome back!"
    finally:
        db.close()


def logout():
    for key in ["user_id", "username", "logged_in"]:
        st.session_state.pop(key, None)


def require_login():
    """Call at top of every page. Stops page if not logged in."""
    if not st.session_state.get("logged_in"):
        st.warning("Please sign in to access this page.")
        st.stop()


def current_user_id() -> int:
    return st.session_state.get("user_id")
