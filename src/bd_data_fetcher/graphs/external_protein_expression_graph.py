"""External Protein Expression data visualization graphs."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import SheetNames
from bd_data_fetcher.graphs.base_graph import BaseGraph

logger = logging.getLogger(__name__)


class ExternalProteinExpressionGraph(BaseGraph):
    """Graph generator for External Protein Expression data.

    This class handles visualization of external proteomics data,
    including normal tissue expression and external protein expression.
    """

    def get_supported_sheets(self) -> list[str]:
        """Get list of sheet names that this graph class can process.

        Returns:
            List of supported sheet names
        """
        return [SheetNames.NORMAL_PROTEOMICS_DATA.value, SheetNames.EXTERNAL_PROTEOMICS_DATA.value]

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for External Protein Expression data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating External Protein Expression graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_excel_data():
                return False

        success = True

        # Generate normal proteomics expression
        if self._generate_normal_proteomics_expression(output_dir):
            logger.info("Generated normal proteomics expression graph")
        else:
            success = False

        # Generate external proteomics comparison
        if self._generate_external_proteomics_comparison(output_dir):
            logger.info("Generated external proteomics comparison")
        else:
            success = False

        # Generate tissue expression heatmap
        if self._generate_tissue_expression_heatmap(output_dir):
            logger.info("Generated tissue expression heatmap")
        else:
            success = False

        return success

    def _generate_normal_proteomics_expression(self, output_dir: str) -> bool:
        """Generate heatmap of normal proteomics expression.

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get normal proteomics data
            df = self.get_sheet_data(SheetNames.NORMAL_PROTEOMICS_DATA.value)
            if df is None or df.empty:
                logger.error("No normal proteomics data available")
                return False

            # Check for required columns (matrix format)
            if 'Gene' not in df.columns:
                logger.error("Missing 'Gene' column in normal proteomics data")
                logger.info(f"Available columns: {list(df.columns)}")
                return False

            # Get gene names and indications
            gene_names = df['Gene'].dropna().tolist()
            indications = [col for col in df.columns if col != 'Gene']

            if not gene_names:
                logger.error("No gene data found")
                return False

            if not indications:
                logger.error("No indication data found")
                return False

            logger.info(f"Creating heatmap for {len(gene_names)} genes across {len(indications)} indications")

            # Create the heatmap data matrix
            heatmap_data = []
            for _, row in df.iterrows():
                gene_name = row['Gene']
                if pd.notna(gene_name):  # Skip rows with no gene name
                    expression_values = [row.get(indication, 0) for indication in indications]
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
                xticklabels=indications,
                yticklabels=gene_names,
                vmin=min_bound,
                vmax=vmax,
                cmap="Blues",
                cbar_kws={
                    "label": "Log2 Expression Value",
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

            plt.title("Normal Tissue Proteomics Expression Heatmap", fontsize=16, fontweight="bold")
            plt.xlabel("Indication", fontsize=14, fontweight="bold")
            plt.ylabel("Gene Symbol", fontsize=14, fontweight="bold")
            plt.tight_layout()

            # Save the plot
            filename = "normal_proteomics_heatmap.png"
            if not self.save_graph(plt.gcf(), filename, output_dir, "external_protein_expression"):
                logger.error("Failed to save normal proteomics heatmap")
                return False

            plt.close()
            logger.info("Successfully generated normal proteomics heatmap")
            return True

        except Exception as e:
            logger.exception(f"Error generating normal proteomics heatmap: {e}")
            return False

    def _generate_external_proteomics_comparison(self, output_dir: str) -> bool:
        """Generate comparison plot for external proteomics data.

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Placeholder implementation
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.set_title("External Proteomics Comparison")
            ax.set_xlabel("Proteins")
            ax.set_ylabel("Expression Level")

            # TODO: Implement actual comparison plotting
            # df = self.get_sheet_data(SheetNames.EXTERNAL_PROTEOMICS_DATA.value)
            # if df is not None:
            #     protein_means = df.groupby('protein')['expression_level'].mean()
            #     ax.bar(protein_means.index, protein_means.values)

            return self.save_graph(fig, "external_proteomics_comparison.png", output_dir, "external_protein_expression")

        except Exception as e:
            logger.exception(f"Error generating external proteomics comparison: {e}")
            return False

    def _generate_tissue_expression_heatmap(self, output_dir: str) -> bool:
        """Generate heatmap of expression across different tissues.

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Placeholder implementation
            fig, ax = plt.subplots(figsize=(14, 8))
            ax.set_title("Tissue Expression Heatmap")
            ax.set_xlabel("Tissues")
            ax.set_ylabel("Proteins")

            # TODO: Implement actual heatmap generation
            # df = self.get_sheet_data(SheetNames.NORMAL_PROTEOMICS_DATA.value)
            # if df is not None:
            #     # Create pivot table and heatmap
            #     pivot_data = df.pivot(index='protein', columns='tissue_type', values='expression_level')
            #     sns.heatmap(pivot_data, ax=ax, cmap='viridis', annot=True, fmt='.2f')

            return self.save_graph(fig, "tissue_expression_heatmap.png", output_dir, "external_protein_expression")

        except Exception as e:
            logger.exception(f"Error generating tissue expression heatmap: {e}")
            return False
