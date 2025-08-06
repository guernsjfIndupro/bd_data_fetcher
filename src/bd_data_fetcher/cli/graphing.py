"""CLI graphing functionality for analyzing Excel files and generating graphs."""

import logging
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from bd_data_fetcher.data_handlers.utils import SheetNames
from bd_data_fetcher.graphs import (
    DepMapGraph,
    ExternalProteinExpressionGraph,
    GeneExpressionGraph,
    InternalWCEGraph,
    UMapGraph,
)

logger = logging.getLogger(__name__)
console = Console()


class ExcelGraphAnalyzer:
    """Analyzes Excel files and generates graphs based on available sheets.

    This class automatically detects which data types are present in the Excel file
    and generates appropriate visualizations for each data type.
    """

    def __init__(self, excel_file_path: str):
        """Initialize the Excel graph analyzer.

        Args:
            excel_file_path: Path to the Excel file to analyze
        """
        self.excel_file_path = Path(excel_file_path)
        self.graph_generators: dict[str, object] = {
            SheetNames.DEPMAP_DATA.value: DepMapGraph,
            SheetNames.NORMAL_PROTEOMICS_DATA.value: ExternalProteinExpressionGraph,
            SheetNames.EXTERNAL_PROTEOMICS_DATA.value: ExternalProteinExpressionGraph,
            SheetNames.NORMAL_GENE_EXPRESSION.value: GeneExpressionGraph,
            SheetNames.GENE_EXPRESSION.value: GeneExpressionGraph,
            SheetNames.GENE_TUMOR_NORMAL_RATIOS.value: GeneExpressionGraph,
            SheetNames.WCE_DATA.value: InternalWCEGraph,
            SheetNames.CELL_LINE_SIGMOIDAL_CURVES.value: InternalWCEGraph,
            SheetNames.UMAP_DATA.value: UMapGraph,
            SheetNames.CELL_LINE_TARGETING.value: UMapGraph,
        }

    def analyze_excel_file(self) -> dict[str, list[str]]:
        """Analyze the Excel file and identify available data types.

        Returns:
            Dictionary mapping data types to their corresponding sheet names
        """
        try:
            if not self.excel_file_path.exists():
                console.print(f"[red]Error: Excel file not found: {self.excel_file_path}[/red]")
                return {}

            # Read Excel file to get sheet names
            excel_file = pd.ExcelFile(self.excel_file_path)
            available_sheets = excel_file.sheet_names

            console.print(f"[green]Found {len(available_sheets)} sheets in Excel file[/green]")

            # Map sheets to data types
            data_type_mapping = {}
            for sheet_name in available_sheets:
                for data_type in self.graph_generators.keys():
                    if sheet_name == data_type:
                        if data_type not in data_type_mapping:
                            data_type_mapping[data_type] = []
                        data_type_mapping[data_type].append(sheet_name)
                        break

            return data_type_mapping

        except Exception as e:
            console.print(f"[red]Error analyzing Excel file: {e}[/red]")
            return {}

    def display_analysis_results(self, data_type_mapping: dict[str, list[str]]) -> None:
        """Display the analysis results in a formatted table.

        Args:
            data_type_mapping: Dictionary mapping data types to sheet names
        """
        if not data_type_mapping:
            console.print("[yellow]No supported data types found in Excel file[/yellow]")
            return

        table = Table(title="Excel File Analysis Results")
        table.add_column("Data Type", style="cyan")
        table.add_column("Graph Generator", style="green")
        table.add_column("Sheets", style="yellow")
        table.add_column("Supported Graphs", style="blue")

        # TODO: This is a placeholder for the actual graphs that will be generated.

        for data_type, sheets in data_type_mapping.items():
            graph_class = self.graph_generators[data_type]
            graph_class(str(self.excel_file_path))
            supported_graphs = [
                "Distribution plots",
                "Comparison charts",
                "Heatmaps",
                "Specialized plots"
            ]

            table.add_row(
                data_type,
                graph_class.__name__,
                ", ".join(sheets),
                ", ".join(supported_graphs)
            )

        console.print(table)

    def generate_all_graphs(self, output_dir: str, data_type_mapping: dict[str, list[str]]) -> bool:
        """Generate graphs for all detected data types.

        Args:
            output_dir: Directory to save generated graphs
            data_type_mapping: Dictionary mapping data types to sheet names

        Returns:
            True if all graphs were generated successfully, False otherwise
        """
        if not data_type_mapping:
            console.print("[yellow]No data types to process[/yellow]")
            return False

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        console.print(f"[green]Generating graphs in: {output_path}[/green]")

        success_count = 0
        total_count = len(data_type_mapping)

        for data_type in data_type_mapping.keys():
            # Only process WCE-related graphs; skip others
            wce_graph_types = {"wce_data", "cell_line_sigmoidal_curves"}
            if data_type not in wce_graph_types:
                console.print(f"[yellow]Skipping non-WCE graph: {data_type}[/yellow]")
                continue

            console.print(f"\n[cyan]Processing {data_type}...[/cyan]")

            try:
                graph_class = self.graph_generators[data_type]
                graph_instance = graph_class(str(self.excel_file_path))

                if graph_instance.generate_graphs(str(output_path)):
                    console.print(f"[green]✓ Successfully generated graphs for {data_type}[/green]")
                    success_count += 1
                else:
                    console.print(f"[red]✗ Failed to generate graphs for {data_type}[/red]")

            except Exception as e:
                console.print(f"[red]✗ Error processing {data_type}: {e}[/red]")

        console.print(f"\n[bold]Summary: {success_count}/{total_count} data types processed successfully[/bold]")
        return success_count == total_count

    def generate_specific_graphs(self, data_types: list[str], output_dir: str) -> bool:
        """Generate graphs for specific data types.

        Args:
            data_types: List of data types to process
            output_dir: Directory to save generated graphs

        Returns:
            True if all specified graphs were generated successfully, False otherwise
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        console.print(f"[green]Generating specific graphs in: {output_path}[/green]")

        success_count = 0
        total_count = len(data_types)

        for data_type in data_types:
            if data_type not in self.graph_generators:
                console.print(f"[red]✗ Unsupported data type: {data_type}[/red]")
                continue

            # Only process WCE-related graphs; skip others
            wce_graph_types = {"wce_data", "cell_line_sigmoidal_curves"}
            if data_type not in wce_graph_types:
                console.print(f"[yellow]Skipping non-WCE graph: {data_type}[/yellow]")
                continue

            console.print(f"\n[cyan]Processing {data_type}...[/cyan]")

            try:

                graph_class = self.graph_generators[data_type]
                graph_instance = graph_class(str(self.excel_file_path))

                if graph_instance.generate_graphs(str(output_path)):
                    console.print(f"[green]✓ Successfully generated graphs for {data_type}[/green]")
                    success_count += 1
                else:
                    console.print(f"[red]✗ Failed to generate graphs for {data_type}[/red]")

            except Exception as e:
                console.print(f"[red]✗ Error processing {data_type}: {e}[/red]")

        console.print(f"\n[bold]Summary: {success_count}/{total_count} data types processed successfully[/bold]")
        return success_count == total_count


def analyze_and_graph(
    excel_file: str = typer.Argument(..., help="Path to the Excel file to analyze"),
    output_dir: str = typer.Option("./graphs", help="Directory to save generated graphs"),
    data_types: list[str] | None = typer.Option(None, help="Specific data types to process"),
    show_analysis: bool = typer.Option(True, help="Show analysis results before generating graphs"),
) -> None:
    """Analyze Excel file and generate graphs based on available data.

    This command analyzes an Excel file generated by the main data fetcher
    and automatically generates appropriate visualizations for each data type found.
    """
    try:
        # Initialize analyzer
        analyzer = ExcelGraphAnalyzer(excel_file)

        # Analyze the Excel file
        data_type_mapping = analyzer.analyze_excel_file()

        if not data_type_mapping:
            console.print("[red]No supported data types found. Exiting.[/red]")
            raise typer.Exit(1)

        # Display analysis results
        if show_analysis:
            analyzer.display_analysis_results(data_type_mapping)

        # Generate graphs
        if data_types:
            # Generate graphs for specific data types
            success = analyzer.generate_specific_graphs(data_types, output_dir)
        else:
            # Generate graphs for all detected data types
            success = analyzer.generate_all_graphs(output_dir, data_type_mapping)

        if success:
            console.print(f"\n[bold green]✓ All graphs generated successfully in: {output_dir}[/bold green]")
        else:
            console.print("\n[bold yellow]⚠ Some graphs failed to generate. Check logs for details.[/bold yellow]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
