import logging
import os
from collections import defaultdict
from functools import lru_cache
from io import BytesIO
from typing import Any, Dict, List, Set, Type
from uuid import UUID

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d, make_splrep, splev
from scipy.optimize import curve_fit
from src.mint_mind.core.config import settings

from ..api.umap_client import UMapServiceClient
from ..api.umap_models import (
    CellLineProteomicsData,
    ExternalProteinExpressionData,
    ProteomicsNormalExpressionData,
    RNAGeneExpressionData,
)
from .base_handler import BaseDataHandler

logger = logging.getLogger(__name__)


class WCEDataHandler(BaseDataHandler):
    """
    This class is responsible for handling WCE data.
    """
    
    @staticmethod
    def build_generalizable_sigmoidal_curve(
        data: List[CellLineProteomicsData],
    ) -> List[np.ndarray]:
        """Builds a generalizable sigmoidal curve from cell line proteomics data.

        This method processes cell line proteomics data to create a standardized curve
        that represents the distribution of protein expression across cell lines. It handles
        interpolation of missing values and normalizes the data for consistent comparison.

        Args:
            data (List[CellLineProteomicsData]): List of cell line proteomics measurements,
                containing weight normalized rankings and intensities.

        Returns:
            List[np.ndarray]: A list containing two numpy arrays:
                - x-axis values representing standardized rankings (0-1000)
                - y-axis values representing log10-transformed normalized intensities
        """
        data_per_cell_line = defaultdict(list)

        for data_point in data:
            data_per_cell_line[data_point.cell_line_name].append(
                (data_point.weight_normalized_intensity_ranking, data_point.normalized_intensity)
            )

        for cell_line_name in data_per_cell_line.keys():
            data_per_cell_line[cell_line_name] = sorted(
                data_per_cell_line[cell_line_name], key=lambda x: x[0]
            )

        common_rankings = np.linspace(start=0, stop=1000, num=1001)

        weight_normalized_intensites = []

        for cell_line_name in data_per_cell_line.keys():
            # NOTE: The current implementation assumes that we have detected at least 1000
            # unique values for the weight normalized intensity ranking.
            # We interpolate the missing values.
            local_weight_normalized_intensites = [0 for i in range(1001)]

            normalized_intensity_ranking_pairs = data_per_cell_line[cell_line_name]
            for (
                normalized_intensity_ranking,
                normalized_intensity,
            ) in normalized_intensity_ranking_pairs:
                local_weight_normalized_intensites[normalized_intensity_ranking] = (
                    normalized_intensity
                )

            # Interpolate zero values.
            # Find indices and values of non-zero points for interpolation
            non_zero_indices = [
                i
                for i, val in enumerate(local_weight_normalized_intensites)
                if val != 0
            ]
            if len(non_zero_indices) > 1:  # Need at least 2 points for interpolation
                non_zero_values = [
                    local_weight_normalized_intensites[i] for i in non_zero_indices
                ]
                interpolator = interp1d(
                    non_zero_indices,
                    non_zero_values,
                    kind="linear",
                    bounds_error=False,
                    fill_value="extrapolate",
                )
                for i in range(len(local_weight_normalized_intensites)):
                    if local_weight_normalized_intensites[i] == 0:
                        local_weight_normalized_intensites[i] = interpolator(i)

            weight_normalized_intensites.append(
                np.log10(local_weight_normalized_intensites)
            )

        # Use spline interpolation to fit the data.
        y_stack = np.vstack(weight_normalized_intensites)
        y_avg = np.mean(y_stack, axis=0)

        spline = make_splrep(common_rankings, y_avg, s=1)
        x_fit = np.linspace(min(common_rankings), max(common_rankings), 500)
        y_fit = splev(x_fit, spline)

        return [x_fit, y_fit]


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
