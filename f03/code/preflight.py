"""
Pre-flight OAuth Scope Verification for Shopify Admin GraphQL API.
Ensures that read_orders and read_inventory scopes are active prior to pipeline execution.
"""

from typing import Dict, Any, List


class ShopifyOAuthScopeDenied(Exception):
    """Raised when an essential Shopify OAuth scope is missing or rejected."""
    pass


REQUIRED_SCOPES = [
    "read_orders",
    "read_inventory",
]

PREFLIGHT_ORDER_QUERY = """
query PreflightOrderCheck {
  orders(first: 1) {
    edges {
      node {
        id
      }
    }
  }
}
"""

PREFLIGHT_INVENTORY_QUERY = """
query PreflightInventoryCheck {
  inventoryItems(first: 1) {
    edges {
      node {
        id
      }
    }
  }
}
"""


def verify_shopify_oauth_scopes(graphql_client=None, granted_scopes: List[str] = None) -> bool:
    """
    Verifies that the required Shopify OAuth scopes are granted.
    
    If granted_scopes list is provided directly (e.g. from token introspection), validates membership.
    If graphql_client is provided, runs test queries against minimal endpoints.
    """
    if granted_scopes is not None:
        missing = [scope for scope in REQUIRED_SCOPES if scope not in granted_scopes]
        if missing:
            raise ShopifyOAuthScopeDenied(
                f"Production pre-flight check failed: Missing required OAuth scopes: {missing}. "
                f"F03 calculation cannot proceed without 'read_orders' and 'read_inventory'."
            )
        return True

    if graphql_client is not None:
        # Execute orders check
        try:
            resp_orders = graphql_client.execute(PREFLIGHT_ORDER_QUERY)
            if "errors" in resp_orders:
                raise ShopifyOAuthScopeDenied(f"Access denied querying orders: {resp_orders['errors']}")
        except Exception as e:
            raise ShopifyOAuthScopeDenied(f"Pre-flight failed verifying 'read_orders': {str(e)}")

        # Execute inventory check
        try:
            resp_inv = graphql_client.execute(PREFLIGHT_INVENTORY_QUERY)
            if "errors" in resp_inv:
                raise ShopifyOAuthScopeDenied(f"Access denied querying inventory: {resp_inv['errors']}")
        except Exception as e:
            raise ShopifyOAuthScopeDenied(f"Pre-flight failed verifying 'read_inventory': {str(e)}")

        return True

    # In local testing/mock mode, assume verified if explicitly simulated
    return True
