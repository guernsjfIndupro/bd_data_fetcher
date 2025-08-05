"""Main CLI application for BD Data Fetcher."""

import os
import sys
from pathlib import Path
from typing import Optional

import structlog
import typer
from rich.console import Console
from rich.table import Table

from ..api.umap_client import UMapServiceClient
from ..data_handlers.gene_expression import GeneExpressionDataHandler
from ..data_handlers.umap import uMapDataHandler

# Initialize Typer app
app = typer.Typer(
    name="bd-fetcher",
    help="A CLI tool for generating gene expression data from protein symbols",
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


@app.command()
def gene_expression(
    symbols: list[str] = typer.Argument(..., help="List of protein symbols (e.g., EGFR TP53 BRCA1)"),
    output: str = typer.Option("output.xlsx", "--output", "-o", help="Output Excel file name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """
    Generate gene expression data for protein symbols.
    
    Maps protein symbols to UniProtKB accession numbers and generates comprehensive gene expression data.
    """
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    logger = structlog.get_logger(__name__)
    
    try:
        # Initialize UMap client
        umap_client = UMapServiceClient()
        
        # Map protein symbols to UniProtKB accession numbers
        console.print(f"Mapping {len(symbols)} protein symbols to UniProtKB accession numbers...")
        symbol_mappings = umap_client.map_protein(symbols)
        
        if not symbol_mappings:
            console.print("No protein mappings found. Please check your protein symbols.", style="red")
            sys.exit(1)
        
        # Display mappings
        table = Table(title="Protein Symbol Mappings")
        table.add_column("Symbol", style="cyan")
        table.add_column("UniProtKB AC", style="green")
        
        for symbol, uniprotkb_ac in symbol_mappings.items():
            table.add_row(symbol, uniprotkb_ac)
        
        console.print(table)
        console.print(f"Successfully mapped {len(symbol_mappings)} proteins")
        
        # Initialize gene expression handler
        gene_handler = GeneExpressionDataHandler()
        umap_handler = uMapDataHandler()
        
        # Generate gene expression data for each protein
        console.print(f"Generating gene expression data for {len(symbol_mappings)} proteins...")
        
        for symbol, uniprotkb_ac in symbol_mappings.items():
            console.print(f"Processing {symbol} ({uniprotkb_ac})...")
            
            try:
                # Generate all three types of gene expression data
                # gene_handler.build_normal_gene_expression_sheet(uniprotkb_ac, output)
                # gene_handler.build_gene_expression_sheet(uniprotkb_ac, output)
                # gene_handler.build_gene_tumor_normal_ratios_sheet(uniprotkb_ac, output)

                # umap_handler.get_umap_data(uniprotkb_ac, output)

                cell_line_set = umap_handler.get_cell_lines(uniprotkb_ac)
                console.print(f"Cell lines: {cell_line_set}")

                # Get WCE data for the appropriate cell lines

                


                
                console.print(f"Completed processing {symbol}")
                
            except Exception as e:
                logger.error(f"Failed to process {symbol}", error=str(e))
                console.print(f"Warning: Failed to process {symbol}: {str(e)}", style="yellow")
                continue
        
        console.print(f"Gene expression data saved to: {output}")
        console.print(f"Processed {len(symbol_mappings)} proteins successfully")
        
        # Show file information
        if Path(output).exists():
            file_size = Path(output).stat().st_size
            console.print(f"File size: {file_size:,} bytes")
        
    except Exception as e:
        logger.error("Failed to generate gene expression data", error=str(e))
        console.print(f"Error: {str(e)}", style="red")
        sys.exit(1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main() 