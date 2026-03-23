import streamlit as st
st.set_page_config(page_title="Inventory · Ledger", page_icon="📦", layout="wide")

import ui, logic
from auth import require_login, current_user_id
from db import get_session, Product

ui.inject_css()
require_login()

# ── Filters ───────────────────────────────────────────────────────────────────
ui.page_header("📦", "INVENTORY")

f1, f2, f3 = st.columns([1, 1, 2])
with f1:
    sf = st.selectbox("Status", ["All"] + ui.STATUSES)
with f2:
    cf = st.selectbox("Category", ["All"] + ui.CATEGORIES)
with f3:
    search = st.text_input("Search", placeholder="title or brand...")

# ── Query ─────────────────────────────────────────────────────────────────────
db    = get_session()
query = db.query(Product).filter(Product.user_id == current_user_id())
if sf != "All":
    query = query.filter(Product.status == sf)
if cf != "All":
    query = query.filter(Product.category == cf)
products = query.order_by(Product.created_at.desc()).all()
db.close()

if search:
    q = search.lower()
    products = [p for p in products if q in (p.title or "").lower() or q in (p.brand or "").lower()]

items = [logic.enrich(p) for p in products]

# ── Alert Banner ──────────────────────────────────────────────────────────────
pd_alerts = [i for i in items if i["price_drop_alert"]]
dn_alerts = [i for i in items if i["donation_alert"]]
if pd_alerts or dn_alerts:
    b1, b2 = st.columns(2)
    with b1:
        if pd_alerts:
            st.markdown(f"<div class='al-yellow'>⚠️ <b style='color:#c8f04d'>{len(pd_alerts)}</b> items need a price drop</div>", unsafe_allow_html=True)
    with b2:
        if dn_alerts:
            st.markdown(f"<div class='al-red'>🗑️ <b style='color:#f04d6b'>{len(dn_alerts)}</b> items are STALE</div>", unsafe_allow_html=True)

st.markdown(f"<div style='color:{ui.MUTED};font-size:0.82rem;margin:0.5rem 0 1rem;'>{len(items)} items</div>", unsafe_allow_html=True)

if not items:
    st.markdown("<div style='color:#888;padding:3rem;text-align:center;'>No items found. Add a thrift find!</div>", unsafe_allow_html=True)
    st.stop()

# ── Item Cards ────────────────────────────────────────────────────────────────
for item in items:
    pid      = item["id"]
    color, bg, badge = ui.STATUS_COLORS.get(item["status"], ("#888","#88888822","⬜"))
    border   = "#f04d6b55" if item["donation_alert"] else ("#c8f04d44" if item["price_drop_alert"] else ui.BORDER)
    profit   = item["net_profit"]
    roi_val  = item["roi"]
    dsl      = item["days_since_listed"]
    pc       = ui.PROFIT if (profit or 0) >= 0 else ui.ACCENT2

    with st.container():
        st.markdown(f"<div style='background:{ui.SURFACE};border:1px solid {border};border-radius:8px;padding:1rem;margin:0.35rem 0;'>", unsafe_allow_html=True)
        img_c, info_c, fin_c, act_c = st.columns([0.7, 2.5, 2, 1.3])

        # Image
        with img_c:
            img = item.get("image_url")
            if img and (img.startswith("http") or img.startswith("data:")):
                try:
                    st.image(img, width=68)
                except Exception:
                    st.markdown("<div style='width:68px;height:68px;background:#242424;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#555;font-size:1.3rem;'>📷</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='width:68px;height:68px;background:#242424;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#555;font-size:1.3rem;'>📷</div>", unsafe_allow_html=True)

        # Info
        with info_c:
            st.markdown(f"""
            <div>
                <div style='font-weight:600;font-size:0.95rem;'>{item['title'][:65]}</div>
                <div style='color:{ui.MUTED};font-size:0.78rem;margin-top:2px;'>
                    {item['brand']} · {item['category']} · {item['source_location'] or '—'}
                </div>
                <div style='margin-top:5px;'>
                    <span style='background:{bg};color:{color};border:1px solid {color}44;
                                 padding:2px 9px;border-radius:20px;font-family:Space Mono,monospace;
                                 font-size:0.7rem;font-weight:700;'>{badge} {item['status']}</span>
                    {'<span style="color:#c8f04d;font-size:0.72rem;margin-left:8px;">⚠️ Drop Price</span>' if item['price_drop_alert'] else ''}
                    {'<span style="color:#f04d6b;font-size:0.72rem;margin-left:8px;">🗑️ Donate</span>' if item['donation_alert'] else ''}
                </div>
                <div style='color:#555;font-size:0.72rem;margin-top:3px;'>
                    {f"{dsl}d listed" if isinstance(dsl,int) else ""}
                </div>
            </div>""", unsafe_allow_html=True)

        # Financials
        with fin_c:
            st.markdown(f"""
            <div style='font-size:0.82rem;display:grid;grid-template-columns:1fr 1fr;
                        gap:3px 10px;align-items:center;'>
                <span style='color:{ui.MUTED};'>Cost</span>
                <span>${item['purchase_price']:.2f}</span>
                <span style='color:{ui.MUTED};'>Listed</span>
                <span>${item['listing_price']:.2f}</span>
                <span style='color:{ui.MUTED};'>Sold</span>
                <span>${item['sold_price'] or 0:.2f}</span>
                <span style='color:{ui.MUTED};'>Profit</span>
                <span style='color:{pc};font-weight:600;'>
                    {f'${profit:.2f}' if profit is not None else '—'}
                </span>
                <span style='color:{ui.MUTED};'>ROI</span>
                <span style='color:{pc};'>
                    {f'{roi_val*100:.1f}%' if roi_val is not None else '—'}
                </span>
            </div>""", unsafe_allow_html=True)

        # Actions
        with act_c:
            new_status = st.selectbox("", ui.STATUSES,
                index=ui.STATUSES.index(item["status"]) if item["status"] in ui.STATUSES else 0,
                key=f"st_{pid}", label_visibility="collapsed")
            if new_status != item["status"]:
                db2 = get_session()
                p = db2.query(Product).filter(Product.id == pid).first()
                if p:
                    p.status = new_status
                    db2.commit()
                db2.close()
                st.rerun()

            eb, db_btn = st.columns(2)
            with eb:
                if st.button("Edit", key=f"e_{pid}", use_container_width=True):
                    st.session_state[f"editing_{pid}"] = True
                    st.rerun()
            with db_btn:
                if st.button("🗑", key=f"d_{pid}", use_container_width=True):
                    db3 = get_session()
                    p = db3.query(Product).filter(Product.id == pid).first()
                    if p: db3.delete(p); db3.commit()
                    db3.close()
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Inline Edit Form ──────────────────────────────────────────────────────
    if st.session_state.get(f"editing_{pid}"):
        with st.expander(f"✏️ Editing: {item['title'][:45]}", expanded=True):
            with st.form(f"ef_{pid}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    e_title  = st.text_input("Title",    value=item["title"])
                    e_brand  = st.text_input("Brand",    value=item["brand"] if item["brand"] != "—" else "")
                    e_cat    = st.selectbox("Category",  ui.CATEGORIES,
                                index=ui.CATEGORIES.index(item["category"])
                                if item["category"] in ui.CATEGORIES else 6)
                    e_src    = st.text_input("Source",   value=item["source_location"] or "")
                with c2:
                    e_buy    = st.number_input("Purchase Price",  value=float(item["purchase_price"]),  step=0.25)
                    e_list   = st.number_input("Listing Price",   value=float(item["listing_price"]),   step=0.25)
                    e_sold   = st.number_input("Sold Price",      value=float(item["sold_price"] or 0), step=0.25)
                    e_status = st.selectbox("Status", ui.STATUSES,
                                index=ui.STATUSES.index(item["status"]) if item["status"] in ui.STATUSES else 0)
                with c3:
                    e_fees   = st.number_input("Platform Fees",   value=float(item["platform_fees"]),   step=0.25)
                    e_sp     = st.number_input("Shipping Paid",   value=float(item["shipping_cost_paid"]), step=0.25)
                    e_sc     = st.number_input("Shipping Charged",value=float(item["shipping_charged_to_customer"]), step=0.25)
                    e_tax    = st.number_input("Tax Collected",   value=float(item["tax_collected"]),    step=0.01)

                sv, cv = st.columns(2)
                with sv:
                    if st.form_submit_button("Save", use_container_width=True):
                        db4 = get_session()
                        p = db4.query(Product).filter(Product.id == pid).first()
                        if p:
                            p.title=e_title; p.brand=e_brand or None; p.category=e_cat
                            p.source_location=e_src or None; p.purchase_price=e_buy
                            p.listing_price=e_list; p.sold_price=e_sold if e_sold>0 else None
                            p.status=e_status; p.platform_fees=e_fees
                            p.shipping_cost_paid=e_sp; p.shipping_charged_to_customer=e_sc
                            p.tax_collected=e_tax
                            db4.commit()
                        db4.close()
                        st.session_state.pop(f"editing_{pid}", None)
                        st.rerun()
                with cv:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.pop(f"editing_{pid}", None)
                        st.rerun()
