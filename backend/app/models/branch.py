"""Branch and Table Database Models."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    opening_hours = Column(String(100), nullable=False, default="10:00 AM - 10:00 PM")
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    tables = relationship("Table", back_populates="branch", cascade="all, delete-orphan")
    menu_categories = relationship("MenuCategory", back_populates="branch", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="branch")
    reservations = relationship("Reservation", back_populates="branch")
    item_stocks = relationship("MenuItemStock", back_populates="branch", cascade="all, delete-orphan")


class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(50), nullable=False)
    seating_area = Column(String(50), nullable=False)  # indoor, outdoor, rooftop
    capacity = Column(Integer, nullable=False, default=2)
    is_available = Column(Boolean, default=True, nullable=False)

    # Relationships
    branch = relationship("Branch", back_populates="tables")
    reservations = relationship("Reservation", back_populates="table")
