"""
Base handler class for common data handler patterns.
"""

import logging
import os
from pathlib import Path

import pandas as pd

from bd_data_fetcher.api.umap_client import UMapServiceClient

logger = logging.getLogger(__name__)


class BaseDataHandler:
    """
    Base class for all data handlers containing common patterns.
    """

    def __init__(self):
        self.umap_client = UMapServiceClient()

    def _ensure_folder_exists(self, folder_path: str) -> None:
        """
        Ensure the output folder exists.

        Args:
            folder_path: Path to the folder
        """
        Path(folder_path).mkdir(parents=True, exist_ok=True)

    def _get_csv_path(self, folder_path: str, file_name: str) -> str:
        """
        Get the full path for a CSV file.

        Args:
            folder_path: Path to the folder
            file_name: Name of the CSV file

        Returns:
            Full path to the CSV file
        """
        return os.path.join(folder_path, file_name)

    def _manage_csv_file(
        self, folder_path: str, file_name: str, columns: list[str]
    ) -> pd.DataFrame:
        """
        Common CSV file management logic.

        Args:
            folder_path: Path to the folder
            file_name: Name of the CSV file
            columns: List of column names for the CSV file

        Returns:
            Existing DataFrame if file exists, empty DataFrame otherwise
        """
        self._ensure_folder_exists(folder_path)
        csv_path = self._get_csv_path(folder_path, file_name)

        # Check if file exists
        if os.path.exists(csv_path):
            try:
                existing_df = pd.read_csv(csv_path, low_memory=False)
                return existing_df
            except Exception as e:
                # Create new file with specified columns
                new_df = pd.DataFrame(columns=columns)
                new_df.to_csv(csv_path, index=False)
                return new_df
        else:
            # Create new file with specified columns
            new_df = pd.DataFrame(columns=columns)
            new_df.to_csv(csv_path, index=False)
            return new_df

    def _append_to_csv_file(
        self,
        folder_path: str,
        file_name: str,
        data_df: pd.DataFrame,
        default_columns: list[str],
    ) -> None:
        """
        Common CSV append logic.

        Args:
            folder_path: Path to the folder
            file_name: Name of the CSV file
            data_df: DataFrame to append
            default_columns: Default columns if file doesn't exist
        """
        if data_df.empty:
            return

        csv_path = self._get_csv_path(folder_path, file_name)

        # Read existing data
        try:
            existing_df = pd.read_csv(csv_path, low_memory=False)
        except (FileNotFoundError, ValueError):
            existing_df = pd.DataFrame(columns=default_columns)

        # Handle empty DataFrames to avoid FutureWarning
        if existing_df.empty and data_df.empty:
            # Both are empty, just save the empty DataFrame with correct columns
            pd.DataFrame(columns=default_columns).to_csv(csv_path, index=False)
            return
        elif existing_df.empty:
            # Only existing is empty, just save the new data
            data_df.to_csv(csv_path, index=False)
            return
        elif data_df.empty:
            # Only new data is empty, keep existing file unchanged
            return
        else:
            # Both have data, concatenate them
            # Preserve column order by using existing_df columns as the base
            existing_columns = list(existing_df.columns)
            new_columns = [col for col in data_df.columns if col not in existing_columns]
            all_columns = existing_columns + new_columns
            
            # Reindex both DataFrames to have the same columns in the correct order
            existing_df = existing_df.reindex(columns=all_columns, fill_value=None)
            data_df = data_df.reindex(columns=all_columns, fill_value=None)
            
            # Filter out empty/NA entries before concatenation to avoid FutureWarning
            existing_df_filtered = existing_df.dropna(how='all')
            data_df_filtered = data_df.dropna(how='all')
            
            # Now concatenate
            combined_df = pd.concat([existing_df_filtered, data_df_filtered], ignore_index=True)
            combined_df.to_csv(csv_path, index=False)

    def _transform_data_to_csv_format(
        self, data_df: pd.DataFrame, column_mapping: dict[str, str]
    ) -> pd.DataFrame:
        """
        Common data transformation logic.

        Args:
            data_df: Original DataFrame
            column_mapping: Dictionary mapping CSV columns to DataFrame columns

        Returns:
            Transformed DataFrame
        """
        # Get the ordered list of CSV columns from the mapping
        csv_columns = list(column_mapping.keys())
        
        transformed_data = []
        for _, row in data_df.iterrows():
            transformed_row = {}
            for csv_col, df_col in column_mapping.items():
                if df_col in row:
                    value = row[df_col]
                    # Handle None values for is_mapped field
                    if df_col == "is_mapped" and value is None:
                        transformed_row[csv_col] = False
                    else:
                        transformed_row[csv_col] = value
                # Handle missing columns with appropriate defaults
                elif df_col == "is_mapped":
                    transformed_row[csv_col] = False
                elif isinstance(row.get(df_col, None), bool):
                    transformed_row[csv_col] = False
                elif isinstance(row.get(df_col, None), int | float):
                    transformed_row[csv_col] = 0
                else:
                    transformed_row[csv_col] = ""
            transformed_data.append(transformed_row)

        # Create DataFrame with explicit column order
        result_df = pd.DataFrame(transformed_data)
        if not result_df.empty:
            # Ensure columns are in the correct order
            result_df = result_df[csv_columns]
        
        return result_df

    def _create_matrix_csv(
        self,
        folder_path: str,
        file_name: str,
        data_df: pd.DataFrame,
        group_field: str,
        value_field: str,
        gene_field: str,
        gene_column_name: str = "Gene",
    ) -> pd.DataFrame:
        """
        Common matrix/pivot logic for creating matrix CSV files.

        Args:
            folder_path: Path to the folder
            file_name: Name of the CSV file
            data_df: DataFrame with data
            group_field: Field to group by (e.g., 'indication', 'primary_site')
            value_field: Field containing values to average (e.g., 'log2_expression', 'expression_value')
            gene_field: Field containing gene/protein symbol
            gene_column_name: Name for the gene column in the CSV

        Returns:
            DataFrame with matrix data
        """
        csv_path = self._get_csv_path(folder_path, file_name)

        # Always create the file structure, even if data is empty
        if data_df.empty:
            # Create a minimal file with just the gene column
            columns = [gene_column_name]
            self._manage_csv_file(folder_path, file_name, columns)
            return data_df

        # Extract all unique groups from the data
        all_groups = sorted(data_df[group_field].unique())

        # Manage CSV file
        columns = [gene_column_name, *all_groups]
        existing_df = self._manage_csv_file(folder_path, file_name, columns)

        # Compute the average for each group
        avg_values = data_df.groupby(group_field)[value_field].mean()

        # Build a single-row DataFrame: Gene + one column per group
        gene_symbol = data_df[gene_field].iloc[0] if not data_df.empty else ""
        row_data = {gene_column_name: gene_symbol}

        # Get all columns from existing file or current data
        if not existing_df.empty:
            all_columns = list(existing_df.columns)
        else:
            all_columns = [gene_column_name, *all_groups]

        # Ensure all columns from the file are present in the row_data, fill missing with None
        avg_dict = avg_values.to_dict()
        for col in all_columns:
            if col == gene_column_name:
                continue  # will set below
            row_data[col] = avg_dict.get(col, None)

        row_data[gene_column_name] = gene_symbol

        # Reorder row_data to match the columns in the file
        ordered_row = [row_data.get(col, None) for col in all_columns]
        pivot_df = pd.DataFrame([ordered_row], columns=all_columns)

        # Append to existing file
        self._append_to_csv_file(folder_path, file_name, pivot_df, all_columns)

        return data_df


