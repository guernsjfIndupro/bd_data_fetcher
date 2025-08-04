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

### 1. Configure Environment

Create a `.env` file in the project root:

```bash
# API Configuration
API_BASE_URL=https://api.example.com
API_KEY=your_api_key_here

# Optional: Customize timeouts and retries
API_TIMEOUT=30
API_MAX_RETRIES=3
API_RETRY_DELAY=1.0
```

### 2. Basic Usage

```bash
# Check API status
bd-fetcher status

# Fetch user data
bd-fetcher users --limit 50

# Fetch product data
bd-fetcher products --limit 100

# Search for specific data
bd-fetcher users --search "john"
bd-fetcher products --category "electronics"

# Get data summary
bd-fetcher users --verbose
```

## CLI Commands

### Users

```bash
# Fetch all users
bd-fetcher users

# Fetch specific number of users
bd-fetcher users --limit 50

# Search users
bd-fetcher users --search "john"

# Fetch specific user by ID
bd-fetcher users --id 123

# Save in different format
bd-fetcher users --format csv --output ./my_data
```

### Products

```bash
# Fetch all products
bd-fetcher products

# Fetch products by category
bd-fetcher products --category "electronics"

# Search products
bd-fetcher products --search "laptop"

# Filter by price range
bd-fetcher products --min-price 100 --max-price 500

# Fetch specific product
bd-fetcher products --id 456
```

### Categories

```bash
# List all available categories
bd-fetcher categories
```

### Status & Configuration

```bash
# Check API connection
bd-fetcher status

# Show current configuration
bd-fetcher config --show
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
