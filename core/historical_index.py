"""
Fast In-Memory 90-Day Historical COGS Lookup Index.
Indexed by variant_id and queried by order created_at timestamp.
Exercises Tier 1 COGS fallback (TC-05).
"""

from bisect import bisect_right
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

class HistoricalCogsIndex:
    """
    In-memory 90-day historical COGS lookup engine.
    Returns the most recent non-null cost in [order_time - 90 days, order_time).
    """
    def __init__(self, raw_index: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self.history: Dict[int, List[Tuple[float, float]]] = {}
        if raw_index:
            for vid_str, entries in raw_index.items():
                vid = int(vid_str)
                parsed = []
                for e in entries:
                    dt = datetime.fromisoformat(e["time"].replace("Z", "+00:00"))
                    cost = float(e["cost"])
                    parsed.append((dt.timestamp(), cost))
                parsed.sort(key=lambda x: x[0])
                self.history[vid] = parsed

    def lookup(self, variant_id: int, order_time: datetime) -> Optional[float]:
        """Looks up the most recent cost within the 90-day historical window (TC-05)."""
        if variant_id not in self.history:
            return None

        entries = self.history[variant_id]
        order_epoch = order_time.timestamp()
        min_epoch = (order_time - timedelta(days=90)).timestamp()

        timestamps = [e[0] for e in entries]
        idx = bisect_right(timestamps, order_epoch) - 1

        while idx >= 0:
            ts, cost = entries[idx]
            if ts < min_epoch:
                break
            if ts <= order_epoch and cost > 0:
                return cost
            idx -= 1

        return None


# Defined Business Configuration Rule:
# Minimum qualifying non-promotional transactions required within the rolling 90-day window
# to establish statistical significance before falling back to storewide default benchmark.
MIN_HISTORICAL_MARGIN_OBSERVATIONS: int = 5

class HistoricalMarginIndex:
    """
    In-memory 90-day rolling historical realized gross margin lookup engine.
    
    BUSINESS & METHODOLOGICAL SPECIFICATION:
    1. Window: Exact [order_time - 90 days, order_time) - strictly historical, strictly excludes future data.
    2. Qualifying Transactions:
       - Order must NOT be cancelled (cancelled_at is None).
       - Order must NOT be voided (financial_status != 'voided').
       - Order must NOT be fully refunded (active line quantity > 0).
       - Excludes zero-price gifts / 100% promotional items where net revenue <= $0.00.
       - Excludes lines with missing or non-positive COGS (cost is None or cost <= 0).
    3. Realized Gross Margin Basis:
       Realized Margin = (Net Revenue - Direct COGS) / Net Revenue
    4. Outlier Treatment:
       Excludes individual sales where realized margin is outside [-0.50, +0.95].
    5. Minimum Observation Threshold:
       Requires at least MIN_HISTORICAL_MARGIN_OBSERVATIONS (5) qualifying transactions within the 90-day rolling window.
       If < 5 transactions exist, returns None, triggering a legitimate fallback to Tier 5 Storewide Default.
    6. Trimming:
       Applies 2.5% trimmed mean (discards top 2.5% and bottom 2.5% of sorted margins when k >= 1).
    """
    def __init__(self):
        # Maps variant_id -> List of (timestamp_epoch, realized_margin)
        self.history: Dict[int, List[Tuple[float, float]]] = {}

    def add_observation(self, variant_id: int, order_time: datetime, realized_margin: float):
        """Adds a single verified historical transaction observation."""
        if -0.50 <= realized_margin <= 0.95:
            if variant_id not in self.history:
                self.history[variant_id] = []
            self.history[variant_id].append((order_time.timestamp(), realized_margin))

    def finalize(self):
        """Sorts chronological observation series for all indexed variants."""
        for vid in self.history:
            self.history[vid].sort(key=lambda x: x[0])

    def lookup(
        self,
        variant_id: int,
        order_time: datetime,
        min_obs: int = MIN_HISTORICAL_MARGIN_OBSERVATIONS
    ) -> Optional[float]:
        """
        Looks up the 90-day rolling realized gross margin for a variant strictly in [order_time - 90d, order_time).
        Returns the 2.5% trimmed mean realized margin if >= min_obs observations exist; else None.
        """
        if variant_id not in self.history:
            return None

        entries = self.history[variant_id]
        order_epoch = order_time.timestamp()
        min_epoch = (order_time - timedelta(days=90)).timestamp()

        # Binary search for strictly past transactions in [min_epoch, order_epoch)
        # Using bisect_left for order_epoch ensures transactions AT or AFTER order_epoch are strictly excluded
        timestamps = [e[0] for e in entries]
        idx_right = bisect_right(timestamps, order_epoch - 1e-6)
        idx_left = bisect_right(timestamps, min_epoch - 1e-6)

        qualifying = [entries[i][1] for i in range(idx_left, idx_right)]
        if len(qualifying) < min_obs:
            return None

        # 2.5% Trimmed Mean
        sorted_margins = sorted(qualifying)
        n = len(sorted_margins)
        k = int(n * 0.025)
        if k > 0 and n - 2 * k >= 1:
            trimmed = sorted_margins[k : n - k]
        else:
            trimmed = sorted_margins

        return round(sum(trimmed) / len(trimmed), 4)

    def lookup_detail(
        self,
        variant_id: int,
        order_time: datetime,
        min_obs: int = MIN_HISTORICAL_MARGIN_OBSERVATIONS
    ) -> Dict[str, Any]:
        """
        Exposes the exact intermediate details of the 90-day historical realized margin calculation.
        Includes timestamps, qualifying observations, outlier handling, trimming, and fallback rationale.
        """
        from core.fallbacks.margin import STOREWIDE_DEFAULT_TARGET_MARGIN
        order_epoch = order_time.timestamp()
        window_start = order_time - timedelta(days=90)
        min_epoch = window_start.timestamp()

        if variant_id not in self.history:
            return {
                "evaluation_time": order_time,
                "window_start": window_start,
                "window_end": order_time,
                "total_recorded_observations": 0,
                "qualifying_count": 0,
                "min_required": min_obs,
                "qualifying_transactions": [],
                "excluded_count": 0,
                "trimmed_count": 0,
                "is_available": False,
                "resolved_margin": STOREWIDE_DEFAULT_TARGET_MARGIN,
                "source": "storewide_default",
                "fallback_used": True,
                "fallback_reason": f"No historical transactions found for Variant #{variant_id} (0 < {min_obs})"
            }

        entries = self.history[variant_id]
        timestamps = [e[0] for e in entries]
        idx_right = bisect_right(timestamps, order_epoch - 1e-6)
        idx_left = bisect_right(timestamps, min_epoch - 1e-6)

        qualifying_items = []
        for i in range(idx_left, idx_right):
            ts, m = entries[i]
            qualifying_items.append({
                "timestamp": datetime.fromtimestamp(ts, tz=order_time.tzinfo or timezone.utc),
                "realized_margin": m
            })

        n = len(qualifying_items)
        qualifying_margins = [item["realized_margin"] for item in qualifying_items]
        sorted_margins = sorted(qualifying_margins)
        k = int(n * 0.025)

        if n >= min_obs:
            if k > 0 and n - 2 * k >= 1:
                trimmed = sorted_margins[k : n - k]
            else:
                trimmed = sorted_margins
            resolved_margin = round(sum(trimmed) / len(trimmed), 4)
            return {
                "evaluation_time": order_time,
                "window_start": window_start,
                "window_end": order_time,
                "total_recorded_observations": len(entries),
                "qualifying_count": n,
                "min_required": min_obs,
                "qualifying_transactions": qualifying_items,
                "excluded_count": len(entries) - n,
                "trimmed_count": 2 * k if (k > 0 and n - 2 * k >= 1) else 0,
                "trimmed_margins": trimmed,
                "is_available": True,
                "resolved_margin": resolved_margin,
                "source": "historical_margin",
                "fallback_used": False,
                "fallback_reason": None
            }
        else:
            return {
                "evaluation_time": order_time,
                "window_start": window_start,
                "window_end": order_time,
                "total_recorded_observations": len(entries),
                "qualifying_count": n,
                "min_required": min_obs,
                "qualifying_transactions": qualifying_items,
                "excluded_count": len(entries) - n,
                "trimmed_count": 0,
                "trimmed_margins": [],
                "is_available": False,
                "resolved_margin": STOREWIDE_DEFAULT_TARGET_MARGIN,
                "source": "storewide_default",
                "fallback_used": True,
                "fallback_reason": f"Only {n} qualifying transactions in 90-day window (minimum required: {min_obs})"
            }


    @classmethod
    def from_orders_and_catalog(
        cls,
        orders: List[Dict[str, Any]],
        catalog_by_variant_id: Dict[int, Any]
    ) -> "HistoricalMarginIndex":
        """
        Builds and indexes qualifying transactions from the order population.
        """
        index = cls()
        seen_order_ids = set()

        for o in orders:
            oid = o.get("id")
            if oid in seen_order_ids:
                continue
            seen_order_ids.add(oid)

            # Exclusion checks
            if o.get("cancelled_at") is not None:
                continue
            if o.get("financial_status") == "voided":
                continue

            # Check if fully refunded
            line_items = o.get("line_items", [])
            all_refunded = True
            for li in line_items:
                q = li.get("quantity", 1)
                cq = li.get("current_quantity", q)
                if cq > 0:
                    all_refunded = False
                    break
            if all_refunded:
                continue

            raw_time = o.get("created_at")
            if not raw_time:
                continue
            try:
                dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            except Exception:
                continue

            for li in line_items:
                vid = li.get("variant_id")
                if not vid:
                    continue
                q = li.get("quantity", 1)
                cq = li.get("current_quantity", q)
                if cq <= 0:
                    continue

                price = float(li.get("price") or 0.0)
                # Compute line discount
                line_disc = 0.0
                for da in li.get("discount_allocations", []):
                    line_disc += float(da.get("amount") or 0.0)

                net_rev = (price * cq) - line_disc
                if net_rev <= 0.0:
                    # Exclude zero-price gifts / 100% promotional items
                    continue

                # Direct COGS resolution
                cat_info = catalog_by_variant_id.get(vid)
                cogs = cat_info.get("true_cogs") if cat_info else None
                if cogs is None or cogs <= 0.0:
                    continue

                total_cogs = cogs * cq
                realized_m = (net_rev - total_cogs) / net_rev
                index.add_observation(vid, dt, realized_m)

        index.finalize()
        return index

