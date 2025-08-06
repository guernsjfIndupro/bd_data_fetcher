"""Gene Expression data visualization graphs."""

import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import SheetNames
from bd_data_fetcher.graphs.base_graph import BaseGraph

logger = logging.getLogger(__name__)


class GeneExpressionGraph(BaseGraph):
    """Graph generator for Gene Expression data.

    This class handles visualization of gene expression data,
    including normal gene expression, tumor-normal ratios, and expression patterns.
    """

    def get_supported_sheets(self) -> list[str]:
        """Get list of sheet names that this graph class can process.

        Returns:
            List of supported sheet names
        """
        return [SheetNames.NORMAL_GENE_EXPRESSION.value, SheetNames.GENE_EXPRESSION.value, SheetNames.GENE_TUMOR_NORMAL_RATIOS.value]

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for Gene Expression data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating Gene Expression graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_excel_data():
                return False

        success = True

        # Generate normal gene expression
        if self._generate_normal_gene_heatmap(output_dir):
            logger.info("Generated normal gene expression graph")
        else:
            success = False

        # Generate tumor-normal ratios
        if self._generate_tumor_normal_ratios(output_dir):
            logger.info("Generated tumor-normal ratios")
        else:
            success = False

        return success

    def _generate_normal_gene_heatmap(self, output_dir: str) -> bool:
        """Generate heatmap of normal gene expression.

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get normal gene expression data
            df = self.get_sheet_data(SheetNames.NORMAL_GENE_EXPRESSION.value)
            if df is None or df.empty:
                logger.error("No normal gene expression data available")
                return False

            # Check for required columns (matrix format)
            if 'Gene' not in df.columns:
                logger.error("Missing 'Gene' column in normal gene expression data")
                logger.info(f"Available columns: {list(df.columns)}")
                return False

            # Get gene names and primary sites
            gene_names = df['Gene'].dropna().tolist()
            primary_sites = [col for col in df.columns if col != 'Gene']
            
            if not gene_names:
                logger.error("No gene data found")
                return False
                
            if not primary_sites:
                logger.error("No primary site data found")
                return False

            logger.info(f"Creating heatmap for {len(gene_names)} genes across {len(primary_sites)} primary sites")

            # Create the heatmap data matrix
            heatmap_data = []
            for _, row in df.iterrows():
                gene_name = row['Gene']
                if pd.notna(gene_name):  # Skip rows with no gene name
                    expression_values = [row.get(site, 0) for site in primary_sites]
                    heatmap_data.append(expression_values)

            if not heatmap_data:
                logger.error("No valid expression data found")
                return False

            heatmap_array = np.array(heatmap_data)

            # Calculate data bounds for color scaling
            valid_values = heatmap_array[heatmap_array != 0]  # Exclude zeros
            if len(valid_values) == 0:
                logger.error("No valid expression values found")
                return False

            min_bound = valid_values.min()
            max_bound = valid_values.max()
            vmax = min(5 * round(max_bound / 5), 20)

            # Create the heatmap
            plt.figure(figsize=(15, 8))
            sns.heatmap(
                heatmap_array,
                xticklabels=primary_sites,
                yticklabels=gene_names,
                vmin=min_bound,
                vmax=vmax,
                cmap="Blues",
                cbar_kws={
                    "label": "Log2 TPM Expression Value",
                    "shrink": 0.5,
                    "aspect": 20,
                    "pad": 0.05,
                },
                linewidths=0.2,
                linecolor="white",
                square=True,
            )

            # Rotate y-labels to horizontal
            plt.yticks(rotation=0, fontsize=12)
            # Rotate x-labels for better readability
            plt.xticks(rotation=45, ha="right", fontsize=12)

            plt.title("Normal Tissue Gene Expression Heatmap", fontsize=16, fontweight="bold")
            plt.xlabel("Primary Site", fontsize=14, fontweight="bold")
            plt.ylabel("Gene Symbol", fontsize=14, fontweight="bold")
            plt.tight_layout()

            # Save the plot
            filename = "normal_gene_expression_heatmap.png"
            if not self.save_graph(plt.gcf(), filename, output_dir):
                logger.error("Failed to save normal gene expression heatmap")
                return False

            plt.close()
            logger.info("Successfully generated normal gene expression heatmap")
            return True

        except Exception as e:
            logger.exception(f"Error generating normal gene expression heatmap: {e}")
            return False

    def _generate_tumor_normal_ratios(self, output_dir: str) -> bool:
        """Generate heatmap of tumor-normal ratios.

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        pass