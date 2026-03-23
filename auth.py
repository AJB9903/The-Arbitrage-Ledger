import streamlit as st
from passlib.context import CryptContext
from db import get_session, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain):
    return pwd_context.hash(plain)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def register_user(username, email, password):
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

def login_user(username, password):
    db = get_session()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            return False, "Invalid username or password."
        st.session_state["user_id"] = user.id
        st.session_state["username"] = user.username
        st.session_state["logged_in"] = True
        return True, "Welcome back!"
    finally:
        db.close()

def logout():
    for key in ["user_id", "username", "logged_in"]:
        st.session_state.pop(key, None)

def current_user_id():
    return st.session_state.get("user_id")

def require_login():
    if st.session_state.get("logged_in"):
        return

    st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("""
        <div style='text-align:center;padding:2rem 0 1.5rem;'>
            <div style='font-family:monospace;font-size:2rem;font-weight:700;color:#c8f04d;'>
                🏷️ ARBITRAGE LEDGER
            </div>
            <div style='color:#888;margin-top:0.5rem;'>Track every flip. Know every dollar.</div>
        </div>""", unsafe_allow_html=True)

        tab_in, tab_up = st.tabs(["Sign In", "Create Account"])

        with tab_in:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_gate"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In →", use_container_width=True):
                    if username and password:
                        ok, msg = login_user(username, password)
                        if ok:
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Fill in both fields.")

        with tab_up:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("register_gate"):
                u = st.text_input("Username")
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                c = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account →", use_container_width=True):
                    if not all([u, e, p, c]):
                        st.error("All fields required.")
                    elif p != c:
                        st.error("Passwords don't match.")
                    elif len(p) < 6:
                        st.error("Password must be 6+ characters.")
                    else:
                        ok, msg = register_user(u, e, p)
                        st.success(msg) if ok else st.error(msg)
    st.stop()
