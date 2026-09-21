"""
Formula F01 Discount Leakage - Evaluation Output Models and Audit Lineage Types.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from core.fallbacks.cogs import CogsSource
from core.fallbacks.margin import TargetMarginSource

InputConfidence = Literal["real", "estimated", "storewide_fallback", "quarantined"]
OrderStatus = Literal["evaluated", "excluded", "quarantined"]
HealthBand = Literal["Healthy", "Warning", "Critical"]

@dataclass
class LineItemEvaluation:
    """
    Evaluated result for a single line item, containing all required audit fields
    for full lineage tracking, discount mechanism separation, pre-vs-post promotion margin,
    inherent COGS deficit separation, and auditability.
    """
    order_id: int
    line_item_id: int
    sku: Optional[str]
    variant_id: Optional[int]
    quantity: int
    active_quantity: int
    original_price: float
    original_line_value: float          # Baseline / pre-promotion gross revenue
    discounted_unit_price: float
    line_discount_amount: float
    line_discount_percentage: float
    order_discount_allocation: float
    total_discount_amount: float
    discount_percentage: float
    discount_code: Optional[str]
    discount_type: str
    net_selling_price: float
    net_revenue: float
    cogs_used: float
    total_cogs: float
    cogs_source: CogsSource
    is_cogs_estimated: bool
    target_margin_used: float
    target_margin_source: TargetMarginSource
    is_target_margin_estimated: bool
    target_profit: float                # Target Minimum Profit: original_line_value * target_margin_used
    baseline_gross_profit: float        # Baseline Pre-Promotion Profit: original_line_value - total_cogs
    actual_gross_profit: float          # Realized Post-Promotion Profit: net_revenue - total_cogs
    inherent_cogs_deficit: float        # Pre-existing deficit: max(0, target_profit - baseline_gross_profit)
    total_target_shortfall: float       # Total gap: max(0, target_profit - actual_gross_profit)
    f01_flagged: bool                   # True if incremental promotional loss > 0
    f01_dollar_loss: float              # Incremental Promotional Leakage: total_target_shortfall - inherent_cogs_deficit
    leakage_reason: str                 # Reason classification
    input_confidence: InputConfidence
    quarantine_reason: Optional[str] = None
    cash_refund_allocated: float = 0.0

@dataclass
class OrderEvaluation:
    """
    Evaluated result for an entire order under Formula F01.
    Strictly isolates F01 promotional margin leakage from F03 operational cash contribution.
    """
    order_id: int
    status: OrderStatus
    is_discounted: bool
    exclusion_reason: Optional[str] = None
    total_original_value: float = 0.0
    total_net_revenue: float = 0.0
    total_discounts: float = 0.0
    cash_refund: float = 0.0
    total_cogs: float = 0.0
    target_minimum_profit: float = 0.0
    baseline_gross_profit: float = 0.0
    actual_gross_profit: float = 0.0
    inherent_cogs_deficit: float = 0.0
    total_target_shortfall: float = 0.0
    f01_flagged: bool = False
    f01_dollar_loss: float = 0.0        # Canonical: sum of line-level f01_dollar_loss
    negative_gross_profit: bool = False # Product-level gross loss (actual_gross_profit < 0)
    
    # Explicit F03 Operational Cash Partitioning Fields
    shipping_revenue_collected: float = 0.0
    carrier_shipping_cost: Optional[float] = None
    gateway_processing_fee: Optional[float] = None
    other_f03_costs: float = 0.0
    actual_cash_contribution: Optional[float] = None
    f03_escalation_status: str = "unable_to_determine" # "escalated", "not_escalated", "unable_to_determine"
    f03_escalation_reason: str = "missing_f03_operational_cost_data"
    
    input_confidence: InputConfidence = "real"
    line_items: List[LineItemEvaluation] = field(default_factory=list)
    quarantine_reason: Optional[str] = None

@dataclass
class BatchEvaluationResult:
    """
    Aggregate evaluation summary across an entire batch of Shopify orders for F01.
    """
    total_orders_received: int
    total_unique_orders: int
    duplicate_payloads_dropped: int
    evaluated_orders: int
    quarantined_orders: int
    excluded_orders: int
    failed_orders: int
    f01_score: float
    health_band: HealthBand
    total_target_profit: float
    total_baseline_profit: float
    total_actual_profit: float
    total_inherent_deficit: float
    total_target_shortfall: float
    total_dollar_loss: float            # Canonical: sum of line-level incremental promotional leakage
    count_based_score: float
    healthy_discounted_orders: int
    leaking_discounted_orders: int
    negative_gross_profit_orders: int
    positive_gp_leaking_orders: int
    
    # Confirmed vs Estimated Breakdown
    confirmed_target_profit: float
    estimated_target_profit: float
    confirmed_actual_profit: float
    estimated_actual_profit: float
    confirmed_promotional_loss: float
    estimated_promotional_loss: float
    
    # Distribution Statistics
    order_leakage_stats: Dict[str, float]
    line_leakage_stats: Dict[str, float]
    
    # Reconciliation Counters
    cogs_waterfall_counts: Dict[str, int]
    target_margin_source_counts: Dict[str, int]
    confidence_counts: Dict[str, int]
    leakage_reason_counts: Dict[str, int]
    f03_escalation_counts: Dict[str, int]
    order_evaluations: List[OrderEvaluation] = field(default_factory=list)
    historical_margin_index: Optional[Any] = None
