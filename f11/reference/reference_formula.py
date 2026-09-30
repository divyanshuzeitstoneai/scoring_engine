"""
Reference Implementation for Formula F11 Order Profitability v2.1.
Written strictly and independently from the specification text.
Operates on integer minor units (e.g. cents). No floats in the financial math.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class LineResult:
    line_id: str
    sku: str
    q0: int
    qc: int
    qs: int
    unit_price: int
    gross: int
    discounts: int
    embedded_tax: int
    net_revenue: int
    unit_cost: Optional[int]
    cogs: Optional[int]
    is_gift_card: bool
    requires_shipping: bool
    cost_status: str


@dataclass
class OrderProfitResult:
    order_id: str
    order_name: str
    as_of: str
    currency: str
    currency_exponent: int
    
    # Financial components (integer minor units)
    L: int                  # List merchandise revenue
    D: int                  # Total discounts
    R: int                  # Net merchandise revenue
    Sc: int                 # Shipping collected (net of embedded tax)
    C: int                  # Total commercial inflow (R + Sc)
    COGS: Optional[int]     # Cost of Goods Sold
    S: Optional[int]        # Shipping / logistics cost
    G: Optional[int]        # Gateway processing fees
    E: int                  # Refund & return cost / provision
    O: int                  # Operational overhead & packaging
    
    P: Optional[int]        # Net contribution profit
    P_upper: int            # Upper bound profit without unmeasured costs
    
    # Ratios and metrics
    margin: Optional[Decimal]
    is_zero_revenue: bool
    
    # Classifications and tags
    classification: str     # profitable, breakeven, unprofitable, excluded
    band: str               # high, acceptable, at_risk, cash_drain, zero_revenue, excluded
    lane: str               # MEASURED, ESTIMATED, CONFIRMED_LOSS, UNDETERMINED, EXCLUDED
    exclusion_reason: Optional[str]
    
    component_tags: Dict[str, str] # component -> measured | structural | estimated | missing
    measured_share: Decimal
    cogs_basis: str
    flags: List[str]
    
    # Driver decomposition
    drivers: Dict[str, Any]
    top_loss_driver: Optional[str]
    
    # Delta view (as-sold vs current)
    P_asold: Optional[int]
    delta_profit: Optional[int]
    delta_cause: Optional[str]

    @property
    def class_(self) -> str:
        return self.classification

    def __getitem__(self, item: str) -> Any:
        if item == "class":
            return self.classification
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_dict(self) -> Dict[str, Any]:
        d = {k: getattr(self, k) for k in self.__dataclass_fields__}
        d["class"] = self.classification
        return d


def parse_iso_datetime(dt_str: str) -> datetime:
    if not dt_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    clean_str = dt_str.replace("Z", "+00:00")
    return datetime.fromisoformat(clean_str)


def round_minor(val: Decimal, mode: str = "half_up") -> int:
    round_rule = ROUND_HALF_EVEN if mode == "half_even" else ROUND_HALF_UP
    return int(val.quantize(Decimal("1"), rounding=round_rule))


def evaluate_order_reference(
    order: Dict[str, Any],
    config: Dict[str, Any]
) -> OrderProfitResult:
    order_id = order.get("id", "")
    order_name = order.get("name", "")
    flags: List[str] = []
    
    # 0. Currency and Config Parameters
    currency = order.get("currencyCode", config.get("shop_currency", "USD"))
    if currency != config.get("shop_currency", "USD"):
        flags.append("CURRENCY_MISMATCH")
        return _make_excluded_result(order_id, order_name, currency, "CURRENCY_MISMATCH", flags, config)

    exp = config.get("currency_exponent", 2)
    as_of_dt = parse_iso_datetime(config.get("as_of", "2026-09-30T23:59:59Z"))
    rounding_mode = config.get("rounding_mode", "half_up")
    
    # Exclusion checks
    if order.get("test", False) and config.get("test_order_policy") == "exclude":
        return _make_excluded_result(order_id, order_name, currency, "TEST_ORDER", flags, config)
        
    fin_status = order.get("displayFinancialStatus", "")
    if fin_status in config.get("excluded_financial_statuses", []):
        return _make_excluded_result(order_id, order_name, currency, f"FINANCIAL_STATUS_{fin_status}", flags, config)
        
    cancelled_at = order.get("cancelledAt")
    if cancelled_at:
        ful_status = order.get("displayFulfillmentStatus", "")
        if ful_status != "FULFILLED" or config.get("cancelled_after_fulfillment_policy") == "exclude":
            return _make_excluded_result(order_id, order_name, currency, "CANCELLED", flags, config)

    # 1. Line Item Processing on Sold Basis (Amendment A1)
    raw_lines = order.get("lineItems", [])
    if isinstance(raw_lines, dict) and "edges" in raw_lines:
        raw_lines = [e.get("node", {}) for e in raw_lines["edges"]]

    refund_lines = order.get("refundLineItems", [])
    refund_qty_by_line: Dict[str, int] = {}
    for rfl in refund_lines:
        lid = rfl.get("lineItemId") or (rfl.get("lineItem", {}) or {}).get("id")
        if lid:
            refund_qty_by_line[lid] = refund_qty_by_line.get(lid, 0) + rfl.get("quantity", 0)

    # Also inspect refunds array
    for r in order.get("refunds", []):
        r_created = parse_iso_datetime(r.get("createdAt"))
        if r_created <= as_of_dt:
            sub_rfls = r.get("refundLineItems", [])
            if isinstance(sub_rfls, dict) and "edges" in sub_rfls:
                sub_rfls = [e.get("node", {}) for e in sub_rfls["edges"]]
            for rfl in sub_rfls:
                lid = rfl.get("lineItemId") or (rfl.get("lineItem", {}) or {}).get("id")
                if lid:
                    refund_qty_by_line[lid] = refund_qty_by_line.get(lid, 0) + rfl.get("quantity", 0)

    processed_lines: List[LineResult] = []
    has_missing_cogs = False
    cogs_basis = "snapshot"
    taxes_included = order.get("taxesIncluded", False)
    tot_embedded_tax = 0

    for li in raw_lines:
        lid = li.get("id", "")
        sku = li.get("sku", "") or ""
        q0 = li.get("quantity", 1)
        qc = li.get("currentQuantity", q0)
        ref_qty = refund_qty_by_line.get(lid, 0)
        
        # Derived removed quantity (qe)
        qe = max(0, q0 - qc - ref_qty)
        qs = max(0, q0 - qe)
        
        if q0 - qc - ref_qty < 0:
            flags.append("UNIT_BASIS_INCONSISTENT")

        # List unit price u
        u_str = (li.get("originalUnitPriceSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00")
        u = int(round_minor(Decimal(str(u_str)) * (10 ** exp), rounding_mode))
        
        is_gift_card = li.get("isGiftCard", False)
        is_tip = (li.get("title") or "").strip().lower() == "tip" or li.get("isTip", False)
        requires_shipping = li.get("requiresShipping", True)
        
        if is_gift_card or is_tip or qs == 0:
            # Excluded from merchandise revenue and cogs
            gross_l = 0
            disc_l = 0
            tax_l = 0
            net_l = 0
            cost_val = 0
            c_status = "excluded"
        else:
            gross_l = u * qs
            
            # Discounts
            disc_allocs = li.get("discountAllocations", [])
            tot_alloc = sum([
                int(round_minor(Decimal(str((da.get("allocatedAmountSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00"))) * (10 ** exp), rounding_mode))
                for da in disc_allocs
            ])
            # Prorate by qs / q0
            if q0 > 0 and qs < q0:
                disc_l = round_minor(Decimal(tot_alloc) * Decimal(qs) / Decimal(q0), rounding_mode)
            else:
                disc_l = tot_alloc
                
            # Embedded Tax
            tax_l = 0
            if taxes_included:
                # If statutory tax embedded
                tax_lines = li.get("taxLines", [])
                tot_tax_line = sum([
                    int(round_minor(Decimal(str((tl.get("priceSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00"))) * (10 ** exp), rounding_mode))
                    for tl in tax_lines
                ])
                tax_l = tot_tax_line
                tot_embedded_tax += tax_l
                
            net_l = gross_l - disc_l - tax_l
            
            # Unit Cost
            v = li.get("variant")
            if v is None and "variant" in li:
                flags.append("DELETED_VARIANT")
                cost_val = None
                c_status = "missing"
            elif not v or not v.get("inventoryItem"):
                if config.get("custom_line_cost_policy") == "missing":
                    cost_val = None
                    c_status = "missing"
                else:
                    cost_val = 0
                    c_status = "zero"
            else:
                inv = v.get("inventoryItem", {})
                uc_node = inv.get("unitCost")
                if uc_node is None or uc_node.get("amount") is None:
                    cost_val = None
                    c_status = "missing"
                else:
                    amt_str = uc_node.get("amount", "0.00")
                    uc_val = int(round_minor(Decimal(str(amt_str)) * (10 ** exp), rounding_mode))
                    if uc_val < 0:
                        flags.append("INVALID_COST")
                        return _make_excluded_result(order_id, order_name, currency, "INVALID_COST", flags, config)
                    elif uc_val == 0 and u > 0:
                        flags.append("SUSPECT_ZERO_COST")
                        if config.get("suspect_zero_cost_policy") == "treat_as_missing":
                            cost_val = None
                            c_status = "missing"
                        else:
                            cost_val = 0
                            c_status = "measured"
                    else:
                        cost_val = uc_val
                        c_status = "measured"
                        
            # Check cost drift
            if li.get("cogs_basis") == "restated_current_cost":
                cogs_basis = "restated_current_cost"

        cogs_l = (cost_val * qs) if cost_val is not None else None
        if cogs_l is None and qs > 0 and not is_gift_card:
            has_missing_cogs = True
            
        processed_lines.append(LineResult(
            line_id=lid,
            sku=sku,
            q0=q0,
            qc=qc,
            qs=qs,
            unit_price=u,
            gross=gross_l,
            discounts=disc_l,
            embedded_tax=tax_l,
            net_revenue=net_l,
            unit_cost=cost_val,
            cogs=cogs_l,
            is_gift_card=is_gift_card,
            requires_shipping=requires_shipping,
            cost_status=c_status
        ))

    L = sum([pl.gross for pl in processed_lines])
    D = sum([pl.discounts for pl in processed_lines])
    R = sum([pl.net_revenue for pl in processed_lines])
    
    if has_missing_cogs:
        COGS = None
        cogs_tag = "missing"
    else:
        COGS = sum([pl.cogs for pl in processed_lines if pl.cogs is not None])
        cogs_tag = "measured"

    # 2. Shipping Collected (Sc)
    ship_str = (order.get("currentShippingPriceSet", {}).get("shopMoney", {}) or {}).get("amount")
    if ship_str is None:
        ship_str = (order.get("totalShippingPriceSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00")
    Sc_raw = int(round_minor(Decimal(str(ship_str)) * (10 ** exp), rounding_mode))
    
    # Strip tax on shipping if inclusive
    if taxes_included and config.get("tax_shipping_included", False):
        Sc = int(round_minor(Decimal(Sc_raw) / Decimal("1.20"), rounding_mode))
    else:
        Sc = Sc_raw
        
    C = R + Sc

    # 3. Shipping Cost (S)
    metafields = order.get("metafields", {})
    actual_carrier_cost = order.get("actual_carrier_cost") or metafields.get("custom.actual_carrier_cost")
    all_digital = all([not pl.requires_shipping for pl in processed_lines])
    has_pickup_sl = any("pickup" in (sl.get("title") or "").lower() for sl in order.get("shippingLines", []))
    is_pickup = order.get("sourceName") == "pos" or "pickup" in (order.get("tags") or []) or has_pickup_sl
    
    if actual_carrier_cost is not None:
        S = int(round_minor(Decimal(str(actual_carrier_cost)) * (10 ** exp), rounding_mode))
        ship_tag = "measured"
    elif all_digital or is_pickup:
        S = 0
        ship_tag = "structural"
    elif config.get("shipping_rate_card"):
        # Rate card estimate
        rate_card = config["shipping_rate_card"].get("default_zone", {"base_cost": 650, "per_kg": 150})
        S = int(rate_card.get("base_cost", 650))
        ship_tag = "estimated"
    else:
        S = None
        ship_tag = "missing"

    # 4. Gateway Fees (G) (Amendment A2)
    txns = order.get("transactions", [])
    measured_fees: List[int] = []
    has_sp_txn = False
    has_non_sp_txn = False
    
    has_zero_fee_txn = False
    for tx in txns:
        gw = (tx.get("gateway") or "").lower()
        if "shopify_payments" in gw:
            has_sp_txn = True
            fees = tx.get("fees", [])
            for fee in fees:
                f_amt = (fee.get("amount", {}) or {}).get("amount", "0.00")
                measured_fees.append(int(round_minor(Decimal(str(f_amt)) * (10 ** exp), rounding_mode)))
        elif gw in config.get("zero_fee_gateways", []):
            has_zero_fee_txn = True
        else:
            has_non_sp_txn = True

    gateways = [gw.lower() for gw in order.get("paymentGatewayNames", [])]
    is_zero_fee_gw = any([gw in config.get("zero_fee_gateways", []) for gw in gateways]) or has_zero_fee_txn
    
    if C == 0 or is_zero_fee_gw:
        G = 0
        fee_tag = "structural"
    elif measured_fees:
        G = sum(measured_fees)
        fee_tag = "measured"
    elif has_sp_txn and not measured_fees:
        flags.append("FEE_ANOMALY")
        G = None
        fee_tag = "missing"
    elif has_non_sp_txn and config.get("gateway_fee_schedule"):
        # Estimate via schedule
        sched = config["gateway_fee_schedule"].get("paypal", {"rate": 0.029, "fixed": 30})
        rate = Decimal(str(sched.get("rate", 0.029)))
        fixed = int(sched.get("fixed", 30))
        # Total charged base (gross, including tax)
        tot_charged_val = (order.get("totalPriceSet", {}).get("shopMoney", {}) or {}).get("amount")
        if tot_charged_val is not None:
            tot_charged = int(round_minor(Decimal(str(tot_charged_val)) * (10 ** exp), rounding_mode))
        else:
            tot_charged = C + tot_embedded_tax + (Sc_raw - Sc)
        G = round_minor(Decimal(tot_charged) * rate, rounding_mode) + fixed
        fee_tag = "estimated"
    else:
        G = None
        fee_tag = "missing"

    # 5. Refunds, Returns & Provision (E) (Amendment A1, A5, I-8)
    order_processed_dt = parse_iso_datetime(order.get(config.get("window_start_event", "processedAt"), order.get("createdAt")))
    order_age_days = (as_of_dt - order_processed_dt).total_seconds() / 86400.0
    
    refunds_list = order.get("refunds", [])
    valid_refunds = [
        r for r in refunds_list
        if parse_iso_datetime(r.get("createdAt")) <= as_of_dt
    ]
    
    if valid_refunds:
        # Realized refund replaces provision completely
        E_tot = 0
        for r in valid_refunds:
            tot_ref_str = (r.get("totalRefundedSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00")
            r_amt = int(round_minor(Decimal(str(tot_ref_str)) * (10 ** exp), rounding_mode))
            
            # Check recovered COGS on restock
            recovered_cogs = 0
            sub_rfls = r.get("refundLineItems", [])
            if isinstance(sub_rfls, dict) and "edges" in sub_rfls:
                sub_rfls = [e.get("node", {}) for e in sub_rfls["edges"]]
            for rfl in sub_rfls:
                if rfl.get("restockType") == "RESTOCK" or rfl.get("restocked", False):
                    lid = rfl.get("lineItemId") or (rfl.get("lineItem", {}) or {}).get("id")
                    match_line = next((pl for pl in processed_lines if pl.line_id == lid), None)
                    if match_line and match_line.unit_cost:
                        recovered_cogs += match_line.unit_cost * rfl.get("quantity", 1)
                        
            return_ship = int(round_minor(Decimal(str(r.get("return_shipping_cost") or r.get("return_label_cost") or order.get("return_shipping_cost") or order.get("return_label_cost") or 0)) * (10 ** exp), rounding_mode))
            handling = int(round_minor(Decimal(str(r.get("restock_handling_fee") or order.get("restock_handling_fee") or 0)) * (10 ** exp), rounding_mode))
            
            E_tot += (r_amt - recovered_cogs + return_ship + handling)
            
        E = E_tot
        refund_tag = "measured"
    else:
        # Window evaluation
        ref_window = config.get("refund_window_days", {}).get("Default", 30)
        if order_age_days < ref_window:
            # Open window: estimated provision
            prov_rate = Decimal(str(config.get("refund_provision_rate", {}).get("Default", 0.05)))
            E = round_minor(Decimal(R) * prov_rate, rounding_mode)
            refund_tag = "estimated"
        else:
            # Closed window: 0 measured
            E = 0
            refund_tag = "measured"

    # 6. Operational Overhead (O)
    packaging = config.get("packaging_cost", 0)
    O = packaging if not all_digital else 0
    other_tag = "measured" if O > 0 else "structural"

    # 7. Upper Bound Profit (P_upper) and Final Profit (P)
    # P_upper = C - sum(measured and structural costs only)
    known_cogs = sum([pl.cogs for pl in processed_lines if pl.cogs is not None and pl.cogs > 0])
    known_deductions = 0
    if COGS is not None:
        known_deductions += COGS
    elif known_cogs > 0:
        known_deductions += known_cogs
    if ship_tag in ["measured", "structural"] and S is not None:
        known_deductions += S
    if fee_tag in ["measured", "structural"] and G is not None:
        known_deductions += G
    if refund_tag in ["measured", "structural"]:
        known_deductions += E
    if other_tag in ["measured", "structural"]:
        known_deductions += O
        
    P_upper = C - known_deductions

    # True P calculation
    has_missing = any([tag == "missing" for tag in [cogs_tag, ship_tag, fee_tag]])
    has_estimated = any([tag == "estimated" for tag in [cogs_tag, ship_tag, fee_tag, refund_tag]])
    
    if has_missing:
        P = None
    else:
        P = C - (COGS or 0) - (S or 0) - (G or 0) - E - O

    # 8. Lane Determination (Section 5.3 & 15.4)
    if not has_missing and not has_estimated:
        lane = "MEASURED"
    elif P_upper < 0:
        lane = "CONFIRMED_LOSS"
    elif has_missing:
        lane = "UNDETERMINED"
    else:
        lane = "ESTIMATED"

    # Measured Share
    all_known_costs = []
    if COGS is not None: all_known_costs.append((COGS, cogs_tag))
    if S is not None: all_known_costs.append((S, ship_tag))
    if G is not None: all_known_costs.append((G, fee_tag))
    all_known_costs.append((E, refund_tag))
    if O > 0: all_known_costs.append((O, other_tag))
    
    tot_cost = sum([amt for amt, _ in all_known_costs])
    meas_cost = sum([amt for amt, tag in all_known_costs if tag in ["measured", "structural"]])
    measured_share = (Decimal(meas_cost) / Decimal(tot_cost)).quantize(Decimal("0.0001")) if tot_cost > 0 else Decimal("1.0000")

    # 9. Margin & Band Classification (Amendment A4, A8, Section 15.5)
    is_zero_revenue = (C == 0)
    if is_zero_revenue or P is None:
        margin = None
    else:
        margin = (Decimal(P) / Decimal(C) * Decimal("100")).quantize(Decimal("0.0001"))

    # Classification
    if P is None:
        if lane == "CONFIRMED_LOSS":
            classification = "unprofitable"
        else:
            classification = "undetermined"
    elif P > 0:
        classification = "profitable"
    elif P == 0:
        classification = "breakeven"
    else:
        classification = "unprofitable"

    # Band (Integer cross-multiplication P * 100 >= t * C)
    thresholds = config.get("band_thresholds", {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0})
    t_high = int(thresholds.get("high", 30.0))
    t_acc = int(thresholds.get("acceptable", 10.0))
    
    if is_zero_revenue:
        band = "zero_revenue"
    elif P is None:
        band = "cash_drain" if lane == "CONFIRMED_LOSS" else "undetermined"
    elif P < 0:
        band = "cash_drain"
    elif P == 0:
        band = "at_risk"
    elif P * 100 >= t_high * C:
        band = "high"
    elif P * 100 >= t_acc * C:
        band = "acceptable"
    else:
        band = "at_risk"

    # 10. Driver Decomposition (Section 5.5, 15.7)
    prod_margin_at_list = (L - (COGS or 0)) if COGS is not None else "unknown"
    disc_leak = -D
    ship_net = (Sc - S) if S is not None else "unknown"
    fee_leak = -G if G is not None else "unknown"
    ref_leak = -E
    oth_leak = -O
    
    drivers = {
        "product_margin_at_list": prod_margin_at_list,
        "discount_leak": disc_leak,
        "shipping_net": ship_net,
        "fee_leak": fee_leak,
        "refund_leak": ref_leak,
        "other_leak": oth_leak
    }

    # Top Loss Driver (tie-break order: shipping_subsidy, discount_leak, fee_leak, refund_leak, other_leak)
    top_driver = None
    if classification == "unprofitable" or band == "cash_drain":
        leak_candidates = []
        if isinstance(ship_net, int) and ship_net < 0:
            leak_candidates.append((-ship_net, 1, "shipping_subsidy"))
        if D > 0:
            leak_candidates.append((D, 2, "discount_leak"))
        if isinstance(G, int) and G > 0:
            leak_candidates.append((G, 3, "fee_leak"))
        if E > 0:
            leak_candidates.append((E, 4, "refund_leak"))
        if O > 0:
            leak_candidates.append((O, 5, "other_leak"))
            
        if leak_candidates:
            leak_candidates.sort(key=lambda x: (-x[0], x[1]))
            top_driver = leak_candidates[0][2]

    # Delta view
    P_asold = C - (COGS or 0) - (S or 0) - (G or 0) - round_minor(Decimal(R) * Decimal("0.05"), rounding_mode) - O if not has_missing else None
    delta_profit = (P - P_asold) if (P is not None and P_asold is not None) else None
    delta_cause = "refund" if valid_refunds else ("edit" if any(pl.q0 > pl.qc for pl in processed_lines) else None)

    return OrderProfitResult(
        order_id=order_id,
        order_name=order_name,
        as_of=config.get("as_of", "2026-09-30T23:59:59Z"),
        currency=currency,
        currency_exponent=exp,
        L=L,
        D=D,
        R=R,
        Sc=Sc,
        C=C,
        COGS=COGS,
        S=S,
        G=G,
        E=E,
        O=O,
        P=P,
        P_upper=P_upper,
        margin=margin,
        is_zero_revenue=is_zero_revenue,
        classification=classification,
        band=band,
        lane=lane,
        exclusion_reason=None,
        component_tags={
            "cogs": cogs_tag,
            "shipping": ship_tag,
            "gateway": fee_tag,
            "refund": refund_tag,
            "other": other_tag
        },
        measured_share=measured_share,
        cogs_basis=cogs_basis,
        flags=flags,
        drivers=drivers,
        top_loss_driver=top_driver,
        P_asold=P_asold,
        delta_profit=delta_profit,
        delta_cause=delta_cause
    )


def _make_excluded_result(
    order_id: str,
    order_name: str,
    currency: str,
    reason: str,
    flags: List[str],
    config: Dict[str, Any]
) -> OrderProfitResult:
    return OrderProfitResult(
        order_id=order_id,
        order_name=order_name,
        as_of=config.get("as_of", "2026-09-30T23:59:59Z"),
        currency=currency,
        currency_exponent=config.get("currency_exponent", 2),
        L=0, D=0, R=0, Sc=0, C=0,
        COGS=0, S=0, G=0, E=0, O=0,
        P=0, P_upper=0,
        margin=None,
        is_zero_revenue=True,
        classification="excluded",
        band="excluded",
        lane="EXCLUDED",
        exclusion_reason=reason,
        component_tags={
            "cogs": "structural",
            "shipping": "structural",
            "gateway": "structural",
            "refund": "structural",
            "other": "structural"
        },
        measured_share=Decimal("1.0000"),
        cogs_basis="none",
        flags=flags,
        drivers={},
        top_loss_driver=None,
        P_asold=0,
        delta_profit=0,
        delta_cause=None
    )
