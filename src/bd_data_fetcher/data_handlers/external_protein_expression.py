from ..api.umap_client import UMapServiceClient
from ..api.umap_models import RNAGeneExpressionData, CellLineProteomicsData, ProteomicsNormalExpressionData
from functools import lru_cache
from typing import List, Set
import pandas as pd
import logging
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

    def get_normal_proteomics_data(self, uniprotkb_ac: str) -> List[ProteomicsNormalExpressionData]:
        """
        Get the normal proteomics data for a given uniprotkb_ac.
        """
        return self._safe_api_call(
            self.umap_client._get_proteomics_normal_expression_data,
            uniprotkb_ac=uniprotkb_ac
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
            group_field='indication',
            value_field='log2_expression',
            gene_field='protein_symbol',
            gene_column_name='Gene'
        )

        return data_df

    def build_study_specific_sheet(self, uniprotkb_ac: str, file_path: str):

        """
        Build a study specific sheet for a given uniprotkb_ac.

        This needs some extra thought
        """
        pass

