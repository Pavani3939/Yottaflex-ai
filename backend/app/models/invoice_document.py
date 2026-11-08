"""
YottaPay AI – Invoice Document ORM Model
Table: invoice_documents

Stores metadata for uploaded invoice files (PDF, images).
Raw text and extracted JSON are persisted for traceability.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Column, DateTime, Enum,
    ForeignKey, JSON, LargeBinary, String, Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class DocumentFileType(str, enum.Enum):
    PDF = "PDF"
    JPEG = "JPEG"
    PNG = "PNG"
    TIFF = "TIFF"
    OTHER = "OTHER"


class ExtractionMethod(str, enum.Enum):
    PYMUPDF = "PYMUPDF"
    TESSERACT_OCR = "TESSERACT_OCR"
    GEMINI_AI = "GEMINI_AI"
    MANUAL = "MANUAL"


class ExtractionStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class InvoiceDocument(Base):
    """
    Tracks uploaded invoice files and their extraction state.
    """

    __tablename__ = "invoice_documents"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(
        String(35),
        ForeignKey("invoices.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, comment="Server-side path")
    file_type = Column(Enum(DocumentFileType), nullable=False, default=DocumentFileType.PDF)
    file_size_bytes = Column(BigInteger, nullable=True)
    extraction_method = Column(Enum(ExtractionMethod), nullable=False)
    extraction_status = Column(
        Enum(ExtractionStatus),
        nullable=False,
        default=ExtractionStatus.PENDING,
    )
    raw_text = Column(Text, nullable=True, comment="Raw extracted text")
    extracted_json = Column(JSON, nullable=True, comment="Structured extracted fields")
    upload_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # --- Relationships ---
    invoice = relationship("Invoice", back_populates="documents")

    def __repr__(self) -> str:
        return (
            f"<InvoiceDocument id={self.id} invoice_id={self.invoice_id} "
            f"file={self.file_name!r} status={self.extraction_status}>"
        )
