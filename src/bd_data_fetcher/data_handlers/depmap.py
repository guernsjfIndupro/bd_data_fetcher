"""
DepMap data handler for processing dep-map data.
"""
from ..api.umap_client import UMapServiceClient
from ..api.umap_models import DepMapData
from functools import lru_cache
from typing import List, Set, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DepMapDataHandler:
    """
    This class is responsible for handling DepMap data.
    """
    def __init__(self):
        self.umap_client = UMapServiceClient()

    def get_dep_map_data(self, uniprotkb_acs: List[str], cell_line_set: Set[str]) -> List[DepMapData]:
        """
        Retrieve DepMap data for given uniprotkb_acs.

        Args:
            uniprotkb_acs: List of UniProtKB accession numbers
            cell_line_set: Set of cell line names

        Returns:
            A list of DepMapData objects
        """
        # This is not working correctly, need to use the ccle_model_id to actually map
        # TODO: Investigate the name mismatch.
        # Okay, this is actually working.
        try:
            dep_map_data = self.umap_client._get_dep_map_data(
                uniprotkb_acs=uniprotkb_acs,
                ccle_model_ids=[]
            )
            missing_cell_lines = cell_line_set - {data.cell_line_name for data in dep_map_data}
            
            if missing_cell_lines:
                from rich.console import Console
                console = Console()
                console.print(
                    f"[yellow]Warning: No DepMap data found for the following cell lines: {', '.join(sorted(missing_cell_lines))}[/yellow]"
                )
            return [data for data in dep_map_data if data.cell_line_name in cell_line_set]
        except Exception as e:
            logger.error(f"Error retrieving DepMap data for {uniprotkb_acs}: {e}")
            return []

    def build_dep_map_data_sheet(self, uniprotkb_acs: List[str], file_path: str, cell_line_set: Set[str]):
        """
        Build a DepMap data sheet for given uniprotkb_acs.
        Stores DepMap data in the Excel sheet, appending to existing data.
        """
        sheet_name = "dep_map_data"
        
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
            columns = ["Protein Symbol", "UniProtKB AC", "Cell Line", "Onc Lineage", "Onc Primary Disease", "Onc Subtype", "TPM Log2", "Gene Level Copy Number"]
            new_df = pd.DataFrame(columns=columns)
            
            if existing_sheets:
                # Append to existing file
                with pd.ExcelWriter(file_path, engine="openpyxl", mode='a') as writer:
                    new_df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                # Create new file
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    new_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Retrieve DepMap data
        dep_map_data = self.get_dep_map_data(uniprotkb_acs, cell_line_set)
        data_df = pd.DataFrame([obj.dict() for obj in dep_map_data])
        
        if not data_df.empty:
            # Transform data to match the sheet column structure
            transformed_data = []
            for _, row in data_df.iterrows():
                transformed_row = {
                    "Protein Symbol": row.get("protein_symbol", ""),
                    "UniProtKB AC": row.get("uniprotkb_ac", ""),
                    "Cell Line": row.get("cell_line_name", ""),
                    "Onc Lineage": row.get("onc_lineage", ""),
                    "Onc Primary Disease": row.get("onc_primary_disease", ""),
                    "Onc Subtype": row.get("onc_subtype", ""),
                    "TPM Log2": row.get("tpm_log2", 0),
                    "Gene Level Copy Number": row.get("gene_level_copy_number", "")
                }
                transformed_data.append(transformed_row)
            
            # Create DataFrame with the correct column structure
            transformed_df = pd.DataFrame(transformed_data)
            
            # Read existing data to get the current row count
            try:
                existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
            except (FileNotFoundError, ValueError):
                existing_df = pd.DataFrame(columns=["Protein Symbol", "UniProtKB AC", "Cell Line", "Onc Lineage", "Onc Primary Disease", "Onc Subtype", "TPM Log2", "Gene Level Copy Number"])
            
            # Append new data to existing sheet
            with pd.ExcelWriter(file_path, engine="openpyxl", mode='a', if_sheet_exists='overlay') as writer:
                start_row = len(existing_df) + 1
                transformed_df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False, header=False)

        return data_df