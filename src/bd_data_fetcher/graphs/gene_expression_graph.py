"""Gene Expression data visualization graphs."""

import logging

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
        if self._generate_tumor_normal_boxplots(output_dir):
            logger.info("Generated tumor normal boxplots")
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
            if not self.save_graph(plt.gcf(), filename, output_dir, "gene_expression"):
                logger.error("Failed to save normal gene expression heatmap")
                return False

            plt.close()
            logger.info("Successfully generated normal gene expression heatmap")
            return True

        except Exception as e:
            logger.exception(f"Error generating normal gene expression heatmap: {e}")
            return False

    def _generate_tumor_normal_boxplots(self, output_dir: str) -> bool:
        """Generate boxplots comparing tumor vs normal expression for each protein.

        Creates professional boxplots showing:
        - One plot per protein
        - Grouped by Primary Site (alphabetically ordered)
        - Two boxes per primary site: Tumor (blue) and Normal (red)
        - Tumor always on the left, Normal always on the right

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get gene expression data
            df = self.get_sheet_data(SheetNames.GENE_EXPRESSION.value)
            if df is None or df.empty:
                logger.error("No gene expression data available")
                return False

            # Check for required columns
            required_columns = ['Gene', 'Expression Value', 'Primary Site', 'Is Cancer']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in gene expression data: {missing_columns}")
                logger.info(f"Available columns: {list(df.columns)}")
                return False

            # Ensure numeric columns are properly formatted
            df['Expression Value'] = pd.to_numeric(df['Expression Value'], errors='coerce')

            # Remove rows with NaN values
            df = df.dropna(subset=['Expression Value', 'Primary Site', 'Is Cancer'])
            if df.empty:
                logger.error("No valid numeric data found in Expression Value column")
                return False

            # Get unique genes
            unique_genes = df['Gene'].unique()
            logger.info(f"Creating tumor-normal boxplots for {len(unique_genes)} genes")

            # Set Seaborn style for professional medical appearance
            sns.set_style("whitegrid")

            # Create boxplot for each gene
            for gene in unique_genes:
                # Filter data for current gene
                gene_data = df[df['Gene'] == gene]

                if gene_data.empty:
                    logger.warning(f"No data found for gene: {gene}")
                    continue

                # Create a new column for plotting that combines Primary Site and Cancer status
                gene_data = gene_data.copy()
                gene_data['Site_Status'] = gene_data['Primary Site'] + '_' + gene_data['Is Cancer'].astype(str)

                # Sort primary sites alphabetically
                primary_sites = sorted(gene_data['Primary Site'].unique())

                # Create the plot
                plt.figure(figsize=(16, 10))

                # Prepare data for plotting with grouped layout
                plot_data = []
                site_labels = []

                for site in primary_sites:
                    site_data = gene_data[gene_data['Primary Site'] == site]

                    # Get tumor data (Is Cancer = True)
                    tumor_data = site_data[site_data['Is Cancer'] is True]['Expression Value']
                    # Get normal data (Is Cancer = False)
                    normal_data = site_data[site_data['Is Cancer'] is False]['Expression Value']

                    # Only add this site if it has data
                    if not tumor_data.empty or not normal_data.empty:
                        # Add tumor data first (left box)
                        if not tumor_data.empty:
                            plot_data.append(tumor_data)
                        else:
                            plot_data.append([])  # Empty list for no data

                        # Add normal data second (right box)
                        if not normal_data.empty:
                            plot_data.append(normal_data)
                        else:
                            plot_data.append([])  # Empty list for no data

                        site_labels.append(site)

                if not plot_data:
                    logger.warning(f"No valid data for gene: {gene}")
                    continue

                # Create boxplot with grouped layout - each site gets one x-tick with two boxes
                # Use positions to create side-by-side boxes for each site
                positions = []
                for i in range(len(site_labels)):
                    positions.extend([i - 0.2, i + 0.2])  # Left and right positions for each site

                bp = plt.boxplot(plot_data, patch_artist=True, positions=positions)

                # Set x-axis labels to show only primary site names
                plt.xticks(range(len(site_labels)), site_labels)

                # Color the boxes: Tumor = blue (even indices), Normal = red (odd indices)
                colors = []
                for i in range(len(bp['boxes'])):
                    if i % 2 == 0:  # Even indices (0, 2, 4...) are tumor (left boxes)
                        colors.append('#45cfe0')  # Blue for tumor
                    else:  # Odd indices (1, 3, 5...) are normal (right boxes)
                        colors.append('#ff6b6b')  # Red for normal

                # Apply colors to boxes
                for patch, color in zip(bp['boxes'], colors, strict=False):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.7)

                # Customize the plot
                plt.title(
                    f'Tumor vs Normal Gene Expression\nGene: {gene}',
                    fontsize=16,
                    fontweight='bold',
                    pad=25
                )
                plt.xlabel('Primary Site', fontsize=14, fontweight='bold')
                plt.ylabel('Expression Value', fontsize=14, fontweight='bold')

                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45, ha='right', fontsize=10)
                plt.yticks(fontsize=12)

                # Add grid
                plt.grid(True, alpha=0.3)

                # Add legend
                from matplotlib.patches import Patch
                legend_elements = [
                    Patch(facecolor='#45cfe0', alpha=0.7, label='Tumor'),
                    Patch(facecolor='#ff6b6b', alpha=0.7, label='Normal')
                ]
                plt.legend(handles=legend_elements, loc='upper right', fontsize=12)

                # Add statistics text
                total_samples = len(gene_data)
                tumor_samples = len(gene_data[gene_data['Is Cancer'] is True])
                normal_samples = len(gene_data[gene_data['Is Cancer'] is False])

                plt.figtext(
                    0.02, 0.02,
                    f'Total samples: {total_samples}\nTumor samples: {tumor_samples}\nNormal samples: {normal_samples}',
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
                safe_gene = gene.replace(' ', '_').replace('/', '_')
                filename = f"tumor_normal_boxplot_{safe_gene}.png"

                if not self.save_graph(plt.gcf(), filename, output_dir, "gene_expression"):
                    logger.error(f"Failed to save tumor-normal boxplot for gene: {gene}")
                    return False

                plt.close()
                logger.info(f"Generated tumor-normal boxplot for gene: {gene}")

            logger.info("Successfully generated all tumor-normal boxplots")
            return True

        except Exception as e:
            logger.exception(f"Error generating tumor-normal boxplots: {e}")
            return False
