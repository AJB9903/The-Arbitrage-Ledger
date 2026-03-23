import streamlit as st
st.set_page_config(page_title="Dashboard · Ledger", page_icon="📊", layout="wide")

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

import ui, logic
from auth import require_login, current_user_id
from db import get_session, Product

ui.inject_css()
require_login()

# ── Load all products for this user ───────────────────────────────────────────
db   = get_session()
rows = db.query(Product).filter(Product.user_id == current_user_id()).all()
db.close()
items = [logic.enrich(p) for p in rows]

sold    = [i for i in items if i["status"] == "Sold"]
listed  = [i for i in items if i["status"] == "Listed"]
draft   = [i for i in items if i["status"] == "Draft"]
stale   = [i for i in items if i["status"] in ("Stale","Donated")]

ui.page_header("📊", "FINANCIAL HEALTH", "real-time snapshot")

# ── Alerts ────────────────────────────────────────────────────────────────────
price_drops  = [i for i in items if i["price_drop_alert"]]
donations    = [i for i in items if i["donation_alert"]]
if price_drops or donations:
    a1, a2 = st.columns(2)
    with a1:
        if price_drops:
            st.markdown(f"<div class='al-yellow'>⚠️ <b style='color:#c8f04d'>{len(price_drops)} items</b> are due for a 10% price drop → visit Inventory</div>", unsafe_allow_html=True)
    with a2:
        if donations:
            st.markdown(f"<div class='al-red'>🗑️ <b style='color:#f04d6b'>{len(donations)} items</b> are STALE (&gt;180 days) — consider donating</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────────────────────────
total_revenue = sum((i["sold_price"] or 0) + i["shipping_charged_to_customer"] for i in sold)
total_cost    = sum(i["purchase_price"] + i["shipping_cost_paid"] + i["platform_fees"] for i in sold)
net_profit    = round(total_revenue - total_cost, 2)
dead_capital  = sum(i["purchase_price"] for i in items if i["status"] in ("Listed","Draft","Stale"))
total_fees    = sum(i["platform_fees"] for i in sold)
fee_ratio     = total_fees / total_revenue if total_revenue > 0 else 0
ship_var      = sum(i["shipping_variance"] for i in items)

# Sales velocity
if sold:
    sold_with_dates = [i for i in sold if i["date_sold"]]
    if sold_with_dates:
        oldest = min(i["date_sold"] for i in sold_with_dates)
        weeks  = max(((date.today() - oldest).days / 7), 1)
        spw    = round(len(sold) / weeks, 1)
    else:
        spw = 0.0
else:
    spw = 0.0

k1,k2,k3,k4,k5,k6 = st.columns(6)
ui.kpi_card(k1, "Net Profit",     f"${net_profit:,.2f}",  ui.PROFIT if net_profit >= 0 else ui.ACCENT2)
ui.kpi_card(k2, "Total Revenue",  f"${total_revenue:,.2f}")
ui.kpi_card(k3, "Dead Capital",   f"${dead_capital:,.2f}", ui.ACCENT2 if dead_capital > 0 else ui.PROFIT)
ui.kpi_card(k4, "Fee Ratio",      f"{fee_ratio*100:.1f}%",  ui.ACCENT2 if fee_ratio > 0.15 else ui.ACCENT)
ui.kpi_card(k5, "Ship. Variance", f"${ship_var:+.2f}",      ui.PROFIT if ship_var >= 0 else ui.ACCENT2)
ui.kpi_card(k6, "Sales / Wk",     f"{spw}")
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── Monthly Revenue Chart + Status Donut ──────────────────────────────────────
col_l, col_r = st.columns([1.4, 1])

with col_l:
    st.markdown("#### Revenue vs. Profit (Monthly)")
    sold_df = pd.DataFrame(sold) if sold else pd.DataFrame()
    if not sold_df.empty and "date_sold" in sold_df.columns:
        sold_df["month"] = pd.to_datetime(sold_df["date_sold"]).dt.to_period("M").astype(str)
        monthly = sold_df.groupby("month").apply(lambda g: pd.Series({
            "revenue": (g["sold_price"].fillna(0) + g["shipping_charged_to_customer"].fillna(0)).sum(),
            "cost":    (g["purchase_price"].fillna(0) + g["shipping_cost_paid"].fillna(0) + g["platform_fees"].fillna(0)).sum(),
        })).reset_index()
        monthly["profit"] = monthly["revenue"] - monthly["cost"]
        fig = go.Figure()
        fig.add_bar(x=monthly["month"], y=monthly["revenue"], name="Revenue", marker_color=ui.ACCENT)
        fig.add_bar(x=monthly["month"], y=monthly["profit"],  name="Profit",  marker_color=ui.PROFIT)
        fig.update_layout(**ui.PLOTLY_THEME, barmode="group",
                          legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown("<div style='color:#888;padding:3rem;text-align:center;'>No sales data yet.</div>", unsafe_allow_html=True)

with col_r:
    st.markdown("#### Inventory Status")
    vals   = [len(listed), len(sold), len(draft), len(stale)]
    labels = ["Listed", "Sold", "Draft", "Stale/Donated"]
    colors = [ui.ACCENT, ui.PROFIT, ui.MUTED, ui.ACCENT2]
    fig2 = go.Figure(go.Pie(
        labels=labels, values=vals, hole=0.6,
        marker=dict(colors=colors, line=dict(color=ui.BG, width=2)),
    ))
    fig2.update_layout(**ui.PLOTLY_THEME, showlegend=True,
                       legend=dict(orientation="v", x=1, y=0.5),
                       annotations=[dict(text=f"<b>{sum(vals)}</b><br>items", x=0.5, y=0.5,
                                         showarrow=False, font=dict(size=15, color="#f0f0f0",
                                         family="Space Mono"))])
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── ROI by Category ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### ROI by Category")
if sold:
    df_cat = pd.DataFrame(sold)
    df_cat = df_cat[df_cat["roi"].notna()]
    if not df_cat.empty:
        cat_stats = df_cat.groupby("category").agg(
            avg_roi=("roi","mean"), count=("roi","count"),
            total_profit=("net_profit","sum")
        ).reset_index()
        cat_stats["roi_pct"] = (cat_stats["avg_roi"] * 100).round(1)
        fig3 = px.bar(cat_stats, x="category", y="roi_pct",
                      color="roi_pct", text=cat_stats["roi_pct"].apply(lambda x: f"{x:.1f}%"),
                      color_continuous_scale=["#f04d6b","#888","#4df0a0"],
                      labels={"roi_pct": "Avg ROI %","category":""})
        fig3.update_traces(textposition="outside", marker_line_width=0)
        fig3.update_layout(**ui.PLOTLY_THEME, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
else:
    st.markdown("<div style='color:#888;'>Sell some items to see category ROI.</div>", unsafe_allow_html=True)

# ── Dead Capital Table ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 💀 Dead Capital")
dead = [i for i in items if i["status"] in ("Listed","Draft","Stale")]
if dead:
    st.markdown(f"<div style='color:{ui.ACCENT2};font-family:Space Mono,monospace;font-size:1rem;margin-bottom:0.5rem;'>${dead_capital:,.2f} locked in {len(dead)} unsold items</div>", unsafe_allow_html=True)
    df_dead = pd.DataFrame(dead)[["title","category","purchase_price","status","days_since_listed"]]
    df_dead = df_dead.sort_values("purchase_price", ascending=False)
    df_dead["purchase_price"]  = df_dead["purchase_price"].apply(lambda x: f"${x:.2f}")
    df_dead["days_since_listed"] = df_dead["days_since_listed"].apply(lambda x: f"{x}d" if isinstance(x,int) else "—")
    st.dataframe(df_dead.rename(columns={"title":"Item","category":"Category","purchase_price":"Cost","status":"Status","days_since_listed":"Days Listed"}),
                 hide_index=True, use_container_width=True)
else:
    st.success("Zero dead capital — everything is sold! 🎉")
