"""
Base handler class for common data handler patterns.
"""

import logging

import pandas as pd

from bd_data_fetcher.api.umap_client import UMapServiceClient
from bd_data_fetcher.data_handlers.utils import SheetNames

logger = logging.getLogger(__name__)


class BaseDataHandler:
    """
    Base class for all data handlers containing common patterns.
    """

    def __init__(self):
        self.umap_client = UMapServiceClient()

    def _manage_excel_sheet(
        self, file_path: str, sheet_name: str, columns: list[str]
    ) -> dict[str, pd.DataFrame]:
        """
        Common Excel sheet management logic.

        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet to manage
            columns: List of column names for the sheet

        Returns:
            Dictionary of existing sheets
        """
        # Check if file exists and what sheets it has
        existing_sheets = {}
        try:
            with pd.ExcelFile(file_path) as xls:
                for sheet in xls.sheet_names:
                    existing_sheets[sheet] = pd.read_excel(file_path, sheet_name=sheet)
        except FileNotFoundError:
            # File doesn't exist, we'll create it
            pass

        # Create the sheet if it doesn't exist
        if sheet_name not in existing_sheets:
            new_df = pd.DataFrame(columns=columns)

            if existing_sheets:
                # Append to existing file
                with pd.ExcelWriter(file_path, engine="openpyxl", mode="a") as writer:
                    new_df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                # Create new file
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    new_df.to_excel(writer, sheet_name=sheet_name, index=False)

        return existing_sheets

    def _append_to_excel_sheet(
        self,
        file_path: str,
        sheet_name: str,
        data_df: pd.DataFrame,
        default_columns: list[str],
    ) -> None:
        """
        Common Excel append logic.

        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet to append to
            data_df: DataFrame to append
            default_columns: Default columns if sheet doesn't exist
        """
        if data_df.empty:
            return

        # Read existing data to get the current row count
        try:
            existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
        except (FileNotFoundError, ValueError):
            existing_df = pd.DataFrame(columns=default_columns)

        # Append new data to existing sheet
        with pd.ExcelWriter(
            file_path, engine="openpyxl", mode="a", if_sheet_exists="overlay"
        ) as writer:
            start_row = len(existing_df) + 1
            data_df.to_excel(
                writer,
                sheet_name=sheet_name,
                startrow=start_row,
                index=False,
                header=False,
            )

    def _transform_data_to_sheet_format(
        self, data_df: pd.DataFrame, column_mapping: dict[str, str]
    ) -> pd.DataFrame:
        """
        Common data transformation logic.

        Args:
            data_df: Original DataFrame
            column_mapping: Dictionary mapping sheet columns to DataFrame columns

        Returns:
            Transformed DataFrame
        """
        transformed_data = []
        for _, row in data_df.iterrows():
            transformed_row = {}
            for sheet_col, df_col in column_mapping.items():
                if df_col in row:
                    transformed_row[sheet_col] = row[df_col]
                # Handle missing columns with appropriate defaults
                elif isinstance(row.get(df_col, None), bool):
                    transformed_row[sheet_col] = False
                elif isinstance(row.get(df_col, None), int | float):
                    transformed_row[sheet_col] = 0
                else:
                    transformed_row[sheet_col] = ""
            transformed_data.append(transformed_row)

        return pd.DataFrame(transformed_data)

    def _create_matrix_sheet(
        self,
        file_path: str,
        sheet_name: str,
        data_df: pd.DataFrame,
        group_field: str,
        value_field: str,
        gene_field: str,
        gene_column_name: str = "Gene",
    ) -> pd.DataFrame:
        """
        Common matrix/pivot logic for creating matrix sheets.

        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet
            data_df: DataFrame with data
            group_field: Field to group by (e.g., 'indication', 'primary_site')
            value_field: Field containing values to average (e.g., 'log2_expression', 'expression_value')
            gene_field: Field containing gene/protein symbol
            gene_column_name: Name for the gene column in the sheet

        Returns:
            DataFrame with matrix data
        """
        # Always create the sheet structure, even if data is empty
        if data_df.empty:
            # Create a minimal sheet with just the gene column
            columns = [gene_column_name]
            self._manage_excel_sheet(file_path, sheet_name, columns)
            return data_df

        # Extract all unique groups from the data
        all_groups = sorted(data_df[group_field].unique())

        # Manage Excel sheet
        columns = [gene_column_name, *all_groups]
        self._manage_excel_sheet(file_path, sheet_name, columns)

        # Compute the average for each group
        avg_values = data_df.groupby(group_field)[value_field].mean()

        # Build a single-row DataFrame: Gene + one column per group
        gene_symbol = data_df[gene_field].iloc[0] if not data_df.empty else ""
        row_data = {gene_column_name: gene_symbol}

        # Read existing sheet to get column structure
        try:
            existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
            all_columns = list(existing_df.columns)
        except (FileNotFoundError, ValueError):
            # If sheet doesn't exist or is empty, use columns from current data
            all_columns = [gene_column_name, *all_groups]
            existing_df = pd.DataFrame(columns=all_columns)

        # Ensure all columns from the sheet are present in the row_data, fill missing with None
        avg_dict = avg_values.to_dict()
        for col in all_columns:
            if col == gene_column_name:
                continue  # will set below
            row_data[col] = avg_dict.get(col, None)

        row_data[gene_column_name] = gene_symbol

        # Reorder row_data to match the columns in the sheet
        ordered_row = [row_data.get(col, None) for col in all_columns]
        pivot_df = pd.DataFrame([ordered_row], columns=all_columns)

        # Append to existing sheet
        with pd.ExcelWriter(
            file_path, engine="openpyxl", mode="a", if_sheet_exists="overlay"
        ) as writer:
            start_row = len(existing_df) + 1
            pivot_df.to_excel(
                writer,
                sheet_name=sheet_name,
                startrow=start_row,
                index=False,
                header=False,
            )

        return data_df

    def _safe_api_call(self, api_method, *args, **kwargs):
        """
        Common error handling for API calls.

        Args:
            api_method: The API method to call
            *args: Arguments for the API method
            **kwargs: Keyword arguments for the API method

        Returns:
            Result of the API call or empty list on error
        """
        try:
            # If it's a lambda function, don't pass keyword arguments
            if callable(api_method) and api_method.__name__ == "<lambda>":
                return api_method(*args)
            else:
                return api_method(*args, **kwargs)
        except Exception as e:
            # Extract uniprotkb_ac from kwargs for error message
            uniprotkb_ac = kwargs.get("uniprotkb_ac", "unknown")
            logger.exception(f"Error in API call for {uniprotkb_ac}: {e}")
            return []
