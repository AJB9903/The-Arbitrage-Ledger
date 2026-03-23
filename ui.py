"""
ui.py — Shared styles, layout helpers, and reusable components.
Import this at the top of every page.
"""
import streamlit as st

ACCENT   = "#c8f04d"
ACCENT2  = "#f04d6b"
PROFIT   = "#4df0a0"
MUTED    = "#888888"
SURFACE  = "#1a1a1a"
BORDER   = "#2e2e2e"
BG       = "#0f0f0f"

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#f0f0f0", size=12),
    xaxis=dict(gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    yaxis=dict(gridcolor=BORDER, linecolor=BORDER, zeroline=False),
    margin=dict(l=20, r=20, t=40, b=20),
)

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --accent:  #c8f04d;
    --accent2: #f04d6b;
    --profit:  #4df0a0;
    --surface: #1a1a1a;
    --surface2:#242424;
    --border:  #2e2e2e;
    --muted:   #888;
    --text:    #f0f0f0;
    --bg:      #0f0f0f;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.stApp                  { background: var(--bg) !important; }
h1, h2, h3              { font-family: 'Space Mono', monospace !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarNav"] a {
    color: var(--muted) !important;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] [aria-selected="true"] {
    color: var(--accent) !important;
}

/* Buttons */
.stButton > button {
    background: var(--accent) !important;
    color: #0f0f0f !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 4px !important;
    letter-spacing: 0.05em;
}
.stButton > button:hover { filter: brightness(1.1); }

/* Danger button */
.btn-danger button {
    background: var(--accent2) !important;
    color: #fff !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 4px !important;
}
.stSelectbox > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}
label, .stTextInput label, .stSelectbox label,
.stNumberInput label, .stDateInput label, .stTextArea label,
.stFileUploader label {
    color: var(--muted) !important;
    font-size: 0.72rem !important;
    font-family: 'Space Mono', monospace !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
}
.stTabs [aria-selected="true"] { color: var(--accent) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--accent) !important; }
.stTabs [data-baseweb="tab-border"]    { background: var(--border) !important; }

/* Dataframe / Tables */
.stDataFrame { background: var(--surface) !important; }
[data-testid="stDataFrameResizable"] { border: 1px solid var(--border) !important; }

/* Divider */
hr { border-color: var(--border) !important; }

/* Expander */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    color: var(--muted) !important;
}

/* Alerts */
.al-yellow {
    background: rgba(200,240,77,0.08);
    border: 1px solid #c8f04d55;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin: 0.3rem 0;
}
.al-red {
    background: rgba(240,77,107,0.1);
    border: 1px solid #f04d6b55;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin: 0.3rem 0;
}
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style='margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid {BORDER};'>
        <span style='font-family:Space Mono,monospace;font-size:1.5rem;
                     font-weight:700;color:{ACCENT};'>{icon} {title}</span>
        {'<span style="color:' + MUTED + ';font-size:0.85rem;margin-left:1rem;">' + subtitle + '</span>' if subtitle else ''}
    </div>""", unsafe_allow_html=True)


def kpi_card(col, label: str, value: str, color: str = ACCENT):
    col.markdown(f"""
    <div style='background:{SURFACE};border:1px solid {BORDER};border-radius:8px;
                padding:1.1rem 1.4rem;text-align:center;'>
        <div style='font-family:Space Mono,monospace;font-size:0.65rem;
                    text-transform:uppercase;letter-spacing:0.1em;color:{MUTED};'>{label}</div>
        <div style='font-family:Space Mono,monospace;font-size:1.7rem;
                    font-weight:700;color:{color};margin-top:0.3rem;'>{value}</div>
    </div>""", unsafe_allow_html=True)


STATUS_COLORS = {
    "Listed":  ("#c8f04d", "#c8f04d22", "🟢"),
    "Sold":    ("#4df0a0", "#4df0a022", "✅"),
    "Draft":   ("#888888", "#88888822", "⬜"),
    "Stale":   ("#f04d6b", "#f04d6b22", "🔴"),
    "Donated": ("#f04d6b", "#f04d6b22", "🤲"),
}

CATEGORIES = ["Shirt", "Pants", "Shoes", "Accessories", "Jacket", "Dress", "Other"]
STATUSES   = ["Draft", "Listed", "Sold", "Stale", "Donated"]
