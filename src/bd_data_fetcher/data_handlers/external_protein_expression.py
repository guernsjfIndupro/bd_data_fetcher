import logging

import pandas as pd

from bd_data_fetcher.api.umap_models import (
    ExternalProteinExpressionData,
    ProteomicsNormalExpressionData,
)

from bd_data_fetcher.data_handlers.base_handler import BaseDataHandler
from bd_data_fetcher.data_handlers.utils import SheetNames

logger = logging.getLogger(__name__)


class ExternalProteinExpressionDataHandler(BaseDataHandler):

    def get_normal_proteomics_data(
        self, uniprotkb_ac: str
    ) -> list[ProteomicsNormalExpressionData]:
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
        
        TODO: This needs to handle the edge case where
        the first protein does not have data, it currently
        generates a sheet with no data exceept for the gene column.
        """
        sheet_name = SheetNames.NORMAL_PROTEOMICS_DATA.value

        # Retrieve normal proteomics data
        normal_proteomics_data = self.get_normal_proteomics_data(uniprotkb_ac)
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
        self, uniprotkb_acs: list[str]
    ) -> list[ExternalProteinExpressionData]:
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
        sheet_name = SheetNames.EXTERNAL_PROTEOMICS_DATA.value

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
