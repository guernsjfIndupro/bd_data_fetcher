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

        Creates line plots showing:
        - X-axis: Standardized rankings (0-1000)
        - Y-axis: Log10-transformed normalized intensities
        - One line per cell line

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

            # Set up the plot
            plt.figure(figsize=(12, 8))
            sns.set_style("whitegrid")

            # Create x-axis values (0-1000)
            x_values = np.linspace(0, 1000, len(point_columns))

            # Plot curves for each cell line
            colors = plt.cm.Set3(np.linspace(0, 1, len(cell_lines)))
            
            for i, cell_line in enumerate(cell_lines):
                cell_line_data = curves_df[curves_df['Cell_Line_Name'] == cell_line]
                
                # Get Y-axis data (Is_Y_Axis = 1)
                y_data = cell_line_data[cell_line_data['Is_Y_Axis'] == 1]
                
                if not y_data.empty:
                    # Extract point values
                    y_values = y_data[point_columns].iloc[0].values
                    
                    # Plot the curve
                    plt.plot(
                        x_values,
                        y_values,
                        color=colors[i],
                        alpha=0.8,
                        linewidth=2,
                        label=cell_line
                    )

            # Customize the plot
            plt.title('Sigmoidal Curves - Cell Line Proteomics Data', fontsize=16, fontweight='bold', pad=25)
            plt.xlabel('Standardized Rankings (0-1000)', fontsize=14, fontweight='bold')
            plt.ylabel('Log10 Normalized Intensity', fontsize=14, fontweight='bold')

            # Add legend
            plt.legend(title='Cell Lines', loc='upper right', fontsize=8, bbox_to_anchor=(1.15, 1))

            plt.tight_layout()

            # Save the plot
            filename = "sigmoidal_curves.png"
            output_path = Path(output_dir) / "internal_wce" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved sigmoidal curves plot: {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating sigmoidal curves: {e}")
            return False
