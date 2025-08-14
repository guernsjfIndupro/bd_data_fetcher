"""Base graph class for data visualization."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class BaseGraph(ABC):
    """Base class for all graph generators.

    This class provides common functionality for reading CSV files,
    processing data, and generating visualizations.
    """

    def __init__(self, data_dir_path: str, anchor_protein: str):
        """Initialize the graph generator.

        Args:
            data_dir_path: Path to the directory containing CSV files
            anchor_protein: Anchor protein symbol to use for graph generation
        """
        self.data_dir_path = Path(data_dir_path)
        self.anchor_protein = anchor_protein
        self.data: dict[str, pd.DataFrame] = {}

    def load_csv_data(self) -> bool:
        """Load all CSV files from the data directory into memory.

        Returns:
            True if data was loaded successfully, False otherwise
        """
        try:
            if not self.data_dir_path.exists():
                logger.error(f"Data directory not found: {self.data_dir_path}")
                return False

            # Read all CSV files into a dictionary
            csv_files = list(self.data_dir_path.glob("*.csv"))
            if not csv_files:
                logger.error(f"No CSV files found in directory: {self.data_dir_path}")
                return False

            for csv_file in csv_files:
                file_name = csv_file.name
                try:
                    self.data[file_name] = pd.read_csv(csv_file, low_memory=False)
                    logger.info(f"Loaded CSV file '{file_name}' with {len(self.data[file_name])} rows")
                except Exception as e:
                    logger.warning(f"Error reading CSV file {file_name}: {e}")
                    continue

            return len(self.data) > 0

        except Exception as e:
            logger.exception(f"Error loading CSV files: {e}")
            return False

    def get_available_files(self) -> list[str]:
        """Get list of available CSV file names.

        Returns:
            List of CSV file names in the data directory
        """
        return list(self.data.keys())

    def get_data_for_file(self, file_name: str) -> pd.DataFrame | None:
        """Get data for a specific CSV file.

        Args:
            file_name: Name of the CSV file

        Returns:
            DataFrame for the file or None if not found
        """
        return self.data.get(file_name)

    @abstractmethod
    def generate_graphs(self, output_dir: str) -> bool:
        """Generate graphs for the loaded data.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """
