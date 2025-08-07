"""Main CLI application for BD Data Fetcher."""

import sys
from pathlib import Path

import requests
import structlog
import typer
from rich.console import Console
from rich.table import Table

from bd_data_fetcher.api.umap_client import UMapServiceClient
from bd_data_fetcher.cli.graphing import analyze_and_graph
from bd_data_fetcher.data_handlers.depmap import DepMapDataHandler
from bd_data_fetcher.data_handlers.external_protein_expression import (
    ExternalProteinExpressionDataHandler,
)
from bd_data_fetcher.data_handlers.gene_expression import GeneExpressionDataHandler
from bd_data_fetcher.data_handlers.internal_wce import WCEDataHandler
from bd_data_fetcher.data_handlers.umap import uMapDataHandler

# Initialize Typer app
app = typer.Typer(
    name="bd-fetcher",
    help="A CLI tool for generating gene expression data from protein symbols",
    add_completion=False,
)

# Initialize console for rich output
console = Console()


# Configure logging
def setup_logging(log_level: str = "INFO", log_file: str | None = None):
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
def data(
    symbols: list[str] = typer.Argument(
        ..., help="List of protein symbols (e.g., EGFR TP53 BRCA1)"
    ),
    output: str = typer.Option(
        "output.xlsx", "--output", "-o", help="Output Excel file name"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """
    Generate gene expression data for protein symbols.

    Maps protein symbols to UniProtKB accession numbers and generates comprehensive gene expression data.
    """
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    logger = structlog.get_logger(__name__)

    # Display data handlers information first
    console.print("\n[bold cyan]Data Handlers Overview:[/bold cyan]")
    handlers_table = Table(title="Available Data Handlers")
    handlers_table.add_column("Handler", style="cyan", width=30)
    handlers_table.add_column("Description", style="green", width=60)
    handlers_table.add_column("Output Sheets", style="yellow", width=40)

    handlers_table.add_row(
        "GeneExpressionDataHandler",
        "Retrieves and prepares gene expression data including normal expression, all expression data, and tumor/normal ratios",
        "normal_gene_expression, gene_expression, gene_tumor_normal_ratios"
    )
    handlers_table.add_row(
        "uMapDataHandler", 
        "Retrieves and prepares uMap data",
        "umap_data, cell_line_targeting"
    )
    handlers_table.add_row(
        "WCEDataHandler",
        "Processes Whole Cell Extract DIA data and generates sigmoidal curves for cell lines",
        "wce_data, cell_line_sigmoidal_curves"
    )
    handlers_table.add_row(
        "DepMapDataHandler",
        "Handles DepMap dependency mapping data for cancer cell lines",
        "depmap_data"
    )
    handlers_table.add_row(
        "ExternalProteinExpressionDataHandler",
        "Manages external proteomics data including normal expression and study-specific data",
        "normal_proteomics_data, external_proteomics_data, study_specific_data"
    )

    console.print(handlers_table)

    try:
        # Initialize UMap client
        umap_client = UMapServiceClient()

        # Map protein symbols to UniProtKB accession numbers
        console.print(
            f"\nMapping {len(symbols)} protein symbols to UniProtKB accession numbers..."
        )
        
        # Add timeout and error handling for the API call
        try:
            symbol_mappings = umap_client.map_protein(symbols)
        except requests.exceptions.Timeout:
            console.print("Error: API request timed out. Please check your internet connection and try again.", style="red")
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            console.print("Error: Could not connect to the API server. Please check your internet connection.", style="red")
            sys.exit(1)
        except Exception as e:
            console.print(f"Error: Failed to map protein symbols: {e}", style="red")
            sys.exit(1)

        if not symbol_mappings:
            console.print(
                "No protein mappings found. Please check your protein symbols.",
                style="red",
            )
            sys.exit(1)

        # Display mappings
        table = Table(title="Protein Symbol Mappings")
        table.add_column("Symbol", style="cyan")
        table.add_column("UniProtKB AC", style="green")

        for symbol, uniprotkb_ac in symbol_mappings.items():
            table.add_row(symbol, uniprotkb_ac)

        console.print(table)
        console.print(f"Successfully mapped {len(symbol_mappings)} proteins")

        # Initialize data handlers
        GeneExpressionDataHandler()
        umap_handler = uMapDataHandler()
        wce_handler = WCEDataHandler()
        DepMapDataHandler()
        ExternalProteinExpressionDataHandler()

        # Generate gene expression data for each protein
        console.print(
            f"\n[bold]Generating data for {len(symbol_mappings)} proteins...[/bold]"
        )

        for symbol, uniprotkb_ac in symbol_mappings.items():
            console.print(f"Processing {symbol} ({uniprotkb_ac})...")

            try:
                # Generate all three types of gene expression data
                # gene_handler.build_normal_gene_expression_sheet(uniprotkb_ac, output)
                # gene_handler.build_gene_expression_sheet(uniprotkb_ac, output)
                # gene_handler.build_gene_tumor_normal_ratios_sheet(uniprotkb_ac, output)



                # umap_handler.get_umap_data(uniprotkb_ac, output)

                cell_line_set = umap_handler.get_cell_lines(uniprotkb_ac)

                console.print(f"Found {len(cell_line_set)} cell lines for {symbol}")

                # Generate WCE data sheet
                if cell_line_set:
                    wce_data = wce_handler.build_wce_data_sheet(uniprotkb_ac, cell_line_set, output)
                    console.print(f"Generated WCE data sheet with {len(wce_data)} records for {symbol}")
                else:
                    console.print(f"No cell lines found for {symbol}, skipping WCE data generation", style="yellow")

                # Generate DepMap data sheet
                # depmap_data = depmap_handler.build_dep_map_data_sheet([uniprotkb_ac], file_path=output, cell_line_set=cell_line_set)
                # console.print(f"Generated DepMap data sheet with {len(depmap_data)} records for {symbol}")

                # Generate normal proteomics data sheet
                # external_protein_handler.build_normal_proteomics_sheet(uniprotkb_ac, output)
                # console.print(f"Generated normal proteomics data sheet records for {symbol}")

                wce_handler.build_cell_line_sigmoidal_curves(cell_line_set, output)
                # external_protein_handler.build_study_specific_sheet(
                #     uniprotkb_ac, output
                # )
                console.print(
                    f"Generated study specific proteomics data sheet records for {symbol}"
                )

                console.print(f"Completed processing {symbol}")

            except Exception as e:
                logger.exception(f"Failed to process {symbol}", error=str(e))
                console.print(
                    f"Warning: Failed to process {symbol}: {e!s}", style="yellow"
                )
                continue

        console.print(f"Gene expression data saved to: {output}")
        console.print(f"Processed {len(symbol_mappings)} proteins successfully")

        # Show file information
        if Path(output).exists():
            file_size = Path(output).stat().st_size
            console.print(f"File size: {file_size:,} bytes")

    except Exception as e:
        logger.exception("Failed to generate gene expression data", error=str(e))
        console.print(f"Error: {e!s}", style="red")
        sys.exit(1)


@app.command()
def graph(
    excel_file: str = typer.Argument(..., help="Path to the Excel file to analyze"),
    output_dir: str = typer.Option("./graphs", help="Directory to save generated graphs"),
    data_types: list[str] = typer.Option(None, help="Specific data types to process"),
    show_analysis: bool = typer.Option(True, help="Show analysis results before generating graphs"),
):
    """
    Analyze Excel file and generate graphs based on available data.

    This command analyzes an Excel file generated by the main data fetcher
    and automatically generates appropriate visualizations for each data type found.
    """
    analyze_and_graph(excel_file, output_dir, data_types, show_analysis)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
