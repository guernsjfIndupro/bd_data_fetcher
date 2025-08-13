# STRING Protein-Protein Interaction Graph

The `StringGraph` class provides visualization capabilities for protein-protein interaction data from the STRING database. It creates network graphs showing interactions between proteins based on various evidence types.

## Features

- **Network Visualization**: Creates interactive protein-protein interaction networks using NetworkX
- **Configurable Thresholds**: Set custom thresholds for different interaction scores
- **Multiple Evidence Types**: Visualize coexpression, experimental, and text mining evidence separately
- **Color-Coded Interactions**: Different colors for different types of evidence
- **Statistical Analysis**: Generate comprehensive statistics about interactions
- **Flexible Data Sources**: Works with any gene expression data and STRING interaction data

## Requirements

- `networkx>=3.0.0` (for network visualization)
- `matplotlib>=3.7.0` (for plotting)
- `pandas>=2.0.0` (for data handling)
- `numpy>=1.24.0` (for numerical operations)

## Data Format

### Input Files

1. **`human_string_protein_scores.csv`** (in project root directory)
   - Contains protein-protein interaction scores from STRING database
   - Required columns:
     - `protein1`, `protein2`: Protein identifiers
     - `symbol1`, `symbol2`: Gene symbols
     - `coexpression_both_prior_corrected`: Coexpression scores
     - `experiments_both_prior_corrected`: Experimental evidence scores
     - `textmining_both_prior_corrected`: Text mining evidence scores
     - `combined_score`: Combined interaction score

2. **`gene_expression.csv`** (in specified data directory)
   - Contains gene expression data
   - Required columns:
     - `Gene`: Gene symbols (used to filter proteins in network)

### Output Files

The graph generator creates the following files in `{output_dir}/string_interactions/`:

1. **`protein_interaction_network_{anchor_protein}.png`**
   - Main network visualization
   - Shows proteins as nodes and interactions as colored edges
   - Different colors for different evidence types

2. **`interaction_statistics_{anchor_protein}.png`**
   - Statistical summary plots
   - Distribution of interaction types and scores

3. **`interaction_statistics_{anchor_protein}.csv`**
   - Numerical statistics in CSV format

## Usage

### Basic Usage

```python
from bd_data_fetcher.graphs.string_graph import StringGraph

# Create StringGraph instance
string_graph = StringGraph(
    data_dir_path="path/to/data/directory",  # Contains gene_expression.csv
    anchor_protein="TACSTD2",                # Anchor protein symbol
    coexpression_threshold=0.0,              # Minimum coexpression score
    experiments_threshold=0.0,               # Minimum experimental score
    textmining_threshold=0.0,                # Minimum text mining score
    combined_score_threshold=400.0           # Minimum combined score
)

# Generate graphs
success = string_graph.generate_graphs("output_directory")
```

### Advanced Configuration

```python
# More restrictive thresholds for higher confidence interactions
string_graph = StringGraph(
    data_dir_path="TROP2",
    anchor_protein="TACSTD2",
    coexpression_threshold=0.1,      # Only show coexpression > 0.1
    experiments_threshold=0.05,      # Only show experimental > 0.05
    textmining_threshold=0.2,        # Only show text mining > 0.2
    combined_score_threshold=500.0   # Only show combined score > 500
)
```

### Example Script

See `example_string_graph.py` for a complete working example.

## Configuration Options

### Thresholds

- **`coexpression_threshold`**: Minimum score for coexpression evidence (default: 0.0)
- **`experiments_threshold`**: Minimum score for experimental evidence (default: 0.0)
- **`textmining_threshold`**: Minimum score for text mining evidence (default: 0.0)
- **`combined_score_threshold`**: Minimum combined score (default: 400.0)

### Color Scheme

The graph uses the following color scheme for different interaction types:
- **Coexpression**: Red (`#FF6B6B`)
- **Experiments**: Teal (`#4ECDC4`)
- **Text Mining**: Blue (`#45B7D1`)

## Network Visualization Features

### Node Representation
- Each protein is represented as a node
- Node size and color can be customized
- Node labels show protein symbols

### Edge Representation
- Edges represent protein-protein interactions
- Edge color indicates the type of evidence
- Edge thickness can represent interaction strength
- Multiple evidence types can be shown simultaneously

### Layout
- Uses spring layout algorithm for optimal node positioning
- Configurable layout parameters for different network sizes
- Automatic adjustment for readability

## Statistical Analysis

The graph generator provides comprehensive statistics:

### Network Statistics
- Total number of nodes (proteins)
- Total number of edges (interactions)
- Number of interactions by evidence type

### Score Statistics
- Average scores for each evidence type
- Score distributions
- Threshold compliance statistics

## Error Handling

The class includes robust error handling for:
- Missing data files
- Invalid file formats
- Empty datasets
- Network creation failures
- File I/O errors

## Performance Considerations

- Large networks (>1000 interactions) may require longer processing time
- Memory usage scales with network size
- Consider adjusting thresholds to reduce network complexity
- Use appropriate figure sizes for large networks

## Integration with Other Graph Types

The `StringGraph` class follows the same interface as other graph classes in the package:
- Inherits from `BaseGraph`
- Implements the `generate_graphs()` method
- Uses consistent logging and error handling
- Follows the same output directory structure

## Troubleshooting

### Common Issues

1. **No interactions found**: Check that thresholds are not too restrictive
2. **Missing STRING data**: Ensure `human_string_protein_scores.csv` is in the project root
3. **Empty gene list**: Verify that `gene_expression.csv` contains the expected genes
4. **Network too dense**: Increase thresholds to reduce the number of interactions

### Debugging

Enable debug logging to see detailed information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

Potential improvements for future versions:
- Interactive network visualization (e.g., using Plotly)
- Additional layout algorithms
- Custom node and edge styling
- Network analysis metrics (centrality, clustering, etc.)
- Export to common network formats (GML, GraphML, etc.)
- Integration with other protein databases 