from ..api.umap_client import UMapServiceClient
from ..api.umap_models import RNAGeneExpressionData, CellLineProteomicsData
from functools import lru_cache
from typing import List, Set
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class WCEDataHandler:
    """
    This class is responsible for handling WCE data.
    """
    def __init__(self):
        self.umap_client = UMapServiceClient()

    def get_wce_data(self, cell_line_set: Set[str], uniprotkb_ac: str) -> List[CellLineProteomicsData]:
        """
        Retrieve WCE data for a given uniprotkb_ac and cell line set.

        Args:
            cell_line_set: Set of cell line names to filter by
            uniprotkb_ac: The uniprotkb_ac of the protein to retrieve WCE data for

        Returns:
            A list of CellLineProteomicsData objects filtered by the cell line set
        """
        try:
            wce_data = self.umap_client._get_proteomics_cell_line_data(uniprotkb_ac=uniprotkb_ac)

            print(cell_line_set)
            print({data.cell_line_name for data in wce_data})
            # Filter the data to only include the cell lines in the cell line set
            wce_data = [data for data in wce_data if data.cell_line_name in cell_line_set]

            return wce_data
        except Exception as e:
            logger.error(f"Error retrieving WCE data for {uniprotkb_ac}: {e}")
            return []

    def build_wce_data_sheet(self, uniprotkb_ac: str, cell_line_set: Set[str], file_path: str):
        """
        Build a WCE data sheet for a given uniprotkb_ac and cell line set.
        Stores WCE data in the Excel sheet, appending to existing data.
        """
        sheet_name = "wce_data"
        
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
            columns = ["Gene", "Cell Line", "Onc Lineage", "Onc Subtype", "Weight Normalized Intensity Ranking", "Experiment Type", "Title", "Copies Per Cell"]
            new_df = pd.DataFrame(columns=columns)
            
            if existing_sheets:
                # Append to existing file
                with pd.ExcelWriter(file_path, engine="openpyxl", mode='a') as writer:
                    new_df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                # Create new file
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    new_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Retrieve WCE data
        wce_data = self.get_wce_data(cell_line_set, uniprotkb_ac)
        data_df = pd.DataFrame([obj.dict() for obj in wce_data])
        
        if not data_df.empty:
            # Transform data to match the sheet column structure
            transformed_data = []
            for _, row in data_df.iterrows():
                transformed_row = {
                    "Gene": row.get("symbol", ""),
                    "Cell Line": row.get("cell_line_name", ""),
                    "Onc Lineage": row.get("onc_lineage", ""),
                    "Onc Subtype": row.get("onc_subtype", ""),
                    "Weight Normalized Intensity Ranking": row.get("weight_normalized_intensity_ranking", ""),
                    "Experiment Type": row.get("experiment_type", ""),
                    "Title": row.get("title", ""),
                    "Copies Per Cell": row.get("copies_per_cell", "")
                }
                transformed_data.append(transformed_row)
            
            # Create DataFrame with the correct column structure
            transformed_df = pd.DataFrame(transformed_data)
            
            # Read existing data to get the current row count
            try:
                existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
            except (FileNotFoundError, ValueError):
                existing_df = pd.DataFrame(columns=["Gene", "Cell Line", "Onc Lineage", "Onc Subtype", "Weight Normalized Intensity Ranking", "Experiment Type", "Title", "Copies Per Cell"])
            
            # Append new data to existing sheet
            with pd.ExcelWriter(file_path, engine="openpyxl", mode='a', if_sheet_exists='overlay') as writer:
                start_row = len(existing_df) + 1
                transformed_df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False, header=False)

        return data_df

    # Eventually I will need to be able to generate the spline function
    # for each cell line, this needs to be cached. 
    # Then i need to be able to place the data on the spline function
    # to display the protein relative rankings.