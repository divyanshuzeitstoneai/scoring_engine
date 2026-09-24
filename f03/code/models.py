"""
Data models for Formula F03 (Margin Floor Breach) — Granular 25-Step Specification.
Enforces exact Decimal arithmetic at line-item, shipping, order, and cohort levels.
"""

from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EvaluabilityStatus(str, Enum):
    EVALUATED_CONFIRMED = "EVALUATED_CONFIRMED"
    EVALUATED_ESTIMATED = "EVALUATED_ESTIMATED"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    EXCLUDED_PROMOTIONAL = "EXCLUDED_PROMOTIONAL"
    FILTERED_NO_CASH = "FILTERED_NO_CASH"
    FILTERED_TEST_ORDER = "FILTERED_TEST_ORDER"


class LineItemGranular(BaseModel):
    """
    Granular Line-Item Economic Fields (Steps 1 through 14).
    Grain: LineItem
    """
    line_item_id: str
    sku: Optional[str] = None
    title: Optional[str] = None
    quantity: int
    
    # Steps 1–5: Price and Discounts
    original_price_i: Decimal = Decimal("0.00")       # Step 1: Pre-discount base selling price (shopMoney)
    line_discount_i: Decimal = Decimal("0.00")        # Step 2: Line-specific discount allocations only
    cart_discount_i: Decimal = Decimal("0.00")        # Step 3: Allocated order-wide cart coupons
    total_discount_i: Decimal = Decimal("0.00")       # Step 4: LineDiscount + CartDiscount
    discounted_price_i: Decimal = Decimal("0.00")     # Step 5: OriginalPrice - TotalDiscount
    
    # Steps 6–7: Tax Adjustment & Net Selling Price
    tax_adjustment_i: Decimal = Decimal("0.00")       # Step 6: Sale-time statutory tax embedded in price
    net_selling_price_i: Decimal = Decimal("0.00")    # Step 7: DiscountedPrice - TaxAdjustment
    
    # Steps 8–9: Net Refund & Post-Refund Net Revenue
    refunded_gross_amount_i: Decimal = Decimal("0.00") # Raw refund amount customer received
    refunded_tax_i: Decimal = Decimal("0.00")          # Statutory tax portion of customer refund
    net_refund_i: Decimal = Decimal("0.00")           # Step 8: RefundedGross - RefundedTax
    net_revenue_i: Decimal = Decimal("0.00")          # Step 9: NetSellingPrice - NetRefund
    
    # Steps 10–14: Cost and Line Gross Profit
    unit_cogs_i: Optional[Decimal] = None             # Step 10: Resolved supplier unit cost
    cogs_source_tier: str = "Tier 4 (Unresolved)"     # Snapshot / Live / BOM / Unresolved
    is_cogs_missing: bool = False
    is_bundle: bool = False
    unrecovered_qty_i: int = 0                        # Step 11: Ordered - Restocked
    unrecovered_cogs_i: Decimal = Decimal("0.00")     # Step 12: UnitCOGS * UnrecoveredQty
    gross_profit_i: Decimal = Decimal("0.00")         # Step 13: NetRevenue - UnrecoveredCOGS

    class Config:
        arbitrary_types_allowed = True


class OrderShippingGranular(BaseModel):
    """
    Granular Shipping Economics (Steps 15 through 18).
    Grain: Order
    """
    gross_shipping_revenue: Decimal = Decimal("0.00")   # Step 15: Customer-paid shipping charge
    shipping_tax_adjustment: Decimal = Decimal("0.00")  # Step 16: Statutory tax embedded in shipping price
    refunded_shipping_gross: Decimal = Decimal("0.00")  # Gross shipping cash returned to customer
    refunded_shipping_tax: Decimal = Decimal("0.00")    # Tax component of refunded shipping
    net_shipping_refund: Decimal = Decimal("0.00")      # Step 17: RefundedShippingGross - RefundedShippingTax
    net_shipping_revenue: Decimal = Decimal("0.00")     # Step 18: GrossShipping - ShippingTax - NetShippingRefund

    class Config:
        arbitrary_types_allowed = True


class F03OrderEvaluation(BaseModel):
    """
    Comprehensive Order Evaluation Model.
    Enforces Steps 19 through 25 and stores all granular sub-components.
    """
    order_id: str
    order_name: str
    processed_at: str
    cancelled_at: Optional[str] = None
    financial_status: str
    currency_code: str
    taxes_included: bool
    test: bool = False
    
    # Granular Line-Items and Shipping
    line_items: List[LineItemGranular] = Field(default_factory=list)
    shipping_economics: OrderShippingGranular = Field(default_factory=OrderShippingGranular)
    
    # Step 14: Sum of Line Gross Profits
    order_gross_profit: Decimal = Decimal("0.00")
    
    # Step 19: Cash Inflow
    gross_merchandise_cash: Decimal = Decimal("0.00")     # Sum of discounted_price_i
    tax_liability_deducted: Decimal = Decimal("0.00")     # Sum of tax_adjustment_i
    shipping_revenue_collected: Decimal = Decimal("0.00") # Equals net_shipping_revenue (Step 18)
    refunded_cash_total: Decimal = Decimal("0.00")        # Sum of net_refund_i + net_shipping_refund
    net_cash_in: Decimal = Decimal("0.00")                # Step 19: Sum(net_revenue_i) + net_shipping_revenue
    
    # Steps 20–22: Operational Outflow
    unrecovered_cogs: Decimal = Decimal("0.00")           # Step 12 sum: Sum(unrecovered_cogs_i)
    outbound_shipping_cost: Decimal = Decimal("0.00")     # Step 20: Carrier freight expense
    gateway_retained_fee: Decimal = Decimal("0.00")       # Step 21: Non-refundable processor fee
    operational_costs: Decimal = Decimal("0.00")          # Step 22: OutboundShipping + GatewayFee
    net_cash_out: Decimal = Decimal("0.00")               # UnrecoveredCOGS + OperationalCosts
    
    # Steps 23–25: Margin Floor Breach & Loss
    net_margin_cash: Decimal = Decimal("0.00")            # Step 23: CashIn - NetCashOut
    f03_breach: bool = False                              # Step 24: NetMarginCash < 0.00
    f03_loss: Decimal = Decimal("0.00")                   # Step 25: abs(NetMarginCash) if breach else 0.00
    
    # Loss Categorization
    is_merchandise_loss: bool = False
    is_fulfillment_induced_loss: bool = False
    
    # Evaluability & Audit Flags
    evaluability_status: EvaluabilityStatus = EvaluabilityStatus.NOT_EVALUABLE
    is_shipping_cost_estimated: bool = False
    is_gateway_fee_estimated: bool = False
    is_cogs_missing: bool = False
    is_bundle: bool = False
    flags: List[str] = Field(default_factory=list)
    
    # Timezone Rollup Fields (BUG 7)
    rollup_date_utc: str = ""
    rollup_date_shop_tz: str = ""
    shop_timezone: str = "UTC"
    
    # Standardized Currency Equivalents (USD Base)
    usd_fx_rate: Decimal = Decimal("1.0")
    net_cash_in_usd: Decimal = Decimal("0.00")
    net_cash_out_usd: Decimal = Decimal("0.00")
    net_margin_cash_usd: Decimal = Decimal("0.00")
    f03_loss_usd: Decimal = Decimal("0.00")

    class Config:
        arbitrary_types_allowed = True
