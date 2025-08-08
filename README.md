# BD Data Fetcher

A comprehensive CLI tool for fetching and processing biological data from the UMap service API. This tool generates multiple CSV files containing gene expression, proteomics, and cell line data for protein analysis.

## Features

- **Multi-Data Type Processing**: Handles gene expression, proteomics, cell line, and dependency mapping data
- **CSV Output**: Generates comprehensive CSV files organized in folders for analysis
- **Protein Symbol Mapping**: Automatically maps protein symbols to UniProtKB accession numbers
- **Advanced Graphing**: Automatic graph generation from CSV data
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

# Custom output directory
bd-fetcher data EGFR TP53 --output-dir my_analysis

# Verbose logging for debugging
bd-fetcher data EGFR --verbose
```

### Example Output

```
Data Handlers Overview:
┌──────────────────────────────┬──────────────────────────────────────────────┬──────────────────────────────┐
│ Handler                      │ Description                                  │ Output Files                │
├──────────────────────────────┼──────────────────────────────────────────────┼──────────────────────────────┤
│ GeneExpressionDataHandler    │ Processes gene expression data from RNA     │ normal_gene_expression.csv, │
│                             │ sequencing studies                          │ gene_expression.csv,        │
│                             │                                             │ gene_tumor_normal_ratios.csv│
│ uMapDataHandler             │ Manages UMap analysis results and cell      │ umap_data.csv,             │
│                             │ line targeting data                         │ cell_line_targeting.csv     │
│ WCEDataHandler              │ Processes Whole Cell Extract DIA            │ wce_data.csv,              │
│                             │ proteomics data                             │ cell_line_sigmoidal_curves.csv│
│ DepMapDataHandler           │ Handles DepMap dependency mapping data      │ depmap_data.csv             │
│ ExternalProteinExpression   │ Manages external proteomics data from       │ normal_proteomics_data.csv, │
│ DataHandler                 │ various cancer studies                      │ external_proteomics_data.csv,│
│                             │                                             │ study_specific_data.csv     │
└──────────────────────────────┴──────────────────────────────────────────────┴──────────────────────────────┘

Generated 11 CSV files with total size: 45,678 bytes
```

## CLI Commands

### Data Generation (`data`)

The main command for generating comprehensive biological data:

```bash
bd-fetcher data <protein_symbols> [OPTIONS]

Arguments:
  protein_symbols    List of protein symbols (e.g., EGFR TP53 BRCA1)

Options:
  --output-dir, -o   Output directory for CSV files [default: output]
  --verbose, -v      Enable verbose logging
  --help             Show this message and exit
```

### Graph Generation (`graph`)

Analyze CSV files and generate visualizations:

```bash
bd-fetcher graph <data_dir> [OPTIONS]

Arguments:
  data_dir           Path to the directory containing CSV files to analyze

Options:
  --output-dir       Directory to save generated graphs [default: ./graphs]
  --data-types       Specific data types to process
  --show-analysis    Show analysis results before generating graphs [default: true]
  --help             Show this message and exit
```

## Data Handlers

The BD Data Fetcher uses specialized data handlers to process different types of biological data. Each handler is responsible for retrieving, processing, and organizing specific data types into CSV files.

### 1. GeneExpressionDataHandler

**Purpose**: Processes gene expression data from RNA sequencing studies.

**Functionality**:
- Retrieves normal gene expression data across different tissue types
- Processes tumor vs. normal expression comparisons
- Calculates expression ratios and statistical measures
- Handles multiple cancer types and primary sites

**Output Files**:
- `normal_gene_expression.csv`: Average normal expression per primary site
- `gene_expression.csv`: All expression data (normal + tumor samples)
- `gene_tumor_normal_ratios.csv`: Tumor minus normal ratios per primary site

**Data Sources**: RNA sequencing data from GTEx and cancer studies

### 2. uMapDataHandler

**Purpose**: Manages UMap analysis results and cell line targeting data.

**Functionality**:
- Retrieves UMap analysis results for targeted proteins
- Processes cell line targeting information
- Extracts replicate set data and analysis parameters
- Maps protein interactions and binding data

**Output Files**:
- `umap_data.csv`: UMap analysis results with log2 fold changes and p-values
- `cell_line_targeting.csv`: Cell line targeting information and metadata

**Data Sources**: UMap service API for targeted proteomics

### 3. WCEDataHandler (Whole Cell Extract)

**Purpose**: Processes Whole Cell Extract DIA (Data Independent Acquisition) proteomics data.

**Functionality**:
- Processes cell line proteomics measurements
- Generates sigmoidal curves for protein expression patterns
- Handles weight-normalized intensity rankings
- Performs data interpolation and normalization

**Output Files**:
- `wce_data.csv`: Cell line proteomics measurements and rankings
- `cell_line_sigmoidal_curves.csv`: Standardized expression curves

**Data Sources**: DIA proteomics data from cell line studies

### 4. DepMapDataHandler

**Purpose**: Handles DepMap (Cancer Dependency Map) dependency mapping data.

**Functionality**:
- Retrieves cancer cell line dependency data
- Processes gene essentiality information
- Maps copy number variations
- Analyzes cancer lineage and subtype data

**Output Files**:
- `depmap_data.csv`: Dependency mapping data with TPM values and copy numbers

**Data Sources**: DepMap database for cancer cell line dependencies

### 5. ExternalProteinExpressionDataHandler

**Purpose**: Manages external proteomics data from various cancer studies.

**Functionality**:
- Processes normal proteomics expression data
- Handles study-specific tumor vs. normal comparisons
- Manages multiple cancer type datasets
- Calculates expression ratios and statistical measures

**Output Files**:
- `normal_proteomics_data.csv`: Normal tissue proteomics data
- `external_proteomics_data.csv`: External study proteomics data
- `study_specific_data.csv`: Study-specific tumor-normal comparisons

**Data Sources**: CPTAC and other external proteomics studies

## Output Structure

The tool generates a directory structure like this:

```
output/
├── depmap_data.csv
├── normal_proteomics_data.csv
├── external_proteomics_data.csv
├── study_specific_data.csv
├── normal_gene_expression.csv
├── gene_expression.csv
├── gene_tumor_normal_ratios.csv
├── wce_data.csv
├── cell_line_sigmoidal_curves.csv
├── umap_data.csv
└── cell_line_targeting.csv
```

## Benefits of CSV Format

- **Better Performance**: CSV files are faster to read/write than Excel
- **Easier Debugging**: Individual CSV files are easier to inspect
- **Better Version Control**: CSV files work better with Git
- **Parallel Processing**: Can process multiple CSV files simultaneously
- **Tool Compatibility**: CSV files work with more data analysis tools
- **Reduced Memory Usage**: No need to load entire Excel file into memory

## Advanced Usage

### Custom Output Directory

```bash
# Generate data in a custom directory
bd-fetcher data EGFR TP53 --output-dir /path/to/my/data

# The tool will create the directory if it doesn't exist
```

### Verbose Logging

```bash
# Enable detailed logging for debugging
bd-fetcher data EGFR --verbose
```

### Graph Generation

```bash
# Generate graphs from existing data
bd-fetcher graph /path/to/data/directory

# Generate specific graph types
bd-fetcher graph /path/to/data/directory --data-types depmap_data.csv

# Custom graph output directory
bd-fetcher graph /path/to/data/directory --output-dir /path/to/graphs
```

## Error Handling

The tool includes comprehensive error handling:

- **API Timeouts**: Graceful handling of network timeouts
- **Missing Data**: Continues processing even if some data is unavailable
- **Invalid Proteins**: Skips invalid protein symbols and continues
- **File System Errors**: Handles permission and disk space issues
- **Data Validation**: Validates data before processing

## Performance Considerations

- **Caching**: Data handlers cache expensive API calls
- **Incremental Processing**: Can append to existing CSV files
- **Memory Efficient**: Processes data in chunks where possible
- **Parallel Ready**: CSV format enables parallel processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
