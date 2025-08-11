"""External protein expression data visualization graphs."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import FileNames
from bd_data_fetcher.graphs.base_graph import BaseGraph

logger = logging.getLogger(__name__)


class ExternalProteinExpressionGraph(BaseGraph):
    """Graph generator for external protein expression data.

    This class handles visualization of external proteomics data,
    including normal expression data and study-specific comparisons.
    Uses an anchor protein as a reference point for visualizations.
    """

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

            # Prepare data for heatmap
            heatmap_data = df.set_index('Gene')[expression_columns]

            # Create heatmap
            sns.heatmap(
                heatmap_data,
                annot=False,
                cmap='Blues',
                cbar_kws={'label': 'Log2 Expression'},
                linewidths=0.2,
                linecolor='white',
                square=True
            )

            # Customize the plot
            plt.title('Normal Proteomics Copies per Cell Data', fontsize=16, fontweight='bold', pad=25)
            plt.xlabel('Indications/Tissue Types', fontsize=14, fontweight='bold')
            plt.ylabel('Proteins', fontsize=14, fontweight='bold')

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)

            # Add caveat about proteomics ruler method
            plt.figtext(0.98, 0.02, 'All copy numbers calculated using the proteomics ruler method', 
                       fontsize=10, ha='right', va='bottom', 
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

            # Prepare data for heatmap
            heatmap_data = df.set_index('Gene')[expression_columns]

            # Create heatmap
            sns.heatmap(
                heatmap_data,
                annot=False,
                cmap='Blues',
                cbar_kws={'label': 'Log2 Expression'},
                linewidths=0.2,
                linecolor='white',
                square=True
            )

            # Customize the plot
            plt.title('Study-Specific Proteomics Expression Data', fontsize=16, fontweight='bold', pad=25)
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
                cmap='RdBu_r',
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
