"""
DepMap data handler for processing dep-map data.
"""

import pandas as pd
import structlog

from bd_data_fetcher.api.umap_models import DepMapData
from bd_data_fetcher.data_handlers.base_handler import BaseDataHandler
from bd_data_fetcher.data_handlers.utils import FileNames

logger = structlog.get_logger(__name__)


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

            return [data for data in dep_map_data if data.cell_line_name in cell_line_set]
        except Exception as e:
            logger.exception(f"Error retrieving DepMap data for {uniprotkb_acs}: {e}")
            return []

    def build_dep_map_data_csv(
        self, uniprotkb_acs: list[str], folder_path: str, cell_line_set: set[str]
    ):
        """
        Build a DepMap data CSV file for given uniprotkb_acs.
        Stores DepMap data in the CSV file, appending to existing data.
        """
        file_name = FileNames.DEPMAP_DATA.value
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

        # Manage CSV file
        self._manage_csv_file(folder_path, file_name, columns)

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
            transformed_df = self._transform_data_to_csv_format(
                data_df, column_mapping
            )

            # Append to CSV file
            self._append_to_csv_file(folder_path, file_name, transformed_df, columns)

        return data_df
