"""Gene expression data visualization graphs."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import FileNames
from bd_data_fetcher.graphs.base_graph import BaseGraph

logger = logging.getLogger(__name__)


class GeneExpressionGraph(BaseGraph):
    """Graph generator for gene expression data.

    This class handles visualization of gene expression data,
    including normal expression, tumor-normal ratios, and expression distributions.
    Uses an anchor protein as a reference point for visualizations.
    """

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for gene expression data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating gene expression graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_csv_data():
                return False

        success = True

        # Generate normal gene expression plot
        if self._generate_normal_gene_expression_plot(output_dir):
            logger.info("Generated normal gene expression plot")
        else:
            success = False

        # Generate gene expression distribution plot
        if self._generate_gene_expression_distribution_plot(output_dir):
            logger.info("Generated gene expression distribution plot")
        else:
            success = False

        return success

    def _generate_normal_gene_expression_plot(self, output_dir: str) -> bool:
        """Generate expression plots for normal gene expression data.

        Creates heatmaps showing:
        - X-axis: Primary sites
        - Y-axis: Genes
        - Color intensity: Expression values

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get normal gene expression data
            df = self.get_data_for_file(FileNames.NORMAL_GENE_EXPRESSION.value)
            if df is None or df.empty:
                logger.error("No normal gene expression data available")
                return False

            # Check for required columns
            required_columns = ['Gene']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in normal gene expression data: {missing_columns}")
                return False

            # Get expression columns (all columns except 'Gene')
            expression_columns = [col for col in df.columns if col != 'Gene']
            
            if not expression_columns:
                logger.error("No expression columns found in normal gene expression data")
                return False

            # Set up the plot
            plt.figure(figsize=(max(12, len(expression_columns) * 0.8), max(8, len(df) * 0.3)))
            sns.set_style("whitegrid")

            # Prepare data for heatmap
            heatmap_data = df.set_index('Gene')[expression_columns]

            # Create heatmap
            sns.heatmap(
                heatmap_data,
                annot=False,
                cmap='Blues',
                cbar_kws={'label': 'Expression Value'},
                linewidths=0.2,
                linecolor='white',
                square=True
            )

            # Customize the plot
            plt.title('Normal Gene Expression Data', fontsize=16, fontweight='bold', pad=25)
            plt.xlabel('Primary Sites', fontsize=14, fontweight='bold')
            plt.ylabel('Genes', fontsize=14, fontweight='bold')

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)

            plt.tight_layout()

            # Save the plot
            filename = "normal_gene_expression.png"
            output_path = Path(output_dir) / "gene_expression" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved normal gene expression plot: {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating normal gene expression plot: {e}")
            return False

    def _generate_gene_expression_distribution_plot(self, output_dir: str) -> bool:
        """Generate distribution plots for gene expression data.

        Creates box plots showing:
        - X-axis: Primary sites
        - Y-axis: Expression values
        - Grouped by cancer status

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get gene expression data
            df = self.get_data_for_file(FileNames.GENE_EXPRESSION.value)
            if df is None or df.empty:
                logger.error("No gene expression data available")
                return False

            # Check for required columns
            required_columns = ['Expression Value', 'Primary Site', 'Is Cancer']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in gene expression data: {missing_columns}")
                return False

            # Ensure numeric column is properly formatted
            df['Expression Value'] = pd.to_numeric(df['Expression Value'], errors='coerce')

            # Remove rows with NaN values
            df = df.dropna(subset=['Expression Value', 'Primary Site', 'Is Cancer'])

            if df.empty:
                logger.error("No valid numeric data found in gene expression data")
                return False

            # Set up the plot
            plt.figure(figsize=(15, 10))
            sns.set_style("whitegrid")

            # Create box plot by primary site and cancer status
            sns.boxplot(
                data=df,
                x='Primary Site',
                y='Expression Value',
                hue='Is Cancer',
                palette=['#2ecc71', '#e74c3c']  # Green for normal, red for cancer
            )

            # Customize the plot
            plt.title('Gene Expression Distribution by Primary Site and Cancer Status', fontsize=16, fontweight='bold', pad=25)
            plt.xlabel('Primary Site', fontsize=14, fontweight='bold')
            plt.ylabel('Expression Value', fontsize=14, fontweight='bold')

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')

            # Update legend labels
            plt.legend(title='Cancer Status', labels=['Normal', 'Cancer'], loc='upper right')

            plt.tight_layout()

            # Save the plot
            filename = "gene_expression_distribution.png"
            output_path = Path(output_dir) / "gene_expression" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved gene expression distribution plot: {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating gene expression distribution plot: {e}")
            return False
