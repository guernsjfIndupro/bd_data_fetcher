"""Internal WCE data visualization graphs."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import FileNames
from bd_data_fetcher.graphs.base_graph import BaseGraph

logger = logging.getLogger(__name__)


class InternalWCEGraph(BaseGraph):
    """Graph generator for internal WCE data.

    This class handles visualization of WCE proteomics data,
    including cell line measurements and sigmoidal curves.
    Uses an anchor protein as a reference point for visualizations.
    """

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for internal WCE data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating internal WCE graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_csv_data():
                return False

        success = True

        # Generate WCE data plots
        if self._generate_wce_data_plots(output_dir):
            logger.info("Generated WCE data plots")
        else:
            success = False

        # Generate sigmoidal curves
        if self._generate_sigmoidal_curves(output_dir):
            logger.info("Generated sigmoidal curves")
        else:
            success = False

        return success

    def _generate_wce_data_plots(self, output_dir: str) -> bool:
        """Generate plots for WCE data.

        Creates bar plots showing:
        - X-axis: Cell lines
        - Y-axis: Weight normalized intensity ranking
        - Grouped by onc lineage

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get WCE data
            df = self.get_data_for_file(FileNames.WCE_DATA.value)
            if df is None or df.empty:
                logger.error("No WCE data available")
                return False

            # Check for required columns
            required_columns = ['Cell Line', 'Weight Normalized Intensity Ranking', 'Onc Lineage']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in WCE data: {missing_columns}")
                return False

            # Ensure numeric column is properly formatted
            df['Weight Normalized Intensity Ranking'] = pd.to_numeric(df['Weight Normalized Intensity Ranking'], errors='coerce')

            # Remove rows with NaN values
            df = df.dropna(subset=['Weight Normalized Intensity Ranking', 'Cell Line', 'Onc Lineage'])

            if df.empty:
                logger.error("No valid numeric data found in WCE data")
                return False

            # Set up the plot
            plt.figure(figsize=(15, 10))
            sns.set_style("whitegrid")

            # Create box plot by onc lineage
            sns.boxplot(
                data=df,
                x='Onc Lineage',
                y='Weight Normalized Intensity Ranking',
                palette='Set3'
            )

            # Customize the plot
            plt.title('WCE Data - Weight Normalized Intensity Ranking by Onc Lineage', fontsize=16, fontweight='bold', pad=25)
            plt.xlabel('Onc Lineage', fontsize=14, fontweight='bold')
            plt.ylabel('Weight Normalized Intensity Ranking', fontsize=14, fontweight='bold')

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')

            plt.tight_layout()

            # Save the plot
            filename = "wce_intensity_ranking.png"
            output_path = Path(output_dir) / "internal_wce" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved WCE intensity ranking plot: {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating WCE data plots: {e}")
            return False

    def _generate_sigmoidal_curves(self, output_dir: str) -> bool:
        """Generate sigmoidal curves from WCE data.

        Creates separate line plots for each cell line showing:
        - X-axis: Standardized rankings (0-1000)
        - Y-axis: Log10-transformed normalized intensities
        - Smooth curves with average protein ranks as points

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get sigmoidal curves data
            curves_df = self.get_data_for_file(FileNames.CELL_LINE_SIGMOIDAL_CURVES.value)
            if curves_df is None or curves_df.empty:
                logger.error("No sigmoidal curves data available")
                return False

            # Get WCE data for protein ranks
            wce_df = self.get_data_for_file(FileNames.WCE_DATA.value)
            if wce_df is None or wce_df.empty:
                logger.warning("No WCE data available for protein ranks")
                wce_df = None

            # Check for required columns
            required_columns = ['Cell_Line_Name', 'Is_Y_Axis']
            missing_columns = [col for col in required_columns if col not in curves_df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in sigmoidal curves data: {missing_columns}")
                return False

            # Get point columns (all columns starting with 'Point_')
            point_columns = [col for col in curves_df.columns if col.startswith('Point_')]
            
            if not point_columns:
                logger.error("No point data found in sigmoidal curves")
                return False

            # Get unique cell lines
            cell_lines = curves_df['Cell_Line_Name'].unique()

            if len(cell_lines) == 0:
                logger.error("No cell lines found in sigmoidal curves data")
                return False

            logger.info(f"Generating sigmoidal curves for {len(cell_lines)} cell lines")

            success_count = 0
            total_count = len(cell_lines)

            # Generate one curve per cell line
            for cell_line in cell_lines:
                try:
                    # Filter data for current cell line
                    cell_line_data = curves_df[curves_df['Cell_Line_Name'] == cell_line]
                    
                    if cell_line_data.empty:
                        logger.warning(f"No data found for cell line: {cell_line}")
                        continue

                    # Get Y-axis data (Is_Y_Axis = 1)
                    y_data = cell_line_data[cell_line_data['Is_Y_Axis'] == 1]
                    
                    if y_data.empty:
                        logger.warning(f"No Y-axis data found for cell line: {cell_line}")
                        continue

                    # Extract point values
                    y_values = y_data[point_columns].iloc[0].values
                    x_values = np.linspace(0, 1000, len(point_columns))

                    # Set up the plot
                    plt.figure(figsize=(12, 8))
                    sns.set_style("whitegrid")

                    # Apply smoothing to the curve using spline interpolation
                    from scipy.interpolate import make_interp_spline
                    
                    # Create smooth curve
                    x_smooth = np.linspace(0, 1000, 1000)  # More points for smoothness
                    spline = make_interp_spline(x_values, y_values, k=3)  # Cubic spline
                    y_smooth = spline(x_smooth)

                    # Plot the smooth curve
                    plt.plot(x_smooth, y_smooth, color='#2a9bb3', linewidth=3, alpha=0.8, label='Sigmoidal Curve')

                    # Add protein rank points if WCE data is available
                    if wce_df is not None and 'Cell Line' in wce_df.columns and 'Gene' in wce_df.columns:
                        # Filter WCE data for this cell line
                        cell_line_wce = wce_df[wce_df['Cell Line'] == cell_line]
                        
                        if not cell_line_wce.empty:
                            # Calculate average rank for each protein
                            protein_ranks = cell_line_wce.groupby('Gene')['Weight Normalized Intensity Ranking'].mean()
                            
                            # Plot protein rank points
                            for protein, avg_rank in protein_ranks.items():
                                # Find corresponding Y value for this rank
                                rank_idx = int((avg_rank / 1000) * len(y_values))
                                rank_idx = min(rank_idx, len(y_values) - 1)  # Ensure within bounds
                                y_point = y_values[rank_idx]
                                
                                plt.scatter(avg_rank, y_point, color='#e74c3c', s=50, alpha=0.7, zorder=5)
                                
                                # Add protein symbol label
                                plt.annotate(
                                    protein,
                                    xy=(avg_rank, y_point),
                                    xytext=(0, -10),
                                    textcoords='offset points',
                                    fontsize=8,
                                    ha='center',
                                    va='top',
                                    color='black'
                                )

                    # Customize the plot
                    plt.title(f'Sigmoidal Curve - {cell_line}', fontsize=16, fontweight='bold', pad=25)
                    plt.xlabel('Standardized Rankings (0-1000)', fontsize=14, fontweight='bold')
                    plt.ylabel('Log10 Normalized Intensity', fontsize=14, fontweight='bold')

                    # Add legend
                    plt.legend(loc='upper right', fontsize=10)

                    # Remove top and right borders
                    ax = plt.gca()
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)

                    plt.tight_layout()

                    # Save the plot
                    safe_cell_line = cell_line.replace(' ', '_').replace('/', '_').replace('\\', '_')
                    filename = f"sigmoidal_curve_{safe_cell_line}.png"
                    output_path = Path(output_dir) / "internal_wce" / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    plt.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close()

                    logger.info(f"Saved sigmoidal curve for {cell_line}: {output_path}")
                    success_count += 1

                except Exception as e:
                    logger.exception(f"Error generating sigmoidal curve for cell line {cell_line}: {e}")
                    continue

            logger.info(f"Generated {success_count}/{total_count} sigmoidal curves successfully")
            return success_count > 0

        except Exception as e:
            logger.exception(f"Error generating sigmoidal curves: {e}")
            return False
