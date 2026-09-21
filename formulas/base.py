"""
Formulas Registry and Common Protocol.
"""

from typing import Protocol, runtime_checkable
from core.shopify_models import Order

@runtime_checkable
class FormulaProtocol(Protocol):
    """Protocol for all profit leakage and margin scoring formulas."""
    formula_id: str
    formula_name: str
