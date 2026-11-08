"""
YottaPay AI – ID Generation Utilities

All IDs are deterministic, zero-padded and immutable after creation.
"""
from datetime import date


def vendor_id(sequence: int) -> str:
    """Generate VND-00001 format ID."""
    return f"VND-{sequence:05d}"


def vendor_code(sequence: int) -> str:
    """Generate VND00001 format code (used in invoice IDs)."""
    return f"VND{sequence:05d}"


def po_id(year: int, sequence: int) -> str:
    """Generate PO-2026-000001 format ID."""
    return f"PO-{year}-{sequence:06d}"


def po_line_id(po: str, line_number: int) -> str:
    """Generate POLINE-PO-2026-000001-01 format ID."""
    return f"POLINE-{po}-{line_number:02d}"


def grn_id(year: int, sequence: int) -> str:
    """Generate GRN-2026-000001 format ID."""
    return f"GRN-{year}-{sequence:06d}"


def grn_line_id(grn: str, line_number: int) -> str:
    """Generate GRNL-GRN-2026-000001-01 format ID."""
    return f"GRNL-{grn}-{line_number:02d}"


def invoice_id(vendor_code_str: str, year: int, sequence: int) -> str:
    """Generate INV-VND00001-2026-000001 format ID."""
    return f"INV-{vendor_code_str}-{year}-{sequence:06d}"


def invoice_line_id(inv_id: str, line_number: int) -> str:
    """Generate INVL-INV-VND00001-2026-000001-01 format ID."""
    return f"INVL-{inv_id}-{line_number:02d}"


def audit_event_id() -> str:
    """Generate EVT-{UUID4} format ID."""
    import uuid
    return f"EVT-{uuid.uuid4()}"
