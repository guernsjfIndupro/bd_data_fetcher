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

        Creates volcano plots showing:
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
            required_columns = ['Log2 FC', 'P-value', 'Protein Symbol']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in UMap data: {missing_columns}")
                return False

            # Ensure numeric columns are properly formatted
            df['Log2 FC'] = pd.to_numeric(df['Log2 FC'], errors='coerce')
            df['P-value'] = pd.to_numeric(df['P-value'], errors='coerce')

            # Remove rows with NaN values
            df = df.dropna(subset=['Log2 FC', 'P-value', 'Protein Symbol'])

            if df.empty:
                logger.error("No valid numeric data found in UMap data")
                return False

            # Calculate -log10(p-value)
            df['-log10_pvalue'] = -np.log10(df['P-value'])

            # Set significance thresholds
            log2fc_threshold = 1.0
            pvalue_threshold = 0.05

            # Create significance categories
            df['Significance'] = 'Not Significant'
            significant_up = (df['Log2 FC'] > log2fc_threshold) & (df['P-value'] < pvalue_threshold)
            significant_down = (df['Log2 FC'] < -log2fc_threshold) & (df['P-value'] < pvalue_threshold)
            df.loc[significant_up, 'Significance'] = 'Significantly Up'
            df.loc[significant_down, 'Significance'] = 'Significantly Down'

            # Set up the plot
            plt.figure(figsize=(12, 10))
            sns.set_style("whitegrid")

            # Create scatter plot
            colors = {'Not Significant': '#808080', 'Significantly Up': '#ff4444', 'Significantly Down': '#4444ff'}
            
            for significance, color in colors.items():
                subset = df[df['Significance'] == significance]
                if not subset.empty:
                    plt.scatter(
                        subset['Log2 FC'],
                        subset['-log10_pvalue'],
                        alpha=0.7,
                        color=color,
                        s=50,
                        label=significance
                    )

            # Add threshold lines
            plt.axhline(y=-np.log10(pvalue_threshold), color='red', linestyle='--', alpha=0.8, label=f'p-value = {pvalue_threshold}')
            plt.axvline(x=log2fc_threshold, color='red', linestyle='--', alpha=0.8, label=f'Log2 FC = {log2fc_threshold}')
            plt.axvline(x=-log2fc_threshold, color='red', linestyle='--', alpha=0.8, label=f'Log2 FC = -{log2fc_threshold}')

            # Customize the plot
            plt.title('UMap Analysis Results - Volcano Plot', fontsize=16, fontweight='bold', pad=25)
            plt.xlabel('Log2 Fold Change', fontsize=14, fontweight='bold')
            plt.ylabel('-log10(p-value)', fontsize=14, fontweight='bold')

            # Add legend
            plt.legend(title='Significance', loc='upper right', fontsize=10)

            plt.tight_layout()

            # Save the plot
            filename = "umap_volcano_plot.png"
            output_path = Path(output_dir) / "umap" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved volcano plot: {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating volcano plot: {e}")
            return False
