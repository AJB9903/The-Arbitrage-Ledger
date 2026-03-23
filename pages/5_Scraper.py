import streamlit as st
st.set_page_config(page_title="Import · Ledger", page_icon="🔍", layout="wide")

import pandas as pd
import io
import ui, logic
from auth import require_login, current_user_id
from db import get_session, Product

ui.inject_css()
require_login()
ui.page_header("🔍", "IMPORT LISTINGS", "bulk add from CSV or Depop")

tab1, tab2 = st.tabs(["📄 CSV Import", "🌐 Depop Scraper"])

# ── CSV IMPORT ────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div style='background:#1a1a1a;border:1px solid #2e2e2e;border-radius:8px;padding:1.2rem;margin-bottom:1rem;'>
        <div style='color:#c8f04d;font-family:Space Mono,monospace;font-size:0.85rem;font-weight:700;margin-bottom:0.5rem;'>
            How to use CSV import
        </div>
        <div style='color:#888;font-size:0.85rem;line-height:1.6;'>
            1. Download the template below<br>
            2. Fill it in (Excel, Google Sheets, anything)<br>
            3. Upload it here — all items import at once
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Download template
    template = pd.DataFrame([{
        "title": "Vintage Levis 501 Jeans",
        "brand": "Levis",
        "category": "Pants",
        "source_location": "Goodwill",
        "purchase_price": 8.00,
        "listing_price": 65.00,
        "sold_price": "",
        "shipping_cost_paid": 5.50,
        "shipping_charged_to_customer": 7.99,
        "platform_fees": 6.50,
        "tax_collected": 0,
        "status": "Listed",
        "date_purchased": "2025-01-15",
        "date_listed": "2025-01-20",
        "date_sold": "",
        "description": "Great condition",
    }])

    csv_bytes = template.to_csv(index=False).encode()
    st.download_button(
        "⬇️ Download CSV Template",
        data=csv_bytes,
        file_name="arbitrage_ledger_template.csv",
        mime="text/csv",
        use_container_width=False,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload your filled CSV", type=["
