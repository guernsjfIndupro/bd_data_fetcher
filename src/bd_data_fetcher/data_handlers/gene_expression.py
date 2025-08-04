"""
What needs to be done here?

This one has 2 parts:

Retrieval of normal gene expression

Retrieval of all gene expression data for a given study
"""
from ..api.umap_client import UMapServiceClient
from ..api.umap_models import RNAGeneExpressionData
from functools import lru_cache
from typing import List
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class GeneExpressionDataHandler:
    """
    This class is responsible for handling gene expression data.

    It has 3 parts:

    - Retrieval of normal gene expression
    - Retrieval of all gene expression data for a given study
    - Calculating tumor/normal ratios for all primary_sites

    Each function is responsible for generating a sheet in the excel file.

    The excel file is generated in the same directory as the script that calls this class.

    The sheet names are:

    - normal_gene_expression
    - gene_expression
    - gene_tumor_normal_ratios
    """
    def __init__(self):
        self.umap_client = UMapServiceClient()
        pass

    def _retrieve_normal_gene_expression(self, uniprotkb_ac: str) -> List[RNAGeneExpressionData]:
        """
        Retrieve normal gene expression data for a given uniprotkb_ac.

        Args:
            uniprotkb_ac: The uniprotkb_ac of the protein to retrieve normal gene expression data for.

        Returns:
            A list of RNAGeneExpressionData objects.
        """
        try:
            return[obj for obj in self.umap_client._get_rna_gene_expression_data(uniprotkb_acs=[uniprotkb_ac]) if not obj.is_cancer]
        except Exception as e:
            logger.error(f"Error retrieving normal gene expression for {uniprotkb_ac}: {e}")
            return []

    @lru_cache
    def get_all_primary_sites(self) -> List[str]:
        """
        Get all possible primary_sites.
        """
        return self.umap_client._get_all_primary_sites()

    def _retrieve_gene_expression_data(self, uniprotkb_ac: str) -> List[RNAGeneExpressionData]:
        """
        Retrieve all gene expression data for a given study.

        Args:
            study: The study to retrieve gene expression data for.

        Returns:
            A list of RNAGeneExpressionData objects.
        """
        try:
            return self.umap_client._get_rna_gene_expression_data(uniprotkb_acs=[uniprotkb_ac])
        except Exception as e:
            logger.error(f"Error retrieving normal gene expression for {uniprotkb_ac}: {e}")
            return []

    def build_normal_gene_expression_sheet(self, uniprotkb_ac: str, file_path: str):
        """
        Build a normal gene expression sheet for a given uniprotkb_ac.
        """
        sheet_name = "normal_gene_expression"

        try:
            with pd.ExcelFile(file_path) as xls:
                if sheet_name not in xls.sheet_names:
                    # Create a new sheet with the default column names
                    primary_sites = self.get_all_primary_sites()
                    columns = ["Gene"] + sorted(primary_sites)
                    new_df = pd.DataFrame(columns=columns)
                    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                        new_df.to_excel(writer, sheet_name=sheet_name, index=False)
        except FileNotFoundError:
            # Create a new sheet with the default column names
            primary_sites = self.get_all_primary_sites()
            columns = ["Gene"] + sorted(primary_sites)
            new_df = pd.DataFrame(columns=columns)
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                new_df.to_excel(writer, sheet_name=sheet_name, index=False)

        normal_gene_expression = self._retrieve_normal_gene_expression(uniprotkb_ac)
        normal_df = pd.DataFrame([obj.dict() for obj in normal_gene_expression])
        
        if not normal_df.empty:
            # Compute the average expression_value for each primary_site
            avg_expression = normal_df.groupby('primary_site')['expression_value'].mean()

            # Build a single-row DataFrame: Gene + one column per primary_site
            gene_symbol = normal_df['symbol'].iloc[0] if not normal_df.empty else ""
            row_data = {'Gene': gene_symbol}
            
            # Read existing sheet to get column structure
            try:
                existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
                all_columns = list(existing_df.columns)
            except (FileNotFoundError, ValueError):
                # If sheet doesn't exist or is empty, use default columns
                primary_sites = self.get_all_primary_sites()
                all_columns = ["Gene"] + sorted(primary_sites)
                existing_df = pd.DataFrame(columns=all_columns)
            
            # Ensure all columns from the sheet are present in the row_data, fill missing with None
            avg_expr_dict = avg_expression.to_dict()
            for col in all_columns:
                if col == "Gene":
                    continue  # will set below
                row_data[col] = avg_expr_dict.get(col, None)
            
            row_data['Gene'] = gene_symbol

            # Reorder row_data to match the columns in the sheet
            ordered_row = [row_data.get(col, None) for col in all_columns]
            pivot_df = pd.DataFrame([ordered_row], columns=all_columns)
            
            # Append to existing sheet
            with pd.ExcelWriter(file_path, engine="openpyxl", mode='a', if_sheet_exists='overlay') as writer:
                start_row = len(existing_df) + 1
                pivot_df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False, header=False)

        return pd.DataFrame(normal_gene_expression)

    def build_gene_expression_sheet(self, uniprotkb_ac: str, file_path: str):
        """
        Build a gene expression sheet for a given study.
        Stores all gene expression data in the Excel sheet, appending to existing data.
        """
        sheet_name = "gene_expression"
        
        # Ensure sheet exists with proper column structure
        try:
            with pd.ExcelFile(file_path) as xls:
                if sheet_name not in xls.sheet_names:
                    # Create a new sheet with the correct column names
                    columns = ["Gene", "Expression Value", "Primary Site", "Is Cancer"]
                    new_df = pd.DataFrame(columns=columns)
                    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                        new_df.to_excel(writer, sheet_name=sheet_name, index=False)
        except FileNotFoundError:
            # Create a new Excel file with the gene_expression sheet
            columns = ["Gene", "Expression Value", "Primary Site", "Is Cancer"]
            new_df = pd.DataFrame(columns=columns)
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                new_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Retrieve gene expression data
        gene_expression = self._retrieve_gene_expression_data(uniprotkb_ac)
        data_df = pd.DataFrame([obj.dict() for obj in gene_expression])
        
        if not data_df.empty:
            # Transform data to match the sheet column structure
            # Map the data fields to the expected columns
            transformed_data = []
            for _, row in data_df.iterrows():
                transformed_row = {
                    "Gene": row.get("symbol", ""),
                    "Expression Value": row.get("expression_value", 0),
                    "Primary Site": row.get("primary_site", ""),
                    "Is Cancer": row.get("is_cancer", False)
                }
                transformed_data.append(transformed_row)
            
            # Create DataFrame with the correct column structure
            transformed_df = pd.DataFrame(transformed_data)
            
            # Read existing data to get the current row count
            try:
                existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
            except (FileNotFoundError, ValueError):
                existing_df = pd.DataFrame(columns=["Gene", "Expression Value", "Primary Site", "Is Cancer"])
            
            # Append new data to existing sheet
            with pd.ExcelWriter(file_path, engine="openpyxl", mode='a', if_sheet_exists='overlay') as writer:
                start_row = len(existing_df) + 1
                transformed_df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False, header=False)

        return data_df

    def build_gene_tumor_normal_ratios_sheet(self, uniprotkb_ac: str, file_path: str):
        """
        Build a gene tumor normal ratios sheet for a given uniprotkb_ac.
        Calculates tumor/normal ratios for each primary site and stores them in the sheet.
        """
        sheet_name = "gene_tumor_normal_ratios"
        
        # Ensure sheet exists with proper column structure (same as normal gene expression)
        try:
            with pd.ExcelFile(file_path) as xls:
                if sheet_name not in xls.sheet_names:
                    # Create a new sheet with the default column names
                    primary_sites = self.get_all_primary_sites()
                    columns = ["Gene"] + sorted(primary_sites)
                    new_df = pd.DataFrame(columns=columns)
                    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                        new_df.to_excel(writer, sheet_name=sheet_name, index=False)
        except FileNotFoundError:
            # Create a new sheet with the default column names
            primary_sites = self.get_all_primary_sites()
            columns = ["Gene"] + sorted(primary_sites)
            new_df = pd.DataFrame(columns=columns)
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                new_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Retrieve gene expression data (contains both normal and tumor data)
        all_gene_expression = self._retrieve_gene_expression_data(uniprotkb_ac)
        
        # Convert to DataFrame
        all_df = pd.DataFrame([obj.dict() for obj in all_gene_expression])
        
        if not all_df.empty:
            # Separate normal and tumor data from the same dataset
            normal_df = all_df[all_df['is_cancer'] == False]
            tumor_df = all_df[all_df['is_cancer'] == True]
            
            if not normal_df.empty and not tumor_df.empty:
                # Calculate average normal expression per primary site
                normal_avg = normal_df.groupby('primary_site')['expression_value'].mean()
                
                # Calculate average tumor expression per primary site
                tumor_avg = tumor_df.groupby('primary_site')['expression_value'].mean()
                
                # Calculate tumor/normal ratios (tumor - normal)
                # Only calculate ratios for primary sites that have both normal and tumor data
                common_sites = set(normal_avg.index) & set(tumor_avg.index)
                ratios = pd.Series(index=common_sites)
                
                for site in common_sites:
                    ratios[site] = tumor_avg[site] - normal_avg[site]
                
                # Get gene symbol
                gene_symbol = normal_df['symbol'].iloc[0] if not normal_df.empty else ""
                
                # Read existing sheet to get column structure
                try:
                    existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
                    all_columns = list(existing_df.columns)
                except (FileNotFoundError, ValueError):
                    # If sheet doesn't exist or is empty, use default columns
                    primary_sites = self.get_all_primary_sites()
                    all_columns = ["Gene"] + sorted(primary_sites)
                    existing_df = pd.DataFrame(columns=all_columns)
                
                # Build row data with ratios
                row_data = {'Gene': gene_symbol}
                ratios_dict = ratios.to_dict()
                
                # Fill in ratio values for each column
                for col in all_columns:
                    if col == "Gene":
                        continue
                    # Set to None if the primary site doesn't have both normal and tumor data
                    row_data[col] = ratios_dict.get(col, None)
                
                # Create DataFrame with correct column order
                ordered_row = [row_data.get(col, None) for col in all_columns]
                ratios_df = pd.DataFrame([ordered_row], columns=all_columns)
                
                # Append to existing sheet
                with pd.ExcelWriter(file_path, engine="openpyxl", mode='a', if_sheet_exists='overlay') as writer:
                    start_row = len(existing_df) + 1
                    ratios_df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False, header=False)

        return pd.DataFrame(all_gene_expression)
