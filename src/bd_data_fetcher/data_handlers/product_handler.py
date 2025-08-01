"""Product data handler for BD Data Fetcher."""

from typing import Any, Dict, List

import structlog
from pydantic import BaseModel

from .base import BaseDataHandler

logger = structlog.get_logger(__name__)


class ProductData(BaseModel):
    """Product data model."""
    
    id: int
    title: str
    description: str
    price: float
    category: str = ""
    brand: str = ""
    stock: int = 0
    rating: float = 0.0
    images: List[str] = []


class ProductDataHandler(BaseDataHandler):
    """Handler for product data operations."""
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        """Fetch product data from the API.
        
        Args:
            **kwargs: Additional parameters (e.g., limit, offset, category)
            
        Returns:
            Raw product data from API
        """
        endpoint = "/products"
        params = {
            "limit": kwargs.get("limit", 100),
            "offset": kwargs.get("offset", 0),
        }
        
        # Add category filter if provided
        if "category" in kwargs:
            params["category"] = kwargs["category"]
        
        # Add price range filters if provided
        if "min_price" in kwargs:
            params["min_price"] = kwargs["min_price"]
        if "max_price" in kwargs:
            params["max_price"] = kwargs["max_price"]
        
        logger.info("Fetching product data", endpoint=endpoint, params=params)
        return self.api_client.get(endpoint, params=params)
    
    def process_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process raw product data into structured format.
        
        Args:
            data: Raw product data from API
            
        Returns:
            List of processed product records
        """
        products = data.get("products", []) if isinstance(data, dict) else data
        
        processed_products = []
        for product in products:
            try:
                # Validate and clean product data
                product_data = ProductData(
                    id=product.get("id"),
                    title=product.get("title", ""),
                    description=product.get("description", ""),
                    price=float(product.get("price", 0)),
                    category=product.get("category", ""),
                    brand=product.get("brand", ""),
                    stock=int(product.get("stock", 0)),
                    rating=float(product.get("rating", 0)),
                    images=product.get("images", []),
                )
                
                processed_products.append(product_data.model_dump())
                
            except Exception as e:
                logger.warning("Failed to process product record", product_id=product.get("id"), error=str(e))
                continue
        
        logger.info("Product data processed", total_products=len(products), processed_products=len(processed_products))
        return processed_products
    
    def fetch_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """Fetch a specific product by ID.
        
        Args:
            product_id: Product ID to fetch
            
        Returns:
            Product data
        """
        endpoint = f"/products/{product_id}"
        logger.info("Fetching product by ID", product_id=product_id)
        return self.api_client.get(endpoint)
    
    def fetch_products_by_category(self, category: str, **kwargs) -> List[Dict[str, Any]]:
        """Fetch products by category.
        
        Args:
            category: Category name
            **kwargs: Additional parameters
            
        Returns:
            List of products in the category
        """
        return self.fetch_data(category=category, **kwargs)
    
    def search_products(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search products by query.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            List of matching products
        """
        endpoint = "/products/search"
        params = {"q": query, **kwargs}
        
        logger.info("Searching products", query=query, params=params)
        raw_data = self.api_client.get(endpoint, params=params)
        return self.process_data(raw_data)
    
    def get_product_categories(self) -> List[str]:
        """Get list of available product categories.
        
        Returns:
            List of category names
        """
        endpoint = "/products/categories"
        logger.info("Fetching product categories")
        response = self.api_client.get(endpoint)
        return response.get("categories", []) 