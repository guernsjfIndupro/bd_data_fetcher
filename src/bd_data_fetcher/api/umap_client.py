from typing import Dict, Any, List, Optional
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from urllib.parse import urljoin

from functools import lru_cache


from .umap_models import (
    CellLineProteomicsData,
    CellLineData,
    ReciprocalMicroMapData,
    TissueSampleDiaIntensity,
    RNAGeneExpressionData,
    ProteomicsNormalExpressionData,
    ExternalProteinExpressionData,
)

logger = logging.getLogger(__name__)


class UMapServiceClient:
    """Client for interacting with the UMap service."""

    def __init__(self):
        """
        Initialize the UMap service client.
        """
        self.base_url = "https://indupro-apps.com/umap-service/api/v1/"

        if not self.base_url:
            raise ValueError("Base URL must set in UMAP_SERVICE_URL environment variable")

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        # Production
        self.session.mount("https://", adapter)
        # Local Development
        self.session.mount("http://", adapter)

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generic GET request.

        Args:
            endpoint: API endpoint to call
            params: Optional query parameters

        Returns:
            Response data
        """
        self.endpoint_url = self.base_url + endpoint
        response = self.session.get(self.endpoint_url, params=params)
        response.raise_for_status()
        return response.json()

    def _post(
        self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generic POST request.

        Args:
            endpoint: API endpoint to call
            data: Data to send in the request body

        Returns:
            Response data
        """
        self.endpoint_url = self.base_url + endpoint
        response = self.session.post(self.endpoint_url, json=data, params=params)
        response.raise_for_status()
        return response.json()

    def _get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Generic paginated GET request.

        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            page_size: Number of items per page
            max_pages: Maximum number of pages to retrieve (None for all)

        Returns:
            List of all items across all pages
        """
        if params is None:
            params = {}

        params["page_size"] = page_size
        params["page_request"] = 1

        all_items = []
        has_more = True

        while has_more:
            response = self._get(endpoint, params)

            items = response.get("data", [])
            all_items.extend(items)

            params["page_request"] = response.get("next_page")
            has_more = response.get("next_page") >= 1

        return all_items

    def _post_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        page_size: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generic paginated GET request.

        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            page_size: Number of items per page
            max_pages: Maximum number of pages to retrieve (None for all)

        Returns:
            List of all items across all pages
        """

        if params is None:
            params = {}

        params["page_size"] = page_size
        params["page_request"] = 1

        all_items = []
        has_more = True

        while has_more:
            response = self._post(endpoint, data=data, params=params)

            items = response.get("data", [])
            all_items.extend(items)
            params["page_request"] = response.get("next_page")
            has_more = response.get("next_page") >= 1

        return all_items

    def _get_reciprocal_micro_map_data(
        self, target_uniprotkb_ac: str, proximal_uniprotkb_ac: str
    ) -> List[Dict[str, Any]]:
        """
        Get reciprocal micro map data from the UMap service.
        """
        unvalidated_data = self._post_paginated(
            "replicate-sets/reciprocal_micro_map",
            params={
                "target_uniprotkb_ac": target_uniprotkb_ac,
                "proximal_uniprotkb_ac": proximal_uniprotkb_ac,
            },
        )

        validated_data = [ReciprocalMicroMapData(**data) for data in unvalidated_data]
        return validated_data

    @lru_cache(maxsize=10000)
    def _get_proteomics_cell_line_data(self, uniprotkb_ac: str) -> List[CellLineProteomicsData]:
        """
        Get cell line data from the UMap service.
        """
        endpoint = "dia/cell-line"

        unvalidated_data = self._get_paginated(
            endpoint=endpoint, params={"uniprotkb_ac": uniprotkb_ac}
        )
        validated_data = [CellLineProteomicsData(**data) for data in unvalidated_data]
        return validated_data

    def _get_proteomics_tissue_data(self, uniprotkb_ac: str) -> List[TissueSampleDiaIntensity]:
        """
        Get proteomics tissue data from the UMap service.
        """
        endpoint = "dia/tissue-sample"
        unvalidated_data = self._get_paginated(
            endpoint=endpoint, params={"uniprotkb_ac": uniprotkb_ac}
        )
        validated_data = [TissueSampleDiaIntensity(**data) for data in unvalidated_data]
        return validated_data

    def _get_all_proteomics_tissue_data(
        self, tissue_type: str, experiment_type: str
    ) -> List[TissueSampleDiaIntensity]:
        """
        Get proteomics tissue data from the UMap service.
        """
        endpoint = "dia/tissue-sample/tissue-type"
        unvalidated_data = self._post_paginated(
            endpoint=endpoint,
            params={"tissue_type": tissue_type, "experiment_type": experiment_type},
        )
        validated_data = [TissueSampleDiaIntensity(**data) for data in unvalidated_data]
        return validated_data

    @lru_cache(maxsize=10000)
    def _get_proteomics_cell_lines(self) -> List[CellLineData]:
        """
        Get all proteomics cell lines from the UMap service.
        """
        endpoint = "dia/cell-lines/WHOLE_CELL_EXTRACT"
        unvalidated_data = self._get(endpoint=endpoint)
        validated_data = [CellLineData(**data) for data in unvalidated_data]
        return validated_data

    def _get_rna_gene_expression_data(
        self, uniprotkb_acs: List[str]
    ) -> List[RNAGeneExpressionData]:
        """
        Get RNA gene expression data from the UMap service.

        NOTE: This table is not expected to be present locally,
        We will need to retrieve the data from production.
        This table is ~99% of our data so it is not restored locally
        in the umap service.
        """
        endpoint = "pancancer/"
        body = {
            "uniprotkb_acs": uniprotkb_acs,
            "ensembl_ids": [],
            "primary_sites": [],
            "sample_types": [],
        }
        # Use paginated POST request to get all data
        unvalidated_data = self._post_paginated(endpoint=endpoint, data=body, page_size=1000)
        validated_data = [RNAGeneExpressionData(**data) for data in unvalidated_data]
        return validated_data

    def _get_proteomics_normal_expression_data(
        self, uniprotkb_ac: str
    ) -> List[ProteomicsNormalExpressionData]:
        """
        Get proteomics normal expression data from the UMap service.
        """
        endpoint = "normal-expression/protein"
        params = {
            "uniprotkb_ac": uniprotkb_ac,
        }
        unvalidated_data = self._get(endpoint=endpoint, params=params)
        validated_data = [ProteomicsNormalExpressionData(**data) for data in unvalidated_data]
        return validated_data

    def _get_proteomics_normal_expression_data_bounds(self) -> Dict[str, float]:
        """
        Get proteomics normal expression data bounds from the UMap service.
        """
        endpoint = "normal-expression/bounds"
        return self._get(endpoint=endpoint)

    def _get_gtex_normal_rna_expression_data_bounds(
        self, studies: List[str], is_cancer: bool
    ) -> Dict[str, float]:
        """
        Get GTEx normal RNA expression data bounds from the UMap service.
        """
        params = {
            "is_cancer": is_cancer,
        }

        endpoint = "pancancer/bounds"
        return self._post(endpoint=endpoint, data=studies, params=params)

    def _get_external_proteomics_data(
        self, uniprotkb_acs: List[str]
    ) -> List[ExternalProteinExpressionData]:
        """
        Get external proteomics data from the UMap service.
        """
        params = {
            "uniprotkb_acs": uniprotkb_acs,
        }
        endpoint = "external/study/data"
        unvalidated_data = self._get_paginated(endpoint=endpoint, params=params)
        validated_data = [ExternalProteinExpressionData(**data) for data in unvalidated_data]
        return validated_data

    def _get_all_primary_sites(self) -> List[str]:
        """
        Get all possible primary_sites.
        """
        endpoint = "pancancer/indications"
        return self._get(endpoint=endpoint)

    def map_protein(self, gene_symbols: List[str]) -> Dict[str, str]:
        """
        Map gene symbols to UniProtKB accession numbers.
        
        Args:
            gene_symbols: List of gene symbols to map
            
        Returns:
            Dictionary mapping symbols to uniprotkb_ac
        """
        endpoint = "proteins/mapping"
        
        # Prepare request body matching the curl command
        body = {
            "protein_ids": [],
            "uniprotkb_acs": [],
            "symbols": gene_symbols
        }
        
        # Make the POST request
        response = self._post(endpoint=endpoint, data=body)
        mappings = {}
        
        # Extract the data from the response
        if "data" in response:
            # Create mapping dictionary: symbol -> uniprotkb_ac
            
            for protein_data in response["data"]:
                uniprotkb_ac = protein_data.get("uniprotkb_ac")
                primary_symbol = protein_data.get("primary_symbol")
                
                if uniprotkb_ac and primary_symbol:
                    mappings[primary_symbol] = uniprotkb_ac
            
        return mappings

