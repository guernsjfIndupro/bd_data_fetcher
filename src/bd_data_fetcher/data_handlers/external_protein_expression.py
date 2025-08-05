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
from src.mint_mind.modules.internal_proteomics_tissue.model import (
    TissueSampleDiaIntensity,
)

from ..api.umap_client import UMapServiceClient
from ..api.umap_models import (
    CellLineProteomicsData,
    ExternalProteinExpressionData,
    ProteomicsNormalExpressionData,
    RNAGeneExpressionData,
)
from .base_handler import BaseDataHandler

logger = logging.getLogger(__name__)


class ExternalProteinExpressionDataHandler(BaseDataHandler):
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

    @staticmethod
    def build_generalizable_sigmoidal_curve(
        data: List[TissueSampleDiaIntensity],
    ) -> List[np.ndarray]:
        """Builds a generalizable sigmoidal curve from tissue sample intensity data.

        This method processes tissue sample intensity data to create a standardized curve
        that represents the distribution of protein expression across samples. It handles
        interpolation of missing values and normalizes the data for consistent comparison.

        Args:
            data (List[TissueSampleDiaIntensity]): List of tissue sample intensity measurements,
                containing weight normalized rankings and intensities.

        Returns:
            List[np.ndarray]: A list containing two numpy arrays:
                - x-axis values representing standardized rankings (0-1000)
                - y-axis values representing log10-transformed normalized intensities


        I need to update this to use the DIA cell line data, this should actually be straightforward.

        """
        data_per_tissue = defaultdict(list)

        for data in data:
            data_per_tissue[data.benchling_aliquot_registry_id].append(
                (data.weight_normalized_intensity_ranking, data.normalized_intensity)
            )

        for benchling_aliquot_registry_id in data_per_tissue.keys():
            data_per_tissue[benchling_aliquot_registry_id] = sorted(
                data_per_tissue[benchling_aliquot_registry_id], key=lambda x: x[0]
            )

        common_rankings = np.linspace(start=0, stop=1000, num=1001)

        weight_normalized_intensites = []

        for benchling_aliquot_registry_id in data_per_tissue.keys():
            # NOTE: The current implementation assumes that we have detected at least 1000
            # unique values for the weight normalized intensity ranking.
            # We interpolate the missing values.
            local_weight_normalized_intensites = [0 for i in range(1001)]

            normalized_intensity_ranking_pairs = data_per_tissue[
                benchling_aliquot_registry_id
            ]
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

    def get_normal_proteomics_data(
        self, uniprotkb_ac: str
    ) -> List[ProteomicsNormalExpressionData]:
        """
        Get the normal proteomics data for a given uniprotkb_ac.
        """
        return self._safe_api_call(
            self.umap_client._get_proteomics_normal_expression_data,
            uniprotkb_ac=uniprotkb_ac,
        )

    def build_normal_proteomics_sheet(self, uniprotkb_ac: str, file_path: str):
        """
        Build a normal proteomics sheet for a given uniprotkb_ac.
        Creates a matrix where each row represents a gene and each column represents an indication.
        """
        sheet_name = "normal_proteomics"

        # Retrieve normal proteomics data
        normal_proteomics_data = self.get_normal_proteomics_data(uniprotkb_ac)
        print(len(normal_proteomics_data))
        data_df = pd.DataFrame([obj.dict() for obj in normal_proteomics_data])

        # Use the matrix sheet creation method
        return self._create_matrix_sheet(
            file_path=file_path,
            sheet_name=sheet_name,
            data_df=data_df,
            group_field="indication",
            value_field="log2_expression",
            gene_field="protein_symbol",
            gene_column_name="Gene",
        )

        return data_df

    def get_external_proteomics_data(
        self, uniprotkb_acs: List[str]
    ) -> List[ExternalProteinExpressionData]:
        """
        Get external proteomics data for given uniprotkb_acs.
        """
        return self._safe_api_call(
            self.umap_client._get_external_proteomics_data, uniprotkb_acs=uniprotkb_acs
        )

    def build_study_specific_sheet(self, uniprotkb_ac: str, file_path: str):
        """
        Build a study-specific sheet for a given uniprotkb_ac.
        Creates a matrix where each row represents a gene and each column represents a study-indication combination,
        with values being tumor-normal ratios (tumor - normal) for each study-indication.

        TODO: This is not ready yet, It needs to be heavily tested.[]
        """
        sheet_name = "external_proteomics_t_n"

        # Retrieve external proteomics data
        external_proteomics_data = self.get_external_proteomics_data([uniprotkb_ac])
        data_df = pd.DataFrame([obj.dict() for obj in external_proteomics_data])

        if not data_df.empty:
            # Separate normal and tumor data by sample_type
            # Assuming 'Normal' and 'Tumor' are in sample_type field
            normal_df = data_df[
                data_df["sample_type"].str.contains("Normal", case=False, na=False)
            ]
            tumor_df = data_df[
                data_df["sample_type"].str.contains("Tumor", case=False, na=False)
            ]

            if not normal_df.empty and not tumor_df.empty:
                # Calculate average normal expression per study-indication combination
                normal_avg = normal_df.groupby(["study_name", "indication"])[
                    "value"
                ].mean()

                # Calculate average tumor expression per study-indication combination
                tumor_avg = tumor_df.groupby(["study_name", "indication"])[
                    "value"
                ].mean()

                # Calculate tumor/normal ratios (tumor - normal)
                # Only calculate ratios for study-indication combinations that have both normal and tumor data
                common_combinations = set(normal_avg.index) & set(tumor_avg.index)
                ratios = pd.Series(index=common_combinations)

                for study_indication in common_combinations:
                    ratios[study_indication] = (
                        tumor_avg[study_indication] - normal_avg[study_indication]
                    )

                # Get protein symbol
                protein_symbol = (
                    normal_df["symbol"].iloc[0] if not normal_df.empty else ""
                )

                # Create a DataFrame with the ratio data for matrix processing
                ratio_data = []
                for study_indication, ratio in ratios.items():
                    study_name, indication = study_indication
                    # Create a column name that combines study and indication
                    column_name = f"{study_name}_{indication}"
                    ratio_data.append(
                        {
                            "study_indication": column_name,
                            "ratio_value": ratio,
                            "symbol": protein_symbol,
                        }
                    )

                ratio_df = pd.DataFrame(ratio_data)

                # Use the matrix sheet creation method
                return self._create_matrix_sheet(
                    file_path=file_path,
                    sheet_name=sheet_name,
                    data_df=ratio_df,
                    group_field="study_indication",
                    value_field="ratio_value",
                    gene_field="symbol",
                    gene_column_name="Gene",
                )

        return data_df
