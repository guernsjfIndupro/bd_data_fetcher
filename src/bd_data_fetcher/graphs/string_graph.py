"""STRING protein-protein interaction data visualization graphs."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
                 coexpression_threshold: float = 0.0,
                 experiments_threshold: float = 0.0,
                 textmining_threshold: float = 0.0,
                 combined_score_threshold: float = 400.0):
        """Initialize the STRING graph generator.

        Args:
            data_dir_path: Path to the directory containing CSV files
            anchor_protein: Anchor protein symbol to use for graph generation
            coexpression_threshold: Minimum threshold for coexpression scores
            experiments_threshold: Minimum threshold for experimental scores
            textmining_threshold: Minimum threshold for text mining scores
            combined_score_threshold: Minimum threshold for combined scores
        """
        super().__init__(data_dir_path, anchor_protein)
        self.coexpression_threshold = coexpression_threshold
        self.experiments_threshold = experiments_threshold
        self.textmining_threshold = textmining_threshold
        self.combined_score_threshold = combined_score_threshold
        
        # Color scheme for different interaction types
        self.interaction_colors = {
            'coexpression': '#FF6B6B',      # Red
            'experiments': '#4ccd4c',       # Green
            'textmining': '#45B7D1'         # Blue
        }

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

    def _load_string_data(self) -> Optional[pd.DataFrame]:
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

    def _get_unique_symbols(self) -> List[str]:
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
                                  unique_symbols: List[str]) -> nx.Graph:
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
        
        # Add edges based on interaction scores
        for _, row in string_data.iterrows():
            symbol1 = row['symbol1']
            symbol2 = row['symbol2']
            
            # Only include interactions between proteins in our gene list
            if symbol1 in unique_symbols and symbol2 in unique_symbols:
                # Check if any score meets the threshold
                has_coexpression = row['coexpression_both_prior_corrected'] > self.coexpression_threshold
                has_experiments = row['experiments_both_prior_corrected'] > self.experiments_threshold
                has_textmining = row['textmining_both_prior_corrected'] > self.textmining_threshold
                
                if has_coexpression or has_experiments or has_textmining:
                    # Add edge with attributes
                    edge_attrs = {
                        'coexpression_score': row['coexpression_both_prior_corrected'],
                        'experiments_score': row['experiments_both_prior_corrected'],
                        'textmining_score': row['textmining_both_prior_corrected'],
                        'combined_score': row['combined_score'],
                        'has_coexpression': has_coexpression,
                        'has_experiments': has_experiments,
                        'has_textmining': has_textmining
                    }
                    G.add_edge(symbol1, symbol2, **edge_attrs)
        
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
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, 
                                 node_color='lightblue',
                                 node_size=500,
                                 alpha=0.8)
            
            # Draw edges with different colors based on interaction type
            coexpression_edges = [(u, v) for u, v, d in G.edges(data=True) 
                                 if d.get('has_coexpression', False)]
            experiments_edges = [(u, v) for u, v, d in G.edges(data=True) 
                               if d.get('has_experiments', False)]
            textmining_edges = [(u, v) for u, v, d in G.edges(data=True) 
                              if d.get('has_textmining', False)]
            
            # Draw edges
            if coexpression_edges:
                nx.draw_networkx_edges(G, pos, edgelist=coexpression_edges,
                                     edge_color=self.interaction_colors['coexpression'],
                                     width=2, alpha=0.7, label='Coexpression')
            
            if experiments_edges:
                nx.draw_networkx_edges(G, pos, edgelist=experiments_edges,
                                     edge_color=self.interaction_colors['experiments'],
                                     width=2, alpha=0.7, label='Experiments')
            
            if textmining_edges:
                nx.draw_networkx_edges(G, pos, edgelist=textmining_edges,
                                     edge_color=self.interaction_colors['textmining'],
                                     width=2, alpha=0.7, label='Text Mining')
            
            # Draw node labels
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
            
            # Customize the plot
            plt.title(f'Protein-Protein Interaction Network\n{self.anchor_protein} and Related Proteins', 
                     fontsize=16, fontweight='bold', pad=20)
            
            # Add legend
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
            
            # Add threshold information
            threshold_text = (f'Thresholds:\n'
                            f'Combined Score > {self.combined_score_threshold}\n'
                            f'Coexpression > {self.coexpression_threshold}\n'
                            f'Experiments > {self.experiments_threshold}\n'
                            f'Text Mining > {self.textmining_threshold}')
            
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
            stats = {
                'Total Nodes': G.number_of_nodes(),
                'Total Edges': G.number_of_edges(),
                'Coexpression Edges': len([(u, v) for u, v, d in G.edges(data=True) 
                                         if d.get('has_coexpression', False)]),
                'Experimental Edges': len([(u, v) for u, v, d in G.edges(data=True) 
                                         if d.get('has_experiments', False)]),
                'Text Mining Edges': len([(u, v) for u, v, d in G.edges(data=True) 
                                        if d.get('has_textmining', False)])
            }

            # Calculate average scores
            coexpression_scores = [d.get('coexpression_score', 0) for _, _, d in G.edges(data=True)]
            experiments_scores = [d.get('experiments_score', 0) for _, _, d in G.edges(data=True)]
            textmining_scores = [d.get('textmining_score', 0) for _, _, d in G.edges(data=True)]
            combined_scores = [d.get('combined_score', 0) for _, _, d in G.edges(data=True)]

            stats.update({
                'Avg Coexpression Score': np.mean(coexpression_scores) if coexpression_scores else 0,
                'Avg Experiments Score': np.mean(experiments_scores) if experiments_scores else 0,
                'Avg Text Mining Score': np.mean(textmining_scores) if textmining_scores else 0,
                'Avg Combined Score': np.mean(combined_scores) if combined_scores else 0
            })

            # Create statistics visualization
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # Edge type distribution
            edge_types = ['Coexpression', 'Experiments', 'Text Mining']
            edge_counts = [stats['Coexpression Edges'], stats['Experimental Edges'], stats['Text Mining Edges']]
            colors = [self.interaction_colors['coexpression'], 
                     self.interaction_colors['experiments'], 
                     self.interaction_colors['textmining']]
            
            ax1.bar(edge_types, edge_counts, color=colors, alpha=0.8)
            ax1.set_title('Interaction Types Distribution', fontweight='bold')
            ax1.set_ylabel('Number of Interactions')
            ax1.tick_params(axis='x', rotation=45)
            
            # Score distributions
            if coexpression_scores:
                ax2.hist(coexpression_scores, bins=20, color=self.interaction_colors['coexpression'], 
                        alpha=0.7, edgecolor='black')
                ax2.set_title('Coexpression Score Distribution', fontweight='bold')
                ax2.set_xlabel('Score')
                ax2.set_ylabel('Frequency')
            
            if experiments_scores:
                ax3.hist(experiments_scores, bins=20, color=self.interaction_colors['experiments'], 
                        alpha=0.7, edgecolor='black')
                ax3.set_title('Experimental Score Distribution', fontweight='bold')
                ax3.set_xlabel('Score')
                ax3.set_ylabel('Frequency')
            
            if textmining_scores:
                ax4.hist(textmining_scores, bins=20, color=self.interaction_colors['textmining'], 
                        alpha=0.7, edgecolor='black')
                ax4.set_title('Text Mining Score Distribution', fontweight='bold')
                ax4.set_xlabel('Score')
                ax4.set_ylabel('Frequency')
            
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
