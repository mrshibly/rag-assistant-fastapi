import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> list[dict]:
    return json.loads((DATA_DIR / filename).read_text())


def get_order_status(order_id: str) -> str:
    for order in _load_json("orders.json"):
        if order["order_id"].upper() == order_id.upper():
            return (
                f"Order {order['order_id']}: Status is '{order['status']}', "
                f"estimated delivery on {order['estimated_delivery']}."
            )
    return f"Order '{order_id}' not found."


def search_product(query: str) -> str:
    """Fuzzy search: matches if any word in the query appears in the product name."""
    query_words = query.lower().split()
    results = [
        p for p in _load_json("products.json")
        if any(word in p["name"].lower() for word in query_words)
    ]
    if not results:
        return f"No products found matching '{query}'."
    lines = []
    for p in results:
        stock = "In Stock" if p["stock"] > 0 else "Out of Stock"
        lines.append(f"- {p['name']}: ${p['price']} ({stock}, {p['stock']} units)")
    return "\n".join(lines)


# Registry mapping tool names to their handler functions
TOOL_REGISTRY = {
    "get_order_status": get_order_status,
    "search_product": search_product,
}

# Tool definitions for the LLM system prompt
TOOL_DEFINITIONS = [
    {
        "name": "get_order_status",
        "description": "Look up the status and estimated delivery date for an order by its order ID.",
        "parameters": {
            "order_id": {"type": "string", "description": "The order ID (e.g., ORD001)"}
        },
    },
    {
        "name": "search_product",
        "description": "Search for a product by name and return its price and stock availability.",
        "parameters": {
            "query": {"type": "string", "description": "Product name to search for"}
        },
    },
]
