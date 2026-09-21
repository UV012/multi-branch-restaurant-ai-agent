"""Menu Categories, Items, Variants, and Stock Models."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)

    # Relationships
    branch = relationship("Branch", back_populates="menu_categories")
    items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    base_price = Column(Float, nullable=False, default=0.0)
    is_available = Column(Boolean, default=True, nullable=False)  # Manual staff toggle

    # Relationships
    category = relationship("MenuCategory", back_populates="items")
    variants = relationship("MenuItemVariant", back_populates="menu_item", cascade="all, delete-orphan")
    stocks = relationship("MenuItemStock", back_populates="menu_item", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="menu_item")


class MenuItemVariant(Base):
    __tablename__ = "menu_item_variants"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_type = Column(String(50), nullable=False)  # e.g. "size", "spice_level", "topping"
    variant_name = Column(String(50), nullable=False)  # e.g. "Large", "Extra Spicy", "Olives"
    price_delta = Column(Float, nullable=False, default=0.0)

    # Relationships
    menu_item = relationship("MenuItem", back_populates="variants")


class MenuItemStock(Base):
    __tablename__ = "menu_item_stocks"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_quantity = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("menu_item_id", "branch_id", name="uq_menu_item_branch_stock"),
        CheckConstraint("stock_quantity >= 0", name="chk_stock_quantity_non_negative"),
    )

    # Relationships
    menu_item = relationship("MenuItem", back_populates="stocks")
    branch = relationship("Branch", back_populates="item_stocks")
