"""STRING protein-protein interaction data visualization graphs."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from bd_data_fetcher.graphs.base_graph import BaseGraph

logger = logging.getLogger(__name__)


class StringGraph(BaseGraph):
    """Graph generator for STRING protein-protein interaction data.

    This class handles visualization of protein-protein interaction networks
    based on STRING database scores, including coexpression, experimental,
    and text mining evidence.
    """

    def __init__(self, data_dir_path: str, anchor_protein: str,
                 combined_score_threshold: float = 400.0):
        """Initialize the STRING graph generator.

        Args:
            data_dir_path: Path to the directory containing CSV files
            anchor_protein: Anchor protein symbol to use for graph generation
            combined_score_threshold: Minimum threshold for combined scores
        """
        super().__init__(data_dir_path, anchor_protein)
        self.combined_score_threshold = combined_score_threshold

        # Single color for all interactions
        self.edge_color = '#2E86AB'  # Blue color for all edges

    def generate_graphs(self, output_dir: str) -> bool:
        """Generate protein-protein interaction network graphs.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
        logger.info("Generating STRING protein-protein interaction graphs...")

        # Load data if not already loaded
        if not self.data:
            if not self.load_csv_data():
                return False

        success = True

        # Generate main interaction network
        if self._generate_interaction_network(output_dir):
            logger.info("Generated protein-protein interaction network")
        else:
            success = False

        # Generate interaction statistics
        if self._generate_interaction_statistics(output_dir):
            logger.info("Generated interaction statistics")
        else:
            success = False

        return success

    def _load_string_data(self) -> pd.DataFrame | None:
        """Load and filter STRING protein interaction data.

        Returns:
            Filtered DataFrame with protein interactions or None if failed
        """
        try:
            # Load the STRING data from the root directory
            string_file = Path(self.data_dir_path).parent / "human_string_protein_scores.csv"
            if not string_file.exists():
                logger.error(f"STRING data file not found: {string_file}")
                return None

            string_data = pd.read_csv(string_file)
            logger.info(f"Loaded STRING data with {len(string_data)} interactions")

            # Filter by combined score threshold
            filtered_data = string_data[string_data['combined_score'] > self.combined_score_threshold]
            logger.info(f"Filtered to {len(filtered_data)} interactions with combined_score > {self.combined_score_threshold}")

            return filtered_data

        except Exception as e:
            logger.exception(f"Error loading STRING data: {e}")
            return None

    def _get_unique_symbols(self) -> list[str]:
        """Get unique protein symbols from gene expression data.

        Returns:
            List of unique protein symbols
        """
        try:
            # Get gene expression data
            gene_expr_data = self.get_data_for_file('gene_expression.csv')
            if gene_expr_data is None or gene_expr_data.empty:
                logger.error("No gene expression data available")
                return []

            # Get unique genes
            unique_symbols = gene_expr_data['Gene'].unique().tolist()
            logger.info(f"Found {len(unique_symbols)} unique protein symbols")
            return unique_symbols

        except Exception as e:
            logger.exception(f"Error getting unique symbols: {e}")
            return []

    def _create_interaction_network(self, string_data: pd.DataFrame,
                                  unique_symbols: list[str]) -> nx.Graph:
        """Create a NetworkX graph from STRING interaction data.

        Args:
            string_data: Filtered STRING interaction data
            unique_symbols: List of unique protein symbols to include

        Returns:
            NetworkX graph with protein interactions
        """
        G = nx.Graph()

        # Add nodes for all unique symbols
        for symbol in unique_symbols:
            G.add_node(symbol)

        # Add edges based on combined_score only
        for _, row in string_data.iterrows():
            symbol1 = row['symbol1']
            symbol2 = row['symbol2']

            # Only include interactions between proteins in our gene list
            if symbol1 in unique_symbols and symbol2 in unique_symbols:
                # Only use combined_score for edge inclusion
                combined_score = row['combined_score']

                if combined_score > self.combined_score_threshold:
                    # Add edge with only combined_score attribute
                    G.add_edge(symbol1, symbol2, combined_score=combined_score)

        logger.info(f"Created network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G

    def _generate_interaction_network(self, output_dir: str) -> bool:
        """Generate the main protein-protein interaction network visualization.

        Args:
            output_dir: Directory to save the graph

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Load STRING data
            string_data = self._load_string_data()
            if string_data is None:
                return False

            # Get unique symbols
            unique_symbols = self._get_unique_symbols()
            if not unique_symbols:
                return False

            # Create network
            G = self._create_interaction_network(string_data, unique_symbols)

            if G.number_of_edges() == 0:
                logger.warning("No interactions found with current thresholds")
                return False

            # Set up the plot
            plt.figure(figsize=(16, 12))

            # Use spring layout for better visualization
            pos = nx.spring_layout(G, k=1, iterations=50, seed=42)

            # Draw nodes with larger size
            nx.draw_networkx_nodes(G, pos,
                                 node_color='lightblue',
                                 node_size=1000,  # Increased from 500 (2x larger)
                                 alpha=0.8)

                        # Draw edges with thickness based on combined_score confidence levels
            edges = list(G.edges(data=True))
            edge_widths = []
            edge_colors = []
            
            for u, v, d in edges:
                combined_score = d.get('combined_score', 0)
                
                # Categorize edges by confidence level
                if combined_score >= 701:  # High confidence
                    width = 6
                    color = '#2E86AB'  # Blue
                elif combined_score >= 400:  # Medium confidence
                    width = 3
                    color = '#7FB3D3'  # Light blue
                else:  # Low confidence (shouldn't happen due to threshold)
                    width = 1
                    color = '#B8D4E3'  # Very light blue
                
                edge_widths.append(width)
                edge_colors.append(color)

            # Draw all edges with varying thickness and colors based on confidence
            nx.draw_networkx_edges(G, pos, edgelist=edges,
                                 edge_color=edge_colors,
                                 width=edge_widths,
                                 alpha=0.7)

            # Draw node labels with larger font
            nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold')  # Increased from 8 (50% larger)

            # Customize the plot
            plt.title(f'Protein-Protein Interaction Network\n{self.anchor_protein} and Related Proteins',
                     fontsize=16, fontweight='bold', pad=20)

                        # Add legend for edge confidence levels
            legend_elements = [
                plt.Line2D([0], [0], color='#2E86AB', 
                          linewidth=6, label='High Confidence (701-1000)'),
                plt.Line2D([0], [0], color='#7FB3D3', 
                          linewidth=3, label='Medium Confidence (400-700)')
            ]
            plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))

            # Add threshold information
            threshold_text = (f'Edge Filtering:\n'
                            f'Combined Score > {self.combined_score_threshold}\n'
                            f'High Confidence: 701-1000 (thick blue)\n'
                            f'Medium Confidence: 400-700 (thin light blue)')

            plt.figtext(0.02, 0.02, threshold_text, fontsize=10,
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

            plt.tight_layout()

            # Save the plot
            filename = f"protein_interaction_network_{self.anchor_protein}.png"
            output_path = Path(output_dir) / "string_interactions" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved protein interaction network: {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating interaction network: {e}")
            return False

    def _generate_interaction_statistics(self, output_dir: str) -> bool:
        """Generate statistics about protein interactions.

        Args:
            output_dir: Directory to save the statistics

        Returns:
            True if generated successfully, False otherwise
        """
        try:
            # Load STRING data
            string_data = self._load_string_data()
            if string_data is None:
                return False

            # Get unique symbols
            unique_symbols = self._get_unique_symbols()
            if not unique_symbols:
                return False

            # Create network for statistics
            G = self._create_interaction_network(string_data, unique_symbols)

            if G.number_of_edges() == 0:
                logger.warning("No interactions found for statistics")
                return False

                        # Calculate statistics
            combined_scores = [d.get('combined_score', 0) for _, _, d in G.edges(data=True)]
            
            # Count edges by confidence level
            high_confidence_edges = len([score for score in combined_scores if score >= 701])
            medium_confidence_edges = len([score for score in combined_scores if 400 <= score < 701])
            
            stats = {
                'Total Nodes': G.number_of_nodes(),
                'Total Edges': G.number_of_edges(),
                'High Confidence Edges (701-1000)': high_confidence_edges,
                'Medium Confidence Edges (400-700)': medium_confidence_edges,
                'Avg Combined Score': np.mean(combined_scores) if combined_scores else 0,
                'Min Combined Score': np.min(combined_scores) if combined_scores else 0,
                'Max Combined Score': np.max(combined_scores) if combined_scores else 0,
                'Std Combined Score': np.std(combined_scores) if combined_scores else 0
            }

                        # Create statistics visualization
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

            # Confidence level distribution
            confidence_levels = ['High (701-1000)', 'Medium (400-700)']
            confidence_counts = [stats['High Confidence Edges (701-1000)'], stats['Medium Confidence Edges (400-700)']]
            confidence_colors = ['#2E86AB', '#7FB3D3']
            ax1.bar(confidence_levels, confidence_counts, color=confidence_colors, alpha=0.8)
            ax1.set_title('Edge Confidence Distribution', fontweight='bold')
            ax1.set_ylabel('Number of Edges')
            ax1.tick_params(axis='x', rotation=45)

            # Combined score distribution
            if combined_scores:
                ax2.hist(combined_scores, bins=20, color=self.edge_color,
                        alpha=0.7, edgecolor='black')
                ax2.set_title('Combined Score Distribution', fontweight='bold')
                ax2.set_xlabel('Combined Score')
                ax2.set_ylabel('Frequency')

            # Network metrics
            network_metrics = ['Nodes', 'Total Edges', 'High Conf', 'Medium Conf']
            network_values = [stats['Total Nodes'], stats['Total Edges'], 
                            stats['High Confidence Edges (701-1000)'], 
                            stats['Medium Confidence Edges (400-700)']]
            ax3.bar(network_metrics, network_values, color=self.edge_color, alpha=0.8)
            ax3.set_title('Network Statistics', fontweight='bold')
            ax3.set_ylabel('Count')
            ax3.tick_params(axis='x', rotation=45)

            # Score range visualization with confidence zones
            if combined_scores:
                sorted_scores = sorted(combined_scores)
                ax4.scatter(range(len(sorted_scores)), sorted_scores, 
                           color=self.edge_color, alpha=0.7, s=50)
                ax4.axhline(y=700, color='#7FB3D3', linestyle='--', alpha=0.7, label='Medium/High Threshold')
                ax4.axhline(y=400, color='#B8D4E3', linestyle='--', alpha=0.7, label='Low/Medium Threshold')
                ax4.set_title('Combined Score Range with Confidence Zones', fontweight='bold')
                ax4.set_xlabel('Edge Index (sorted)')
                ax4.set_ylabel('Combined Score')
                ax4.legend()

            plt.suptitle(f'Protein Interaction Statistics - {self.anchor_protein}',
                        fontsize=16, fontweight='bold')
            plt.tight_layout()

            # Save the plot
            filename = f"interaction_statistics_{self.anchor_protein}.png"
            output_path = Path(output_dir) / "string_interactions" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            # Save statistics to CSV
            stats_df = pd.DataFrame(list(stats.items()), columns=['Metric', 'Value'])
            stats_filename = f"interaction_statistics_{self.anchor_protein}.csv"
            stats_path = Path(output_dir) / "string_interactions" / stats_filename
            stats_df.to_csv(stats_path, index=False)

            logger.info(f"Saved interaction statistics: {output_path}")
            logger.info(f"Saved statistics CSV: {stats_path}")
            return True

        except Exception as e:
            logger.exception(f"Error generating interaction statistics: {e}")
            return False
