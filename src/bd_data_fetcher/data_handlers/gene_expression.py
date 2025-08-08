"""
What needs to be done here?

This one has 2 parts:

Retrieval of normal gene expression

Retrieval of all gene expression data for a given study
"""

from functools import lru_cache

import pandas as pd
import structlog

from bd_data_fetcher.api.umap_models import RNAGeneExpressionData
from bd_data_fetcher.data_handlers.base_handler import BaseDataHandler
from bd_data_fetcher.data_handlers.utils import FileNames

logger = structlog.get_logger(__name__)


class GeneExpressionDataHandler(BaseDataHandler):
    """
    This class is responsible for handling gene expression data.

    It has 3 parts:

    - Retrieval of normal gene expression
    - Retrieval of all gene expression data for a given study
    - Calculating tumor/normal ratios for all primary_sites

    Each function is responsible for generating a CSV file in the output folder.

    The CSV files are generated in the same directory as the script that calls this class.

    The file names are:

    - normal_gene_expression.csv
    - gene_expression.csv
    - gene_tumor_normal_ratios.csv
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

    def build_normal_gene_expression_csv(self, uniprotkb_ac: str, folder_path: str):
        """
        Build a normal gene expression CSV file for a given uniprotkb_ac.
        """
        file_name = FileNames.NORMAL_GENE_EXPRESSION.value

        # Retrieve normal gene expression data
        normal_gene_expression = self._retrieve_normal_gene_expression(uniprotkb_ac)
        normal_df = pd.DataFrame([obj.dict() for obj in normal_gene_expression])

        # Use the matrix CSV creation method
        return self._create_matrix_csv(
            folder_path=folder_path,
            file_name=file_name,
            data_df=normal_df,
            group_field="primary_site",
            value_field="expression_value",
            gene_field="symbol",
            gene_column_name="Gene",
        )

        return normal_df

    def build_gene_expression_csv(self, uniprotkb_ac: str, folder_path: str):
        """
        Build a gene expression CSV file for a given study.
        Stores all gene expression data in the CSV file, appending to existing data.
        """
        file_name = FileNames.GENE_EXPRESSION.value
        columns = ["Gene", "Expression Value", "Primary Site", "Is Cancer"]

        # Manage CSV file
        self._manage_csv_file(folder_path, file_name, columns)

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
            transformed_df = self._transform_data_to_csv_format(
                data_df, column_mapping
            )

            # Append to CSV file
            self._append_to_csv_file(folder_path, file_name, transformed_df, columns)

        return data_df

    def build_gene_tumor_normal_ratios_csv(self, uniprotkb_ac: str, folder_path: str):
        """
        Build a gene tumor-normal ratios CSV file for a given uniprotkb_ac.
        Creates a matrix where each row represents a gene and each column represents a primary site,
        with values being tumor-normal ratios (tumor - normal) for each primary site.
        """
        file_name = FileNames.GENE_TUMOR_NORMAL_RATIOS.value

        # Retrieve gene expression data
        gene_expression = self._retrieve_gene_expression_data(uniprotkb_ac)
        data_df = pd.DataFrame([obj.dict() for obj in gene_expression])

        if data_df.empty:
            logger.warning(f"No gene expression data found for {uniprotkb_ac}")
            return None

        # Calculate tumor-normal ratios for each primary site
        results = []
        primary_sites = data_df['primary_site'].unique()

        for primary_site in primary_sites:
            site_data = data_df[data_df['primary_site'] == primary_site]
            
            # Separate tumor and normal data
            tumor_data = site_data[site_data['is_cancer'] == True]
            normal_data = site_data[site_data['is_cancer'] == False]

            if not tumor_data.empty and not normal_data.empty:
                avg_tumor = tumor_data['expression_value'].mean()
                avg_normal = normal_data['expression_value'].mean()
                tumor_normal_ratio = avg_tumor - avg_normal

                # Get the symbol (should be the same for all rows in this primary site)
                symbol = site_data['symbol'].iloc[0]

                results.append({
                    'symbol': symbol,
                    'primary_site': primary_site,
                    'tumor_normal_ratio': tumor_normal_ratio,
                    'avg_tumor': avg_tumor,
                    'avg_normal': avg_normal,
                    'num_tumor_samples': len(tumor_data),
                    'num_normal_samples': len(normal_data)
                })

        if not results:
            logger.info(f"No gene expression data available for tumor-normal calculations for uniprotkb_ac: {uniprotkb_ac}")
            return None

        # Create results DataFrame
        results_df = pd.DataFrame(results)

        # Use the matrix CSV creation method
        return self._create_matrix_csv(
            folder_path=folder_path,
            file_name=file_name,
            data_df=results_df,
            group_field="primary_site",
            value_field="tumor_normal_ratio",
            gene_field="symbol",
            gene_column_name="Gene",
        )
