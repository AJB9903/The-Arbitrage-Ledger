import os
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func

def get_database_url():
    try:
        url = st.secrets["DATABASE_URL"]
    except Exception:
        url = os.getenv("DATABASE_URL", "")
    
    if not url:
        st.error("DATABASE_URL not found in secrets. Go to Manage App → Settings → Secrets and add it.")
        st.stop()
    
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    if "sslmode" not in url:
        url = url + "?sslmode=require"
    
    return url

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
    title           = Column(String(255), nullable=False)
    brand           = Column(String(100))
    description     = Column(Text)
    category        = Column(String(50))
    source_location = Column(String(255))
    purchase_price               = Column(Float, default=0.0)
    listing_price                = Column(Float, default=0.0)
    sold_price                   = Column(Float, nullable=True)
    shipping_cost_paid           = Column(Float, default=0.0)
    shipping_charged_to_customer = Column(Float, default=0.0)
    platform_fees                = Column(Float, default=0.0)
    tax_collected                = Column(Float, default=0.0)
    date_purchased  = Column(Date, nullable=True)
    date_listed     = Column(Date, nullable=True)
    date_sold       = Column(Date, nullable=True)
    status          = Column(String(20), default="Draft")
    depop_url       = Column(String(500), nullable=True)
    image_url       = Column(Text, nullable=True)
    source          = Column(String(50), default="manual")
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    owner           = relationship("User", back_populates="products")

@st.cache_resource
def get_engine():
    url = get_database_url()
    try:
        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            connect_args={"sslmode": "require", "connect_timeout": 10},
        )
        Base.metadata.create_all(bind=engine)
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        st.info("Check your DATABASE_URL in Streamlit secrets. Make sure it's the Session Pooler URL from Supabase.")
        st.stop()

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
