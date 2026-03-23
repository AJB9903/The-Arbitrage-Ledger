import streamlit as st
st.set_page_config(page_title="Scraper · Ledger", page_icon="🔍", layout="wide")

import re, time, requests
from bs4 import BeautifulSoup

import ui, logic
from auth import require_login, current_user_id
from db import get_session, Product

ui.inject_css()
require_login()
ui.page_header("🔍", "DEPOP SCRAPER", "import your public listings")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

with st.expander("ℹ️ How this works"):
    st.markdown("""
    Paste any **public** Depop profile URL (e.g. `https://www.depop.com/username/`).

    The scraper tries two strategies:
    1. **Depop's web API** — fastest, pulls title + price + first image
    2. **HTML fallback** — if the API is blocked

    **Duplicate detection**: if a listing URL already exists in your inventory it's skipped on import.
    Depop may rate-limit requests — if it fails, wait 2 minutes and try again.
    """)

# ── Input ─────────────────────────────────────────────────────────────────────
ic, bc = st.columns([3,1])
with ic:
    url_input = st.text_input("Depop Profile URL", placeholder="https://www.depop.com/username/")
with bc:
    st.markdown("<br>", unsafe_allow_html=True)
    go = st.button("🔍 Scrape", use_container_width=True)


def _price(text: str) -> float:
    m = re.search(r"[\d,]+\.?\d*", str(text).replace(",",""))
    return float(m.group()) if m else 0.0


def scrape(profile_url: str) -> list[dict]:
    profile_url = profile_url.rstrip("/")
    m = re.search(r"depop\.com/([^/?#]+)", profile_url)
    if not m:
        return []
    username = m.group(1)
    listings = []

    # Strategy 1 — Depop web API
    try:
        api = f"https://webapi.depop.com/api/v2/search/products/?sellers={username}&limit=48"
        r   = requests.get(api, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data  = r.json()
            items = data.get("products", []) or data.get("objects", [])
            for item in items:
                slug  = item.get("slug","")
                iid   = item.get("id","")
                lurl  = f"https://www.depop.com/products/{slug or iid}/"
                price_info = item.get("price",{})
                price = float(price_info.get("priceAmount", 0)) if isinstance(price_info, dict) else _price(price_info)
                preview = item.get("preview",[])
                img = None
                if isinstance(preview, list) and preview:
                    first = preview[0]
                    img   = first.get("url") or first.get("src") if isinstance(first, dict) else str(first)
                listings.append({"title": (item.get("description","") or f"Item {iid}")[:100],
                                  "price": price, "image_url": img,
                                  "description": item.get("description",""),
                                  "depop_url": lurl})
            if listings:
                return listings
    except Exception:
        pass

    # Strategy 2 — HTML parse
    try:
        time.sleep(1.5)
        r = requests.get(profile_url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        cards = (soup.select("[class*='styles__ProductCard']") or
                 soup.select("article") or
                 soup.select("[data-testid='product-card']"))
        for card in cards[:48]:
            link  = card.find("a")
            lurl  = "https://www.depop.com" + link["href"] if link and link.get("href") else None
            if not lurl: continue
            title_el = card.find(["h3","h2","p"])
            title = title_el.get_text(strip=True) if title_el else "Untitled"
            price_el = card.find(string=re.compile(r"\$\d+"))
            price = _price(price_el) if price_el else 0.0
            img = card.find("img")
            img_url = img.get("src") or img.get("data-src") if img else None
            listings.append({"title": title[:100], "price": price,
                              "image_url": img_url, "description": "",
                              "depop_url": lurl})
    except Exception:
        pass

    return listings


# ── Run Scrape ────────────────────────────────────────────────────────────────
if go and url_input:
    with st.spinner("Scraping Depop… this can take 10–20 seconds"):
        results = scrape(url_input)
    if results:
        st.session_state["scraped"] = results
        st.success(f"Found {len(results)} listings!")
    else:
        st.error("No listings found. Check the URL, or Depop may be blocking — wait 2 min and retry.")

# ── Display Results ───────────────────────────────────────────────────────────
if "scraped" in st.session_state:
    db = get_session()
    existing_urls = {r[0] for r in db.query(Product.depop_url)
                     .filter(Product.user_id == current_user_id(),
                             Product.depop_url.isnot(None)).all()}
    db.close()

    results  = st.session_state["scraped"]
    new_ones = [r for r in results if r["depop_url"] not in existing_urls]
    dups     = [r for r in results if r["depop_url"] in existing_urls]

    st.markdown(f"""
    <div style='display:flex;gap:1rem;margin:1rem 0;'>
        <div style='background:rgba(77,240,160,0.08);border:1px solid #4df0a044;
                    border-radius:6px;padding:0.5rem 1.2rem;'>
            <span style='color:{ui.PROFIT};font-weight:700;font-family:Space Mono,monospace;'>{len(new_ones)}</span>
            <span style='color:{ui.MUTED};font-size:0.85rem;'> new listings</span>
        </div>
        <div style='background:rgba(240,77,107,0.08);border:1px solid #f04d6b44;
                    border-radius:6px;padding:0.5rem 1.2rem;'>
            <span style='color:{ui.ACCENT2};font-weight:700;font-family:Space Mono,monospace;'>{len(dups)}</span>
            <span style='color:{ui.MUTED};font-size:0.85rem;'> already in inventory</span>
        </div>
    </div>""", unsafe_allow_html=True)

    if new_ones:
        select_all = st.checkbox("Select all new listings", value=True)
        import_btn = st.button("📥 Import Selected", use_container_width=False)

        selected = []
        cols_n   = 3
        for i in range(0, len(new_ones), cols_n):
            chunk = new_ones[i:i+cols_n]
            cols  = st.columns(cols_n)
            for j, item in enumerate(chunk):
                with cols[j]:
                    checked = st.checkbox("Import this", value=select_all, key=f"chk_{i+j}",
                                          label_visibility="collapsed")
                    if checked:
                        selected.append(item)

                    if item.get("image_url"):
                        try:
                            st.image(item["image_url"], use_column_width=True)
                        except Exception:
                            pass

                    st.markdown(f"""
                    <div style='background:{ui.SURFACE};border:1px solid {ui.BORDER};
                                border-radius:6px;padding:0.75rem;margin-top:0.3rem;'>
                        <div style='font-weight:600;font-size:0.88rem;'>{item['title'][:55]}</div>
                        <div style='font-family:Space Mono,monospace;color:{ui.ACCENT};
                                    font-size:1rem;margin-top:0.3rem;'>${item['price']:.2f}</div>
                        {'<a href="' + item["depop_url"] + '" target="_blank" style="color:#4db0f0;font-size:0.75rem;">View on Depop ↗</a>' if item.get("depop_url") else ''}
                    </div>""", unsafe_allow_html=True)

        if import_btn:
            if not selected:
                st.warning("No listings selected.")
            else:
                db = get_session()
                count = 0
                for item in selected:
                    # Final dedup check
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
                        status="Listed", source="depop",
                        purchase_price=0.0,
                    )
                    db.add(p)
                    count += 1
                db.commit()
                db.close()
                st.success(f"✅ Imported {count} listings! Go to Inventory to add purchase prices.")
                del st.session_state["scraped"]
                st.rerun()

    if dups:
        with st.expander(f"🔁 {len(dups)} duplicates (already in inventory)"):
            for d in dups:
                st.markdown(f"""
                <div style='background:{ui.SURFACE};border:1px solid {ui.BORDER};border-radius:6px;
                            padding:0.6rem 1rem;margin:0.3rem 0;font-size:0.85rem;'>
                    {d['title'][:60]} — <span style='color:{ui.ACCENT};'>${d['price']:.2f}</span>
                    {'<a href="' + d["depop_url"] + '" target="_blank" style="color:#4db0f0;margin-left:8px;">View ↗</a>' if d.get("depop_url") else ''}
                </div>""", unsafe_allow_html=True)
