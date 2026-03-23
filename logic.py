"""
logic.py — All financial calculations, alert triggers, and analytics.
Pure Python — no DB calls here, just functions that take Product objects.
"""
from datetime import date
from typing import Optional
from db import Product


# ── Core Calculations ─────────────────────────────────────────────────────────

def days_since_listed(p: Product) -> Optional[int]:
    if not p.date_listed:
        return None
    return (date.today() - p.date_listed).days


def net_profit(p: Product) -> Optional[float]:
    if p.status != "Sold" or p.sold_price is None:
        return None
    revenue = (p.sold_price or 0) + (p.shipping_charged_to_customer or 0)
    cost    = (p.purchase_price or 0) + (p.shipping_cost_paid or 0) + (p.platform_fees or 0)
    return round(revenue - cost, 2)


def roi(p: Product) -> Optional[float]:
    if p.status != "Sold" or not p.purchase_price:
        return None
    profit = net_profit(p)
    if profit is None:
        return None
    return round(profit / p.purchase_price, 4)


def fee_ratio(p: Product) -> Optional[float]:
    if not p.listing_price:
        return None
    return round((p.platform_fees or 0) / p.listing_price, 4)


def shipping_variance(p: Product) -> float:
    return round((p.shipping_charged_to_customer or 0) - (p.shipping_cost_paid or 0), 2)


# ── Alert Triggers ────────────────────────────────────────────────────────────

def price_drop_alert(p: Product) -> bool:
    """Every 14 days a listed item hasn't sold → recommend 10% price drop."""
    if p.status != "Listed":
        return False
    dsl = days_since_listed(p)
    if not dsl or dsl == 0:
        return False
    return dsl % 14 == 0


def donation_alert(p: Product) -> bool:
    """Listed more than 180 days → flag for donation."""
    if p.status not in ("Listed", "Stale"):
        return False
    dsl = days_since_listed(p)
    return bool(dsl and dsl > 180)


# ── Helpers for UI ────────────────────────────────────────────────────────────

def enrich(p: Product) -> dict:
    """Return a flat dict of the product + all computed fields."""
    return {
        "id":                           p.id,
        "user_id":                      p.user_id,
        "title":                        p.title,
        "brand":                        p.brand or "—",
        "description":                  p.description,
        "category":                     p.category or "—",
        "source_location":              p.source_location,
        "purchase_price":               p.purchase_price or 0,
        "listing_price":                p.listing_price or 0,
        "sold_price":                   p.sold_price,
        "shipping_cost_paid":           p.shipping_cost_paid or 0,
        "shipping_charged_to_customer": p.shipping_charged_to_customer or 0,
        "platform_fees":                p.platform_fees or 0,
        "tax_collected":                p.tax_collected or 0,
        "date_purchased":               p.date_purchased,
        "date_listed":                  p.date_listed,
        "date_sold":                    p.date_sold,
        "status":                       p.status,
        "depop_url":                    p.depop_url,
        "image_url":                    p.image_url,
        "source":                       p.source,
        "created_at":                   p.created_at,
        # Computed
        "days_since_listed":            days_since_listed(p),
        "net_profit":                   net_profit(p),
        "roi":                          roi(p),
        "fee_ratio":                    fee_ratio(p),
        "shipping_variance":            shipping_variance(p),
        "price_drop_alert":             price_drop_alert(p),
        "donation_alert":               donation_alert(p),
    }


# ── Quick fee calculator ──────────────────────────────────────────────────────

def calc_depop_fees(listing_price: float) -> dict:
    depop   = round(listing_price * 0.10, 2)
    paypal  = round(listing_price * 0.029 + 0.30, 2)
    total   = round(depop + paypal, 2)
    return {"depop": depop, "paypal": paypal, "total": total}


def estimate_profit(purchase: float, listing: float, ship_paid: float,
                    ship_charged: float, fees: float) -> dict:
    revenue = listing + ship_charged
    cost    = purchase + ship_paid + fees
    profit  = round(revenue - cost, 2)
    r       = round(profit / purchase, 4) if purchase > 0 else 0
    return {"profit": profit, "roi": r, "revenue": revenue, "cost": cost}
