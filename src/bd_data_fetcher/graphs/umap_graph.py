"""UMap data visualization graphs."""

import logging

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import SheetNames
from bd_data_fetcher.graphs.base_graph import BaseGraph

logger = logging.getLogger(__name__)


class UMapGraph(BaseGraph):
    """Graph generator for UMap data.

    This class handles visualization of UMap data,
    including cell line information and protein targeting data.
    """

    def get_supported_sheets(self) -> list[str]:
        """Get list of sheet names that this graph class can process.

        Returns:
            List of supported sheet names
        """
        return [SheetNames.UMAP_DATA.value, SheetNames.CELL_LINE_TARGETING.value]

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for UMap data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating UMap graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_excel_data():
                return False

        success = True

        # Generate cell line comparison
        if self._generate_volcano_plots(output_dir):
            logger.info("Generated cell line comparison")
        else:
            success = False

        return success

    def _generate_volcano_plots(self, output_dir: str) -> bool:
        """Generate volcano plots of UMap data.

        Creates professional volcano plots showing:
        - X-axis: Log2 Fold Change
        - Y-axis: -log10 P-value
        - Significant points highlighted
        - Chemistry, cell line, and target protein in title

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get UMap data
            df = self.get_sheet_data(SheetNames.UMAP_DATA.value)
            if df is None or df.empty:
                logger.error("No UMap data available")
                return False

            # Check for required columns
            required_columns = ['Log2 FC', 'P-value', 'Cell Line', 'Chemistry', 'Target Protein', 'Protein Symbol']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in UMap data: {missing_columns}")
                logger.info(f"Available columns: {list(df.columns)}")
                return False

            # Ensure numeric columns are properly formatted
            df['Log2 FC'] = pd.to_numeric(df['Log2 FC'], errors='coerce')
            df['P-value'] = pd.to_numeric(df['P-value'], errors='coerce')

            # Remove rows with NaN values
            df = df.dropna(subset=['Log2 FC', 'P-value'])
            if df.empty:
                logger.error("No valid numeric data found in Log2 FC or P-value columns")
                return False

                        # Get unique replicate set IDs
            unique_replicate_sets = df['Replicate Set ID'].unique()
            
            # Get all target proteins from all UMap data (not just current replicate set)
            all_target_proteins = df['Target Protein'].unique()
            
            logger.info(f"Creating volcano plots for {len(unique_replicate_sets)} replicate sets")
            logger.info(f"Found {len(all_target_proteins)} unique target proteins across all replicate sets")

            # Set Seaborn style for professional medical appearance
            sns.set_style("whitegrid")
            sns.set_palette(["#45cfe0"])  # Use the specified light blue color

            # Create volcano plot for each replicate set ID
            for replicate_set_id in unique_replicate_sets:
                # Filter data for this replicate set
                plot_data = df[df['Replicate Set ID'] == replicate_set_id]
                
                if plot_data.empty:
                    logger.warning(f"No data found for replicate set ID: {replicate_set_id}")
                    continue
                
                # Get metadata for this replicate set (should be consistent within a replicate set)
                cell_line = plot_data['Cell Line'].iloc[0]
                chemistry = plot_data['Chemistry'].iloc[0]
                target_protein = plot_data['Target Protein'].iloc[0]

                # Highlight target proteins from ALL replicate sets (not just current one)
                target_points = plot_data[plot_data['Protein Symbol'].isin(all_target_proteins)]

                # Create the volcano plot
                plt.figure(figsize=(12, 10))

                # Plot all points
                plt.scatter(
                    plot_data['Log2 FC'],
                    plot_data['P-value'],
                    alpha=0.6,
                    color='#45cfe0',
                    s=50,
                    edgecolors='#2a9bb3',
                    linewidth=0.5
                )

                # Highlight target proteins from ALL replicate sets (not just current one)
                target_points = plot_data[plot_data['Protein Symbol'].isin(all_target_proteins)]

                if not target_points.empty:
                    plt.scatter(
                        target_points['Log2 FC'],
                        target_points['P-value'],
                        color='#ff6b6b',  # Red for target proteins
                        s=80,
                        alpha=0.8,
                        edgecolors='#d63031',
                        linewidth=1,
                        zorder=5
                    )

                    # Add labels for target proteins
                    for _, point in target_points.iterrows():
                        plt.annotate(
                            point['Protein Symbol'],
                            xy=(point['Log2 FC'], point['P-value']),
                            xytext=(5, 5),
                            textcoords='offset points',
                            fontsize=8,
                            fontweight='bold',
                            color='#2a9bb3',
                            bbox={
                                "boxstyle": 'round,pad=0.3',
                                "facecolor": 'white',
                                "edgecolor": '#45cfe0',
                                "alpha": 0.8
                            },
                            arrowprops={
                                "arrowstyle": '->',
                                "color": '#45cfe0',
                                "alpha": 0.7
                            }
                        )

                # Customize the plot
                plt.title(
                    f'Volcano Plot: {target_protein} in {cell_line}\nChemistry: {chemistry}\nReplicate Set: {replicate_set_id}',
                    fontsize=16,
                    fontweight='bold',
                    pad=25
                )
                plt.xlabel('Log2 Fold Change', fontsize=14, fontweight='bold')
                plt.ylabel('-log10 P-value', fontsize=14, fontweight='bold')

                # Set axis limits with some padding
                x_min, x_max = plot_data['Log2 FC'].min(), plot_data['Log2 FC'].max()
                _y_min, y_max = plot_data['P-value'].min(), plot_data['P-value'].max()

                plt.xlim(x_min - 0.5, x_max + 0.5)
                plt.ylim(0, y_max + 0.5)

                # Add grid
                plt.grid(True, alpha=0.3)

                # Add statistics text
                total_points = len(plot_data)
                target_count = len(target_points)
                plt.figtext(
                    0.02, 0.02,
                    f'Total proteins: {total_points}\nTarget proteins: {target_count}',
                    fontsize=10,
                    bbox={
                        "boxstyle": 'round,pad=0.5',
                        "facecolor": 'white',
                        "edgecolor": '#45cfe0',
                        "alpha": 0.8
                    }
                )

                plt.tight_layout()

                # Save the plot
                safe_cell_line = cell_line.replace(' ', '_').replace('/', '_')
                safe_chemistry = chemistry.replace(' ', '_').replace('/', '_')
                safe_replicate_id = str(replicate_set_id).replace(' ', '_').replace('/', '_')
                filename = f"volcano_plot_{target_protein}_{safe_cell_line}_{safe_chemistry}_{safe_replicate_id}.png"

                if not self.save_graph(plt.gcf(), filename, output_dir):
                    logger.error(f"Failed to save volcano plot for replicate set {replicate_set_id}")
                    return False

                plt.close()
                logger.info(f"Generated volcano plot for replicate set {replicate_set_id} ({cell_line} - {chemistry} - {target_protein})")

            logger.info("Successfully generated all volcano plots")
            return True

        except Exception as e:
            logger.exception(f"Error generating volcano plots: {e}")
            return False
