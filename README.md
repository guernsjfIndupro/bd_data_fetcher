# BD Data Fetcher

A production-grade CLI tool for fetching and processing data from REST APIs.

## Features

- 🚀 **Fast & Efficient**: Built with modern Python and optimized for performance
- 🔧 **Configurable**: Easy configuration via environment variables
- 📊 **Data Processing**: Built-in data validation and processing
- 📝 **Structured Logging**: Comprehensive logging with structlog
- 🎨 **Rich CLI**: Beautiful command-line interface with rich
- 🧪 **Tested**: Comprehensive test suite with pytest
- 📦 **Production Ready**: Type hints, error handling, and best practices


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

### 1. Install and Setup

```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### 2. Gene Expression Data Generation

The main functionality generates comprehensive gene expression data from protein symbols:

```bash
# Basic usage - generate data for EGFR, TP53, BRCA1
bd-fetcher gene-expression EGFR TP53 BRCA1

# Custom output file
bd-fetcher gene-expression EGFR TP53 --output my_data.xlsx

# Verbose logging
bd-fetcher gene-expression EGFR TP53 --verbose
```

### 3. What It Does

1. **Maps protein symbols** to UniProtKB accession numbers
2. **Generates three Excel sheets**:
   - `normal_gene_expression`: Average normal expression per primary site
   - `gene_expression`: All expression data (normal + tumor)
   - `gene_tumor_normal_ratios`: Tumor minus normal ratios per primary site
3. **Saves to Excel file** with multiple sheets for analysis

### 4. Example Output

```
Mapping 3 protein symbols to UniProtKB accession numbers...

┌─────────┬──────────────┐
│ Symbol  │ UniProtKB AC │
├─────────┼──────────────┤
│ EGFR    │ P00533       │
│ TP53    │ P04637       │
│ BRCA1   │ P38398       │
└─────────┴──────────────┘

Successfully mapped 3 proteins
Generating gene expression data for 3 proteins...
Processing EGFR (P00533)...
Completed processing EGFR
Processing TP53 (P04637)...
Completed processing TP53
Processing BRCA1 (P38398)...
Completed processing BRCA1

Gene expression data saved to: gene_expression_data.xlsx
Processed 3 proteins successfully
```

## CLI Commands

### Gene Expression (Main Functionality)

```bash
# Generate gene expression data for multiple proteins
bd-fetcher gene-expression EGFR TP53 BRCA1

# Custom output file
bd-fetcher gene-expression EGFR TP53 --output my_data.xlsx

# Verbose logging for debugging
bd-fetcher gene-expression EGFR TP53 --verbose

# Help
bd-fetcher gene-expression --help
```

### Other Commands

```bash
# Check API connection status
bd-fetcher status

# Show current configuration
bd-fetcher config --show

# Legacy commands (for reference)
bd-fetcher users --help
bd-fetcher products --help
```

## Project Structure

```
bd_data_fetcher/
├── src/bd_data_fetcher/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── client.py          # REST API client
│   ├── data_handlers/
│   │   ├── __init__.py
│   │   ├── base.py            # Base data handler
│   │   ├── user_handler.py    # User data handler
│   │   └── product_handler.py # Product data handler
│   └── cli/
│       ├── __init__.py
│       └── main.py            # CLI implementation
├── tests/                     # Test suite
├── logs/                      # Log files
├── docs/                      # Documentation
├── data/                      # Output data files
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

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
uv run pytest tests/test_api.py

# Run with verbose output
uv run pytest -v
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Sort imports
uv run isort src/ tests/

# Type checking
uv run mypy src/

# Linting
uv run flake8 src/ tests/
```

### Building

```bash
# Build package
uv build

# Install in development mode
uv pip install -e .
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | Base URL for the API | `https://api.example.com` |
| `API_KEY` | API key for authentication | None |
| `API_TIMEOUT` | Request timeout in seconds | `30` |
| `API_MAX_RETRIES` | Maximum number of retries | `3` |
| `API_RETRY_DELAY` | Delay between retries | `1.0` |

### Output Configuration

- **Output Directory**: Data files are saved to the `data/` directory by default
- **File Formats**: Supports JSON and CSV formats
- **Timestamps**: Files include timestamps by default for versioning

## Logging

The application uses structured logging with `structlog`. Logs include:

- Request/response information
- Error details with stack traces
- Performance metrics
- Data processing statistics

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General information about operations
- `WARNING`: Warning messages for non-critical issues
- `ERROR`: Error messages for failed operations

### Verbose Mode

Use the `--verbose` flag to enable debug logging:

```bash
bd-fetcher users --verbose
```

## Error Handling

The application includes comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **API Errors**: Proper error messages with status codes
- **Data Validation**: Pydantic models for data validation
- **Graceful Degradation**: Continues processing even if some records fail

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
- Basic CLI functionality
- User and product data handlers
- API client with retry logic
- Structured logging
- Rich CLI interface
