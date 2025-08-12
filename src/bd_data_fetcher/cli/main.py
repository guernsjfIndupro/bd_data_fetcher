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


def setup_logging(log_level: str) -> None:
    """Setup structured logging with the specified log level."""
    import logging

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def display_data_handlers_overview() -> None:
    """Display an overview of available data handlers."""
    table = Table(title="Data Handlers Overview")
    table.add_column("Handler", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Output Files", style="yellow")

    handlers_info = [
        (
            "GeneExpressionDataHandler",
            "Processes gene expression data from TCGA/GTEX",
            "normal_gene_expression.csv, gene_expression.csv, gene_tumor_normal_ratios.csv"
        ),
        (
            "uMapDataHandler",
            "Manages UMap analysis results",
            "umap_data.csv"
        ),
        (
            "WCEDataHandler",
            "Processes Whole Cell Extract DIA proteomics data",
            "wce_data.csv, cell_line_sigmoidal_curves.csv"
        ),
        (
            "DepMapDataHandler",
            "Handles DepMap cell line data",
            "depmap_data.csv"
        ),
        (
            "ExternalProteinExpressionDataHandler",
            "Manages external proteomics data from various cancer studies",
            "normal_proteomics_data.csv, study_specific_data.csv, protein_expression.csv"
        ),
    ]

    for handler, description, outputs in handlers_info:
        table.add_row(handler, description, outputs)

    console.print(table)


@app.command()
def data(
    symbols: list[str] = typer.Argument(
        ..., help="List of protein symbols (e.g., EGFR TP53 BRCA1)"
    ),
    output_dir: str = typer.Option(
        "output", "--output-dir", "-o", help="Output directory for CSV files"
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
    display_data_handlers_overview()

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
        gene_handler = GeneExpressionDataHandler()
        umap_handler = uMapDataHandler()
        wce_handler = WCEDataHandler()
        depmap_handler = DepMapDataHandler()
        external_protein_handler = ExternalProteinExpressionDataHandler()

        # Retrieve all cell lines for all proteins and combine them
        console.print(f"\n[bold]Retrieving cell lines for {len(symbol_mappings)} proteins...[/bold]")
        all_cell_lines = set()
        for symbol, uniprotkb_ac in symbol_mappings.items():
            try:
                cell_lines = umap_handler.get_cell_lines(uniprotkb_ac)
                all_cell_lines.update(cell_lines)
                console.print(f"  [green]✓[/green] {symbol}: Found {len(cell_lines)} cell lines")
            except Exception as e:
                console.print(f"  [yellow]⚠[/yellow] {symbol}: Failed to get cell lines: {e}")
                continue

        console.print(f"[bold]Combined cell line set: {len(all_cell_lines)} unique cell lines[/bold]")

        # Generate gene expression data for each protein
        console.print(
            f"\n[bold]Generating data for {len(symbol_mappings)} proteins...[/bold]"
        )

        # Generate cell line sigmoidal curves
        console.print(f"\n[bold]Generating cell line sigmoidal curves...[/bold]")
        wce_handler.build_cell_line_sigmoidal_curves_csv(all_cell_lines, output_dir)

        for i, (symbol, uniprotkb_ac) in enumerate(symbol_mappings.items(), 1):
            console.print(f"\n[bold cyan]Processing {symbol} ({uniprotkb_ac})...[/bold cyan]")

            try:
                # Generate all data types using the combined cell line set
                # external_protein_handler.build_normal_proteomics_csv(uniprotkb_ac, output_dir)

                wce_data = wce_handler.build_wce_data_csv(uniprotkb_ac, all_cell_lines, output_dir)
                depmap_data = depmap_handler.build_dep_map_data_csv([uniprotkb_ac], folder_path=output_dir, cell_line_set=all_cell_lines)
                external_protein_handler.build_normal_proteomics_csv(uniprotkb_ac, output_dir)
                external_protein_handler.build_protein_expression_csv(uniprotkb_ac, output_dir)
                external_protein_handler.build_study_specific_csv(uniprotkb_ac, output_dir)
                gene_handler.build_normal_gene_expression_csv(uniprotkb_ac, output_dir)
                gene_handler.build_gene_expression_csv(uniprotkb_ac, output_dir)
                gene_handler.build_gene_tumor_normal_ratios_csv(uniprotkb_ac, output_dir)
                umap_handler.get_umap_data_csv(uniprotkb_ac, output_dir)

                console.print(f"  [bold green]✓[/bold green] Completed {symbol}")

            except Exception as e:
                logger.exception(f"Failed to process protein {i}/{len(symbol_mappings)}",
                               symbol=symbol, uniprotkb_ac=uniprotkb_ac, error=str(e))
                console.print(
                    f"  [bold red]✗[/bold red] Failed to process {symbol}: {e!s}", style="red"
                )
                continue

        # Generate summary
        processed_count = len(symbol_mappings)
        console.print(f"\n[bold green]✓[/bold green] Completed processing {processed_count} proteins")
        console.print(f"[bold green]✓[/bold green] Data saved to: {output_dir}")

        # Show directory information
        output_path = Path(output_dir)
        if output_path.exists():
            csv_files = list(output_path.glob("*.csv"))
            total_size = sum(f.stat().st_size for f in csv_files)
            console.print(f"[bold]Generated {len(csv_files)} CSV files ({total_size:,} bytes)[/bold]")

    except Exception as e:
        logger.exception("Failed to generate gene expression data", error=str(e))
        console.print(f"Error: {e!s}", style="red")
        sys.exit(1)


@app.command()
def graph(
    data_dir: str = typer.Argument(..., help="Path to the directory containing CSV files to analyze"),
    anchor_protein: str = typer.Argument(..., help="Anchor protein symbol (e.g., EGFR, TP53)"),
    output_dir: str = typer.Option("./graphs", help="Directory to save generated graphs"),
):
    """
    Analyze CSV files and generate graphs based on available data.

    This command analyzes CSV files generated by the main data fetcher
    and automatically generates appropriate visualizations for each data type found.
    The anchor protein is used as a reference point for all generated graphs.
    """
    analyze_and_graph(data_dir, anchor_protein, output_dir)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
