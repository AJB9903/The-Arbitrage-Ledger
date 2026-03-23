# 🏷️ The Arbitrage Ledger

> Track every flip. Know every dollar.

A browser-based inventory system for thrift resellers.
**No local setup needed** — runs 100% in the cloud via GitHub + Supabase + Streamlit Cloud.

---

## Deploy in 3 steps (all in your browser)

### Step 1 — Get a free database at Supabase

1. Go to **supabase.com** → Sign up free
2. Click **"New project"** → name it `arbitrage-ledger` → set a database password → click Create
3. Wait ~2 min for it to provision
4. Go to **Project Settings → Database**
5. Scroll to **"Connection string"** → select **URI** tab
6. Copy the string — it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres
   ```
7. Replace `[YOUR-PASSWORD]` with the password you set in step 2
8. **Save this string** — you'll need it in Step 3

---

### Step 2 — Push to GitHub

1. Go to **github.com** → click **+** → **New repository**
2. Name it `arbitrage-ledger` → keep it **Private** → click **Create repository**
3. Back in this chat, download the zip file
4. Go to your new GitHub repo → click **"uploading an existing file"**
5. Drag and drop ALL the files from the zip (keep the folder structure)
6. Click **"Commit changes"**

---

### Step 3 — Deploy on Streamlit Cloud

1. Go to **share.streamlit.io** → Sign in with GitHub
2. Click **"New app"**
3. Select your `arbitrage-ledger` repo
4. Set **Main file path** to: `app.py`
5. Click **"Advanced settings"** → in the **Secrets** box paste exactly this:
   ```toml
   DATABASE_URL = "postgresql://postgres:YOUR-PASSWORD@db.xxxx.supabase.co:5432/postgres"
   ```
   (paste your actual Supabase connection string from Step 1)
6. Click **"Deploy"** → wait 2–3 minutes

**That's it.** Your app is live at a URL like `https://yourname-arbitrage-ledger.streamlit.app`.
Create an account, log in, and start adding inventory.

---

## Editing code (vibe coding in the browser)

You never need to open a terminal. To change anything:

1. Go to your **github.com** repo
2. Click any file → click the ✏️ pencil icon to edit
3. Make your changes → click **"Commit changes"**
4. Streamlit Cloud **auto-redeploys** within ~60 seconds

Or use **GitHub Codespaces** (browser VS Code):
- In your repo click **Code → Codespaces → Create codespace**
- Full VS Code in your browser with a terminal

---

## File structure

```
app.py               ← Main entry + login/register
auth.py              ← Password hashing + session auth
db.py                ← Database models (auto-creates tables on boot)
logic.py             ← All business logic: ROI, alerts, profit calc
ui.py                ← Shared styles + components
requirements.txt     ← All Python packages
.streamlit/
  config.toml        ← Dark theme config
pages/
  1_📊_Dashboard.py  ← Financial health overview
  2_📦_Inventory.py  ← Browse + edit all items
  3_➕_Add_Item.py   ← Manual entry form + image upload
  4_📈_Analytics.py  ← Deep charts: ROI, aging, shipping
  5_🔍_Scraper.py    ← Import from Depop profile URL
```

---

## Business logic

| Rule | Trigger | What happens |
|---|---|---|
| Price Drop | Item listed for a multiple of 14 days | ⚠️ Alert shown in Inventory + Dashboard |
| Stale/Donate | Listed > 180 days without selling | 🗑️ Alert shown, status flipped to Stale |
| ROI | Sold items only | `(sold + ship_charged - purchase - ship_paid - fees) / purchase` |
| Dead Capital | Listed + Draft + Stale items | Sum of purchase prices = money locked up |
| Sales Velocity | Based on oldest sale date | Sales/week and Sales/month |

---

## Tech stack

| Layer | What |
|---|---|
| App | Streamlit 1.35 |
| Database | PostgreSQL via Supabase (free tier) |
| ORM | SQLAlchemy 2.0 (auto-creates tables) |
| Auth | bcrypt passwords + Streamlit session state |
| Charts | Plotly 5 |
| Scraping | requests + BeautifulSoup4 |
| Hosting | Streamlit Cloud (free) |
