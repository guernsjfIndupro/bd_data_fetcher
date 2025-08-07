# BD Data Fetcher

A comprehensive CLI tool for fetching and processing biological data from the UMap service API. This tool generates multi-sheet Excel files containing gene expression, proteomics, and cell line data for protein analysis.

## Features

- **Multi-Data Type Processing**: Handles gene expression, proteomics, cell line, and dependency mapping data
- **Excel Output**: Generates comprehensive multi-sheet Excel files for analysis
- **Protein Symbol Mapping**: Automatically maps protein symbols to UniProtKB accession numbers
- **Advanced Graphing**: Automatic graph generation from Excel data
- **Structured Logging**: Detailed progress tracking with rich console output
- **Performance Optimized**: Caching and efficient data processing
- **Error Handling**: Robust error handling with graceful degradation

## Installation

### Using UV (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd bd_data_fetcher

# Install dependencies
uv sync

# Install the package in development mode
uv pip install -e .
```

### Using pip

```bash
pip install bd-data-fetcher
```

## Quick Start

### Basic Usage

```bash
# Generate data for a single protein
bd-fetcher data EGFR

# Generate data for multiple proteins
bd-fetcher data EGFR TP53 BRCA1

# Custom output file
bd-fetcher data EGFR TP53 --output my_analysis.xlsx

# Verbose logging for debugging
bd-fetcher data EGFR --verbose
```

### Example Output

```
Data Handlers Overview:
┌──────────────────────────────┬──────────────────────────────────────────────┬──────────────────────────────┐
│ Handler                      │ Description                                  │ Output Sheets                │
├──────────────────────────────┼──────────────────────────────────────────────┼──────────────────────────────┤
│ GeneExpressionDataHandler    │ Retrieves and prepares gene expression...   │ normal_gene_expression...   │
│ uMapDataHandler             │ Retrieves and prepares uMap data            │ umap_data, cell_line_targeting │
│ WCEDataHandler              │ Processes Whole Cell Extract DIA data...    │ wce_data, cell_line_sigmoidal_curves │
│ DepMapDataHandler           │ Handles DepMap dependency mapping data...   │ depmap_data                 │
│ ExternalProteinExpressionDataHandler │ Manages external proteomics data... │ normal_proteomics_data...   │
└──────────────────────────────┴──────────────────────────────────────────────┴──────────────────────────────┘

Mapping 1 protein symbols to UniProtKB accession numbers...

┌─────────┬──────────────┐
│ Symbol  │ UniProtKB AC │
├─────────┼──────────────┤
│ EGFR    │ P00533       │
└─────────┴──────────────┘

Processing EGFR (P00533)...
  → Retrieving UMap cell line data...
  ✓ Found 15 cell lines for EGFR
  → Generating WCE data sheet...
  ✓ Generated WCE data sheet with 150 records
  → Generating sigmoidal curves...
  ✓ Generated sigmoidal curves
  ✓ Completed processing EGFR

✓ Gene expression data saved to: output.xlsx
✓ Processed 1 proteins successfully
File size: 45,678 bytes
```

## CLI Commands

### Data Generation (`data`)

The main command for generating comprehensive biological data:

```bash
bd-fetcher data <protein_symbols> [OPTIONS]

Arguments:
  protein_symbols    List of protein symbols (e.g., EGFR TP53 BRCA1)

Options:
  --output, -o      Output Excel file name [default: output.xlsx]
  --verbose, -v     Enable verbose logging
  --help            Show this message and exit
```

### Graph Generation (`graph`)

Analyze Excel files and generate visualizations:

```bash
bd-fetcher graph <excel_file> [OPTIONS]

Arguments:
  excel_file         Path to the Excel file to analyze

Options:
  --output-dir       Directory to save generated graphs [default: ./graphs]
  --data-types       Specific data types to process
  --show-analysis    Show analysis results before generating graphs [default: true]
  --help             Show this message and exit
```

## Data Handlers

The BD Data Fetcher uses specialized data handlers to process different types of biological data. Each handler is responsible for retrieving, processing, and organizing specific data types into Excel sheets.

### 1. GeneExpressionDataHandler

**Purpose**: Processes gene expression data from RNA sequencing studies.

**Functionality**:
- Retrieves normal gene expression data across different tissue types
- Processes tumor vs. normal expression comparisons
- Calculates expression ratios and statistical measures
- Handles multiple cancer types and primary sites

**Output Sheets**:
- `normal_gene_expression`: Average normal expression per primary site
- `gene_expression`: All expression data (normal + tumor samples)
- `gene_tumor_normal_ratios`: Tumor minus normal ratios per primary site

**Data Sources**: RNA sequencing data from GTEx and cancer studies

### 2. uMapDataHandler

**Purpose**: Manages UMap analysis results and cell line targeting data.

**Functionality**:
- Retrieves UMap analysis results for targeted proteins
- Processes cell line targeting information
- Extracts replicate set data and analysis parameters
- Maps protein interactions and binding data

**Output Sheets**:
- `umap_data`: UMap analysis results with log2 fold changes and p-values
- `cell_line_targeting`: Cell line targeting information and metadata

**Data Sources**: UMap service API for targeted proteomics

### 3. WCEDataHandler (Whole Cell Extract)

**Purpose**: Processes Whole Cell Extract DIA (Data Independent Acquisition) proteomics data.

**Functionality**:
- Processes cell line proteomics measurements
- Generates sigmoidal curves for protein expression patterns
- Handles weight-normalized intensity rankings
- Performs data interpolation and normalization

**Output Sheets**:
- `wce_data`: Cell line proteomics measurements and rankings
- `cell_line_sigmoidal_curves`: Standardized expression curves

**Data Sources**: DIA proteomics data from cell line studies

### 4. DepMapDataHandler

**Purpose**: Handles DepMap (Cancer Dependency Map) dependency mapping data.

**Functionality**:
- Retrieves cancer cell line dependency data
- Processes gene essentiality information
- Maps copy number variations
- Analyzes cancer lineage and subtype data

**Output Sheets**:
- `depmap_data`: Dependency mapping data with TPM values and copy numbers

**Data Sources**: DepMap database for cancer cell line dependencies

### 5. ExternalProteinExpressionDataHandler

**Purpose**: Manages external proteomics data from various cancer studies.

**Functionality**:
- Processes normal proteomics expression data
- Handles study-specific tumor vs. normal comparisons
- Manages multiple cancer type datasets
- Calculates expression ratios and statistical measures

**Output Sheets**:
- `normal_proteomics_data`: Normal tissue proteomics data
- `external_proteomics_data`: External study proteomics data
- `study_specific_data`: Study-specific tumor-normal comparisons

**Data Sources**: CPTAC and other external proteomics studies

## Graphing Process

The graphing functionality automatically analyzes Excel files and generates appropriate visualizations based on the data types present.

### Automatic Data Detection

The graph analyzer automatically detects which data types are present in the Excel file:

- **DepMap Data**: Dependency mapping visualizations
- **Gene Expression Data**: Expression plots and heatmaps
- **WCE Data**: Cell line proteomics visualizations
- **UMap Data**: UMap analysis result plots
- **External Proteomics Data**: Proteomics expression plots

### Graph Types Generated

#### 1. Distribution Plots
- Histograms of expression values
- Box plots for tissue type comparisons
- Violin plots for cell line distributions

#### 2. Comparison Charts
- Bar charts for tissue type comparisons
- Scatter plots for correlation analysis
- Heatmaps for multi-dimensional data

#### 3. Specialized Plots
- Sigmoidal curves for cell line data
- Volcano plots for differential expression
- PCA plots for dimensionality reduction

### Usage Examples

```bash
# Generate all graphs from an Excel file
bd-fetcher graph my_data.xlsx

# Generate graphs in a specific directory
bd-fetcher graph my_data.xlsx --output-dir ./my_graphs

# Generate only specific data type graphs
bd-fetcher graph my_data.xlsx --data-types wce depmap

# Show analysis before generating graphs
bd-fetcher graph my_data.xlsx --show-analysis
```

### Graph Output Structure

```
graphs/
├── depmap/
│   └── copy_number_scatter_plot_*.png
├── gene_expression/
│   ├── normal_gene_expression_heatmap.png
│   └── tumor_normal_boxplot_*.png
├── wce/
│   ├── wce_bar_plot_*.png
│   └── sigmoidal_curve_*.png
├── umap/
│   └── volcano_plot_*.png
└── external_protein_expression/
    ├── normal_proteomics_expression.png
    ├── external_proteomics_comparison.png
    └── tissue_expression_heatmap.png
```

## Data Processing Pipeline

### 1. Protein Symbol Mapping
- Maps user-provided protein symbols to UniProtKB accession numbers
- Validates symbols against the UMap service database
- Provides clear mapping feedback to users

### 2. Data Retrieval
- Each handler retrieves relevant data from the UMap API
- Implements caching for performance optimization
- Handles pagination for large datasets

### 3. Data Processing
- Normalizes and validates retrieved data
- Performs statistical calculations and transformations
- Handles missing data and edge cases

### 4. Excel Generation
- Creates multi-sheet Excel files with organized data
- Implements proper data formatting and validation
- Provides clear sheet naming and structure

### 5. Progress Tracking
- Real-time progress indicators for each step
- Detailed logging with structured data
- Error handling with graceful degradation

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UMAP_SERVICE_URL` | UMap service API base URL | `https://indupro-apps.com/umap-service/api/v1/` |
| `API_TIMEOUT` | Request timeout in seconds | `30` |
| `API_MAX_RETRIES` | Maximum number of retries | `3` |

### Logging Configuration

The application uses structured logging with different levels:

- **DEBUG**: Detailed API calls and data processing steps
- **INFO**: General progress and completion information
- **WARNING**: Non-critical issues and skipped operations
- **ERROR**: Failed operations with full context

Enable verbose logging for detailed debugging:

```bash
bd-fetcher data EGFR --verbose
```

## Error Handling

The application implements comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **API Errors**: Proper error messages with status codes
- **Data Validation**: Pydantic models for data validation
- **Graceful Degradation**: Continues processing even if some operations fail
- **Timeout Protection**: Prevents hanging on slow API responses

## Performance Optimizations

- **Caching**: LRU cache for expensive API calls
- **Pagination**: Efficient handling of large datasets
- **Parallel Processing**: Concurrent data retrieval where possible
- **Memory Management**: Efficient data structures and cleanup

## Development

### Setup Development Environment

```bash
# Install development dependencies
uv sync --extra dev

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/bd_data_fetcher --cov-report=html

# Run specific test file
uv run pytest tests/test_api_client.py
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Sort imports
uv run isort src/ tests/

# Linting
uv run ruff check src/ tests/
```

## Project Structure

```
bd_data_fetcher/
├── src/bd_data_fetcher/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── umap_client.py      # UMap API client
│   │   └── umap_models.py      # Data models
│   ├── data_handlers/
│   │   ├── __init__.py
│   │   ├── base_handler.py     # Base handler class
│   │   ├── gene_expression.py  # Gene expression handler
│   │   ├── umap.py            # UMap data handler
│   │   ├── internal_wce.py    # WCE data handler
│   │   ├── depmap.py          # DepMap data handler
│   │   ├── external_protein_expression.py # External proteomics handler
│   │   └── utils.py           # Handler utilities
│   ├── graphs/
│   │   ├── __init__.py
│   │   ├── base_graph.py      # Base graph class
│   │   ├── gene_expression_graph.py
│   │   ├── depmap_graph.py
│   │   ├── wce_graph.py
│   │   ├── umap_graph.py
│   │   └── external_protein_expression_graph.py
│   └── cli/
│       ├── __init__.py
│       ├── main.py            # Main CLI implementation
│       └── graphing.py        # Graph generation CLI
├── tests/                     # Test suite
├── logs/                      # Log files
├── graphs/                    # Generated graphs
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive docstrings
- Include tests for new features
- Update documentation as needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the test examples for usage patterns

## Changelog

### v0.1.0

- Initial release
- Multi-data type processing (Gene Expression, UMap, WCE, DepMap, External Proteomics)
- Comprehensive Excel output with multiple sheets
- Advanced graphing functionality with automatic data detection
- Structured logging with progress tracking
- Rich CLI interface with error handling
- Protein symbol to UniProtKB mapping
- Caching and performance optimizations
