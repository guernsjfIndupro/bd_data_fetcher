"""Gene expression data visualization graphs."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import FileNames
from bd_data_fetcher.graphs.base_graph import BaseGraph
from bd_data_fetcher.api.umap_client import UMapClient

logger = logging.getLogger(__name__)


class GeneExpressionGraph(BaseGraph):
    """Graph generator for gene expression data.

    This class handles visualization of gene expression data,
    including normal expression, tumor-normal ratios, and expression distributions.
    Uses an anchor protein as a reference point for visualizations.
    """
    
    # Cache for gene expression bounds to avoid repeated API calls
    _gene_expression_bounds_cache = None

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

        # Generate gene coexpression plots
        if self._generate_gene_coexpression_plots(output_dir):
            logger.info("Generated gene coexpression plots")
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

            # Define primary sites to filter out
            filtered_sites = ['Cells', 'Blood', 'Blood Vessel', 'Muscle', 'White blood cell']
            
            # Filter out the specified primary sites
            filtered_columns = [col for col in expression_columns if col not in filtered_sites]
            
            if not filtered_columns:
                logger.error("No expression columns remaining after filtering")
                return False
            
            logger.info(f"Filtered out {len(expression_columns) - len(filtered_columns)} primary sites: {filtered_sites}")
            logger.info(f"Remaining primary sites: {filtered_columns}")

            # Set up the plot
            plt.figure(figsize=(max(12, len(filtered_columns) * 0.8), max(8, len(df) * 0.3)))
            sns.set_style("whitegrid")

            # Prepare data for heatmap with filtered columns
            heatmap_data = df.set_index('Gene')[filtered_columns]

            # Get bounds from UMAP API (cached)
            if GeneExpressionGraph._gene_expression_bounds_cache is None:
                try:
                    umap_client = UMapClient()
                    # Get all primary sites for the studies parameter
                    studies = ["TCGA"]  # Use filtered columns as studies
                    GeneExpressionGraph._gene_expression_bounds_cache = umap_client._get_gtex_normal_rna_expression_data_bounds(
                        studies=studies, is_cancer=False
                    )
                    logger.info(f"Cached gene expression bounds: {GeneExpressionGraph._gene_expression_bounds_cache}")
                except Exception as e:
                    logger.warning(f"Failed to get gene expression bounds from API: {e}")
                    GeneExpressionGraph._gene_expression_bounds_cache = {}

            # Get min and max values for heatmap limits
            vmin = None
            vmax = None
            if GeneExpressionGraph._gene_expression_bounds_cache:
                vmin = GeneExpressionGraph._gene_expression_bounds_cache.get('min_bound')
                vmax = GeneExpressionGraph._gene_expression_bounds_cache.get('max_bound')
                print(f"Using heatmap limits: vmin={vmin}, vmax={vmax}")

            # Create heatmap with bounds
            sns.heatmap(
                heatmap_data,
                annot=False,
                cmap='Blues',
                cbar_kws={'label': 'Log2 Expression Value'},
                linewidths=0.2,
                linecolor='white',
                square=True,
                vmin=vmin,
                vmax=vmax
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

    def _calculate_gene_coexpression(self, data: pd.DataFrame, anchor_gene: str, other_gene: str) -> tuple:
        """Calculate coexpression between anchor gene and another gene.

        Args:
            data: DataFrame containing gene expression data
            anchor_gene: Name of the anchor gene
            other_gene: Name of the other gene to compare

        Returns:
            Tuple containing (coexpression_percentage, threshold_anchor, threshold_other, 
                            tumor_data_df, tumor_sample_count)
        """
        # Filter data for the two genes
        gene_data = data[data['Gene'].isin([anchor_gene, other_gene])].copy()
        
        if gene_data.empty:
            return None, None, None, None, 0
        
        # Get normal tissue data for both genes to calculate thresholds
        normal_anchor = gene_data.loc[
            (gene_data['Gene'] == anchor_gene) & 
            (gene_data['Is Cancer'] == False)
        ]
        
        normal_other = gene_data.loc[
            (gene_data['Gene'] == other_gene) & 
            (gene_data['Is Cancer'] == False)
        ]
        
        # Calculate median thresholds from normal tissue
        anchor_median = normal_anchor['Expression Value'].median()
        other_median = normal_other['Expression Value'].median()
        
        # Get tumor data for both genes
        tumor_data = gene_data.loc[gene_data['Is Cancer'] == True]
        
        if tumor_data.empty:
            return 0.0, anchor_median, other_median, pd.DataFrame(), 0
        
        # Create a simple DataFrame with both genes' expression values for each sample
        
        anchor_tumor = tumor_data[tumor_data['Gene'] == anchor_gene][['Sample Name', 'Expression Value']].copy()
        other_tumor = tumor_data[tumor_data['Gene'] == other_gene][['Sample Name', 'Expression Value']].copy()
        
        # Rename columns to avoid conflicts
        anchor_tumor = anchor_tumor.rename(columns={'Expression Value': anchor_gene})
        other_tumor = other_tumor.rename(columns={'Expression Value': other_gene})
        
        # Merge the data to get both genes' expression for each sample using Sample Name
        combined_tumor = pd.merge(anchor_tumor, other_tumor, on='Sample Name', how='inner')

        if combined_tumor.empty:
            return 0.0, anchor_median, other_median, combined_tumor, 0
        
        # Calculate coexpression percentage
        coexpression_count = combined_tumor.loc[
            (combined_tumor[anchor_gene] > anchor_median) & 
            (combined_tumor[other_gene] > other_median)
        ].shape[0]
        
        coexpression_percentage = coexpression_count / combined_tumor.shape[0]
        
        return coexpression_percentage, anchor_median, other_median, combined_tumor, combined_tumor.shape[0]

    def _generate_gene_coexpression_plots(self, output_dir: str) -> bool:
        """Generate coexpression plots for gene expression data.

        Creates scatter plots showing coexpression between anchor gene and other genes:
        - Each plot shows tumor samples for a specific primary site
        - High/low coexpression samples with threshold lines
        - Coexpression percentage and sample counts
        - One plot per primary site per gene comparison

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
            required_columns = ['Gene', 'Expression Value', 'Primary Site', 'Is Cancer']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in gene expression data: {missing_columns}")
                return False

            # Check for Sample Name column (optional but preferred)
            has_sample_name = 'Sample Name' in df.columns
            if has_sample_name:
                logger.info("Sample Name column found - will use for precise sample matching")
            else:
                logger.warning("Sample Name column not found - will use Primary Site aggregation")

            # Ensure numeric column is properly formatted
            df['Expression Value'] = pd.to_numeric(df['Expression Value'], errors='coerce')
            
            # Drop rows with missing required data
            drop_columns = ['Expression Value', 'Gene', 'Primary Site', 'Is Cancer']
            if has_sample_name:
                drop_columns.append('Sample Name')
            df = df.dropna(subset=drop_columns)

            if df.empty:
                logger.error("No valid numeric data found in gene expression data")
                return False

            # Get unique genes and primary sites
            unique_genes = df['Gene'].unique()
            other_genes = [gene for gene in unique_genes if gene != self.anchor_protein]
            unique_primary_sites = df['Primary Site'].unique()
            
            if len(other_genes) == 0:
                logger.warning(f"No genes found other than anchor gene: {self.anchor_protein}")
                return False

            logger.info(f"Generating coexpression plots for {len(unique_primary_sites)} primary sites and {len(other_genes)} genes")

            # Set up the plotting style
            plt.style.use('default')
            sns.set_style('white')

            # Create plots for each primary site and gene combination
            for primary_site in unique_primary_sites:
                for other_gene in other_genes:
                    # Filter data for this primary site
                    site_data = df[df['Primary Site'] == primary_site].copy()
                    
                    if site_data.empty:
                        logger.warning(f"No data found for primary site: {primary_site}")
                        continue

                    # Calculate coexpression for this site
                    coexpression_result = self._calculate_gene_coexpression(site_data, self.anchor_protein, other_gene)
                    
                    if coexpression_result[0] is None:
                        logger.warning(f"No data available for {self.anchor_protein} vs {other_gene} in {primary_site}")
                        continue
                    
                    coexpression, threshold_anchor, threshold_other, tumor_data, tumor_count = coexpression_result
                    
                    if tumor_count == 0:
                        logger.warning(f"No tumor data available for {self.anchor_protein} vs {other_gene} in {primary_site}")
                        continue

                    # Separate high and low coexpression samples
                    high_coexpression = tumor_data.loc[
                        (tumor_data[self.anchor_protein] > threshold_anchor) &
                        (tumor_data[other_gene] > threshold_other)
                    ]
                    
                    low_coexpression = tumor_data.loc[
                        (tumor_data[self.anchor_protein] <= threshold_anchor) |
                        (tumor_data[other_gene] <= threshold_other)
                    ]

                    # Create the plot
                    fig, ax = plt.subplots(figsize=(8, 6))
                    
                    # Plot high coexpression samples with improved definition
                    if not high_coexpression.empty:
                        ax.scatter(
                            high_coexpression[self.anchor_protein],
                            high_coexpression[other_gene],
                            color='cornflowerblue',
                            alpha=0.7,
                            s=40,
                            edgecolors='darkblue',
                            linewidth=0.5,
                            label=f'High Coexpression (n={len(high_coexpression)})'
                        )
                    
                    # Plot low coexpression samples with improved definition
                    if not low_coexpression.empty:
                        ax.scatter(
                            low_coexpression[self.anchor_protein],
                            low_coexpression[other_gene],
                            color='gray',
                            alpha=0.7,
                            s=40,
                            edgecolors='darkgray',
                            linewidth=0.5,
                            label=f'Low Coexpression (n={len(low_coexpression)})'
                        )

                    # Add threshold lines
                    ax.axvline(threshold_anchor, color='rosybrown', linestyle='--', alpha=0.8, linewidth=2)
                    ax.axhline(threshold_other, color='rosybrown', linestyle='--', alpha=0.8, linewidth=2)

                    # Set axis limits
                    all_data = tumor_data[[self.anchor_protein, other_gene]]
                    ax.set_xlim(0, all_data[self.anchor_protein].max() * 1.05)
                    ax.set_ylim(0, all_data[other_gene].max() * 1.05)

                    # Set labels
                    ax.set_xlabel(f'{self.anchor_protein} Expression (Log2)', fontsize=12)
                    ax.set_ylabel(f'{other_gene} Expression (Log2)', fontsize=12)

                    # Set title
                    ax.set_title(f'{self.anchor_protein} and {other_gene} Coexpression\n{primary_site} Tumor Samples', 
                               fontsize=14, fontweight='bold')

                    # Add coexpression statistics
                    ax.text(
                        0.05, 0.95, 
                        f'{int(coexpression * 100)}% of samples above threshold\n'
                        f'Total tumor samples: n={tumor_count}\n'
                        f'{self.anchor_protein} threshold: {threshold_anchor:.2f}\n'
                        f'{other_gene} threshold: {threshold_other:.2f}',
                        transform=ax.transAxes,
                        verticalalignment='top',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9),
                        fontsize=10
                    )

                    # Add legend
                    ax.legend(loc='lower right')

                    # Clean up the plot
                    sns.despine()
                    plt.tight_layout()

                    # Save the plot
                    safe_anchor = self.anchor_protein.replace('/', '_').replace(' ', '_')
                    safe_other = other_gene.replace('/', '_').replace(' ', '_')
                    safe_site = primary_site.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')
                    filename = f"gene_coexpression_{safe_anchor}_{safe_other}_{safe_site}.png"
                    output_path = Path(output_dir) / "gene_expression" / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    plt.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close()

                    logger.info(f"Saved gene coexpression plot: {self.anchor_protein} vs {other_gene} in {primary_site}")

            return True

        except Exception as e:
            logger.exception(f"Error generating gene coexpression plots: {e}")
            return False
