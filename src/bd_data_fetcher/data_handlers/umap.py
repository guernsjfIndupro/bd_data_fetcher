from ..api.umap_client import UMapServiceClient
import pandas as pd
import logging
from typing import Set

logger = logging.getLogger(__name__)


class uMapDataHandler:
    """
    This class is responsible for handling UMap data.
    """
    def __init__(self):
        self.umap_client = UMapServiceClient()

    def get_targeted_replicate_sets(self, uniprotkb_ac: str):
        """
        Get all replicate sets that have targeted the given protein.
        """
        replicate_sets = self.umap_client._get_replicate_sets()
        
        return [
            replicate_set
            for replicate_set in replicate_sets
            if (
                isinstance(replicate_set.target.proteins, list)
                and len(replicate_set.target.proteins) == 1
                and replicate_set.target.proteins[0].uniprotkb_ac == uniprotkb_ac
                and len(replicate_set.cell_source.cell_lines) > 0
            )
        ]

    def get_umap_data(self, uniprotkb_ac: str, file_path: str):
        """
        Build a UMap analysis results sheet for a given uniprotkb_ac.
        Stores all analysis results data in the Excel sheet, appending to existing data.
        """
        sheet_name = "replicate_set_results"
        
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
            columns = [
                "Replicate Set ID", "Cell Line", "Chemistry", "Target Protein", 
                "Protein Symbol", "Protein UniProtKB AC", "Log2 FC", "P-value", 
                "Number of Peptides", "Binder"
            ]
            new_df = pd.DataFrame(columns=columns)
            
            if existing_sheets:
                # Append to existing file
                with pd.ExcelWriter(file_path, engine="openpyxl", mode='a') as writer:
                    new_df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                # Create new file
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    new_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Get targeted replicate sets
        replicate_sets = self.get_targeted_replicate_sets(uniprotkb_ac)
        
        if replicate_sets:
            # Transform data to match the sheet column structure
            transformed_data = []
            
            for replicate_set in replicate_sets:
                # Retrieve all replicate set data
                analysis_results = self.umap_client._get_analysis_results(replicate_set_id=replicate_set.id)
                
                # Get cell line name
                cell_line = replicate_set.cell_source.cell_lines[0].name if replicate_set.cell_source.cell_lines else "Unknown"
                
                # Get target protein info
                target_protein = replicate_set.target.proteins[0].symbol if replicate_set.target else "Unknown"
                
                for result in analysis_results:
                    transformed_row = {
                        "Replicate Set ID": replicate_set.id,
                        "Cell Line": cell_line,
                        "Chemistry": replicate_set.chemistry,
                        "Target Protein": target_protein,
                        "Protein Symbol": result.protein.symbol,
                        "Protein UniProtKB AC": result.protein.uniprotkb_ac,
                        "Log2 FC": result.log2_fc,
                        "P-value": result.nlog10_pvalue,
                        "Number of Peptides": result.number_of_peptides,
                        "Binder": replicate_set.binder.display_name if replicate_set.binder else "Unknown"
                    }
                    transformed_data.append(transformed_row)
            
            # Create DataFrame with the correct column structure
            transformed_df = pd.DataFrame(transformed_data)
            
            if not transformed_df.empty:
                # Read existing data to get the current row count
                try:
                    existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
                except (FileNotFoundError, ValueError):
                    existing_df = pd.DataFrame(columns=[
                        "Replicate Set ID", "Cell Line", "Chemistry", "Target Protein", 
                        "Protein Symbol", "Protein UniProtKB AC", "Log2 FC", "P-value", 
                        "Number of Peptides", "Binder"
                    ])
                
                # Append new data to existing sheet
                with pd.ExcelWriter(file_path, engine="openpyxl", mode='a', if_sheet_exists='overlay') as writer:
                    start_row = len(existing_df) + 1
                    transformed_df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False, header=False)

        return replicate_sets


    def get_cell_lines(self, uniprotkb_ac: str) -> Set[str]:
        """
        Get all cell lines that have targeted the given protein.

        # TODO: Determine if we should use the name or the ID.
        """
        replicate_sets = self.get_targeted_replicate_sets(uniprotkb_ac)
        return {replicate_set.cell_source.cell_lines[0].name for replicate_set in replicate_sets}
