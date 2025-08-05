import logging
from functools import lru_cache
from typing import List, Set

import pandas as pd

from ..api.umap_client import UMapServiceClient
from ..api.umap_models import CellLineProteomicsData, RNAGeneExpressionData
from .base_handler import BaseDataHandler

logger = logging.getLogger(__name__)


class WCEDataHandler(BaseDataHandler):
    """
    This class is responsible for handling WCE data.
    """

    def get_wce_data(
        self, cell_line_set: Set[str], uniprotkb_ac: str
    ) -> List[CellLineProteomicsData]:
        """
        Retrieve WCE data for a given uniprotkb_ac and cell line set.

        Args:
            cell_line_set: Set of cell line names to filter by
            uniprotkb_ac: The uniprotkb_ac of the protein to retrieve WCE data for

        Returns:
            A list of CellLineProteomicsData objects filtered by the cell line set
        """
        try:
            wce_data = self.umap_client._get_proteomics_cell_line_data(
                uniprotkb_ac=uniprotkb_ac
            )
            # Filter the data to only include the cell lines in the cell line set
            wce_data = [
                data for data in wce_data if data.cell_line_name in cell_line_set
            ]

            return wce_data
        except Exception as e:
            logger.error(f"Error retrieving WCE data for {uniprotkb_ac}: {e}")
            return []

    def build_wce_data_sheet(
        self, uniprotkb_ac: str, cell_line_set: Set[str], file_path: str
    ):
        """
        Build a WCE data sheet for a given uniprotkb_ac and cell line set.
        Stores WCE data in the Excel sheet, appending to existing data.
        """
        sheet_name = "wce_data"
        columns = [
            "Gene",
            "Cell Line",
            "Onc Lineage",
            "Onc Subtype",
            "Weight Normalized Intensity Ranking",
            "Experiment Type",
            "Title",
            "Copies Per Cell",
        ]

        # Manage Excel sheet
        self._manage_excel_sheet(file_path, sheet_name, columns)

        # Retrieve WCE data
        wce_data = self.get_wce_data(cell_line_set, uniprotkb_ac)
        data_df = pd.DataFrame([obj.dict() for obj in wce_data])

        if not data_df.empty:
            # Transform data using common method
            column_mapping = {
                "Gene": "symbol",
                "Cell Line": "cell_line_name",
                "Onc Lineage": "onc_lineage",
                "Onc Subtype": "onc_subtype",
                "Weight Normalized Intensity Ranking": "weight_normalized_intensity_ranking",
                "Experiment Type": "experiment_type",
                "Title": "title",
                "Copies Per Cell": "copies_per_cell",
            }
            transformed_df = self._transform_data_to_sheet_format(
                data_df, column_mapping
            )

            # Append to Excel sheet
            self._append_to_excel_sheet(file_path, sheet_name, transformed_df, columns)

        return data_df

    # Eventually I will need to be able to generate the spline function
    # for each cell line, this needs to be cached.
    # Then i need to be able to place the data on the spline function
    # to display the protein relative rankings.
