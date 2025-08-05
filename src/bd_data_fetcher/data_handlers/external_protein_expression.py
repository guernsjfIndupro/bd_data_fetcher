from ..api.umap_client import UMapServiceClient
from ..api.umap_models import RNAGeneExpressionData, CellLineProteomicsData, ProteomicsNormalExpressionData
from functools import lru_cache
from typing import List, Set
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ExternalProteinExpressionDataHandler:
    """
    This class is responsible for handling external proteomics data.

    What do i need to do here?

    Two main things

    1. Get the normal proteomics data - This is very straightforward, just use the designated endpoint.
    2. Get the study specific data - 
    This is a bit more complicated, I need to keep all studies seperated for now. 
    Need to handle the Korean data seperately
    Need to handle the various different indication naming
    Need to handle the different Mass spec experiment types. 
    """
    def __init__(self):
        self.umap_client = UMapServiceClient()

    def get_normal_proteomics_data(self, uniprotkb_ac: str) -> List[ProteomicsNormalExpressionData]:
        """
        Get the normal proteomics data for a given uniprotkb_ac.
        """
        return self.umap_client._get_proteomics_normal_expression_data(uniprotkb_ac=uniprotkb_ac)

    def build_normal_proteomics_sheet(self, uniprotkb_ac: str, file_path: str):
        """
        Build a normal proteomics sheet for a given uniprotkb_ac.
        Creates a matrix where each row represents a gene and each column represents an indication.
        """
        sheet_name = "normal_proteomics"
        
        # Check if file exists and what sheets it has
        existing_sheets = {}
        try:
            with pd.ExcelFile(file_path) as xls:
                for sheet in xls.sheet_names:
                    existing_sheets[sheet] = pd.read_excel(file_path, sheet_name=sheet)
        except FileNotFoundError:
            # File doesn't exist, we'll create it
            pass

        # Retrieve normal proteomics data
        normal_proteomics_data = self.get_normal_proteomics_data(uniprotkb_ac)
        data_df = pd.DataFrame([obj.dict() for obj in normal_proteomics_data])
        
        if not data_df.empty:
            # Extract all unique indications from the data
            all_indications = sorted(data_df['indication'].unique())
            
            # Create the sheet if it doesn't exist
            if sheet_name not in existing_sheets:
                columns = ["Gene"] + all_indications
                new_df = pd.DataFrame(columns=columns)
                
                if existing_sheets:
                    # Append to existing file
                    with pd.ExcelWriter(file_path, engine="openpyxl", mode='a') as writer:
                        new_df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    # Create new file
                    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                        new_df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Compute the average log2_expression for each indication
            avg_expression = data_df.groupby('indication')['log2_expression'].mean()

            # Build a single-row DataFrame: Gene + one column per indication
            protein_symbol = data_df['protein_symbol'].iloc[0] if not data_df.empty else ""
            row_data = {'Gene': protein_symbol}
            
            # Read existing sheet to get column structure
            try:
                existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
                all_columns = list(existing_df.columns)
            except (FileNotFoundError, ValueError):
                # If sheet doesn't exist or is empty, use columns from current data
                all_columns = ["Gene"] + all_indications
                existing_df = pd.DataFrame(columns=all_columns)
            
            # Ensure all columns from the sheet are present in the row_data, fill missing with None
            avg_expr_dict = avg_expression.to_dict()
            for col in all_columns:
                if col == "Gene":
                    continue  # will set below
                row_data[col] = avg_expr_dict.get(col, None)
            
            row_data['Gene'] = protein_symbol

            # Reorder row_data to match the columns in the sheet
            ordered_row = [row_data.get(col, None) for col in all_columns]
            pivot_df = pd.DataFrame([ordered_row], columns=all_columns)
            
            # Append to existing sheet
            with pd.ExcelWriter(file_path, engine="openpyxl", mode='a', if_sheet_exists='overlay') as writer:
                start_row = len(existing_df) + 1
                pivot_df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False, header=False)

        return data_df

    def build_study_specific_sheet(self, uniprotkb_ac: str, file_path: str):

        """
        Build a study specific sheet for a given uniprotkb_ac.

        This needs some extra thought
        """
        pass

