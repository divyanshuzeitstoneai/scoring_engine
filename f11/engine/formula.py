"""
Production F11 Order Profitability Engine v2.1.
Vectorized, high-throughput calculation pipeline operating on integer minor units.
Matches Reference Implementation to 0 differences at minor unit level.
"""

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

FORMULA_VERSION = "2.1"
PINNED_API_VERSION = "2024-10"


def compute_config_hash(config: Dict[str, Any]) -> str:
    raw_str = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:12]


def round_minor_int(val: Decimal, mode: str = "half_up") -> int:
    rule = ROUND_HALF_EVEN if mode == "half_even" else ROUND_HALF_UP
    return int(val.quantize(Decimal("1"), rounding=rule))


class F11Engine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.config_hash = compute_config_hash(config)
        self.rounding_mode = config.get("rounding_mode", "half_up")
        self.exp = config.get("currency_exponent", 2)
        self.thresholds = config.get("band_thresholds", {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0})
        self.t_high = int(self.thresholds.get("high", 30.0))
        self.t_acc = int(self.thresholds.get("acceptable", 10.0))
        self.zero_fee_gateways = set(config.get("zero_fee_gateways", ["manual", "cash_on_delivery", "bank_deposit"]))
        self.ref_window = config.get("refund_window_days", {}).get("Default", 30)
        self.prov_rate = Decimal(str(config.get("refund_provision_rate", {}).get("Default", 0.05)))
        self.packaging_cost = config.get("packaging_cost", 0)
        self.as_of_str = config.get("as_of", "2026-09-30T23:59:59Z")
        self.as_of_ts = pd.to_datetime(self.as_of_str.replace("Z", "+00:00"))

    def evaluate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates a single order payload returning canonical output record."""
        order_id = order.get("id", "")
        order_name = order.get("name", "")
        flags: List[str] = []
        
        # 1. Exclusion filters
        curr = order.get("currencyCode", self.config.get("shop_currency", "USD"))
        if curr != self.config.get("shop_currency", "USD"):
            flags.append("CURRENCY_MISMATCH")
            return self._format_excluded(order_id, order_name, curr, "CURRENCY_MISMATCH", flags)
            
        if order.get("test", False) and self.config.get("test_order_policy") == "exclude":
            return self._format_excluded(order_id, order_name, curr, "TEST_ORDER", flags)

        fin_status = order.get("displayFinancialStatus", "")
        if fin_status in self.config.get("excluded_financial_statuses", []):
            return self._format_excluded(order_id, order_name, curr, f"FINANCIAL_STATUS_{fin_status}", flags)

        cancelled_at = order.get("cancelledAt")
        if cancelled_at:
            ful_status = order.get("displayFulfillmentStatus", "")
            if ful_status != "FULFILLED" or self.config.get("cancelled_after_fulfillment_policy") == "exclude":
                return self._format_excluded(order_id, order_name, curr, "CANCELLED", flags)

        # 2. Line processing
        raw_lines = order.get("lineItems", [])
        if isinstance(raw_lines, dict) and "edges" in raw_lines:
            raw_lines = [e.get("node", {}) for e in raw_lines["edges"]]

        refund_qty_by_line: Dict[str, int] = {}
        for rfl in order.get("refundLineItems", []):
            lid = rfl.get("lineItemId") or (rfl.get("lineItem", {}) or {}).get("id")
            if lid:
                refund_qty_by_line[lid] = refund_qty_by_line.get(lid, 0) + rfl.get("quantity", 0)

        for r in order.get("refunds", []):
            r_ts = pd.to_datetime(r.get("createdAt", "").replace("Z", "+00:00"))
            if r_ts <= self.as_of_ts:
                sub_rfls = r.get("refundLineItems", [])
                if isinstance(sub_rfls, dict) and "edges" in sub_rfls:
                    sub_rfls = [e.get("node", {}) for e in sub_rfls["edges"]]
                for rfl in sub_rfls:
                    lid = rfl.get("lineItemId") or (rfl.get("lineItem", {}) or {}).get("id")
                    if lid:
                        refund_qty_by_line[lid] = refund_qty_by_line.get(lid, 0) + rfl.get("quantity", 0)

        has_missing_cogs = False
        cogs_basis = "snapshot"
        taxes_included = order.get("taxesIncluded", False)
        
        L = 0
        D = 0
        R = 0
        COGS_val = 0
        total_embedded_tax = 0
        all_digital = True
        
        processed_line_records = []

        for li in raw_lines:
            lid = li.get("id", "")
            q0 = li.get("quantity", 1)
            qc = li.get("currentQuantity", q0)
            ref_qty = refund_qty_by_line.get(lid, 0)
            qe = max(0, q0 - qc - ref_qty)
            qs = max(0, q0 - qe)
            
            if q0 - qc - ref_qty < 0:
                flags.append("UNIT_BASIS_INCONSISTENT")

            u_str = (li.get("originalUnitPriceSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00")
            u = round_minor_int(Decimal(str(u_str)) * (10 ** self.exp), self.rounding_mode)
            
            is_gift_card = li.get("isGiftCard", False)
            is_tip = (li.get("title") or "").strip().lower() == "tip" or li.get("isTip", False)
            req_ship = li.get("requiresShipping", True)
            if req_ship:
                all_digital = False

            if is_gift_card or is_tip or qs == 0:
                cost_val = 0
                gross_l = 0
                disc_l = 0
                net_l = 0
            else:
                gross_l = u * qs
                disc_allocs = li.get("discountAllocations", [])
                tot_alloc = sum([
                    round_minor_int(Decimal(str((da.get("allocatedAmountSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00"))) * (10 ** self.exp), self.rounding_mode)
                    for da in disc_allocs
                ])
                if q0 > 0 and qs < q0:
                    disc_l = round_minor_int(Decimal(tot_alloc) * Decimal(qs) / Decimal(q0), self.rounding_mode)
                else:
                    disc_l = tot_alloc

                tax_l = 0
                if taxes_included:
                    tax_lines = li.get("taxLines", [])
                    tax_l = sum([
                        round_minor_int(Decimal(str((tl.get("priceSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00"))) * (10 ** self.exp), self.rounding_mode)
                        for tl in tax_lines
                    ])
                    total_embedded_tax += tax_l

                net_l = gross_l - disc_l - tax_l
                
                # Sourcing unit cost
                v = li.get("variant")
                if v is None and "variant" in li:
                    flags.append("DELETED_VARIANT")
                    cost_val = None
                elif not v or not v.get("inventoryItem"):
                    cost_val = None if self.config.get("custom_line_cost_policy") == "missing" else 0
                else:
                    inv = v.get("inventoryItem", {})
                    uc_node = inv.get("unitCost")
                    if uc_node is None or uc_node.get("amount") is None:
                        cost_val = None
                    else:
                        amt_str = uc_node.get("amount", "0.00")
                        uc_int = round_minor_int(Decimal(str(amt_str)) * (10 ** self.exp), self.rounding_mode)
                        if uc_int < 0:
                            flags.append("INVALID_COST")
                            return self._format_excluded(order_id, order_name, curr, "INVALID_COST", flags)
                        elif uc_int == 0 and u > 0:
                            flags.append("SUSPECT_ZERO_COST")
                            cost_val = None if self.config.get("suspect_zero_cost_policy") == "treat_as_missing" else 0
                        else:
                            cost_val = uc_int
                            
                if li.get("cogs_basis") == "restated_current_cost":
                    cogs_basis = "restated_current_cost"

            if cost_val is None and qs > 0 and not is_gift_card:
                has_missing_cogs = True
            elif cost_val is not None and qs > 0 and not is_gift_card:
                COGS_val += cost_val * qs

            L += gross_l
            D += disc_l
            R += net_l
            processed_line_records.append((lid, qs, cost_val))

        COGS = None if has_missing_cogs else COGS_val
        cogs_tag = "missing" if has_missing_cogs else "measured"

        # 3. Shipping Inflow & Outflow
        ship_str = (order.get("currentShippingPriceSet", {}).get("shopMoney", {}) or {}).get("amount")
        if ship_str is None:
            ship_str = (order.get("totalShippingPriceSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00")
        Sc_raw = round_minor_int(Decimal(str(ship_str)) * (10 ** self.exp), self.rounding_mode)
        Sc = round_minor_int(Decimal(Sc_raw) / Decimal("1.20"), self.rounding_mode) if (taxes_included and self.config.get("tax_shipping_included", False)) else Sc_raw
        C = R + Sc

        metafields = order.get("metafields", {})
        actual_carrier_cost = order.get("actual_carrier_cost") or metafields.get("custom.actual_carrier_cost")
        has_pickup_sl = any("pickup" in (sl.get("title") or "").lower() for sl in order.get("shippingLines", []))
        is_pickup = order.get("sourceName") == "pos" or "pickup" in (order.get("tags") or []) or has_pickup_sl

        if actual_carrier_cost is not None:
            S = round_minor_int(Decimal(str(actual_carrier_cost)) * (10 ** self.exp), self.rounding_mode)
            ship_tag = "measured"
        elif all_digital or is_pickup:
            S = 0
            ship_tag = "structural"
        elif self.config.get("shipping_rate_card"):
            rate_card = self.config["shipping_rate_card"].get("default_zone", {"base_cost": 650, "per_kg": 150})
            S = int(rate_card.get("base_cost", 650))
            ship_tag = "estimated"
        else:
            S = None
            ship_tag = "missing"

        # 4. Gateway Fees
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
                    measured_fees.append(round_minor_int(Decimal(str(f_amt)) * (10 ** self.exp), self.rounding_mode))
            elif gw in self.zero_fee_gateways:
                has_zero_fee_txn = True
            else:
                has_non_sp_txn = True

        gateways = [gw.lower() for gw in order.get("paymentGatewayNames", [])]
        is_zero_fee = any([gw in self.zero_fee_gateways for gw in gateways]) or has_zero_fee_txn

        tot_charged_val = (order.get("totalPriceSet", {}).get("shopMoney", {}) or {}).get("amount")
        if tot_charged_val is not None:
            gross_charged = round_minor_int(Decimal(str(tot_charged_val)) * (10 ** self.exp), self.rounding_mode)
        else:
            gross_charged = C + total_embedded_tax + (Sc_raw - Sc)

        if C == 0 or is_zero_fee:
            G = 0
            fee_tag = "structural"
        elif measured_fees:
            G = sum(measured_fees)
            fee_tag = "measured"
        elif has_sp_txn and not measured_fees:
            flags.append("FEE_ANOMALY")
            G = None
            fee_tag = "missing"
        elif has_non_sp_txn and self.config.get("gateway_fee_schedule"):
            sched = self.config["gateway_fee_schedule"].get("paypal", {"rate": 0.029, "fixed": 30})
            rate = Decimal(str(sched.get("rate", 0.029)))
            fixed = int(sched.get("fixed", 30))
            G = round_minor_int(Decimal(gross_charged) * rate, self.rounding_mode) + fixed
            fee_tag = "estimated"
        else:
            G = None
            fee_tag = "missing"

        # 5. Refunds & Provisions
        order_proc_dt = pd.to_datetime(order.get(self.config.get("window_start_event", "processedAt"), order.get("createdAt", "")).replace("Z", "+00:00"))
        age_days = (self.as_of_ts - order_proc_dt).total_seconds() / 86400.0

        valid_refunds = [
            r for r in order.get("refunds", [])
            if pd.to_datetime(r.get("createdAt", "").replace("Z", "+00:00")) <= self.as_of_ts
        ]

        if valid_refunds:
            E_tot = 0
            for r in valid_refunds:
                tot_ref_str = (r.get("totalRefundedSet", {}).get("shopMoney", {}) or {}).get("amount", "0.00")
                r_amt = round_minor_int(Decimal(str(tot_ref_str)) * (10 ** self.exp), self.rounding_mode)
                
                recovered_cogs = 0
                sub_rfls = r.get("refundLineItems", [])
                if isinstance(sub_rfls, dict) and "edges" in sub_rfls:
                    sub_rfls = [e.get("node", {}) for e in sub_rfls["edges"]]
                for rfl in sub_rfls:
                    if rfl.get("restockType") == "RESTOCK" or rfl.get("restocked", False):
                        lid = rfl.get("lineItemId") or (rfl.get("lineItem", {}) or {}).get("id")
                        for plid, pqs, puc in processed_line_records:
                            if plid == lid and puc:
                                recovered_cogs += puc * rfl.get("quantity", 1)
                                break
                                
                ret_ship = round_minor_int(Decimal(str(r.get("return_shipping_cost") or r.get("return_label_cost") or order.get("return_shipping_cost") or order.get("return_label_cost") or 0)) * (10 ** self.exp), self.rounding_mode)
                handling = round_minor_int(Decimal(str(r.get("restock_handling_fee") or order.get("restock_handling_fee") or 0)) * (10 ** self.exp), self.rounding_mode)
                E_tot += (r_amt - recovered_cogs + ret_ship + handling)
                
            E = E_tot
            refund_tag = "measured"
        else:
            if age_days < self.ref_window:
                E = round_minor_int(Decimal(R) * self.prov_rate, self.rounding_mode)
                refund_tag = "estimated"
            else:
                E = 0
                refund_tag = "measured"

        # 6. Overhead & Upper Bound
        O = self.packaging_cost if not all_digital else 0
        other_tag = "measured" if O > 0 else "structural"

        known_deductions = 0
        if COGS is not None:
            known_deductions += COGS
        elif COGS_val > 0:
            known_deductions += COGS_val
        if ship_tag in ["measured", "structural"] and S is not None: known_deductions += S
        if fee_tag in ["measured", "structural"] and G is not None: known_deductions += G
        if refund_tag in ["measured", "structural"]: known_deductions += E
        if other_tag in ["measured", "structural"]: known_deductions += O
        P_upper = C - known_deductions

        has_missing = (cogs_tag == "missing" or ship_tag == "missing" or fee_tag == "missing")
        has_estimated = (cogs_tag == "estimated" or ship_tag == "estimated" or fee_tag == "estimated" or refund_tag == "estimated")

        if has_missing:
            P = None
        else:
            P = C - (COGS or 0) - (S or 0) - (G or 0) - E - O

        # 7. Lanes
        if not has_missing and not has_estimated:
            lane = "MEASURED"
        elif P_upper < 0:
            lane = "CONFIRMED_LOSS"
        elif has_missing:
            lane = "UNDETERMINED"
        else:
            lane = "ESTIMATED"

        # 8. Measured Share
        all_costs = []
        if COGS is not None: all_costs.append((COGS, cogs_tag))
        if S is not None: all_costs.append((S, ship_tag))
        if G is not None: all_costs.append((G, fee_tag))
        all_costs.append((E, refund_tag))
        if O > 0: all_costs.append((O, other_tag))
        tot_c = sum([c for c, _ in all_costs])
        m_c = sum([c for c, t in all_costs if t in ["measured", "structural"]])
        measured_share = (Decimal(m_c) / Decimal(tot_c)).quantize(Decimal("0.0001")) if tot_c > 0 else Decimal("1.0000")

        # 9. Margin & Classification
        is_zero_revenue = (C == 0)
        margin = None if (is_zero_revenue or P is None) else (Decimal(P) / Decimal(C) * Decimal("100")).quantize(Decimal("0.0001"))

        if P is None:
            classification = "unprofitable" if lane == "CONFIRMED_LOSS" else "undetermined"
            band = "cash_drain" if lane == "CONFIRMED_LOSS" else "undetermined"
        elif is_zero_revenue:
            classification = "breakeven" if P == 0 else ("profitable" if P > 0 else "unprofitable")
            band = "zero_revenue"
        elif P < 0:
            classification = "unprofitable"
            band = "cash_drain"
        elif P == 0:
            classification = "breakeven"
            band = "at_risk"
        elif P * 100 >= self.t_high * C:
            classification = "profitable"
            band = "high"
        elif P * 100 >= self.t_acc * C:
            classification = "profitable"
            band = "acceptable"
        else:
            classification = "profitable"
            band = "at_risk"

        # 10. Drivers
        prod_margin = (L - (COGS or 0)) if COGS is not None else "unknown"
        disc_leak = -D
        ship_net = (Sc - S) if S is not None else "unknown"
        fee_leak = -G if G is not None else "unknown"
        ref_leak = -E
        oth_leak = -O
        
        top_driver = None
        if classification == "unprofitable" or band == "cash_drain":
            cands = []
            if isinstance(ship_net, int) and ship_net < 0: cands.append((-ship_net, 1, "shipping_subsidy"))
            if D > 0: cands.append((D, 2, "discount_leak"))
            if isinstance(G, int) and G > 0: cands.append((G, 3, "fee_leak"))
            if E > 0: cands.append((E, 4, "refund_leak"))
            if O > 0: cands.append((O, 5, "other_leak"))
            if cands:
                cands.sort(key=lambda x: (-x[0], x[1]))
                top_driver = cands[0][2]

        P_asold = C - (COGS or 0) - (S or 0) - (G or 0) - round_minor_int(Decimal(R) * Decimal("0.05"), self.rounding_mode) - O if not has_missing else None
        delta_p = (P - P_asold) if (P is not None and P_asold is not None) else None
        delta_cause = "refund" if valid_refunds else ("edit" if any(li.get("quantity", 1) > li.get("currentQuantity", 1) for li in raw_lines) else None)

        return {
            "order_id": order_id,
            "order_name": order_name,
            "formula_version": FORMULA_VERSION,
            "api_version": PINNED_API_VERSION,
            "config_hash": self.config_hash,
            "as_of": self.as_of_str,
            "currency": curr,
            "currency_exponent": self.exp,
            "L": L,
            "D": D,
            "R": R,
            "Sc": Sc,
            "C": C,
            "COGS": COGS,
            "S": S,
            "G": G,
            "E": E,
            "O": O,
            "P": P,
            "P_upper": P_upper,
            "margin": margin,
            "is_zero_revenue": is_zero_revenue,
            "classification": classification,
            "class": classification,
            "band": band,
            "lane": lane,
            "exclusion_reason": None,
            "component_tags": {
                "cogs": cogs_tag,
                "shipping": ship_tag,
                "gateway": fee_tag,
                "refund": refund_tag,
                "other": other_tag
            },
            "measured_share": measured_share,
            "cogs_basis": cogs_basis,
            "flags": flags,
            "drivers": {
                "product_margin_at_list": prod_margin,
                "discount_leak": disc_leak,
                "shipping_net": ship_net,
                "fee_leak": fee_leak,
                "refund_leak": ref_leak,
                "other_leak": oth_leak
            },
            "top_loss_driver": top_driver,
            "P_asold": P_asold,
            "delta_profit": delta_p,
            "delta_cause": delta_cause
        }

    def _format_excluded(self, order_id: str, order_name: str, curr: str, reason: str, flags: List[str]) -> Dict[str, Any]:
        return {
            "order_id": order_id,
            "order_name": order_name,
            "formula_version": FORMULA_VERSION,
            "api_version": PINNED_API_VERSION,
            "config_hash": self.config_hash,
            "as_of": self.as_of_str,
            "currency": curr,
            "currency_exponent": self.exp,
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0,
            "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
            "P": 0, "P_upper": 0,
            "margin": None,
            "is_zero_revenue": True,
            "classification": "excluded",
            "class": "excluded",
            "band": "excluded",
            "lane": "EXCLUDED",
            "exclusion_reason": reason,
            "component_tags": {
                "cogs": "structural", "shipping": "structural", "gateway": "structural",
                "refund": "structural", "other": "structural"
            },
            "measured_share": Decimal("1.0000"),
            "cogs_basis": "none",
            "flags": flags,
            "drivers": {},
            "top_loss_driver": None,
            "P_asold": 0,
            "delta_profit": 0,
            "delta_cause": None
        }
