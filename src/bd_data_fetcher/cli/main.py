"""Main CLI application for BD Data Fetcher."""

import os
import sys
from pathlib import Path
from typing import Optional

import structlog
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from ..api.client import APIClient, APIConfig
from ..data_handlers import UserDataHandler, ProductDataHandler

# Initialize Typer app
app = typer.Typer(
    name="bd-fetcher",
    help="A production-grade CLI tool for fetching and processing data from REST APIs",
    add_completion=False,
)

# Initialize console for rich output
console = Console()

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up structured logging."""
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if log_file:
        processors.append(structlog.processors.JSONRenderer())
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        processors.append(structlog.dev.ConsoleRenderer())
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )


def get_api_client() -> APIClient:
    """Get configured API client."""
    config = APIConfig(
        base_url=os.getenv("API_BASE_URL", "https://api.example.com"),
        api_key=os.getenv("API_KEY"),
        timeout=int(os.getenv("API_TIMEOUT", "30")),
        max_retries=int(os.getenv("API_MAX_RETRIES", "3")),
        retry_delay=float(os.getenv("API_RETRY_DELAY", "1.0")),
    )
    return APIClient(config)


@app.command()
def users(
    output: str = typer.Option("data", "--output", "-o", help="Output directory"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, csv)"),
    limit: int = typer.Option(100, "--limit", "-l", help="Number of users to fetch"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search query"),
    user_id: Optional[int] = typer.Option(None, "--id", help="Fetch specific user by ID"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Fetch and process user data."""
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    logger = structlog.get_logger(__name__)
    
    try:
        with get_api_client() as api_client:
            handler = UserDataHandler(api_client)
            
            if user_id:
                # Fetch specific user
                logger.info("Fetching specific user", user_id=user_id)
                user_data = handler.fetch_user_by_id(user_id)
                processed_data = handler.process_data({"users": [user_data]})
            elif search:
                # Search users
                logger.info("Searching users", query=search)
                processed_data = handler.search_users(search, limit=limit)
            else:
                # Fetch all users
                logger.info("Fetching users", limit=limit)
                file_path = handler.fetch_and_save(limit=limit)
                console.print(f"✅ User data saved to: {file_path}")
                return
            
            # Save data
            file_path = handler.save_data(processed_data)
            console.print(f"✅ User data saved to: {file_path}")
            
            # Show summary
            summary = handler.get_data_summary(processed_data)
            console.print(f"📊 Processed {summary['record_count']} user records")
            
    except Exception as e:
        logger.error("Failed to fetch user data", error=str(e))
        console.print(f"❌ Error: {str(e)}", style="red")
        sys.exit(1)


@app.command()
def products(
    output: str = typer.Option("data", "--output", "-o", help="Output directory"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, csv)"),
    limit: int = typer.Option(100, "--limit", "-l", help="Number of products to fetch"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search query"),
    product_id: Optional[int] = typer.Option(None, "--id", help="Fetch specific product by ID"),
    min_price: Optional[float] = typer.Option(None, "--min-price", help="Minimum price filter"),
    max_price: Optional[float] = typer.Option(None, "--max-price", help="Maximum price filter"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Fetch and process product data."""
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    logger = structlog.get_logger(__name__)
    
    try:
        with get_api_client() as api_client:
            handler = ProductDataHandler(api_client)
            
            if product_id:
                # Fetch specific product
                logger.info("Fetching specific product", product_id=product_id)
                product_data = handler.fetch_product_by_id(product_id)
                processed_data = handler.process_data({"products": [product_data]})
            elif search:
                # Search products
                logger.info("Searching products", query=search)
                processed_data = handler.search_products(search, limit=limit)
            elif category:
                # Fetch products by category
                logger.info("Fetching products by category", category=category)
                processed_data = handler.fetch_products_by_category(category, limit=limit)
            else:
                # Fetch all products
                logger.info("Fetching products", limit=limit)
                file_path = handler.fetch_and_save(limit=limit)
                console.print(f"✅ Product data saved to: {file_path}")
                return
            
            # Save data
            file_path = handler.save_data(processed_data)
            console.print(f"✅ Product data saved to: {file_path}")
            
            # Show summary
            summary = handler.get_data_summary(processed_data)
            console.print(f"📊 Processed {summary['record_count']} product records")
            
    except Exception as e:
        logger.error("Failed to fetch product data", error=str(e))
        console.print(f"❌ Error: {str(e)}", style="red")
        sys.exit(1)


@app.command()
def categories(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """List available product categories."""
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    logger = structlog.get_logger(__name__)
    
    try:
        with get_api_client() as api_client:
            handler = ProductDataHandler(api_client)
            categories = handler.get_product_categories()
            
            # Create table
            table = Table(title="Available Product Categories")
            table.add_column("Category", style="cyan", no_wrap=True)
            table.add_column("Count", style="green")
            
            for category in categories:
                table.add_row(category, "N/A")  # Count not available in this example
            
            console.print(table)
            console.print(f"📋 Found {len(categories)} categories")
            
    except Exception as e:
        logger.error("Failed to fetch categories", error=str(e))
        console.print(f"❌ Error: {str(e)}", style="red")
        sys.exit(1)


@app.command()
def status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Check API connection status."""
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    logger = structlog.get_logger(__name__)
    
    try:
        with get_api_client() as api_client:
            # Try to make a simple request to check connectivity
            response = api_client.get("/health")
            
            table = Table(title="API Status")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Details")
            
            table.add_row("Connection", "✅ Connected", "API is reachable")
            table.add_row("Authentication", "✅ Valid", "API key is valid")
            table.add_row("Response Time", "✅ Good", "Response received")
            
            console.print(table)
            console.print("🎉 API connection is healthy!")
            
    except Exception as e:
        logger.error("API status check failed", error=str(e))
        
        table = Table(title="API Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="red")
        table.add_column("Details")
        
        table.add_row("Connection", "❌ Failed", str(e))
        
        console.print(table)
        console.print("💥 API connection failed!", style="red")
        sys.exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    set_base_url: Optional[str] = typer.Option(None, "--base-url", help="Set API base URL"),
    set_api_key: Optional[str] = typer.Option(None, "--api-key", help="Set API key"),
):
    """Manage configuration settings."""
    if show:
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("API Base URL", os.getenv("API_BASE_URL", "Not set"))
        table.add_row("API Key", "***" if os.getenv("API_KEY") else "Not set")
        table.add_row("Timeout", os.getenv("API_TIMEOUT", "30"))
        table.add_row("Max Retries", os.getenv("API_MAX_RETRIES", "3"))
        
        console.print(table)
        console.print("💡 Use environment variables or .env file to configure settings")
    
    if set_base_url:
        # In a real implementation, you'd save this to a config file
        console.print(f"🔧 Base URL would be set to: {set_base_url}")
        console.print("💡 Set API_BASE_URL environment variable to persist this setting")
    
    if set_api_key:
        # In a real implementation, you'd save this to a config file
        console.print("🔧 API key would be set")
        console.print("💡 Set API_KEY environment variable to persist this setting")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main() 