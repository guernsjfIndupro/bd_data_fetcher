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
    StringGraph,
    UMapGraph,
)

logger = logging.getLogger(__name__)
console = Console()


class CSVGraphAnalyzer:
    """Analyzes CSV files and generates graphs based on available files.

    This class automatically detects which data types are present in the CSV directory
    and generates appropriate visualizations for each data type.
    """

    def __init__(self, data_dir_path: str, anchor_protein: str):
        """Initialize the CSV graph analyzer.

        Args:
            data_dir_path: Path to the directory containing CSV files to analyze
            anchor_protein: Anchor protein symbol to use for graph generation
        """
        self.data_dir_path = Path(data_dir_path)
        self.anchor_protein = anchor_protein
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

    def _check_string_data_availability(self) -> bool:
        """Check if STRING data files are available for graph generation.
        
        Returns:
            True if both human_string_protein_scores.csv and gene_expression.csv exist
        """
        try:
            # Check for human_string_protein_scores.csv in the root directory (parent of data_dir)
            string_file = self.data_dir_path.parent / "human_string_protein_scores.csv"
            string_exists = string_file.exists()
            
            # Check for gene_expression.csv in the data directory
            gene_expr_file = self.data_dir_path / "gene_expression.csv"
            gene_expr_exists = gene_expr_file.exists()
            
            if string_exists and gene_expr_exists:
                console.print(f"[green]✓ STRING data files found - will generate protein interaction graphs[/green]")
                return True
            elif string_exists and not gene_expr_exists:
                console.print(f"[yellow]⚠ human_string_protein_scores.csv found but gene_expression.csv missing[/yellow]")
            elif not string_exists and gene_expr_exists:
                console.print(f"[yellow]⚠ gene_expression.csv found but human_string_protein_scores.csv missing[/yellow]")
            else:
                console.print(f"[blue]ℹ No STRING data files found - skipping protein interaction graphs[/blue]")
            
            return False
            
        except Exception as e:
            console.print(f"[red]Error checking STRING data availability: {e}[/red]")
            return False

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

        # Process regular data types
        for data_type in data_type_mapping.keys():
            console.print(f"\n[cyan]Processing {data_type}...[/cyan]")

            try:
                graph_class = self.graph_generators[data_type]
                graph_instance = graph_class(str(self.data_dir_path), self.anchor_protein)

                if graph_instance.generate_graphs(str(output_path)):
                    console.print(f"[green]✓ Successfully generated graphs for {data_type}[/green]")
                    success_count += 1
                else:
                    console.print(f"[red]✗ Failed to generate graphs for {data_type}[/red]")

            except Exception as e:
                console.print(f"[red]✗ Error processing {data_type}: {e}[/red]")

        # Check for STRING data and generate protein interaction graphs
        if self._check_string_data_availability():
            console.print(f"\n[cyan]Processing STRING protein-protein interactions...[/cyan]")
            total_count += 1
            
            try:
                # Create StringGraph with default thresholds
                string_graph = StringGraph(
                    data_dir_path=str(self.data_dir_path),
                    anchor_protein=self.anchor_protein
                )

                if string_graph.generate_graphs(str(output_path)):
                    console.print(f"[green]✓ Successfully generated STRING protein interaction graphs[/green]")
                    success_count += 1
                else:
                    console.print(f"[red]✗ Failed to generate STRING protein interaction graphs[/red]")

            except Exception as e:
                console.print(f"[red]✗ Error processing STRING data: {e}[/red]")

        console.print(f"\n[bold]Summary: {success_count}/{total_count} data types processed successfully[/bold]")
        return success_count == total_count




def analyze_and_graph(
    data_dir: str = typer.Argument(..., help="Path to the directory containing CSV files to analyze"),
    anchor_protein: str = typer.Argument(..., help="Anchor protein symbol (e.g., EGFR, TP53)"),
    output_dir: str = typer.Option("./graphs", help="Directory to save generated graphs"),
) -> None:
    """Analyze CSV files and generate graphs based on available data.

    This command analyzes CSV files generated by the main data fetcher
    and automatically generates appropriate visualizations for each data type found.
    
    If both human_string_protein_scores.csv (in project root) and gene_expression.csv 
    (in data directory) are present, it will also generate protein-protein interaction 
    network graphs using STRING database data.
    """
    try:
        # Initialize analyzer
        analyzer = CSVGraphAnalyzer(data_dir, anchor_protein)

        # Analyze the CSV directory
        data_type_mapping = analyzer.analyze_csv_directory()

        if not data_type_mapping:
            console.print("[red]No supported data types found. Exiting.[/red]")
            raise typer.Exit(1)

        # Generate all graphs
        success = analyzer.generate_all_graphs(output_dir, data_type_mapping)

        if success:
            console.print(f"\n[bold green]✓ All graphs generated successfully in: {output_dir}[/bold green]")
        else:
            console.print("\n[bold yellow]⚠ Some graphs failed to generate. Check logs for details.[/bold yellow]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
