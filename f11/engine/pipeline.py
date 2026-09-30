"""
Production Execution Pipeline for Formula F11.
Loads order dataset, executes vectorized F11Engine, computes rollups,
enforces coverage gate, and formats audit reports.
"""

import json
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional
import pandas as pd
import yaml
from f11.engine.formula import F11Engine, compute_config_hash, FORMULA_VERSION, PINNED_API_VERSION



class AggregatedLaneResult:
    def __init__(self, lane_name: str, order_count: int, total_revenue: int, total_profit: Optional[int], margin: Optional[Decimal], headroom: Optional[int] = None):
        self.lane_name = lane_name
        self.order_count = order_count
        self.total_revenue = total_revenue
        self.total_profit = total_profit
        self.margin = margin
        self.headroom = headroom

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lane_name": self.lane_name,
            "order_count": self.order_count,
            "total_revenue": self.total_revenue,
            "total_profit": self.total_profit,
            "margin": float(self.margin) if self.margin is not None else None,
            "headroom": self.headroom
        }


class PipelineSummary:
    def __init__(self, lanes: Dict[str, AggregatedLaneResult], total_orders: int, active_orders: int, excluded_orders: int):
        self.lanes = lanes
        self.total_orders = total_orders
        self.active_orders = active_orders
        self.excluded_orders = excluded_orders

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_orders": self.total_orders,
            "active_orders": self.active_orders,
            "excluded_orders": self.excluded_orders,
            "lanes": {k: v.to_dict() for k, v in self.lanes.items()}
        }


def aggregate_orders(results: List[Dict[str, Any]]) -> PipelineSummary:
    # Separate into lanes
    lanes_data: Dict[str, List[Dict[str, Any]]] = {
        "MEASURED": [],
        "ESTIMATED": [],
        "UNDETERMINED": [],
        "CONFIRMED_LOSS": [],
        "EXCLUDED": []
    }
    for r in results:
        lane = r.get("lane", "UNDETERMINED")
        if lane in lanes_data:
            lanes_data[lane].append(r)
        else:
            lanes_data.setdefault(lane, []).append(r)

    total_orders = len(results)
    excluded_orders = len(lanes_data.get("EXCLUDED", []))
    active_orders = total_orders - excluded_orders

    lane_aggregates = {}
    for lane_name in ["MEASURED", "ESTIMATED"]:
        orders = lanes_data.get(lane_name, [])
        count = len(orders)
        tot_c = sum(o.get("C", 0) for o in orders)
        profits = [o.get("P") for o in orders if o.get("P") is not None]
        tot_p = sum(profits) if profits else 0
        margin = (Decimal(tot_p) / Decimal(tot_c) * Decimal("100")).quantize(Decimal("0.0001")) if tot_c > 0 and count > 0 and len(profits) == count else None
        lane_aggregates[lane_name] = AggregatedLaneResult(lane_name, count, tot_c, tot_p if count > 0 else None, margin)

    # UNDETERMINED: strictly NO total_profit or margin
    u_orders = lanes_data.get("UNDETERMINED", [])
    u_count = len(u_orders)
    u_c = sum(o.get("C", 0) for o in u_orders)
    u_headroom = sum(o.get("P_upper", 0) for o in u_orders if o.get("P_upper") is not None)
    lane_aggregates["UNDETERMINED"] = AggregatedLaneResult("UNDETERMINED", u_count, u_c, None, None, headroom=u_headroom)

    # CONFIRMED_LOSS: strictly NO total_profit or margin
    x_orders = lanes_data.get("CONFIRMED_LOSS", [])
    x_count = len(x_orders)
    x_c = sum(o.get("C", 0) for o in x_orders)
    x_headroom = sum(o.get("P_upper", 0) for o in x_orders if o.get("P_upper") is not None)
    lane_aggregates["CONFIRMED_LOSS"] = AggregatedLaneResult("CONFIRMED_LOSS", x_count, x_c, None, None, headroom=x_headroom)

    # EXCLUDED
    ex_orders = lanes_data.get("EXCLUDED", [])
    lane_aggregates["EXCLUDED"] = AggregatedLaneResult("EXCLUDED", len(ex_orders), 0, None, None)

    return PipelineSummary(lane_aggregates, total_orders, active_orders, excluded_orders)


def load_config(config_path: str = "f11/config/f11.config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(
    data_path: str = "f11/data/synthetic_orders.jsonl",
    config_path: str = "f11/config/f11.config.yaml",
    output_dir: str = "f11/output",
    limit: Optional[int] = None
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("f11/reports", exist_ok=True)
    
    config = load_config(config_path)
    engine = F11Engine(config)
    
    # 1. Ingest orders (handling JSONL with __parentId or standalone lines)
    orders: Dict[str, Dict[str, Any]] = {}
    lines_by_order: Dict[str, List[Dict[str, Any]]] = {}
    refunds_by_order: Dict[str, List[Dict[str, Any]]] = {}
    txns_by_order: Dict[str, List[Dict[str, Any]]] = {}
    
    print(f"Ingesting orders from {data_path}...")
    seen_ids = set()
    duplicate_count = 0
    
    with open(data_path, "r", encoding="utf-8") as f:
        for line_str in f:
            if not line_str.strip():
                continue
            item = json.loads(line_str)
            item_type = item.get("__typename")
            parent_id = item.get("__parentId")
            
            if not parent_id and (item_type == "Order" or "lineItems" in item or "totalPriceSet" in item):
                oid = item["id"]
                if oid in seen_ids:
                    duplicate_count += 1
                    continue
                seen_ids.add(oid)
                orders[oid] = item
                if limit and len(orders) >= limit:
                    break
            elif parent_id:
                if item_type == "LineItem":
                    lines_by_order.setdefault(parent_id, []).append(item)
                elif item_type == "Refund":
                    refunds_by_order.setdefault(parent_id, []).append(item)
                elif item_type == "OrderTransaction":
                    txns_by_order.setdefault(parent_id, []).append(item)

    print(f"Loaded {len(orders)} unique orders ({duplicate_count} duplicates skipped).")

    # 2. Re-attach children if separate
    for oid, o in orders.items():
        if oid in lines_by_order and "lineItems" not in o:
            o["lineItems"] = lines_by_order[oid]
        if oid in refunds_by_order and "refunds" not in o:
            o["refunds"] = refunds_by_order[oid]
        if oid in txns_by_order and "transactions" not in o:
            o["transactions"] = txns_by_order[oid]

    # 3. Evaluate orders
    results = []
    cogs_complete_rev = 0
    total_inflow = 0
    
    for oid, o in orders.items():
        res = engine.evaluate_order(o)
        results.append(res)
        
        c = res["C"]
        total_inflow += c
        if res["component_tags"]["cogs"] in ["measured", "structural"]:
            cogs_complete_rev += c

    df = pd.DataFrame(results)

    # 4. Coverage Gate Check
    coverage_gate = config.get("cogs_coverage_gate", 90.0)
    cogs_coverage_pct = (cogs_complete_rev / total_inflow * 100.0) if total_inflow > 0 else 100.0
    gate_passed = cogs_coverage_pct >= coverage_gate

    # 5. Lane Rollups (no blending!)
    lane_summary = {}
    for lane_name, lane_df in df.groupby("lane"):
        valid_p = [p for p in lane_df["P"] if p is not None]
        tot_c = lane_df["C"].sum()
        tot_p = sum(valid_p) if valid_p else 0
        lane_margin = (tot_p / tot_c * 100.0) if tot_c > 0 and valid_p else None
        
        lane_summary[lane_name] = {
            "order_count": len(lane_df),
            "total_revenue": tot_c,
            "total_profit": tot_p,
            "aggregate_margin_pct": lane_margin,
            "profitable_count": len(lane_df[lane_df["classification"] == "profitable"]),
            "breakeven_count": len(lane_df[lane_df["classification"] == "breakeven"]),
            "unprofitable_count": len(lane_df[lane_df["classification"] == "unprofitable"]),
        }

    # 6. Save Tables
    csv_path = os.path.join(output_dir, "order_profitability.csv")
    parquet_path = os.path.join(output_dir, "order_profitability.parquet")
    
    df_export = df.copy()
    for col in ["drivers", "component_tags", "flags"]:
        if col in df_export.columns:
            df_export[col] = df_export[col].apply(lambda x: json.dumps(x, default=str) if isinstance(x, (dict, list)) else str(x))
            
    df_export.to_csv(csv_path, index=False)
    
    df_parquet = df_export.copy()
    for col in ["margin", "measured_share"]:
        if col in df_parquet.columns:
            df_parquet[col] = pd.to_numeric(df_parquet[col], errors="coerce")
    df_parquet.to_parquet(parquet_path, index=False)

    summary_out = {
        "formula_version": FORMULA_VERSION,
        "api_version": PINNED_API_VERSION,
        "config_hash": engine.config_hash,
        "as_of": config.get("as_of"),
        "total_orders": len(df),
        "cogs_coverage_pct": cogs_coverage_pct,
        "cogs_coverage_gate_passed": gate_passed,
        "lane_summary": lane_summary
    }

    with open(os.path.join(output_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(summary_out, f, indent=2, default=str)

    print(f"Pipeline complete. Evaluated {len(df)} orders. Coverage: {cogs_coverage_pct:.2f}% (Gate Passed: {gate_passed})")
    return summary_out
