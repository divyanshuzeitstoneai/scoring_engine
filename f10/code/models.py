"""
F10 Product Contribution v2 Data Models.
Strict Decimal precision for all monetary values.
Adheres to Shopify Admin GraphQL API 2024-10.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class CogsState(str, Enum):
    COGS_OBSERVED = "COGS_OBSERVED"
    COGS_MISSING = "COGS_MISSING"
    COGS_ZERO_SUSPECT = "COGS_ZERO_SUSPECT"


class EvidenceTier(str, Enum):
    T1 = "T1"  # Actual Shopify data
    T2 = "T2"  # Merchant-confirmed config
    T3 = "T3"  # Derived from Shopify fields
    T4 = "T4"  # Category prior (unconfirmed)


class VariantStatus(str, Enum):
    HEALTHY = "HEALTHY"
    UNDERPERFORMING = "UNDERPERFORMING"
    VALUE_DESTROYING = "VALUE_DESTROYING"
    BREAKEVEN = "BREAKEVEN"
    UNSCOREABLE = "UNSCOREABLE"
    NO_DATA = "NO_DATA"
    PROVISIONAL = "PROVISIONAL"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNRESOLVED = "UNRESOLVED"
    INCOMPLETE_COSTS = "INCOMPLETE_COSTS"
    RANGE_ONLY = "RANGE_ONLY"


@dataclass
class LineDiscountAllocation:
    amount: Decimal
    target_type: str = "LINE_ITEM"
    target_selection: str = "ALL"
    allocation_method: str = "ACROSS"


@dataclass
class LineFact:
    """Grain: One order line item (the atom of F10)."""
    line_item_id: str
    order_id: str
    variant_id: Optional[str]
    product_id: Optional[str]
    sku: Optional[str]
    title: str
    cohort_date: str  # YYYY-MM-DD
    is_matured: bool
    
    # Unit taxonomy
    q_ordered: int
    q_removed: int
    q_cancelled: int
    q_shipped: int
    q_refunded: int
    q_restocked: int
    q_not_restocked: int
    q_lost_returns: int
    q_kept: int
    q_physical_returns: int
    
    # Revenue ($ Decimal)
    gross_line: Decimal
    disc_line: Decimal
    net_billed: Decimal
    refund_item: Decimal
    goodwill: Decimal
    retained_rev: Decimal
    
    # Cost & Valuation
    cost_snapshot: Optional[Decimal]
    cogs_state: CogsState
    cogs_tier: EvidenceTier
    cogs_lost: Decimal
    cogs_unresolved: Decimal
    
    # Allocated operational costs ($ Decimal)
    carrier_cost_allocated: Decimal
    shipping_charged_allocated: Decimal
    outbound: Decimal
    outbound_tier: EvidenceTier
    
    pay_fees: Decimal
    pay_fees_tier: EvidenceTier
    
    return_ship: Decimal
    return_ship_tier: EvidenceTier
    
    handling: Decimal
    handling_tier: EvidenceTier
    
    packaging: Decimal
    packaging_tier: EvidenceTier
    
    total_costs: Decimal
    contribution: Decimal
    
    # Metadata & Flags
    flags: List[str] = field(default_factory=list)
    line_weight_kg: Optional[Decimal] = None


@dataclass
class VariantMetric:
    """Rollup grain: variant_id per evaluation window."""
    variant_id: str
    product_id: Optional[str]
    sku: Optional[str]
    title: str
    category: str
    window_days: int
    as_of: str
    
    # Aggregated units (ratio of sums, across all lines)
    q_ordered: int = 0
    q_shipped: int = 0
    q_refunded: int = 0
    q_restocked: int = 0
    q_not_restocked: int = 0
    q_kept: int = 0
    return_rate: Optional[Decimal] = None
    
    # Revenue conservation ($ Decimal)
    revenue_total: Decimal = Decimal("0.00")
    revenue_scored: Decimal = Decimal("0.00")
    revenue_quarantined: Decimal = Decimal("0.00")
    cost_unknown_share: Decimal = Decimal("0.00")
    
    # Financial metrics (Scored lines only)
    retained_rev: Decimal = Decimal("0.00")
    cogs_lost: Decimal = Decimal("0.00")
    outbound: Decimal = Decimal("0.00")
    pay_fees: Decimal = Decimal("0.00")
    return_ship: Decimal = Decimal("0.00")
    handling: Decimal = Decimal("0.00")
    packaging: Decimal = Decimal("0.00")
    total_costs: Decimal = Decimal("0.00")
    contribution: Decimal = Decimal("0.00")
    
    margin_pct: Optional[Decimal] = None
    score: Optional[Decimal] = None
    
    naive_profit: Decimal = Decimal("0.00")
    hidden_leakage: Decimal = Decimal("0.00")
    estimated_share: Decimal = Decimal("0.00")
    
    status: VariantStatus = VariantStatus.HEALTHY
    is_provisional: bool = False
    is_low_confidence: bool = False
    config_hash: str = ""
    api_version: str = "2024-10"
    formula_version: str = "v2.0"
