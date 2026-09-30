"""
In-Memory GraphQL Mock Server & Bulk Operation Lifecycle Emulator for F11.
Serves synthetic orders with pagination, throttle simulation, and JSONL exports.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional


class MockShopifyGraphQLServer:
    def __init__(self, data_path: str = "f11/data/synthetic_orders.jsonl"):
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.bulk_jobs: Dict[str, Dict[str, Any]] = {}
        self.job_counter = 0
        self.throttled_mode = False
        
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        obj = json.loads(line)
                        if "id" in obj:
                            self.orders[obj["id"]] = obj

    def query(self, query_str: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes simulated GraphQL query against internal state."""
        if self.throttled_mode:
            return {
                "errors": [
                    {
                        "message": "Throttled",
                        "extensions": {"code": "THROTTLED", "documentation": "https://shopify.dev/api/usage/rate-limits"}
                    }
                ]
            }

        variables = variables or {}
        
        # 1. Single order query
        if "order(id:" in query_str or "$id" in query_str:
            order_id = variables.get("id")
            if order_id and order_id in self.orders:
                return {"data": {"order": self.orders[order_id]}}
            return {"data": {"order": None}}

        # 2. Paged orders query
        if "orders(" in query_str:
            first = variables.get("first", 10)
            after = variables.get("after")
            all_orders = list(self.orders.values())
            
            start_idx = 0
            if after:
                for idx, o in enumerate(all_orders):
                    if o["id"] == after:
                        start_idx = idx + 1
                        break
                        
            page = all_orders[start_idx : start_idx + first]
            has_next = (start_idx + first) < len(all_orders)
            end_cursor = page[-1]["id"] if page else None
            
            edges = [{"cursor": o["id"], "node": o} for o in page]
            return {
                "data": {
                    "orders": {
                        "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
                        "edges": edges
                    }
                }
            }

        # 3. Bulk operation query polling
        if "currentBulkOperation" in query_str:
            job_id = variables.get("id", list(self.bulk_jobs.keys())[-1] if self.bulk_jobs else "gid://shopify/BulkOperation/1")
            job = self.bulk_jobs.get(job_id, {
                "id": job_id,
                "status": "COMPLETED",
                "errorCode": None,
                "createdAt": "2026-09-30T10:00:00Z",
                "completedAt": "2026-09-30T10:05:00Z",
                "objectCount": str(len(self.orders)),
                "url": "file://f11/data/synthetic_orders.jsonl"
            })
            return {"data": {"currentBulkOperation": job}}

        return {"data": {"shop": {"id": "gid://shopify/Shop/1", "name": "Audit Store", "currencyCode": "USD"}}}

    def mutate_bulk_operation(self, query_text: str) -> Dict[str, Any]:
        """Spawns an asynchronous bulk operation job."""
        self.job_counter += 1
        job_id = f"gid://shopify/BulkOperation/{self.job_counter}"
        self.bulk_jobs[job_id] = {
            "id": job_id,
            "status": "COMPLETED",
            "errorCode": None,
            "createdAt": "2026-09-30T10:00:00Z",
            "completedAt": "2026-09-30T10:05:00Z",
            "objectCount": str(len(self.orders)),
            "url": "file://f11/data/synthetic_orders.jsonl"
        }
        return {
            "data": {
                "bulkOperationRunQuery": {
                    "bulkOperation": self.bulk_jobs[job_id],
                    "userErrors": []
                }
            }
        }
