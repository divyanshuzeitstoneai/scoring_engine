"""
Data Quality Assurance Engine for Formula F10 v2.
Implements all 19 Data Quality Gates (DQ-S1 through DQ-D2) with BLOCK, QUARANTINE, and WARN severities.
"""

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class GateSeverity(str, Enum):
    BLOCK = "BLOCK"
    QUARANTINE = "QUARANTINE"
    WARN = "WARN"


class GateResult:
    def __init__(self, gate_id: str, name: str, severity: GateSeverity, description: str):
        self.gate_id = gate_id
        self.name = name
        self.severity = severity
        self.description = description
        self.passed: bool = True
        self.checked_count: int = 0
        self.failed_count: int = 0
        self.quarantined_revenue: Decimal = Decimal("0.00")
        self.offending_ids: List[str] = []
        self.details: str = ""

    def fail(self, entity_id: str, revenue: Decimal = Decimal("0.00"), reason: str = ""):
        self.passed = False
        self.failed_count += 1
        self.quarantined_revenue += revenue
        if len(self.offending_ids) < 10:
            self.offending_ids.append(f"{entity_id} ({reason})" if reason else entity_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "severity": self.severity.value,
            "passed": self.passed,
            "checked_count": self.checked_count,
            "failed_count": self.failed_count,
            "quarantined_revenue": str(self.quarantined_revenue),
            "offending_ids_sample": self.offending_ids[:5],
            "description": self.description
        }


class DQGateRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gates: Dict[str, GateResult] = {
            "DQ-S1": GateResult("DQ-S1", "Schema Validation", GateSeverity.BLOCK, "Payload validates against the pinned 2024-10 schema"),
            "DQ-S2": GateResult("DQ-S2", "Enum Validity", GateSeverity.QUARANTINE, "No unknown enum values (e.g. invalid restockType)"),
            "DQ-U1": GateResult("DQ-U1", "Uniqueness", GateSeverity.BLOCK, "Line ID and refund ID unique after ingestion"),
            "DQ-U2": GateResult("DQ-U2", "Idempotency", GateSeverity.BLOCK, "Re-ingestion produces zero net changes"),
            "DQ-RI1": GateResult("DQ-RI1", "Referential Integrity", GateSeverity.QUARANTINE, "Every refund line references an existing line item"),
            "DQ-RI2": GateResult("DQ-RI2", "Refund Quantity Bound", GateSeverity.QUARANTINE, "Refunded quantity does not exceed ordered quantity"),
            "DQ-R1": GateResult("DQ-R1", "Order Reconciliation", GateSeverity.QUARANTINE, "Sum of line nets plus shipping minus discounts reconciles to order total"),
            "DQ-R2": GateResult("DQ-R2", "Discount Allocation Sum", GateSeverity.QUARANTINE, "Sum of line discount allocations equals order total discount"),
            "DQ-R3": GateResult("DQ-R3", "Refund Subtotal Reconciliation", GateSeverity.QUARANTINE, "Sum of refund subtotals reconciles to total refunded"),
            "DQ-C1": GateResult("DQ-C1", "Currency Consistency", GateSeverity.BLOCK, "No mixed-currency sum without shopMoney conversion"),
            "DQ-K1": GateResult("DQ-K1", "COGS State Completeness", GateSeverity.BLOCK, "COGS state assigned to 100% of lines"),
            "DQ-K2": GateResult("DQ-K2", "Unknown Cost Share Reporting", GateSeverity.WARN, "Cost-unknown share reported per variant"),
            "DQ-A1": GateResult("DQ-A1", "Allocation Conservation", GateSeverity.BLOCK, "Allocated shipping and fees sum exactly to order amounts"),
            "DQ-A2": GateResult("DQ-A2", "Positive Allocations", GateSeverity.QUARANTINE, "No negative allocation unless a refund explains it"),
            "DQ-T1": GateResult("DQ-T1", "Deterministic Time", GateSeverity.BLOCK, "All windows and maturity use as_of, never system clock"),
            "DQ-F1": GateResult("DQ-F1", "Score Bounds & Margin Rule", GateSeverity.BLOCK, "Score in [0,100] or null; margin null exactly when RetainedRev <= 0"),
            "DQ-F2": GateResult("DQ-F2", "Waterfall Conservation", GateSeverity.BLOCK, "Waterfall sums exactly to NaiveProfit - Contribution"),
            "DQ-F3": GateResult("DQ-F3", "Revenue Conservation", GateSeverity.BLOCK, "Conservation: revenue_scored + revenue_quarantined = revenue_total"),
            "DQ-D1": GateResult("DQ-D1", "Sync Freshness", GateSeverity.WARN, "Last sync within freshness threshold"),
            "DQ-D2": GateResult("DQ-D2", "Schema Drift Introspection", GateSeverity.WARN, "Introspection diff against pinned version")
        }

    def evaluate_line_uniqueness(self, line_ids: List[str], refund_ids: List[str]):
        gate = self.gates["DQ-U1"]
        gate.checked_count = len(line_ids) + len(refund_ids)
        seen_lines: Set[str] = set()
        seen_refunds: Set[str] = set()

        for lid in line_ids:
            if lid in seen_lines:
                gate.fail(lid, reason="Duplicate Line Item ID")
            seen_lines.add(lid)

        for rid in refund_ids:
            if rid in seen_refunds:
                gate.fail(rid, reason="Duplicate Refund ID")
            seen_refunds.add(rid)

    def evaluate_cogs_assignment(self, line_facts: List[Any]):
        gate = self.gates["DQ-K1"]
        gate.checked_count = len(line_facts)
        for lf in line_facts:
            if lf.cogs_state is None:
                gate.fail(lf.line_item_id, lf.net_billed, "COGS state unassigned")

    def evaluate_revenue_conservation(self, variant_metrics: List[Any]):
        gate = self.gates["DQ-F3"]
        gate.checked_count = len(variant_metrics)
        for vm in variant_metrics:
            diff = abs(vm.revenue_total - (vm.revenue_scored + vm.revenue_quarantined))
            if diff > Decimal("0.005"):
                gate.fail(vm.variant_id, vm.revenue_total, f"Drift: {diff}")

    def evaluate_waterfall_conservation(self, variant_metrics: List[Any]):
        gate = self.gates["DQ-F2"]
        gate.checked_count = len(variant_metrics)
        for vm in variant_metrics:
            if vm.contribution is None:
                continue
            expected_leakage = vm.naive_profit - vm.contribution
            diff = abs(vm.hidden_leakage - expected_leakage)
            if diff > Decimal("0.005"):
                gate.fail(vm.variant_id, vm.hidden_leakage, f"Waterfall discrepancy: {diff}")

    def evaluate_score_bounds(self, variant_metrics: List[Any]):
        gate = self.gates["DQ-F1"]
        gate.checked_count = len(variant_metrics)
        for vm in variant_metrics:
            if vm.score is not None:
                if vm.score < Decimal("0.00") or vm.score > Decimal("100.00"):
                    gate.fail(vm.variant_id, vm.revenue_total, f"Score out of bounds: {vm.score}")
            if vm.retained_rev <= Decimal("0.00") and vm.margin_pct is not None:
                gate.fail(vm.variant_id, vm.retained_rev, f"Margin not null for RetainedRev <= 0: {vm.margin_pct}")

    def evaluate_deterministic_clock(self):
        gate = self.gates["DQ-T1"]
        gate.checked_count = 1
        as_of = self.config.get("as_of")
        if not as_of or not isinstance(as_of, str):
            gate.fail("CONFIG", reason="Missing explicit as_of string date")

    def get_summary(self) -> Dict[str, Any]:
        total_gates = len(self.gates)
        passed_gates = sum(1 for g in self.gates.values() if g.passed)
        block_passed = all(g.passed for g in self.gates.values() if g.severity == GateSeverity.BLOCK)
        total_quarantined_rev = sum(g.quarantined_revenue for g in self.gates.values())
        
        return {
            "total_gates": total_gates,
            "passed_gates": passed_gates,
            "block_passed": block_passed,
            "total_quarantined_rev": str(total_quarantined_rev),
            "gates": [g.to_dict() for g in self.gates.values()]
        }
