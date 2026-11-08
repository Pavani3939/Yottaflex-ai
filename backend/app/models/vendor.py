"""
YottaPay AI – Vendor ORM Model
Table: vendors
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class VendorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLACKLISTED = "BLACKLISTED"
    PENDING_REVIEW = "PENDING_REVIEW"


class Vendor(Base):
    """
    Represents a supplier/vendor in the system.

    ID format : VND-00001
    Code format: VND00001  (used in invoice IDs)
    """

    __tablename__ = "vendors"

    id = Column(String(12), primary_key=True, comment="VND-00001")
    name = Column(String(255), nullable=False, comment="Full legal business name")
    code = Column(String(10), nullable=False, unique=True, comment="Short code for invoice IDs")
    email = Column(String(255), nullable=False, comment="Primary contact email")
    phone = Column(String(30), nullable=True)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False, default="India")
    pincode = Column(String(20), nullable=True)
    gstin = Column(String(20), nullable=True, unique=True, comment="GST Identification Number")
    pan = Column(String(20), nullable=True, unique=True, comment="Permanent Account Number")
    bank_account = Column(String(30), nullable=True)
    bank_ifsc = Column(String(15), nullable=True)
    payment_terms = Column(Integer, nullable=False, default=30, comment="Net payment days")
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(
        Enum(VendorStatus),
        nullable=False,
        default=VendorStatus.ACTIVE,
    )
    category = Column(String(100), nullable=True, comment="Vendor category")
    contact_person = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    is_deleted = Column(Boolean, nullable=False, default=False, comment="Soft delete flag")

    # --- Relationships ---
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    invoices = relationship("Invoice", back_populates="vendor")
    goods_receipts = relationship("GoodsReceipt", back_populates="vendor")
    payments = relationship("Payment", back_populates="vendor")

    def __repr__(self) -> str:
        return f"<Vendor id={self.id} name={self.name!r} status={self.status}>"
