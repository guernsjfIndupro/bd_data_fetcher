"""
What needs to be done here?

This one has 2 parts:

Retrieval of normal gene expression

Retrieval of all gene expression data for a given study
"""

import logging
from functools import lru_cache

import pandas as pd

from bd_data_fetcher.api.umap_models import RNAGeneExpressionData
from bd_data_fetcher.data_handlers.base_handler import BaseDataHandler
from bd_data_fetcher.data_handlers.utils import SheetNames

logger = logging.getLogger(__name__)


class GeneExpressionDataHandler(BaseDataHandler):
    """
    This class is responsible for handling gene expression data.

    It has 3 parts:

    - Retrieval of normal gene expression
    - Retrieval of all gene expression data for a given study
    - Calculating tumor/normal ratios for all primary_sites

    Each function is responsible for generating a sheet in the excel file.

    The excel file is generated in the same directory as the script that calls this class.

    The sheet names are:

    - normal_gene_expression
    - gene_expression
    - gene_tumor_normal_ratios
    """

    def _retrieve_normal_gene_expression(
        self, uniprotkb_ac: str
    ) -> list[RNAGeneExpressionData]:
        """
        Retrieve normal gene expression data for a given uniprotkb_ac.

        Args:
            uniprotkb_ac: The uniprotkb_ac of the protein to retrieve normal gene expression data for.

        Returns:
            A list of RNAGeneExpressionData objects.
        """
        try:
            all_data = self.umap_client._get_rna_gene_expression_data(
                uniprotkb_acs=[uniprotkb_ac]
            )
            return [obj for obj in all_data if not obj.is_cancer]
        except Exception as e:
            logger.exception(f"Error in API call for {uniprotkb_ac}: {e}")
            return []

    @lru_cache
    def get_all_primary_sites(self) -> list[str]:
        """
        Get all possible primary_sites.
        """
        return self.umap_client._get_all_primary_sites()

    def _retrieve_gene_expression_data(
        self, uniprotkb_ac: str
    ) -> list[RNAGeneExpressionData]:
        """
        Retrieve all gene expression data for a given study.

        Args:
            study: The study to retrieve gene expression data for.

        Returns:
            A list of RNAGeneExpressionData objects.
        """
        try:
            return self.umap_client._get_rna_gene_expression_data(uniprotkb_acs=[uniprotkb_ac])
        except Exception as e:
            logger.exception(f"Error in API call for {uniprotkb_ac}: {e}")
            return []

    def build_normal_gene_expression_sheet(self, uniprotkb_ac: str, file_path: str):
        """
        Build a normal gene expression sheet for a given uniprotkb_ac.
        """
        sheet_name = SheetNames.NORMAL_GENE_EXPRESSION.value

        # Retrieve normal gene expression data
        normal_gene_expression = self._retrieve_normal_gene_expression(uniprotkb_ac)
        normal_df = pd.DataFrame([obj.dict() for obj in normal_gene_expression])

        # Use the matrix sheet creation method
        return self._create_matrix_sheet(
            file_path=file_path,
            sheet_name=sheet_name,
            data_df=normal_df,
            group_field="primary_site",
            value_field="expression_value",
            gene_field="symbol",
            gene_column_name="Gene",
        )

        return normal_df

    def build_gene_expression_sheet(self, uniprotkb_ac: str, file_path: str):
        """
        Build a gene expression sheet for a given study.
        Stores all gene expression data in the Excel sheet, appending to existing data.
        """
        sheet_name = SheetNames.GENE_EXPRESSION.value
        columns = ["Gene", "Expression Value", "Primary Site", "Is Cancer"]

        # Manage Excel sheet
        self._manage_excel_sheet(file_path, sheet_name, columns)

        # Retrieve gene expression data
        gene_expression = self._retrieve_gene_expression_data(uniprotkb_ac)
        data_df = pd.DataFrame([obj.dict() for obj in gene_expression])

        if not data_df.empty:
            # Transform data using common method
            column_mapping = {
                "Gene": "symbol",
                "Expression Value": "expression_value",
                "Primary Site": "primary_site",
                "Is Cancer": "is_cancer",
            }
            transformed_df = self._transform_data_to_sheet_format(
                data_df, column_mapping
            )

            # Append to Excel sheet
            self._append_to_excel_sheet(file_path, sheet_name, transformed_df, columns)

        return data_df

    def build_gene_tumor_normal_ratios_sheet(self, uniprotkb_ac: str, file_path: str):
        """
        Build a gene tumor normal ratios sheet for a given uniprotkb_ac.
        Calculates tumor/normal ratios for each primary site and stores them in the sheet.
        """
        sheet_name = SheetNames.GENE_TUMOR_NORMAL_RATIOS.value

        # Retrieve gene expression data (contains both normal and tumor data)
        all_gene_expression = self._retrieve_gene_expression_data(uniprotkb_ac)

        # Convert to DataFrame
        all_df = pd.DataFrame([obj.dict() for obj in all_gene_expression])

        if not all_df.empty:
            # Separate normal and tumor data from the same dataset
            normal_df = all_df[all_df["is_cancer"] is False]
            tumor_df = all_df[all_df["is_cancer"] is True]

            if not normal_df.empty and not tumor_df.empty:
                # Calculate average normal expression per primary site
                normal_avg = normal_df.groupby("primary_site")[
                    "expression_value"
                ].mean()

                # Calculate average tumor expression per primary site
                tumor_avg = tumor_df.groupby("primary_site")["expression_value"].mean()

                # Calculate tumor/normal ratios (tumor - normal)
                # Only calculate ratios for primary sites that have both normal and tumor data
                common_sites = set(normal_avg.index) & set(tumor_avg.index)
                ratios = pd.Series(index=common_sites)

                for site in common_sites:
                    ratios[site] = tumor_avg[site] - normal_avg[site]

                # Get gene symbol
                gene_symbol = normal_df["symbol"].iloc[0] if not normal_df.empty else ""

                # Create a DataFrame with the ratio data for matrix processing
                ratio_data = []
                for site, ratio in ratios.items():
                    ratio_data.append(
                        {
                            "primary_site": site,
                            "ratio_value": ratio,
                            "symbol": gene_symbol,
                        }
                    )

                ratio_df = pd.DataFrame(ratio_data)

                # Use the matrix sheet creation method
                return self._create_matrix_sheet(
                    file_path=file_path,
                    sheet_name=sheet_name,
                    data_df=ratio_df,
                    group_field="primary_site",
                    value_field="ratio_value",
                    gene_field="symbol",
                    gene_column_name="Gene",
                )

        return all_df
