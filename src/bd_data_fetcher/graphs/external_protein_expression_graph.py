"""External protein expression data visualization graphs."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import FileNames
from bd_data_fetcher.graphs.base_graph import BaseGraph
from bd_data_fetcher.api.umap_client import UMapClient
from bd_data_fetcher.graphs.shared import TumorNormalColors

logger = logging.getLogger(__name__)


class ExternalProteinExpressionGraph(BaseGraph):
    """Graph generator for external protein expression data.

    This class handles visualization of external proteomics data,
    including normal expression data and study-specific comparisons.
    Uses an anchor protein as a reference point for visualizations.
    """
    
    # Cache for proteomics bounds to avoid repeated API calls
    _proteomics_bounds_cache = None

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for external protein expression data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating external protein expression graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_csv_data():
                return False

        success = True

        # Generate normal proteomics expression plot
        if self._generate_normal_proteomics_plot(output_dir):
            logger.info("Generated normal proteomics expression plot")
        else:
            success = False

        # Generate study-specific proteomics expression plot
        if self._generate_study_specific_proteomics_plot(output_dir):
            logger.info("Generated study-specific proteomics expression plot")
        else:
            success = False

        # Generate protein expression boxplots
        if self._generate_protein_expression_boxplots(output_dir):
            logger.info("Generated protein expression boxplots")
        else:
            success = False

        return success

    def _generate_normal_proteomics_plot(self, output_dir: str) -> bool:
        """Generate expression plots for normal proteomics data.

        Creates heatmaps showing:
        - X-axis: Indications/Tissue types
        - Y-axis: Proteins
        - Color intensity: Expression values

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get normal proteomics data
            df = self.get_data_for_file(FileNames.NORMAL_PROTEOMICS_DATA.value)
            if df is None or df.empty:
                logger.error("No normal proteomics data available")
                return False

            # Check for required columns
            required_columns = ['Gene']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in normal proteomics data: {missing_columns}")
                return False

            # Get expression columns (all columns except 'Gene')
            expression_columns = [col for col in df.columns if col != 'Gene']
            
            if not expression_columns:
                logger.error("No expression columns found in normal proteomics data")
                return False

            # Set up the plot
            plt.figure(figsize=(max(12, len(expression_columns) * 0.8), max(8, len(df) * 0.3)))
            sns.set_style("whitegrid")

            # Prepare data for heatmap and apply log10 transformation
            heatmap_data = df.set_index('Gene')[expression_columns]
            
            # Apply log10 transformation to copies per cell values
            # Replace zeros and negative values with NaN to avoid log(0) and log(negative) issues
            heatmap_data_log10 = heatmap_data.copy()
            
            heatmap_data_log10[heatmap_data_log10 <= 0] = np.nan

            heatmap_data_log10 = np.log10(heatmap_data_log10)

            # Get bounds from UMAP API (cached)
            if ExternalProteinExpressionGraph._proteomics_bounds_cache is None:
                try:
                    umap_client = UMapClient()
                    ExternalProteinExpressionGraph._proteomics_bounds_cache = umap_client._get_proteomics_normal_expression_data_bounds()
                    logger.info(f"Cached proteomics bounds: {ExternalProteinExpressionGraph._proteomics_bounds_cache}")
                except Exception as e:
                    logger.warning(f"Failed to get proteomics bounds from API: {e}")
                    ExternalProteinExpressionGraph._proteomics_bounds_cache = {}

            # Get min and max values for heatmap limits
            vmin = None
            vmax = None
            if ExternalProteinExpressionGraph._proteomics_bounds_cache:
                vmin = ExternalProteinExpressionGraph._proteomics_bounds_cache.get('min_copies_per_cell')
                vmax = ExternalProteinExpressionGraph._proteomics_bounds_cache.get('max_copies_per_cell')
                logger.info(f"Using heatmap limits: vmin={vmin}, vmax={vmax}")

            # Create heatmap with masked zeros and forced limits
            sns.heatmap(
                heatmap_data_log10,
                annot=False,
                cmap='Blues',
                cbar_kws={'label': 'Log10(Copies per Cell)'},
                linewidths=0.2,
                linecolor='white',
                square=True,
                mask=heatmap_data_log10.isna(),  # Mask NaN values (original zeros)
                vmin=vmin,
                vmax=np.log10(vmax)
            )

            # Customize the plot
            plt.title('Normal Proteomics Log10(Copies per Cell) Data', fontsize=20, fontweight='bold', pad=30)
            plt.xlabel('Indications/Tissue Types', fontsize=16, fontweight='bold')
            plt.ylabel('Proteins', fontsize=16, fontweight='bold')

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right', fontsize=12)
            plt.yticks(rotation=0, fontsize=12)

            # Add caveat about proteomics ruler method
            plt.figtext(0.98, 0.02, 'All copy numbers calculated using the proteomics ruler method', 
                       fontsize=12, ha='right', va='bottom', 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.8))

            plt.tight_layout()

            # Save the plot
            filename = "normal_proteomics_expression.png"
            output_path = Path(output_dir) / "external_protein_expression" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved normal proteomics expression plot: {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating normal proteomics expression plot: {e}")
            return False

    def _generate_study_specific_proteomics_plot(self, output_dir: str) -> bool:
        """Generate expression plots for study-specific proteomics data.

        Creates heatmaps showing:
        - X-axis: Indications/Studies
        - Y-axis: Proteins
        - Color intensity: Expression values

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get study-specific proteomics data
            df = self.get_data_for_file(FileNames.STUDY_SPECIFIC_DATA.value)
            if df is None or df.empty:
                logger.error("No study-specific proteomics data available")
                return False

            # Check for required columns
            required_columns = ['Gene']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in study-specific proteomics data: {missing_columns}")
                return False

            # Get expression columns (all columns except 'Gene')
            expression_columns = [col for col in df.columns if col != 'Gene']
            
            if not expression_columns:
                logger.error("No expression columns found in study-specific proteomics data")
                return False

            # Set up the plot
            plt.figure(figsize=(max(12, len(expression_columns) * 0.8), max(8, len(df) * 0.3)))
            sns.set_style("whitegrid")

            # Prepare data for heatmap and apply log2 transformation for tumor/normal ratios
            heatmap_data = df.set_index('Gene')[expression_columns]
            
            # Apply log2 transformation for tumor/normal ratios (study-specific data)
            # Handle negative values properly for log transformation
            heatmap_data_log2 = heatmap_data.copy()
            
            # Handle zeros and negative values properly for log2 transformation
            # Only convert zeros to NaN, keep negative values for log2
            heatmap_data_log2[heatmap_data_log2 == 0] = np.nan

            # Create heatmap with masked zeros and diverging colormap for tumor/normal ratios
            sns.heatmap(
                heatmap_data_log2,
                annot=False,
                cmap='RdBu',  # Red-Blue diverging colormap for tumor/normal ratios
                center=0,  # Center at 0 for log2 ratios
                cbar_kws={'label': 'Log2(Tumor/Normal Ratio)'},
                linewidths=0.2,
                linecolor='white',
                square=True,
                mask=heatmap_data_log2.isna()  # Mask NaN values (original zeros)
            )

            # Customize the plot
            plt.title('Tumor Over Normal Proteomics', fontsize=16, fontweight='bold', pad=25)
            plt.xlabel('Indications/Studies', fontsize=14, fontweight='bold')
            plt.ylabel('Proteins', fontsize=14, fontweight='bold')

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)

            plt.tight_layout()

            # Save the plot
            filename = "study_specific_proteomics_expression.png"
            output_path = Path(output_dir) / "external_protein_expression" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved study-specific proteomics expression plot: {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating study-specific proteomics expression plot: {e}")
            return False

    def _generate_study_specific_plot(self, output_dir: str) -> bool:
        """Generate expression plots for study-specific data.

        Creates heatmaps showing:
        - X-axis: Studies/Indications
        - Y-axis: Proteins
        - Color intensity: Tumor-normal ratios

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get study-specific data
            df = self.get_data_for_file(FileNames.STUDY_SPECIFIC_DATA.value)
            if df is None or df.empty:
                logger.error("No study-specific data available")
                return False

            # Check for required columns
            required_columns = ['Gene']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in study-specific data: {missing_columns}")
                return False

            # Get expression columns (all columns except 'Gene')
            expression_columns = [col for col in df.columns if col != 'Gene']
            
            if not expression_columns:
                logger.error("No expression columns found in study-specific data")
                return False

            # Set up the plot
            plt.figure(figsize=(max(12, len(expression_columns) * 0.8), max(8, len(df) * 0.3)))
            sns.set_style("whitegrid")

            # Prepare data for heatmap
            heatmap_data = df.set_index('Gene')[expression_columns]

            # Create heatmap
            sns.heatmap(
                heatmap_data,
                annot=True,
                fmt='.2f',
                cmap='Blues',
                center=0,
                cbar_kws={'label': 'Tumor-Normal Ratio'},
                square=False
            )

            # Customize the plot
            plt.title('Study-Specific Tumor-Normal Ratios', fontsize=16, fontweight='bold', pad=25)
            plt.xlabel('Studies/Indications', fontsize=14, fontweight='bold')
            plt.ylabel('Proteins', fontsize=14, fontweight='bold')

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)

            plt.tight_layout()

            # Save the plot
            filename = "study_specific_ratios.png"
            output_path = Path(output_dir) / "external_protein_expression" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved study-specific ratios plot: {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating study-specific ratios plot: {e}")
            return False

    def _generate_protein_expression_boxplots(self, output_dir: str) -> bool:
        """Generate boxplots for protein expression data.

        Creates individual boxplots for each indication-protein combination:
        - Each plot shows 4 boxplots: Anchor Tumor, Anchor Normal, Other Protein Tumor, Other Protein Normal
        - Individual data points overlaid on the boxplots
        - One plot per indication per non-anchor protein

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get protein expression data
            df = self.get_data_for_file(FileNames.PROTEIN_EXPRESSION.value)
            if df is None or df.empty:
                logger.error("No protein expression data available")
                return False

            # Check for required columns
            required_columns = ['Protein', 'Expression Value', 'Tissue Type', 'Indication']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in protein expression data: {missing_columns}")
                return False

            # Get unique indications and proteins
            unique_indications = df['Indication'].unique()
            unique_proteins = df['Protein'].unique()
            
            # Filter out anchor protein to get other proteins
            other_proteins = [p for p in unique_proteins if p != self.anchor_protein]
            
            if len(other_proteins) == 0:
                logger.warning(f"No proteins found other than anchor protein: {self.anchor_protein}")
                return False

            logger.info(f"Generating {len(unique_indications) * len(other_proteins)} individual boxplots")

            # Set up the plotting style
            plt.style.use('default')
            sns.set_palette("husl")

            # Create individual plots for each indication-protein combination
            for indication in unique_indications:
                for other_protein in other_proteins:
                    # Filter data for this indication
                    indication_data = df[df['Indication'] == indication].copy()
                    
                    if indication_data.empty:
                        logger.warning(f"No data found for indication: {indication}")
                        continue

                    # Get data for both anchor protein and other protein in this indication
                    anchor_data = indication_data[indication_data['Protein'] == self.anchor_protein]
                    other_protein_data = indication_data[indication_data['Protein'] == other_protein]
                    
                    # Separate tumor and normal data for both proteins
                    anchor_tumor = anchor_data[anchor_data['Tissue Type'] == 'Tumor']['Expression Value']
                    anchor_normal = anchor_data[anchor_data['Tissue Type'] == 'Normal']['Expression Value']
                    other_tumor = other_protein_data[other_protein_data['Tissue Type'] == 'Tumor']['Expression Value']
                    other_normal = other_protein_data[other_protein_data['Tissue Type'] == 'Normal']['Expression Value']
                    
                    # Create boxplot data - always show Normal then Tumor for each protein
                    plot_data = []
                    labels = []
                    colors = []
                    
                    # Anchor protein: Normal first, then Tumor
                    if len(anchor_normal) > 0:
                        plot_data.append(anchor_normal)
                        labels.append(f'{self.anchor_protein}\nNormal')
                        colors.append(TumorNormalColors.NORMAL)
                    
                    if len(anchor_tumor) > 0:
                        plot_data.append(anchor_tumor)
                        labels.append(f'{self.anchor_protein}\nTumor')
                        colors.append(TumorNormalColors.TUMOR)
                    
                    # Other protein: Normal first, then Tumor
                    if len(other_normal) > 0:
                        plot_data.append(other_normal)
                        labels.append(f'{other_protein}\nNormal')
                        colors.append(TumorNormalColors.NORMAL)
                    
                    if len(other_tumor) > 0:
                        plot_data.append(other_tumor)
                        labels.append(f'{other_protein}\nTumor')
                        colors.append(TumorNormalColors.TUMOR)
                    
                    if not plot_data:
                        logger.warning(f"No data available for {indication} - {self.anchor_protein} vs {other_protein}")
                        continue
                    
                    # Create individual plot
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Create boxplot with individual points and grouped positioning
                    positions = []
                    current_pos = 1
                    
                    # Group positions: Anchor protein (Normal, Tumor) then Other protein (Normal, Tumor)
                    # Add small gap between proteins
                    for i in range(len(plot_data)):
                        if i == 2:  # Start of other protein group
                            current_pos += 0.5  # Add gap between proteins
                        positions.append(current_pos)
                        current_pos += 1
                    
                    bp = ax.boxplot(plot_data, labels=labels, positions=positions, patch_artist=True, 
                                  boxprops=dict(facecolor='lightgrey', alpha=0.7),
                                  medianprops=dict(color='lightgray', linewidth=2),
                                  flierprops=dict(marker='o', markerfacecolor='red', markersize=4))
                    
                    # Color the boxplots using light grey for all boxes
                    for patch in bp['boxes']:
                        patch.set_facecolor('lightgrey')
                        patch.set_alpha(0.7)
                    
                    # Add individual data points with tumor/normal colors
                    for i, (data, color, pos) in enumerate(zip(plot_data, colors, positions)):
                        # Add jitter to x-coordinates for better visibility
                        jitter = np.random.normal(0, 0.05, len(data))
                        ax.scatter(pos + jitter, data, alpha=0.6, s=20, 
                                 color=color, edgecolors='black', linewidth=0.5, zorder=10)
                    
                    # Customize the plot
                    ax.set_title(f'{indication}\n{self.anchor_protein} vs {other_protein}', 
                               fontsize=14, fontweight='bold')
                    ax.set_ylabel('Expression Value (Log2)', fontsize=12)
                    
                    # Remove top and right spines
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    
                    # Rotate x-axis labels to horizontal
                    ax.tick_params(axis='x', rotation=0)
                    
                    # Update x-axis labels to include sample counts
                    new_labels = []
                    for i, (label, data) in enumerate(zip(labels, plot_data)):
                        count = len(data)
                        new_labels.append(f'{label}\n(n={count})')
                    
                    ax.set_xticks(positions)
                    ax.set_xticklabels(new_labels)

                    # Adjust layout
                    plt.tight_layout()

                    # Save the individual plot
                    safe_indication = indication.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')
                    safe_protein = other_protein.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')
                    filename = f"protein_expression_{safe_indication}_{safe_protein}.png"
                    output_path = Path(output_dir) / "external_protein_expression" / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    plt.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close()

                    logger.info(f"Saved protein expression plot: {indication} - {self.anchor_protein} vs {other_protein}")

            return True

        except Exception as e:
            logger.exception(f"Error generating protein expression boxplots: {e}")
            return False
