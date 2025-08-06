"""
DepMap data handler for processing dep-map data.
"""

import logging

import pandas as pd

from bd_data_fetcher.api.umap_models import DepMapData

from .base_handler import BaseDataHandler

logger = logging.getLogger(__name__)


class DepMapDataHandler(BaseDataHandler):
    """
    This class is responsible for handling DepMap data.
    """

    def get_dep_map_data(
        self, uniprotkb_acs: list[str], cell_line_set: set[str]
    ) -> list[DepMapData]:
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
                uniprotkb_acs=uniprotkb_acs, ccle_model_ids=[]
            )
            missing_cell_lines = cell_line_set - {
                data.cell_line_name for data in dep_map_data
            }

            if missing_cell_lines:
                from rich.console import Console

                console = Console()
                console.print(
                    f"[yellow]Warning: No DepMap data found for the following cell lines: {', '.join(sorted(missing_cell_lines))}[/yellow]"
                )
            return [
                data for data in dep_map_data if data.cell_line_name in cell_line_set
            ]
        except Exception as e:
            logger.exception(f"Error retrieving DepMap data for {uniprotkb_acs}: {e}")
            return []

    def build_dep_map_data_sheet(
        self, uniprotkb_acs: list[str], file_path: str, cell_line_set: set[str]
    ):
        """
        Build a DepMap data sheet for given uniprotkb_acs.
        Stores DepMap data in the Excel sheet, appending to existing data.
        """
        sheet_name = "dep_map_data"
        columns = [
            "Protein Symbol",
            "UniProtKB AC",
            "Cell Line",
            "Onc Lineage",
            "Onc Primary Disease",
            "Onc Subtype",
            "TPM Log2",
            "Gene Level Copy Number",
        ]

        # Manage Excel sheet
        self._manage_excel_sheet(file_path, sheet_name, columns)

        # Retrieve DepMap data
        dep_map_data = self.get_dep_map_data(uniprotkb_acs, cell_line_set)
        data_df = pd.DataFrame([obj.dict() for obj in dep_map_data])

        if not data_df.empty:
            # Transform data using common method
            column_mapping = {
                "Protein Symbol": "protein_symbol",
                "UniProtKB AC": "uniprotkb_ac",
                "Cell Line": "cell_line_name",
                "Onc Lineage": "onc_lineage",
                "Onc Primary Disease": "onc_primary_disease",
                "Onc Subtype": "onc_subtype",
                "TPM Log2": "tpm_log2",
                "Gene Level Copy Number": "gene_level_copy_number",
            }
            transformed_df = self._transform_data_to_sheet_format(
                data_df, column_mapping
            )

            # Append to Excel sheet
            self._append_to_excel_sheet(file_path, sheet_name, transformed_df, columns)

        return data_df
