"""DepMap data visualization graphs."""

import logging
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bd_data_fetcher.api.umap_client import UMapClient
from bd_data_fetcher.data_handlers.utils import FileNames
from bd_data_fetcher.graphs.base_graph import BaseGraph
from bd_data_fetcher.graphs.shared import OncLineageColors

logger = logging.getLogger(__name__)


class DepMapGraph(BaseGraph):
    """Graph generator for DepMap data.

    This class handles visualization of DepMap dependency data,
    including copy number analysis and TPM expression data.
    Uses an anchor protein as a reference point for visualizations.
    """

    def _add_labels_with_adjusttext(self, ax, points, labels, fontsize=12):
        """
        Add labels using adjustText library for optimal positioning in DepMap plots.
        
        Args:
            ax: Matplotlib axis object
            points: List of (x, y) coordinates for points
            labels: List of label texts
            fontsize: Font size for labels
        """
        from adjustText import adjust_text
        
        texts = []
        for (x, y), label in zip(points, labels):
            # Create text directly under the point by default
            text = ax.text(x, y-0.5, label, fontsize=fontsize, ha='center', va='top', 
                          color='black', weight='bold')
            texts.append(text)
        
        # Use adjustText to optimize label positions - only adjust if poor overlap
        adjust_text(
            texts,
            arrowprops=dict(arrowstyle='-', color='black', alpha=0.8, lw=0.5),
            expand_points=(1.2, 1.2),
            force_points=(0.1, 0.1),
            force_text=(0.5, 0.5),
            min_arrow_len=3,
            avoid_points=False,  # Don't avoid data points, only avoid text overlaps
            avoid_self=False,    # Don't avoid the point the label belongs to
            only_move={'points': 'xy', 'text': 'xy'}  # Allow both points and text to move
        )

    def _get_depmap_bounds_for_protein(self, uniprotkb_ac: str) -> dict[str, float]:
        """
        Get DepMap bounds for a specific protein, using LRU caching to avoid repeated API calls.
        
        Args:
            uniprotkb_ac: UniProtKB accession number
            
        Returns:
            Dictionary containing min_tpm_log2 and max_tpm_log2 values
        """
        try:
            # Get bounds from UMAP API
            umap_client = UMapClient()
            bounds = umap_client._get_dep_map_bounds(uniprotkb_ac)

            logger.info(f"Retrieved DepMap bounds for {uniprotkb_ac}: {bounds}")
            return bounds

        except Exception as e:
            logger.warning(f"Failed to get DepMap bounds for {uniprotkb_ac}: {e}")
            # Return default bounds if API call fails
            return {"min_tpm_log2": 0, "max_tpm_log2": 10}

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for DepMap data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating DepMap graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_csv_data():
                return False

        success = True

        # Generate copy number scatter plot
        if self._generate_depmap_copy_number_scatter_plot(output_dir):
            logger.info("Generated copy number scatter plot")
        else:
            success = False

        return success

    def _generate_depmap_copy_number_scatter_plot(self, output_dir: str) -> bool:
        """Generate scatter plots of DepMap copy number data for each protein.

        Creates separate scatter plots for each protein showing:
        - X-axis: DepMap TPM Log2 values
        - Y-axis: Log2 of copy number from WCE data
        - One dot per cell line

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get DepMap data
            depmap_df = self.get_data_for_file(FileNames.DEPMAP_DATA.value)
            if depmap_df is None or depmap_df.empty:
                logger.error("No DepMap data available")
                return False

            # Get WCE data
            wce_df = self.get_data_for_file(FileNames.WCE_DATA.value)
            if wce_df is None or wce_df.empty:
                logger.error("No WCE data available")
                return False

            # Check for required columns in DepMap data
            depmap_required_columns = ['Cell Line', 'TPM Log2', 'Protein Symbol', 'UniProtKB AC']
            depmap_missing_columns = [col for col in depmap_required_columns if col not in depmap_df.columns]
            if depmap_missing_columns:
                logger.error(f"Missing required columns in DepMap data: {depmap_missing_columns}")
                logger.info(f"Available columns in DepMap data: {list(depmap_df.columns)}")
                return False

            # Check for required columns in WCE data
            wce_required_columns = ['Cell Line', 'Copies Per Cell', 'Gene', 'Onc Lineage']
            wce_missing_columns = [col for col in wce_required_columns if col not in wce_df.columns]
            if wce_missing_columns:
                logger.error(f"Missing required columns in WCE data: {wce_missing_columns}")
                logger.info(f"Available columns in WCE data: {list(wce_df.columns)}")
                return False

            # Ensure numeric columns are properly formatted
            depmap_df['TPM Log2'] = pd.to_numeric(depmap_df['TPM Log2'], errors='coerce')
            wce_df['Copies Per Cell'] = pd.to_numeric(wce_df['Copies Per Cell'], errors='coerce')

            # Remove rows with NaN values
            depmap_df = depmap_df.dropna(subset=['TPM Log2', 'Cell Line', 'Protein Symbol'])
            wce_df = wce_df.dropna(subset=['Copies Per Cell', 'Cell Line', 'Gene', 'Onc Lineage'])

            if depmap_df.empty:
                logger.error("No valid numeric data found in DepMap TPM Log2 column")
                return False

            if wce_df.empty:
                logger.error("No valid numeric data found in WCE Copies Per Cell column")
                return False

            # Calculate log2 of copy number for WCE data
            wce_df['Log2_Copy_Number'] = np.log2(wce_df['Copies Per Cell'])

            # Take average of copy numbers per cell line per gene
            wce_avg_df = wce_df.groupby(['Cell Line', 'Gene', 'Onc Lineage'])['Log2_Copy_Number'].mean().reset_index()

            # Get unique proteins from both datasets
            depmap_proteins = set(depmap_df['Protein Symbol'].unique())
            wce_genes = set(wce_avg_df['Gene'].unique())
            common_proteins = depmap_proteins.intersection(wce_genes)

            if not common_proteins:
                logger.error("No common proteins found between DepMap and WCE data")
                return False

            logger.info(f"Found {len(common_proteins)} common proteins to process")

            # Set Seaborn style for professional medical appearance
            sns.set_style("white")
            sns.set_palette(["#45cfe0"])

            success_count = 0
            total_proteins = len(common_proteins)

            # Generate scatter plot for each protein
            for protein in sorted(common_proteins):
                try:
                    # Filter data for current protein
                    protein_depmap = depmap_df[depmap_df['Protein Symbol'] == protein]
                    protein_wce = wce_avg_df[wce_avg_df['Gene'] == protein]

                    # Merge data on Cell Line for this protein
                    merged_df = pd.merge(
                        protein_depmap[['Cell Line', 'TPM Log2']],
                        protein_wce[['Cell Line', 'Log2_Copy_Number', 'Onc Lineage']],
                        on='Cell Line',
                        how='inner'
                    )

                    if merged_df.empty:
                        logger.warning(f"No matching cell lines found for protein: {protein}")
                        continue

                    logger.info(f"Creating scatter plot for protein {protein} with {len(merged_df)} cell lines")

                    # Create the scatter plot
                    plt.figure(figsize=(12, 10))

                    # Set light gray background
                    plt.gca().set_facecolor('#f8f9fa')

                    # Get unique onc lineages for color mapping using shared colors
                    onc_lineages = merged_df['Onc Lineage'].unique()
                    color_map = OncLineageColors.get_color_map(onc_lineages)

                    # Create scatter plot colored by onc lineage
                    for lineage in onc_lineages:
                        lineage_data = merged_df[merged_df['Onc Lineage'] == lineage]
                        plt.scatter(
                            lineage_data['TPM Log2'],
                            lineage_data['Log2_Copy_Number'],
                            alpha=0.7,
                            color=color_map[lineage],
                            s=100,
                            edgecolors='#2a9bb3',
                            linewidth=1,
                            label=lineage
                        )

                    # Collect points and labels for smart positioning
                    points = []
                    labels = []
                    
                    for _, row in merged_df.iterrows():
                        points.append((row['TPM Log2'], row['Log2_Copy_Number']))
                        labels.append(row['Cell Line'])
                    
                    # Add labels using adjustText for optimal positioning
                    if points:
                        ax = plt.gca()
                        self._add_labels_with_adjusttext(ax, points, labels, fontsize=10)

                    # Customize the plot
                    plt.title(
                        f'DepMap TPM Log2 vs WCE Copy Number\nProtein: {protein}',
                        fontsize=24,  # Increased from 16 (50% larger)
                        fontweight='bold',
                        pad=25
                    )
                    plt.xlabel('DepMap TPM Log2', fontsize=21, fontweight='bold')  # Increased from 14 (50% larger)
                    plt.ylabel('Log2 Copy Number (WCE)', fontsize=21, fontweight='bold')  # Increased from 14 (50% larger)



                    # Get DepMap bounds for this protein to set axis limits
                    protein_uniprotkb_ac = protein_depmap['UniProtKB AC'].iloc[0] if not protein_depmap.empty else None
                    if protein_uniprotkb_ac:
                        bounds = self._get_depmap_bounds_for_protein(protein_uniprotkb_ac)
                        min_tpm = bounds.get('min_tpm_log2', 0)
                        max_tpm = bounds.get('max_tpm_log2', 10)

                        # Set x-axis limits (DepMap TPM Log2)
                        plt.xlim(min_tpm, max_tpm)
                        logger.info(f"Set DepMap TPM Log2 axis limits for {protein}: {min_tpm} to {max_tpm}")
                    else:
                        logger.warning(f"No UniProtKB AC found for protein {protein}, using default axis limits")

                    # Add legend
                    plt.legend(title='Onc Lineage', loc='upper left', fontsize=15)  # Increased from 10 (50% larger)

                    # Remove top and right borders
                    ax = plt.gca()
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)

                    plt.tight_layout()

                    # Save the plot with protein name in filename
                    safe_protein_name = protein.replace(' ', '_').replace('/', '_').replace('\\', '_')
                    filename = f"copy_number_scatter_plot_{safe_protein_name}.png"

                    # Create output directory and save
                    output_path = Path(output_dir) / "depmap" / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    plt.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close()

                    logger.info(f"Saved graph: {output_path}")
                    success_count += 1
                    logger.info(f"Successfully generated copy number scatter plot for protein: {protein}")

                except Exception as e:
                    logger.exception(f"Error generating scatter plot for protein {protein}: {e}")
                    continue

            logger.info(f"Generated {success_count}/{total_proteins} protein scatter plots successfully")
            return success_count > 0

        except Exception as e:
            logger.exception(f"Error generating copy number scatter plots: {e}")
            return False

