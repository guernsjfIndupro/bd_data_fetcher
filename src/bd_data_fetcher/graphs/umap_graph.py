"""UMap data visualization graphs."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from bd_data_fetcher.data_handlers.utils import FileNames
from bd_data_fetcher.graphs.base_graph import BaseGraph
from bd_data_fetcher.graphs.shared import ProteinColors

logger = logging.getLogger(__name__)


class UMapGraph(BaseGraph):
    """Graph generator for UMap data.

    This class handles visualization of UMap analysis results,
    including log2 fold changes, p-values, and cell line targeting data.
    Uses an anchor protein as a reference point for visualizations.
    """

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for UMap data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating UMap graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_csv_data():
                return False

        success = True

        # Generate volcano plot
        if self._generate_volcano_plot(output_dir):
            logger.info("Generated volcano plot")
        else:
            success = False

        # Generate zoomed volcano plots
        if self._generate_zoomed_volcano_plot(output_dir):
            logger.info("Generated zoomed volcano plots")
        else:
            success = False

        return success

    def _add_labels_with_adjusttext(self, ax, points, labels, fontsize=20):
        """
        Add labels using adjustText library for optimal positioning in volcano plots.
        
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
            text = ax.text(x, y-0.2, label, fontsize=fontsize, ha='center', va='top', 
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

    def _generate_volcano_plot(self, output_dir: str) -> bool:
        """Generate volcano plots for UMap analysis results.

        Creates separate volcano plots for each replicate set showing:
        - X-axis: Log2 fold change
        - Y-axis: -log10(p-value)
        - Points colored by significance

        Args:
            output_dir: Directory to save the graphs

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get UMap data
            df = self.get_data_for_file(FileNames.UMAP_DATA.value)
            if df is None or df.empty:
                logger.error("No UMap data available")
                return False

            # Check for required columns
            required_columns = ['Log2 FC', 'P-value', 'Protein Symbol', 'Replicate Set ID']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in UMap data: {missing_columns}")
                return False

            # Ensure numeric columns are properly formatted
            df['Log2 FC'] = pd.to_numeric(df['Log2 FC'], errors='coerce')
            df['P-value'] = pd.to_numeric(df['P-value'], errors='coerce')

            # Remove rows with NaN values
            df = df.dropna(subset=['Log2 FC', 'P-value', 'Protein Symbol', 'Replicate Set ID'])

            if df.empty:
                logger.error("No valid numeric data found in UMap data")
                return False

            # The P-value column already contains -log10(p-value) values
            df['-log10_pvalue'] = df['P-value']

            # Get TAPA genes from normal gene expression data
            tapa_genes = set()
            try:
                normal_gene_df = self.get_data_for_file(FileNames.NORMAL_GENE_EXPRESSION.value)
                if normal_gene_df is not None and not normal_gene_df.empty and 'Gene' in normal_gene_df.columns:
                    # Get unique genes from normal gene expression data, excluding the anchor protein
                    tapa_genes = set(normal_gene_df['Gene'].unique()) - {self.anchor_protein}
                    logger.info(f"Found {len(tapa_genes)} TAPA genes from normal gene expression data")
                else:
                    logger.warning("No normal gene expression data available, will highlight all non-anchor proteins as TAPA")
            except Exception as e:
                logger.warning(f"Error loading normal gene expression data: {e}, will highlight all non-anchor proteins as TAPA")

            # Get unique replicate set IDs
            replicate_set_ids = df['Replicate Set ID'].unique()

            if len(replicate_set_ids) == 0:
                logger.error("No replicate set IDs found in UMap data")
                return False

            logger.info(f"Generating volcano plots for {len(replicate_set_ids)} replicate sets")

            success_count = 0
            total_count = len(replicate_set_ids)

            # Generate one volcano plot per replicate set
            for replicate_set_id in replicate_set_ids:
                try:
                    # Filter data for current replicate set
                    replicate_df = df[df['Replicate Set ID'] == replicate_set_id]

                    if replicate_df.empty:
                        logger.warning(f"No data found for replicate set ID: {replicate_set_id}")
                        continue

                    # Get additional info for the plot title
                    cell_line = replicate_df['Cell Line'].iloc[0] if 'Cell Line' in replicate_df.columns else "Unknown"
                    chemistry = replicate_df['Chemistry'].iloc[0] if 'Chemistry' in replicate_df.columns else "Unknown"
                    target_protein = replicate_df['Target Protein'].iloc[0] if 'Target Protein' in replicate_df.columns else "Unknown"

                    # Set up the plot
                    plt.figure(figsize=(12, 10))
                    sns.set_style("white")

                    # Create scatter plot with highlighted anchor and TAPA targets
                    # Separate data by fold change threshold - gray out values below -0.5
                    low_fc_data = replicate_df[replicate_df['Log2 FC'] < 0.5]
                    high_fc_data = replicate_df[replicate_df['Log2 FC'] >= 0.5]

                    # Plot low fold change points (below -0.5) in grey
                    if not low_fc_data.empty:
                        plt.scatter(
                            low_fc_data['Log2 FC'],
                            low_fc_data['-log10_pvalue'],
                            alpha=0.2,
                            color='grey',
                            s=20,
                        )

                    # Plot high fold change points (≥-0.5) in light blue
                    if not high_fc_data.empty:
                        plt.scatter(
                            high_fc_data['Log2 FC'],
                            high_fc_data['-log10_pvalue'],
                            alpha=0.3,
                            color='lightblue',
                            s=30,
                        )

                    # Collect points and labels for smart positioning
                    points = []
                    labels = []
                    colors = []

                    # Highlight anchor protein (if present) - always highlight regardless of fold change
                    anchor_data = replicate_df[replicate_df['Protein Symbol'] == self.anchor_protein]
                    if not anchor_data.empty:
                        anchor_color = ProteinColors.get_color(self.anchor_protein, self.anchor_protein)
                        plt.scatter(
                            anchor_data['Log2 FC'],
                            anchor_data['-log10_pvalue'],
                            alpha=0.8,
                            color=anchor_color,
                            s=100,
                            label=f'Anchor Protein ({self.anchor_protein})',
                            zorder=5
                        )
                        # Collect anchor protein data for labeling
                        for _, row in anchor_data.iterrows():
                            points.append((row['Log2 FC'], row['-log10_pvalue']))
                            labels.append(self.anchor_protein)
                            colors.append(anchor_color)

                    # Highlight only TAPA genes from normal gene expression data
                    if tapa_genes:
                        tapa_data = replicate_df[replicate_df['Protein Symbol'].isin(tapa_genes)]
                        if not tapa_data.empty:
                            tapa_color = ProteinColors.get_color('tapa', self.anchor_protein)
                            plt.scatter(
                                tapa_data['Log2 FC'],
                                tapa_data['-log10_pvalue'],
                                alpha=0.8,
                                color=tapa_color,
                                s=100,
                                label='TAPA Proteins',
                                zorder=5
                            )
                            # Collect TAPA protein data for labeling
                            for _, row in tapa_data.iterrows():
                                points.append((row['Log2 FC'], row['-log10_pvalue']))
                                labels.append(row['Protein Symbol'])
                                colors.append(tapa_color)
                    else:
                        # Fallback: highlight all other proteins as TAPA proteins if no normal gene expression data
                        other_proteins_data = replicate_df[replicate_df['Protein Symbol'] != self.anchor_protein]
                        if not other_proteins_data.empty:
                            tapa_color = ProteinColors.get_color('tapa', self.anchor_protein)
                            plt.scatter(
                                other_proteins_data['Log2 FC'],
                                other_proteins_data['-log10_pvalue'],
                                alpha=0.8,
                                color=tapa_color,
                                s=100,
                                label='TAPA Proteins',
                                zorder=5
                            )
                            # Collect other protein data for labeling
                            for _, row in other_proteins_data.iterrows():
                                points.append((row['Log2 FC'], row['-log10_pvalue']))
                                labels.append(row['Protein Symbol'])
                                colors.append(tapa_color)

                    # Add labels using adjustText for optimal positioning
                    if points:
                        ax = plt.gca()
                        self._add_labels_with_adjusttext(ax, points, labels, fontsize=12)

                    # Customize the plot
                    # Remove title and axis labels as requested
                    # plt.title(f'UMap Analysis Results - Volcano Plot\nReplicate Set {replicate_set_id}\nCell Line: {cell_line} | Chemistry: {chemistry} | Target: {target_protein}',
                    #          fontsize=16, fontweight='bold', pad=25)
                    # plt.xlabel('Log2 Fold Change', fontsize=14, fontweight='bold')
                    # plt.ylabel('-log10(p-value)', fontsize=14, fontweight='bold')



                    # Add legend - moved to top left as requested
                    plt.legend(loc='upper left', fontsize=10)

                    # Remove top and right borders
                    ax = plt.gca()
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)

                    plt.tight_layout()

                    # Save the plot
                    filename = f"umap_volcano_plot_replicate_set_{replicate_set_id}.png"
                    output_path = Path(output_dir) / "umap" / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    plt.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close()

                    logger.info(f"Saved volcano plot for replicate set {replicate_set_id}: {output_path}")
                    success_count += 1

                except Exception as e:
                    logger.exception(f"Error generating volcano plot for replicate set {replicate_set_id}: {e}")
                    continue

            logger.info(f"Generated {success_count}/{total_count} volcano plots successfully")
            return success_count > 0

        except Exception as e:
            logger.exception(f"Error generating volcano plots: {e}")
            return False

    def _generate_zoomed_volcano_plot(self, output_dir: str, label_size: int = 20) -> bool:
        """Generate zoomed-in volcano plots for UMap analysis results.

        Creates separate zoomed-in volcano plots for each replicate set showing:
        - X-axis: Log2 fold change (filtered to > 0.5)
        - Y-axis: -log10(p-value) (filtered to > 1.3)
        - Points colored by significance with large, non-overlapping labels

        Args:
            output_dir: Directory to save the graphs
            label_size: Font size for protein labels (default: 20)

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Get UMap data
            df = self.get_data_for_file(FileNames.UMAP_DATA.value)
            if df is None or df.empty:
                logger.error("No UMap data available")
                return False

            # Check for required columns
            required_columns = ['Log2 FC', 'P-value', 'Protein Symbol', 'Replicate Set ID']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in UMap data: {missing_columns}")
                return False

            # Ensure numeric columns are properly formatted
            df['Log2 FC'] = pd.to_numeric(df['Log2 FC'], errors='coerce')
            df['P-value'] = pd.to_numeric(df['P-value'], errors='coerce')

            # Remove rows with NaN values
            df = df.dropna(subset=['Log2 FC', 'P-value', 'Protein Symbol', 'Replicate Set ID'])

            if df.empty:
                logger.error("No valid numeric data found in UMap data")
                return False

            # The P-value column already contains -log10(p-value) values
            df['-log10_pvalue'] = df['P-value']

            # Filter for zoomed-in view: Log2 FC > 0.5 and -log10(p-value) > 1.3
            zoomed_df = df[(df['Log2 FC'] > 0.5) & (df['-log10_pvalue'] > 1.3)]

            if zoomed_df.empty:
                logger.warning("No data points meet the zoom criteria (Log2 FC > 0.5 and -log10(p-value) > 1.3)")
                return False

            # Get TAPA genes from normal gene expression data
            tapa_genes = set()
            try:
                normal_gene_df = self.get_data_for_file(FileNames.NORMAL_GENE_EXPRESSION.value)
                if normal_gene_df is not None and not normal_gene_df.empty and 'Gene' in normal_gene_df.columns:
                    # Get unique genes from normal gene expression data, excluding the anchor protein
                    tapa_genes = set(normal_gene_df['Gene'].unique()) - {self.anchor_protein}
                    logger.info(f"Found {len(tapa_genes)} TAPA genes from normal gene expression data")
                else:
                    logger.warning("No normal gene expression data available, will highlight all non-anchor proteins as TAPA")
            except Exception as e:
                logger.warning(f"Error loading normal gene expression data: {e}, will highlight all non-anchor proteins as TAPA")

            # Get unique replicate set IDs from filtered data
            replicate_set_ids = zoomed_df['Replicate Set ID'].unique()

            if len(replicate_set_ids) == 0:
                logger.error("No replicate set IDs found in zoomed UMap data")
                return False

            logger.info(f"Generating zoomed volcano plots for {len(replicate_set_ids)} replicate sets")

            success_count = 0
            total_count = len(replicate_set_ids)

            # Generate one zoomed volcano plot per replicate set
            for replicate_set_id in replicate_set_ids:
                try:
                    # Filter data for current replicate set
                    replicate_df = zoomed_df[zoomed_df['Replicate Set ID'] == replicate_set_id]

                    if replicate_df.empty:
                        logger.warning(f"No zoomed data found for replicate set ID: {replicate_set_id}")
                        continue

                    # Set up the plot
                    plt.figure(figsize=(14, 12))
                    sns.set_style("white")

                    # Collect points and labels for smart positioning
                    points = []
                    labels = []
                    colors = []

                    # Plot all points in the zoomed region
                    plt.scatter(
                        replicate_df['Log2 FC'],
                        replicate_df['-log10_pvalue'],
                        alpha=0.6,
                        color='lightblue',
                        s=100,
                        zorder=3
                    )

                    # Highlight anchor protein (if present)
                    anchor_data = replicate_df[replicate_df['Protein Symbol'] == self.anchor_protein]
                    if not anchor_data.empty:
                        anchor_color = ProteinColors.get_color(self.anchor_protein, self.anchor_protein)
                        plt.scatter(
                            anchor_data['Log2 FC'],
                            anchor_data['-log10_pvalue'],
                            alpha=0.9,
                            color=anchor_color,
                            s=200,
                            label=f'Anchor Protein ({self.anchor_protein})',
                            zorder=5
                        )
                        
                        # Collect anchor protein data for labeling
                        for _, row in anchor_data.iterrows():
                            points.append((row['Log2 FC'], row['-log10_pvalue']))
                            labels.append(self.anchor_protein)
                            colors.append(anchor_color)

                    # Highlight TAPA genes
                    if tapa_genes:
                        tapa_data = replicate_df[replicate_df['Protein Symbol'].isin(tapa_genes)]
                        if not tapa_data.empty:
                            tapa_color = ProteinColors.get_color('tapa', self.anchor_protein)
                            plt.scatter(
                                tapa_data['Log2 FC'],
                                tapa_data['-log10_pvalue'],
                                alpha=0.8,
                                color=tapa_color,
                                s=150,
                                label='TAPA Proteins',
                                zorder=4
                            )
                            
                            # Collect TAPA protein data for labeling
                            for _, row in tapa_data.iterrows():
                                points.append((row['Log2 FC'], row['-log10_pvalue']))
                                labels.append(row['Protein Symbol'])
                                colors.append(tapa_color)
                    else:
                        # Fallback: highlight all other proteins as TAPA proteins
                        other_proteins_data = replicate_df[replicate_df['Protein Symbol'] != self.anchor_protein]
                        if not other_proteins_data.empty:
                            tapa_color = ProteinColors.get_color('tapa', self.anchor_protein)
                            plt.scatter(
                                other_proteins_data['Log2 FC'],
                                other_proteins_data['-log10_pvalue'],
                                alpha=0.8,
                                color=tapa_color,
                                s=150,
                                label='TAPA Proteins',
                                zorder=4
                            )
                            
                            # Collect other protein data for labeling
                            for _, row in other_proteins_data.iterrows():
                                points.append((row['Log2 FC'], row['-log10_pvalue']))
                                labels.append(row['Protein Symbol'])
                                colors.append(tapa_color)

                    # Add labels using adjustText for optimal positioning
                    if points:
                        ax = plt.gca()
                        self._add_labels_with_adjusttext(ax, points, labels, fontsize=label_size)

                    # Customize the plot
                    # Title and axis labels removed as requested

                    # Set axis limits for zoomed view
                    plt.xlim(0.5, replicate_df['Log2 FC'].max() * 1.1)
                    plt.ylim(1.3, replicate_df['-log10_pvalue'].max() * 1.1)

                    # Add legend
                    plt.legend(loc='upper left', fontsize=12)

                    # Remove top and right borders
                    ax = plt.gca()
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)

                    plt.tight_layout()

                    # Save the plot in zoomed_in subfolder
                    safe_replicate_id = str(replicate_set_id).replace(' ', '_').replace('/', '_').replace('\\', '_')
                    filename = f"zoomed_volcano_plot_{safe_replicate_id}.png"
                    output_path = Path(output_dir) / "umap" / "zoomed_in" / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    plt.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close()

                    logger.info(f"Saved zoomed volcano plot for replicate set {replicate_set_id}: {output_path}")
                    success_count += 1

                except Exception as e:
                    logger.exception(f"Error generating zoomed volcano plot for replicate set {replicate_set_id}: {e}")
                    continue

            logger.info(f"Generated {success_count}/{total_count} zoomed volcano plots successfully")
            return success_count > 0

        except Exception as e:
            logger.exception(f"Error generating zoomed volcano plots: {e}")
            return False
