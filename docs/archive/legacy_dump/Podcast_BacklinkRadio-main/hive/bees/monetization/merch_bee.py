"""
MerchBee - Merchandise Management Bee

Manages merchandise design, inventory, and fulfillment.
Tracks merch revenue and popular items.
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json
import uuid

# Import base
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import BaseBee


class MerchBee(BaseBee):
    """
    Manages station merchandise operations.
    
    Type: Employed bee
    Priority: Low
    Schedule: On-demand / Daily inventory check
    """
    
    BEE_TYPE = "merch"
    BEE_NAME = "MerchBee"
    CATEGORY = "monetization"
    LINEAGE_VERSION = "1.0.0"
    
    def __init__(self, hive_path: Optional[Path] = None):
        super().__init__(hive_path=hive_path)
        self.merch_file = self.honeycomb_path / "merchandise.json"
        self._ensure_merch_file()
    
    def _ensure_merch_file(self):
        """Initialize merchandise storage."""
        if not self.merch_file.exists():
            initial = {
                "products": [],
                "designs": [],
                "orders": [],
                "fulfillment_partners": [],
                "stats": {
                    "total_products": 0,
                    "total_orders": 0,
                    "total_revenue": 0,
                    "top_sellers": []
                }
            }
            self.merch_file.write_text(json.dumps(initial, indent=2))
    
    def _load_data(self) -> Dict:
        return json.loads(self.merch_file.read_text())
    
    def _save_data(self, data: Dict):
        self.merch_file.write_text(json.dumps(data, indent=2))
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check inventory status."""
        return self._inventory_check(task or {})
    
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute merchandise tasks."""
        action = task.get("action", "list_products")
        
        actions = {
            "add_product": self._add_product,
            "update_product": self._update_product,
            "list_products": self._list_products,
            "add_design": self._add_design,
            "list_designs": self._list_designs,
            "create_order": self._create_order,
            "fulfill_order": self._fulfill_order,
            "list_orders": self._list_orders,
            "inventory_check": self._inventory_check,
            "get_stats": self._get_stats
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}"}
        
        return self.safe_action(actions[action], task)
    
    def _add_product(self, task: Dict) -> Dict:
        """Add a new merchandise product."""
        data = self._load_data()
        
        product = {
            "id": str(uuid.uuid4())[:8],
            "name": task.get("name"),
            "type": task.get("type", "apparel"),  # apparel, accessory, digital, collectible
            "design_id": task.get("design_id"),
            "variants": task.get("variants", []),  # sizes, colors
            "price": task.get("price", 0),
            "cost": task.get("cost", 0),
            "inventory": task.get("inventory", 0),
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["products"].append(product)
        data["stats"]["total_products"] = len(data["products"])
        self._save_data(data)
        
        return {"success": True, "product": product}
    
    def _update_product(self, task: Dict) -> Dict:
        """Update product details."""
        product_id = task.get("product_id")
        updates = task.get("updates", {})
        
        data = self._load_data()
        
        for product in data["products"]:
            if product["id"] == product_id:
                for key, value in updates.items():
                    if key in product and key != "id":
                        product[key] = value
                product["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save_data(data)
                return {"success": True, "product": product}
        
        return {"error": f"Product not found: {product_id}"}
    
    def _list_products(self, task: Dict) -> Dict:
        """List merchandise products."""
        data = self._load_data()
        products = data["products"]
        
        product_type = task.get("type")
        status = task.get("status", "active")
        
        if product_type:
            products = [p for p in products if p["type"] == product_type]
        if status:
            products = [p for p in products if p["status"] == status]
        
        return {
            "success": True,
            "count": len(products),
            "products": products
        }
    
    def _add_design(self, task: Dict) -> Dict:
        """Add a new design."""
        data = self._load_data()
        
        design = {
            "id": str(uuid.uuid4())[:8],
            "name": task.get("name"),
            "description": task.get("description", ""),
            "designer": task.get("designer", "internal"),
            "file_url": task.get("file_url"),
            "applicable_products": task.get("applicable_products", ["t-shirt", "hoodie", "mug"]),
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        data["designs"].append(design)
        self._save_data(data)
        
        return {"success": True, "design": design}
    
    def _list_designs(self, task: Dict) -> Dict:
        """List available designs."""
        data = self._load_data()
        
        status = task.get("status")
        designs = data["designs"]
        
        if status:
            designs = [d for d in designs if d["status"] == status]
        
        return {
            "success": True,
            "count": len(designs),
            "designs": designs
        }
    
    def _create_order(self, task: Dict) -> Dict:
        """Create a merchandise order."""
        data = self._load_data()
        
        order = {
            "id": str(uuid.uuid4())[:8],
            "customer_id": task.get("customer_id"),
            "items": task.get("items", []),  # [{product_id, variant, quantity}]
            "total": task.get("total", 0),
            "shipping_address": task.get("shipping_address"),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update inventory
        for item in order["items"]:
            for product in data["products"]:
                if product["id"] == item.get("product_id"):
                    product["inventory"] = max(0, product["inventory"] - item.get("quantity", 1))
        
        data["orders"].append(order)
        data["stats"]["total_orders"] = len(data["orders"])
        data["stats"]["total_revenue"] += order["total"]
        
        self._save_data(data)
        
        return {"success": True, "order": order}
    
    def _fulfill_order(self, task: Dict) -> Dict:
        """Mark order as fulfilled."""
        order_id = task.get("order_id")
        tracking = task.get("tracking_number")
        
        data = self._load_data()
        
        for order in data["orders"]:
            if order["id"] == order_id:
                order["status"] = "fulfilled"
                order["tracking_number"] = tracking
                order["fulfilled_at"] = datetime.now(timezone.utc).isoformat()
                self._save_data(data)
                return {"success": True, "order": order}
        
        return {"error": f"Order not found: {order_id}"}
    
    def _list_orders(self, task: Dict) -> Dict:
        """List orders."""
        data = self._load_data()
        
        status = task.get("status")
        orders = data["orders"]
        
        if status:
            orders = [o for o in orders if o["status"] == status]
        
        return {
            "success": True,
            "count": len(orders),
            "orders": orders[-50:]  # Last 50
        }
    
    def _inventory_check(self, task: Dict) -> Dict:
        """Check inventory levels."""
        data = self._load_data()
        
        low_stock = []
        out_of_stock = []
        
        threshold = task.get("low_stock_threshold", 10)
        
        for product in data["products"]:
            if product["status"] == "active":
                if product["inventory"] == 0:
                    out_of_stock.append(product)
                elif product["inventory"] <= threshold:
                    low_stock.append(product)
        
        return {
            "success": True,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "alerts": len(low_stock) + len(out_of_stock)
        }
    
    def _get_stats(self, task: Dict) -> Dict:
        """Get merchandise statistics."""
        data = self._load_data()
        
        active_products = len([p for p in data["products"] if p["status"] == "active"])
        pending_orders = len([o for o in data["orders"] if o["status"] == "pending"])
        
        return {
            "success": True,
            "stats": {
                **data["stats"],
                "active_products": active_products,
                "pending_orders": pending_orders,
                "designs_count": len(data["designs"])
            }
        }
