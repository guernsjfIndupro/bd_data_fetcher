"""CLI graphing functionality for analyzing CSV files and generating graphs."""

import logging
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from bd_data_fetcher.data_handlers.utils import FileNames
from bd_data_fetcher.graphs import (
    DepMapGraph,
    ExternalProteinExpressionGraph,
    GeneExpressionGraph,
    InternalWCEGraph,
    UMapGraph,
)

logger = logging.getLogger(__name__)
console = Console()


class CSVGraphAnalyzer:
    """Analyzes CSV files and generates graphs based on available files.

    This class automatically detects which data types are present in the CSV directory
    and generates appropriate visualizations for each data type.
    """

    def __init__(self, data_dir_path: str):
        """Initialize the CSV graph analyzer.

        Args:
            data_dir_path: Path to the directory containing CSV files to analyze
        """
        self.data_dir_path = Path(data_dir_path)
        self.graph_generators: dict[str, object] = {
            FileNames.DEPMAP_DATA.value: DepMapGraph,
            FileNames.NORMAL_PROTEOMICS_DATA.value: ExternalProteinExpressionGraph,
            FileNames.EXTERNAL_PROTEOMICS_DATA.value: ExternalProteinExpressionGraph,
            FileNames.STUDY_SPECIFIC_DATA.value: ExternalProteinExpressionGraph,
            FileNames.NORMAL_GENE_EXPRESSION.value: GeneExpressionGraph,
            FileNames.GENE_EXPRESSION.value: GeneExpressionGraph,
            FileNames.GENE_TUMOR_NORMAL_RATIOS.value: GeneExpressionGraph,
            FileNames.WCE_DATA.value: InternalWCEGraph,
            FileNames.CELL_LINE_SIGMOIDAL_CURVES.value: InternalWCEGraph,
            FileNames.UMAP_DATA.value: UMapGraph,
            FileNames.CELL_LINE_TARGETING.value: UMapGraph,
        }

    def analyze_csv_directory(self) -> dict[str, list[str]]:
        """Analyze the CSV directory and identify available data types.

        Returns:
            Dictionary mapping data types to their corresponding file names
        """
        try:
            if not self.data_dir_path.exists():
                console.print(f"[red]Error: Data directory not found: {self.data_dir_path}[/red]")
                return {}

            # Read CSV directory to get file names
            csv_files = list(self.data_dir_path.glob("*.csv"))
            available_files = [f.name for f in csv_files]

            console.print(f"[green]Found {len(available_files)} CSV files in directory[/green]")

            # Map files to data types
            data_type_mapping = {}
            for file_name in available_files:
                for data_type in self.graph_generators.keys():
                    if file_name == data_type:
                        if data_type not in data_type_mapping:
                            data_type_mapping[data_type] = []
                        data_type_mapping[data_type].append(file_name)
                        break

            return data_type_mapping

        except Exception as e:
            console.print(f"[red]Error analyzing CSV directory: {e}[/red]")
            return {}

    def display_analysis_results(self, data_type_mapping: dict[str, list[str]]) -> None:
        """Display analysis results in a formatted table.

        Args:
            data_type_mapping: Dictionary mapping data types to file names
        """
        if not data_type_mapping:
            console.print("[yellow]No supported data types found[/yellow]")
            return

        table = Table(title="CSV Directory Analysis Results")
        table.add_column("Data Type", style="cyan")
        table.add_column("Files Found", style="green")
        table.add_column("Graph Generator", style="yellow")

        for data_type, files in data_type_mapping.items():
            graph_class = self.graph_generators.get(data_type, "Unknown")
            graph_name = graph_class.__name__ if hasattr(graph_class, '__name__') else str(graph_class)
            table.add_row(data_type, ", ".join(files), graph_name)

        console.print(table)

    def generate_all_graphs(self, output_dir: str, data_type_mapping: dict[str, list[str]]) -> bool:
        """Generate graphs for all detected data types.

        Args:
            output_dir: Directory to save generated graphs
            data_type_mapping: Dictionary mapping data types to file names

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
            # Only process DepMap copy number scatter plot; skip others
            allowed_graph_types = {"depmap_data.csv"}
            if data_type not in allowed_graph_types:
                console.print(f"[yellow]Skipping unsupported graph type: {data_type}[/yellow]")
                continue

            console.print(f"\n[cyan]Processing {data_type}...[/cyan]")

            try:
                graph_class = self.graph_generators[data_type]
                graph_instance = graph_class(str(self.data_dir_path))

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

            # Only process DepMap copy number scatter plot; skip others
            allowed_graph_types = {"depmap_data.csv"}
            if data_type not in allowed_graph_types:
                console.print(f"[yellow]Skipping unsupported graph type: {data_type}[/yellow]")
                continue

            console.print(f"\n[cyan]Processing {data_type}...[/cyan]")

            try:

                graph_class = self.graph_generators[data_type]
                graph_instance = graph_class(str(self.data_dir_path))

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
    data_dir: str = typer.Argument(..., help="Path to the directory containing CSV files to analyze"),
    output_dir: str = typer.Option("./graphs", help="Directory to save generated graphs"),
    data_types: list[str] | None = typer.Option(None, help="Specific data types to process"),
    show_analysis: bool = typer.Option(True, help="Show analysis results before generating graphs"),
) -> None:
    """Analyze CSV files and generate graphs based on available data.

    This command analyzes CSV files generated by the main data fetcher
    and automatically generates appropriate visualizations for each data type found.
    """
    try:
        # Initialize analyzer
        analyzer = CSVGraphAnalyzer(data_dir)

        # Analyze the CSV directory
        data_type_mapping = analyzer.analyze_csv_directory()

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
