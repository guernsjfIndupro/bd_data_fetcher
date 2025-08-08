"""UMap data visualization graphs."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import FileNames
from bd_data_fetcher.graphs.base_graph import BaseGraph

logger = logging.getLogger(__name__)


class UMapGraph(BaseGraph):
    """Graph generator for UMap data.

    This class handles visualization of UMap analysis results,
    including log2 fold changes, p-values, and cell line targeting data.
    Uses an anchor protein as a reference point for visualizations.
    """

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
            if not self.load_csv_data():
                return False

        success = True

        # Generate volcano plot
        if self._generate_volcano_plot(output_dir):
            logger.info("Generated volcano plot")
        else:
            success = False

        return success

    def _generate_volcano_plot(self, output_dir: str) -> bool:
        """Generate volcano plots for UMap analysis results.

        Creates separate volcano plots for each replicate set showing:
        - X-axis: Log2 fold change
        - Y-axis: -log10(p-value)
        - Points colored by significance

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get UMap data
            df = self.get_data_for_file(FileNames.UMAP_DATA.value)
            if df is None or df.empty:
                logger.error("No UMap data available")
                return False

            # Check for required columns
            required_columns = ['Log2 FC', 'P-value', 'Protein Symbol', 'Replicate Set ID']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in UMap data: {missing_columns}")
                return False

            # Ensure numeric columns are properly formatted
            df['Log2 FC'] = pd.to_numeric(df['Log2 FC'], errors='coerce')
            df['P-value'] = pd.to_numeric(df['P-value'], errors='coerce')

            # Remove rows with NaN values
            df = df.dropna(subset=['Log2 FC', 'P-value', 'Protein Symbol', 'Replicate Set ID'])

            if df.empty:
                logger.error("No valid numeric data found in UMap data")
                return False

            # The P-value column already contains -log10(p-value) values
            df['-log10_pvalue'] = df['P-value']



            # Get unique replicate set IDs
            replicate_set_ids = df['Replicate Set ID'].unique()
            
            if len(replicate_set_ids) == 0:
                logger.error("No replicate set IDs found in UMap data")
                return False

            logger.info(f"Generating volcano plots for {len(replicate_set_ids)} replicate sets")

            success_count = 0
            total_count = len(replicate_set_ids)

            # Generate one volcano plot per replicate set
            for replicate_set_id in replicate_set_ids:
                try:
                    # Filter data for current replicate set
                    replicate_df = df[df['Replicate Set ID'] == replicate_set_id]
                    
                    if replicate_df.empty:
                        logger.warning(f"No data found for replicate set ID: {replicate_set_id}")
                        continue

                    # Get additional info for the plot title
                    cell_line = replicate_df['Cell Line'].iloc[0] if 'Cell Line' in replicate_df.columns else "Unknown"
                    chemistry = replicate_df['Chemistry'].iloc[0] if 'Chemistry' in replicate_df.columns else "Unknown"
                    target_protein = replicate_df['Target Protein'].iloc[0] if 'Target Protein' in replicate_df.columns else "Unknown"

                    # Set up the plot
                    plt.figure(figsize=(12, 10))
                    sns.set_style("whitegrid")

                    # Create scatter plot - all points uniform
                    plt.scatter(
                        replicate_df['Log2 FC'],
                        replicate_df['-log10_pvalue'],
                        alpha=0.7,
                        color='#2a9bb3',
                        s=50
                    )



                    # Customize the plot
                    plt.title(f'UMap Analysis Results - Volcano Plot\nReplicate Set {replicate_set_id}\nCell Line: {cell_line} | Chemistry: {chemistry} | Target: {target_protein}', 
                             fontsize=16, fontweight='bold', pad=25)
                    plt.xlabel('Log2 Fold Change', fontsize=14, fontweight='bold')
                    plt.ylabel('-log10(p-value)', fontsize=14, fontweight='bold')



                    # Remove top and right borders
                    ax = plt.gca()
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)

                    plt.tight_layout()

                    # Save the plot
                    filename = f"umap_volcano_plot_replicate_set_{replicate_set_id}.png"
                    output_path = Path(output_dir) / "umap" / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    plt.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close()

                    logger.info(f"Saved volcano plot for replicate set {replicate_set_id}: {output_path}")
                    success_count += 1

                except Exception as e:
                    logger.exception(f"Error generating volcano plot for replicate set {replicate_set_id}: {e}")
                    continue

            logger.info(f"Generated {success_count}/{total_count} volcano plots successfully")
            return success_count > 0

        except Exception as e:
            logger.exception(f"Error generating volcano plots: {e}")
            return False
