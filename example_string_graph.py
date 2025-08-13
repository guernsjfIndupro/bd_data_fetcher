#!/usr/bin/env python3
"""Example script demonstrating the StringGraph functionality."""

import logging
from pathlib import Path

from bd_data_fetcher.graphs.string_graph import StringGraph

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run the STRING graph example."""
    
    # Example parameters
    data_dir = "TROP2"  # Directory containing gene_expression.csv
    anchor_protein = "TACSTD2"  # Anchor protein symbol
    output_dir = "string_graph_example"
    
    # Configure thresholds
    coexpression_threshold = 0.0
    experiments_threshold = 0.0
    textmining_threshold = 0.0
    combined_score_threshold = 400.0
    
    logger.info(f"Creating STRING graph for {anchor_protein}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Thresholds: coexpression={coexpression_threshold}, "
               f"experiments={experiments_threshold}, "
               f"textmining={textmining_threshold}, "
               f"combined={combined_score_threshold}")
    
    try:
        # Create the StringGraph instance
        string_graph = StringGraph(
            data_dir_path=data_dir,
            anchor_protein=anchor_protein,
            coexpression_threshold=coexpression_threshold,
            experiments_threshold=experiments_threshold,
            textmining_threshold=textmining_threshold,
            combined_score_threshold=combined_score_threshold
        )
        
        # Generate the graphs
        success = string_graph.generate_graphs(output_dir)
        
        if success:
            logger.info("✅ Successfully generated STRING protein interaction graphs!")
            logger.info(f"Check the '{output_dir}/string_interactions/' directory for output files")
        else:
            logger.error("❌ Failed to generate STRING graphs")
            
    except Exception as e:
        logger.exception(f"Error running STRING graph example: {e}")


if __name__ == "__main__":
    main() 