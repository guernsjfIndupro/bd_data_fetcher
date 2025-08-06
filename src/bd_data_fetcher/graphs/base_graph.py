"""Base graph class for data visualization."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


class BaseGraph(ABC):
    """Base class for all graph generators.

    This class provides common functionality for reading Excel files,
    processing data, and generating visualizations.
    """

    def __init__(self, excel_file_path: str):
        """Initialize the graph generator.

        Args:
            excel_file_path: Path to the Excel file containing data
        """
        self.excel_file_path = Path(excel_file_path)
        self.data: dict[str, pd.DataFrame] = {}

    def load_excel_data(self) -> bool:
        """Load all sheets from the Excel file into memory.

        Returns:
            True if data was loaded successfully, False otherwise
        """
        try:
            if not self.excel_file_path.exists():
                logger.error(f"Excel file not found: {self.excel_file_path}")
                return False

            # Read all sheets into a dictionary
            excel_file = pd.ExcelFile(self.excel_file_path)
            for sheet_name in excel_file.sheet_names:
                self.data[sheet_name] = pd.read_excel(
                    self.excel_file_path, sheet_name=sheet_name
                )
                logger.info(f"Loaded sheet '{sheet_name}' with {len(self.data[sheet_name])} rows")

            return True

        except Exception as e:
            logger.exception(f"Error loading Excel file: {e}")
            return False

    def get_available_sheets(self) -> list[str]:
        """Get list of available sheet names.

        Returns:
            List of sheet names in the Excel file
        """
        return list(self.data.keys())

    def get_sheet_data(self, sheet_name: str) -> pd.DataFrame | None:
        """Get data for a specific sheet.

        Args:
            sheet_name: Name of the sheet to retrieve

        Returns:
            DataFrame for the sheet, or None if not found
        """
        return self.data.get(sheet_name)

    @abstractmethod
    def generate_graphs(self, output_dir: str) -> bool:
        """Generate all relevant graphs for this data handler.

        Args:
            output_dir: Directory to save generated graphs

        Returns:
            True if graphs were generated successfully, False otherwise
        """

    @abstractmethod
    def get_supported_sheets(self) -> list[str]:
        """Get list of sheet names that this graph class can process.

        Returns:
            List of supported sheet names
        """

    def save_graph(self, fig: plt.Figure, filename: str, output_dir: str) -> bool:
        """Save a matplotlib figure to file.

        Args:
            fig: Matplotlib figure to save
            filename: Name of the output file
            output_dir: Directory to save the file

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            output_path = Path(output_dir) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Saved graph: {output_path}")
            return True
        except Exception as e:
            logger.exception(f"Error saving graph {filename}: {e}")
            return False
