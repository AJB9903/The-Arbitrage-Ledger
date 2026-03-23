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
    uploaded = st.file_uploader("Upload your filled CSV", type=["csv"])

    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            st.markdown(f"**Preview — {len(df)} items found:**")
            st.dataframe(df.head(5), use_container_width=True)

            if st.button("📥 Import All", use_container_width=False):
                db = get_session()
                count = 0
                errors = []

                for _, row in df.iterrows():
                    try:
                        def val(col, default=None):
                            v = row.get(col, default)
                            if pd.isna(v) or v == "":
                                return default
                            return v

                        def fval(col):
                            v = val(col, 0)
                            try:
                                return float(v)
                            except Exception:
                                return 0.0

                        def dval(col):
                            v = val(col)
                            if not v:
                                return None
                            try:
                                return pd.to_datetime(v).date()
                            except Exception:
                                return None

                        title = val("title")
                        if not title:
                            continue

                        status = val("status", "Draft")
                        if status not in ["Draft", "Listed", "Sold", "Stale", "Donated"]:
                            status = "Draft"

                        p = Product(
                            user_id=current_user_id(),
                            title=str(title)[:255],
                            brand=val("brand"),
                            description=val("description"),
                            category=val("category"),
                            source_location=val("source_location"),
                            purchase_price=fval("purchase_price"),
                            listing_price=fval("listing_price"),
                            sold_price=fval("sold_price") if val("sold_price") else None,
                            shipping_cost_paid=fval("shipping_cost_paid"),
                            shipping_charged_to_customer=fval("shipping_charged_to_customer"),
                            platform_fees=fval("platform_fees"),
                            tax_collected=fval("tax_collected"),
                            date_purchased=dval("date_purchased"),
                            date_listed=dval("date_listed"),
                            date_sold=dval("date_sold"),
                            status=status,
                            source="csv",
                        )
                        db.add(p)
                        count += 1
                    except Exception as e:
                        errors.append(str(e))

                db.commit()
                db.close()

                st.success(f"✅ Imported {count} items!")
                if errors:
                    st.warning(f"{len(errors)} rows had errors and were skipped.")

        except Exception as e:
            st.error(f"Could not read CSV: {e}")

# ── DEPOP SCRAPER ─────────────────────────────────────────────────────────────
with tab2:
    st.markdown("""
    <div class='al-yellow'>
        ⚠️ <b style='color:#c8f04d;'>Heads up:</b> Depop actively blocks scraping from cloud servers.
        This may not work reliably. The CSV import above is the more dependable option.
    </div>
    <br>
    """, unsafe_allow_html=True)

    import re, time, requests
    from bs4 import BeautifulSoup

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    url_input = st.text_input("Depop Profile URL", placeholder="https://www.depop.com/username/")
    go = st.button("🔍 Try Scrape", use_container_width=False)

    def _price(text):
        m = re.search(r"[\d,]+\.?\d*", str(text).replace(",", ""))
        return float(m.group()) if m else 0.0

    def scrape(profile_url):
        profile_url = profile_url.rstrip("/")
        m = re.search(r"depop\.com/([^/?#]+)", profile_url)
        if not m:
            return []
        username = m.group(1)
        listings = []

        try:
            api = f"https://webapi.depop.com/api/v2/search/products/?sellers={username}&limit=48"
            r = requests.get(api, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                items = data.get("products", []) or data.get("objects", [])
                for item in items:
                    slug = item.get("slug", "")
                    iid = item.get("id", "")
                    lurl = f"https://www.depop.com/products/{slug or iid}/"
                    price_info = item.get("price", {})
                    price = float(price_info.get("priceAmount", 0)) if isinstance(price_info, dict) else _price(price_info)
                    preview = item.get("preview", [])
                    img = None
                    if isinstance(preview, list) and preview:
                        first = preview[0]
                        img = first.get("url") or first.get("src") if isinstance(first, dict) else str(first)
                    listings.append({
                        "title": (item.get("description", "") or f"Item {iid}")[:100],
                        "price": price,
                        "image_url": img,
                        "description": item.get("description", ""),
                        "depop_url": lurl,
                    })
                if listings:
                    return listings
        except Exception:
            pass

        try:
            time.sleep(1.5)
            r = requests.get(profile_url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            cards = (soup.select("[class*='styles__ProductCard']") or
                     soup.select("article") or
                     soup.select("[data-testid='product-card']"))
            for card in cards[:48]:
                link = card.find("a")
                lurl = "https://www.depop.com" + link["href"] if link and link.get("href") else None
                if not lurl:
                    continue
                title_el = card.find(["h3", "h2", "p"])
                title = title_el.get_text(strip=True) if title_el else "Untitled"
                price_el = card.find(string=re.compile(r"\$\d+"))
                price = _price(price_el) if price_el else 0.0
                img = card.find("img")
                img_url = img.get("src") or img.get("data-src") if img else None
                listings.append({
                    "title": title[:100],
                    "price": price,
                    "image_url": img_url,
                    "description": "",
                    "depop_url": lurl,
                })
        except Exception:
            pass

        return listings

    if go and url_input:
        with st.spinner("Trying to scrape Depop..."):
            results = scrape(url_input)
        if results:
            st.session_state["scraped"] = results
            st.success(f"Found {len(results)} listings!")
        else:
            st.error("Depop blocked the request. Use CSV Import instead — download the template, fill in your listings, upload it.")

    if "scraped" in st.session_state:
        db = get_session()
        existing_urls = {r[0] for r in db.query(Product.depop_url)
                         .filter(Product.user_id == current_user_id(),
                                 Product.depop_url.isnot(None)).all()}
        db.close()

        results = st.session_state["scraped"]
        new_ones = [r for r in results if r["depop_url"] not in existing_urls]

        if new_ones:
            if st.button("📥 Import All", use_container_width=False):
                db = get_session()
                count = 0
                for item in new_ones:
                    if db.query(Product).filter(
                        Product.depop_url == item["depop_url"],
                        Product.user_id == current_user_id()
                    ).first():
                        continue
                    p = Product(
                        user_id=current_user_id(),
                        title=item["title"][:255],
                        listing_price=item["price"],
                        image_url=item.get("image_url"),
                        description=item.get("description"),
                        depop_url=item["depop_url"],
                        status="Listed",
                        source="depop",
                        purchase_price=0.0,
                    )
                    db.add(p)
                    count += 1
                db.commit()
                db.close()
                st.success(f"✅ Imported {count} listings!")
                del st.session_state["scraped"]
                st.rerun()

            cols = st.columns(3)
            for i, item in enumerate(new_ones):
                with cols[i % 3]:
                    if item.get("image_url"):
                        try:
                            st.image(item["image_url"], use_column_width=True)
                        except Exception:
                            pass
                    st.markdown(f"""
                    <div style='background:#1a1a1a;border:1px solid #2e2e2e;border-radius:6px;padding:0.75rem;margin-bottom:0.5rem;'>
                        <div style='font-weight:600;font-size:0.88rem;'>{item['title'][:55]}</div>
                        <div style='color:#c8f04d;font-family:Space Mono,monospace;'>${item['price']:.2f}</div>
                    </div>""", unsafe_allow_html=True)
