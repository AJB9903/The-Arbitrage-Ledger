"""
db.py — Database connection + all models.
Connects to Supabase PostgreSQL (or SQLite for local testing).
Tables are created automatically on first run.
"""
import os
import streamlit as st
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Date, DateTime, Text, Boolean, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func

# ── Connection ────────────────────────────────────────────────────────────────
def get_database_url():
    # 1. Streamlit Cloud secrets
    try:
        url = st.secrets["DATABASE_URL"]
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    except Exception:
        pass
    # 2. Environment variable (local dev)
    url = os.getenv("DATABASE_URL", "sqlite:///./arbitrage_ledger.db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


@st.cache_resource
def get_engine():
    url = get_database_url()
    connect_args = {"check_same_thread": False} if "sqlite" in url else {}
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)  # auto-create tables
    return engine


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


# ── ORM Models ────────────────────────────────────────────────────────────────
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50), unique=True, nullable=False)
    email           = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    is_active       = Column(Boolean, default=True)
    products        = relationship("Product", back_populates="owner", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Info
    title           = Column(String(255), nullable=False)
    brand           = Column(String(100))
    description     = Column(Text)
    category        = Column(String(50))
    source_location = Column(String(255))
    # Financials
    purchase_price              = Column(Float, default=0.0)
    listing_price               = Column(Float, default=0.0)
    sold_price                  = Column(Float, nullable=True)
    shipping_cost_paid          = Column(Float, default=0.0)
    shipping_charged_to_customer = Column(Float, default=0.0)
    platform_fees               = Column(Float, default=0.0)
    tax_collected               = Column(Float, default=0.0)
    # Dates
    date_purchased  = Column(Date, nullable=True)
    date_listed     = Column(Date, nullable=True)
    date_sold       = Column(Date, nullable=True)
    # Meta
    status          = Column(String(20), default="Draft")
    depop_url       = Column(String(500), nullable=True)
    image_url       = Column(Text, nullable=True)
    source          = Column(String(50), default="manual")
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    owner           = relationship("User", back_populates="products")
