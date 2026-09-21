"""
Core Shopify Admin API and GraphQL Data Models.
Strictly maps to Shopify Order, LineItem, ProductVariant, InventoryItem, Metafield, and Refund resources.

CRITICAL ARCHITECTURAL BOUNDARY:
Excludes shipping charges, payment processor gateway fees, packaging supplies,
and fulfillment pick/pack labor. Those operational costs are strictly reserved for Formula F10.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class Metafield:
    """Shopify Metafield object (Admin API / GraphQL)."""
    namespace: str
    key: str
    value: str
    type: str = "number_decimal"

@dataclass
class InventoryItem:
    """Shopify InventoryItem resource."""
    id: int
    cost: Optional[str] = None  # Shopify returns decimal strings e.g. "25.00"
    sku: Optional[str] = None
    tracked: bool = True

@dataclass
class ProductVariant:
    """Shopify ProductVariant resource."""
    id: int
    product_id: int
    title: str
    sku: Optional[str]
    price: str  # Unit catalog price
    compare_at_price: Optional[str] = None  # MSRP strike-through price
    inventory_item_id: Optional[int] = None
    inventory_item: Optional[InventoryItem] = None

@dataclass
class Product:
    """Shopify Product resource."""
    id: int
    title: str
    product_type: Optional[str] = None
    category: Optional[Dict[str, Any]] = None  # Standard Product Taxonomy
    variants: List[ProductVariant] = field(default_factory=list)
    metafields: List[Metafield] = field(default_factory=list)

@dataclass
class DiscountAllocation:
    """Shopify DiscountAllocation mapping order-level discounts to line items."""
    amount: str
    discount_application_index: int = 0

@dataclass
class LineItem:
    """Shopify LineItem resource."""
    id: int
    variant_id: Optional[int]
    product_id: Optional[int]
    sku: Optional[str]
    title: str
    price: str  # Unit selling price at purchase
    quantity: int
    current_quantity: Optional[int] = None  # Non-returned active quantity
    total_discount: Optional[str] = "0.00"
    discount_allocations: List[DiscountAllocation] = field(default_factory=list)

@dataclass
class RefundLineItem:
    """Shopify RefundLineItem resource representing physical returns."""
    line_item_id: int
    quantity: int
    subtotal: str

@dataclass
class RefundTransaction:
    """Shopify Transaction resource inside a Refund."""
    amount: str
    kind: str = "refund"
    status: str = "success"

@dataclass
class Refund:
    """Shopify Refund resource."""
    id: int
    order_id: int
    created_at: str
    refund_line_items: List[RefundLineItem] = field(default_factory=list)
    transactions: List[RefundTransaction] = field(default_factory=list)

@dataclass
class Order:
    """Shopify Order resource (REST / GraphQL Admin API / Webhook Payload)."""
    id: int
    name: str
    created_at: str
    financial_status: str  # 'paid', 'partially_paid', 'partially_refunded', 'refunded', 'voided'
    cancelled_at: Optional[str]
    total_discounts: str
    total_price: str
    subtotal_price: str
    line_items: List[LineItem] = field(default_factory=list)
    refunds: List[Refund] = field(default_factory=list)
    _variants: Optional[List[Dict[str, Any]]] = None
