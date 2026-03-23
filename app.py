import streamlit as st
st.set_page_config(page_title="Add Item · Ledger", page_icon="➕", layout="wide")

import base64
from datetime import date
import ui, logic
from auth import require_login, current_user_id
from db import get_session, Product

ui.inject_css()
require_login()
ui.page_header("➕", "ADD NEW FIND", "log a thrift haul")

form_col, preview_col = st.columns([2.2, 1])

with form_col:
    with st.form("add_item", clear_on_submit=True):
        # ── Core Info ─────────────────────────────────────────────────────────
        st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.12em;color:#888;border-bottom:1px solid #2e2e2e;padding-bottom:0.4rem;margin-bottom:0.8rem;'>Core Information</div>", unsafe_allow_html=True)
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            title    = st.text_input("Title *", placeholder="Vintage Levi's 501 Jeans")
            brand    = st.text_input("Brand",   placeholder="Levi's")
        with r1c2:
            category = st.selectbox("Category", ui.CATEGORIES)
            status   = st.selectbox("Status",   ui.STATUSES)

        source = st.text_input("Source Location", placeholder="Goodwill — 5th Ave")
        desc   = st.text_area("Description", height=70, placeholder="Notes for your records...")

        # ── Image ─────────────────────────────────────────────────────────────
        st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.12em;color:#888;border-bottom:1px solid #2e2e2e;padding-bottom:0.4rem;margin:1rem 0 0.8rem;'>Image (optional)</div>", unsafe_allow_html=True)
        ic1, ic2 = st.columns(2)
        with ic1:
            uploaded = st.file_uploader("Upload photo", type=["jpg","jpeg","png","webp"])
        with ic2:
            img_url = st.text_input("Or paste image URL", placeholder="https://...")

        # ── Financials ────────────────────────────────────────────────────────
        st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.12em;color:#888;border-bottom:1px solid #2e2e2e;padding-bottom:0.4rem;margin:1rem 0 0.8rem;'>Pricing & Financials</div>", unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            purchase_price = st.number_input("Purchase Price ($) *", min_value=0.0, step=0.25, format="%.2f")
            listing_price  = st.number_input("Listing Price ($)",     min_value=0.0, step=0.25, format="%.2f")
        with fc2:
            ship_paid      = st.number_input("Shipping Cost Paid ($)",     min_value=0.0, step=0.25, format="%.2f")
            ship_charged   = st.number_input("Shipping Charged to Buyer ($)", min_value=0.0, step=0.25, format="%.2f")
        with fc3:
            platform_fees  = st.number_input("Platform Fees ($)", min_value=0.0, step=0.25, format="%.2f",
                                              help="Depop ~10% of listing price")
            tax_collected  = st.number_input("Tax Collected ($)", min_value=0.0, step=0.01, format="%.2f")

        sold_price = None
        if status == "Sold":
            sold_price = st.number_input("Sold Price ($) *", min_value=0.0, step=0.25, format="%.2f")

        # ── Dates ─────────────────────────────────────────────────────────────
        st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.12em;color:#888;border-bottom:1px solid #2e2e2e;padding-bottom:0.4rem;margin:1rem 0 0.8rem;'>Dates</div>", unsafe_allow_html=True)
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            date_purchased = st.date_input("Date Purchased", value=date.today())
        with dc2:
            date_listed    = st.date_input("Date Listed",    value=None)
        with dc3:
            date_sold      = st.date_input("Date Sold",      value=None) if status == "Sold" else None

        submitted = st.form_submit_button("💾  Save Item", use_container_width=True)

    if submitted:
        if not title:
            st.error("Title is required.")
        else:
            # Process image
            final_image_url = None
            if uploaded:
                b64  = base64.b64encode(uploaded.read()).decode()
                final_image_url = f"data:{uploaded.type};base64,{b64}"
            elif img_url:
                final_image_url = img_url

            db = get_session()
            p  = Product(
                user_id=current_user_id(),
                title=title, brand=brand or None,
                description=desc or None, category=category,
                source_location=source or None,
                purchase_price=purchase_price, listing_price=listing_price,
                sold_price=sold_price if sold_price and sold_price > 0 else None,
                shipping_cost_paid=ship_paid, shipping_charged_to_customer=ship_charged,
                platform_fees=platform_fees, tax_collected=tax_collected,
                date_purchased=date_purchased,
                date_listed=date_listed if date_listed else None,
                date_sold=date_sold if date_sold else None,
                status=status, image_url=final_image_url, source="manual",
            )
            db.add(p)
            db.commit()
            new_id = p.id
            db.close()
            st.success(f"✅ '{title}' saved! (ID #{new_id})")


# ── Live Preview Sidebar ───────────────────────────────────────────────────────
with preview_col:
    st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.12em;color:#888;padding-bottom:0.4rem;border-bottom:1px solid #2e2e2e;margin-bottom:1rem;'>Live Profit Preview</div>", unsafe_allow_html=True)

    # Compute from current form state (uses last committed values)
    try:
        est = logic.estimate_profit(
            purchase_price, listing_price, ship_paid, ship_charged, platform_fees
        )
    except Exception:
        est = {"profit": 0, "roi": 0, "revenue": 0, "cost": 0}

    pc = ui.PROFIT if est["profit"] >= 0 else ui.ACCENT2

    st.markdown(f"""
    <div style='background:{ui.SURFACE};border:1px solid {ui.BORDER};border-radius:8px;padding:1.5rem;'>
        <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:{ui.MUTED};
                    text-transform:uppercase;letter-spacing:0.1em;'>Est. Profit</div>
        <div style='font-family:Space Mono,monospace;font-size:2.4rem;font-weight:700;
                    color:{pc};margin:0.4rem 0;'>${est['profit']:+.2f}</div>
        <div style='font-family:Space Mono,monospace;font-size:1.1rem;color:{pc};'>
            ROI: {est['roi']*100:+.1f}%
        </div>
        <hr style='border-color:{ui.BORDER};margin:1rem 0;'>
        <div style='font-size:0.82rem;'>
            <div style='display:flex;justify-content:space-between;margin:0.25rem 0;'>
                <span style='color:{ui.MUTED};'>Revenue</span>
                <span>${est['revenue']:.2f}</span>
            </div>
            <div style='display:flex;justify-content:space-between;margin:0.25rem 0;'>
                <span style='color:{ui.MUTED};'>Total Cost</span>
                <span>${est['cost']:.2f}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fee Calculator ────────────────────────────────────────────────────────
    st.markdown("<div style='font-family:Space Mono,monospace;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;color:#888;padding:1rem 0 0.4rem;border-bottom:1px solid #2e2e2e;margin-bottom:0.8rem;'>Fee Calculator</div>", unsafe_allow_html=True)
    calc = st.number_input("Enter listing price →", min_value=0.0, step=1.0, key="fee_calc")
    if calc > 0:
        fees = logic.calc_depop_fees(calc)
        st.markdown(f"""
        <div style='font-size:0.83rem;background:{ui.SURFACE};border:1px solid {ui.BORDER};
                    border-radius:6px;padding:0.9rem;'>
            <div style='display:flex;justify-content:space-between;margin:0.2rem 0;'>
                <span style='color:{ui.MUTED};'>Depop (10%)</span>
                <span>${fees['depop']:.2f}</span>
            </div>
            <div style='display:flex;justify-content:space-between;margin:0.2rem 0;'>
                <span style='color:{ui.MUTED};'>PayPal (2.9%+$0.30)</span>
                <span>${fees['paypal']:.2f}</span>
            </div>
            <div style='display:flex;justify-content:space-between;font-weight:700;
                        border-top:1px solid {ui.BORDER};padding-top:0.5rem;margin-top:0.5rem;'>
                <span style='color:{ui.ACCENT};'>Total Fees</span>
                <span style='color:{ui.ACCENT2};'>${fees['total']:.2f}</span>
            </div>
            <div style='color:{ui.MUTED};font-size:0.72rem;margin-top:0.6rem;'>
                You keep: ${calc - fees['total']:.2f} before shipping
            </div>
        </div>
        """, unsafe_allow_html=True)
