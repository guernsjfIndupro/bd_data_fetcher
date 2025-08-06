"""Internal WCE data visualization graphs."""

import logging

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from bd_data_fetcher.data_handlers.utils import SheetNames
from bd_data_fetcher.graphs.base_graph import BaseGraph

logger = logging.getLogger(__name__)


class InternalWCEGraph(BaseGraph):
    """Graph generator for Internal WCE data.

    This class handles visualization of WCE (Whole Cell Extract) data,
    including proteomics measurements and sigmoidal curves.
    """

    def get_supported_sheets(self) -> list[str]:
        """Get list of sheet names that this graph class can process.

        Returns:
            List of supported sheet names
        """
        return [SheetNames.WCE_DATA.value, SheetNames.CELL_LINE_SIGMOIDAL_CURVES.value]

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for Internal WCE data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating Internal WCE graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_excel_data():
                return False

        success = True

        # Generate WCE data distribution
        if self._generate_wce_bar_plots(output_dir):
            logger.info("Generated WCE data distribution graph")
        else:
            success = False

        # Generate sigmoidal curves
        if self._generate_sigmoidal_curves(output_dir):
            logger.info("Generated sigmoidal curves")
        else:
            success = False

        return success

    def _generate_wce_bar_plots(self, output_dir: str) -> bool:
        """Generate bar plots of WCE data for each unique gene.

        Creates professional bar plots using Seaborn with:
        - X-axis: cell line names
        - Y-axis: average Weight Normalized Intensity Ranking
        - One plot per unique gene

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get WCE data
            df = self.get_sheet_data(SheetNames.WCE_DATA.value)
            if df is None or df.empty:
                logger.error("No WCE data available")
                return False

            # Check for required columns
            required_columns = ['Gene', 'Cell Line', 'Onc Lineage', 'Weight Normalized Intensity Ranking', 'Is Mapped']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in WCE data: {missing_columns}")
                logger.info(f"Available columns: {list(df.columns)}")
                return False

            # Set Seaborn style for professional medical appearance
            sns.set_style("whitegrid")
            sns.set_palette(["#45cfe0"])  # Use the specified light blue color

            # Get unique genes
            unique_genes = df['Gene'].unique()
            logger.info(f"Found {len(unique_genes)} unique genes for plotting")

            # Ensure Weight Normalized Intensity Ranking is numeric
            df['Weight Normalized Intensity Ranking'] = pd.to_numeric(
                df['Weight Normalized Intensity Ranking'], errors='coerce'
            )
            
            # Remove rows with NaN values in the ranking column
            df = df.dropna(subset=['Weight Normalized Intensity Ranking'])
            if df.empty:
                logger.error("No valid numeric data found in Weight Normalized Intensity Ranking column")
                return False

            # Filter to only include mapped proteins
            df = df[df['Is Mapped'] == True]
            if df.empty:
                logger.error("No mapped proteins found in WCE data")
                return False

            # Get unique genes from mapped data
            unique_genes = df['Gene'].unique()
            logger.info(f"Found {len(unique_genes)} unique mapped genes for plotting")

            # Create plots for each gene
            for gene in unique_genes:
                # Filter data for current gene
                gene_data = df[df['Gene'] == gene]
                
                if gene_data.empty:
                    logger.warning(f"No data found for gene: {gene}")
                    continue

                # Calculate average Weight Normalized Intensity Ranking by cell line
                avg_data = gene_data.groupby(['Cell Line', 'Onc Lineage'])['Weight Normalized Intensity Ranking'].mean().reset_index()
                
                if avg_data.empty:
                    logger.warning(f"No valid data for gene: {gene}")
                    continue

                # Sort by onc_lineage and then by cell line name
                avg_data = avg_data.sort_values(['Onc Lineage', 'Cell Line'])
                
                # Create the plot
                plt.figure(figsize=(16, 10))
                
                # Create bar plot using Seaborn with different colors per onc_lineage
                ax = sns.barplot(
                    data=avg_data,
                    x='Cell Line',
                    y='Weight Normalized Intensity Ranking',
                    hue='Onc Lineage',
                    palette='Set2',
                    alpha=0.9
                )

                # Customize the plot for medical professional appearance
                plt.title(f'Protein Expression Analysis\nGene: {gene}', 
                         fontsize=18, fontweight='bold', pad=25)
                plt.xlabel('Cell Line', fontsize=14, fontweight='bold')
                plt.ylabel('Weight Normalized Intensity Ranking', fontsize=14, fontweight='bold')
                
                # Set Y-axis range from 0 to 1000
                plt.ylim(0, 1000)
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45, ha='right', fontsize=12)
                plt.yticks(fontsize=12)
                
                # Add legend for onc_lineage colors
                plt.legend(title='Onc Lineage', loc='upper right', fontsize=10)
                
                # Add grid for better readability
                plt.grid(True, alpha=0.3, linestyle='--')

                # Adjust layout to prevent label cutoff
                plt.tight_layout()
                
                # Save the plot
                filename = f"wce_bar_plot_{gene.replace(' ', '_').replace('/', '_')}.png"
                if not self.save_graph(plt.gcf(), filename, output_dir):
                    logger.error(f"Failed to save plot for gene: {gene}")
                    return False
                
                plt.close()

            logger.info(f"Successfully generated bar plots for {len(unique_genes)} genes")
            return True

        except Exception as e:
            logger.exception(f"Error generating WCE bar plots: {e}")
            return False

    def _generate_sigmoidal_curves(self, output_dir: str) -> bool:
        """Generate sigmoidal curve plots for each cell line with protein dots.

        Creates professional plots showing sigmoidal curves for each cell line
        with protein dots plotted along the curve and labels underneath.

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get sigmoidal curves data
            curves_df = self.get_sheet_data(SheetNames.CELL_LINE_SIGMOIDAL_CURVES.value)
            if curves_df is None or curves_df.empty:
                logger.error("No sigmoidal curves data available")
                return False

            # Get WCE data for protein information
            wce_df = self.get_sheet_data(SheetNames.WCE_DATA.value)
            if wce_df is None or wce_df.empty:
                logger.error("No WCE data available for protein plotting")
                return False

            # Check for required columns in curves data
            required_curve_columns = ['Cell_Line_Name', 'Is_Y_Axis']
            missing_curve_columns = [col for col in required_curve_columns if col not in curves_df.columns]
            if missing_curve_columns:
                logger.error(f"Missing required columns in sigmoidal curves data: {missing_curve_columns}")
                return False

            # Check for required columns in WCE data
            required_wce_columns = ['Gene', 'Cell Line', 'Weight Normalized Intensity Ranking']
            missing_wce_columns = [col for col in required_wce_columns if col not in wce_df.columns]
            if missing_wce_columns:
                logger.error(f"Missing required columns in WCE data: {missing_wce_columns}")
                return False

            # Ensure Weight Normalized Intensity Ranking is numeric
            wce_df['Weight Normalized Intensity Ranking'] = pd.to_numeric(
                wce_df['Weight Normalized Intensity Ranking'], errors='coerce'
            )
            
            # Remove rows with NaN values in the ranking column
            wce_df = wce_df.dropna(subset=['Weight Normalized Intensity Ranking'])
            if wce_df.empty:
                logger.error("No valid numeric data found in Weight Normalized Intensity Ranking column")
                return False

            # Set Seaborn style for professional appearance
            sns.set_style("whitegrid")
            sns.set_palette("husl")

            # Get unique cell lines from curves data
            unique_cell_lines = curves_df['Cell_Line_Name'].unique()
            logger.info(f"Found {len(unique_cell_lines)} unique cell lines for sigmoidal curves")

            # Create plots for each cell line
            for cell_line in unique_cell_lines:
                # Filter curve data for current cell line
                cell_line_curves = curves_df[curves_df['Cell_Line_Name'] == cell_line]
                
                if cell_line_curves.empty:
                    logger.warning(f"No curve data found for cell line: {cell_line}")
                    continue

                # Separate X and Y data
                x_data = cell_line_curves[cell_line_curves['Is_Y_Axis'] == 0]
                y_data = cell_line_curves[cell_line_curves['Is_Y_Axis'] == 1]

                if x_data.empty or y_data.empty:
                    logger.warning(f"Incomplete curve data for cell line: {cell_line}")
                    continue

                # Extract curve points (500 points from Point_0 to Point_499)
                point_columns = [f"Point_{i}" for i in range(500)]
                x_points = x_data[point_columns].iloc[0].values
                y_points = y_data[point_columns].iloc[0].values

                # Filter WCE data for proteins detected in this cell line
                cell_line_proteins = wce_df[wce_df['Cell Line'] == cell_line]
                
                if cell_line_proteins.empty:
                    logger.warning(f"No protein data found for cell line: {cell_line}")
                    continue

                # Average protein values for each gene (in case of duplicates)
                protein_averages = cell_line_proteins.groupby('Gene')['Weight Normalized Intensity Ranking'].mean().reset_index()
                logger.info(f"Found {len(protein_averages)} unique proteins for cell line {cell_line}")

                # Create the plot
                plt.figure(figsize=(16, 12))
                
                # Plot the sigmoidal curve
                plt.plot(x_points, y_points, 'b-', linewidth=3, alpha=0.9, label='Sigmoidal Curve')
                
                # Plot protein dots along the curve
                for _, protein in protein_averages.iterrows():
                    gene_name = protein['Gene']
                    ranking = protein['Weight Normalized Intensity Ranking']
                    
                    # Find the closest point on the curve to the protein's ranking
                    closest_idx = np.argmin(np.abs(x_points - ranking))
                    curve_x = x_points[closest_idx]
                    curve_y = y_points[closest_idx]
                    
                    # Plot the protein dot
                    plt.scatter(curve_x, curve_y, color='#45cfe0', s=150, alpha=0.9, zorder=5, edgecolors='#2a9bb3', linewidth=1)
                    
                    # Calculate label position to avoid overlap
                    label_offset = 0.3
                    label_x = curve_x
                    label_y = curve_y - label_offset
                    
                    # Add protein label with improved styling
                    plt.annotate(
                        gene_name,
                        xy=(curve_x, curve_y),
                        xytext=(label_x, label_y),
                        ha='center',
                        va='top',
                        fontsize=10,
                        fontweight='bold',
                        color='#2a9bb3',
                        bbox=dict(
                            boxstyle='round,pad=0.3', 
                            facecolor='white', 
                            alpha=0.95,
                            edgecolor='#45cfe0',
                            linewidth=1
                        ),
                        arrowprops=dict(
                            arrowstyle='->', 
                            color='#45cfe0', 
                            alpha=0.8,
                            lw=1.5,
                            shrinkA=5,
                            shrinkB=5
                        )
                    )

                # Customize the plot
                plt.title(f'Protein Distribution on Sigmoidal Curve\nCell Line: {cell_line}', 
                         fontsize=18, fontweight='bold', pad=25)
                plt.xlabel('Weight Normalized Intensity Ranking', fontsize=14, fontweight='bold')
                plt.ylabel('Log10 Normalized Intensity', fontsize=14, fontweight='bold')
                
                # Add grid for better readability
                plt.grid(True, alpha=0.2, linestyle='--')
                
                # Add legend with better positioning
                plt.legend(loc='upper right', fontsize=12, framealpha=0.9)
                
                # Adjust layout to prevent label cutoff
                plt.tight_layout()
                
                # Save the plot
                filename = f"sigmoidal_curve_{cell_line.replace(' ', '_').replace('/', '_')}.png"
                if not self.save_graph(plt.gcf(), filename, output_dir):
                    logger.error(f"Failed to save sigmoidal curve plot for cell line: {cell_line}")
                    return False
                
                plt.close()

            logger.info(f"Successfully generated sigmoidal curve plots for {len(unique_cell_lines)} cell lines")
            return True

        except Exception as e:
            logger.exception(f"Error generating sigmoidal curves: {e}")
            return False
