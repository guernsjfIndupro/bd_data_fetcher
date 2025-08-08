import pandas as pd
import structlog

from bd_data_fetcher.api.umap_models import (
    ExternalProteinExpressionData,
    ProteomicsNormalExpressionData,
)
from bd_data_fetcher.data_handlers.base_handler import BaseDataHandler
from bd_data_fetcher.data_handlers.utils import FileNames

logger = structlog.get_logger(__name__)

regular_studies = {
    "Prospective Breast BI Proteome": "Breast Invasive Carcinoma",
    "NCC iCC - Proteome": "Cholangiocarcinoma",
    "CPTAC CCRCC Discovery Study - Proteome": "Clear Cell Renal Cell Carcinoma",
    "Proteogenomic Analysis of Human Colon Cancer Reveals New Therapeutic Opportunities": "Colon",
    "Prospective Colon PNNL Proteome Qeplus": "Colon Adenocarcinoma",
    "Proteogenomic Characterization of Endometrial Carcinoma": "endometrial carcinoma",
    "Large-scale and high-resolution mass spectrometry-based proteomics profiling defines molecular subtypes of esophageal cancer for therapeutic targeting ": "Esophageal",
    "CPTAC GBM Discovery Study - Proteome": "Glioblastoma",
    "CPTAC HNSCC Discovery Study - Proteome": "Head and Neck Squamous Cell Carcinoma",
    "HBV-Related Hepatocellular Carcinoma - Proteome": "Hepatocellular Carcinoma",
    "CPTAC LUAD Confirmatory Study - Proteome": "Lung Adenocarcinoma",
    "CPTAC LSCC Discovery Study - Proteome": "Lung Squamous Cell Carcinoma",
    "CPTAC non-ccRCC Study - Proteome": "Non-Clear Cell Renal Cell Carcinoma",
    "CGU OSCC APOBEC3A - Proteome": "Oral Squamous Cell Carcinoma",
    "Prospective Ovarian JHU Proteome": "Ovarian Serous Cystadenocarcinoma",
    "CPTAC PDA Discovery Study - Proteome": "Pancreatic Ductal Adenocarcinoma",
    "Proteogenomic characterization of small cell lung cancer identifies biological insights and subtype- specific therapeutic strategies": "small cell lung cancer",
    "CPTAC UCEC Discovery Study - Proteome": "Uterine Corpus Endometrial Carcinoma"
}

tumor_normal_studies = {
    "Proteogenomics of Gastric Cancer - Proteome": "Early Onset Gastric Cancer"
}


class ExternalProteinExpressionDataHandler(BaseDataHandler):

    def get_normal_proteomics_data(
        self, uniprotkb_ac: str
    ) -> list[ProteomicsNormalExpressionData]:
        """
        Get the normal proteomics data for a given uniprotkb_ac.
        """
        try:
            return self.umap_client._get_proteomics_normal_expression_data(uniprotkb_ac=uniprotkb_ac)
        except Exception as e:
            logger.exception(f"Error in API call for {uniprotkb_ac}: {e}")
            return []

    def build_normal_proteomics_csv(self, uniprotkb_ac: str, folder_path: str):
        """
        Build a normal proteomics CSV file for a given uniprotkb_ac.
        Creates a matrix where each row represents a gene and each column represents an indication.
        """
        file_name = FileNames.NORMAL_PROTEOMICS_DATA.value

        # Retrieve normal proteomics data
        normal_proteomics_data = self.get_normal_proteomics_data(uniprotkb_ac)
        data_df = pd.DataFrame([obj.dict() for obj in normal_proteomics_data])

        # Use the matrix CSV creation method
        if data_df.empty:
            logger.warning(f"No normal proteomics data found for {uniprotkb_ac}")
            return None

        return self._create_matrix_csv(
            folder_path=folder_path,
            file_name=file_name,
            data_df=data_df,
            group_field="indication",
            value_field="log2_expression",
            gene_field="protein_symbol",
            gene_column_name="Gene",
        )

    def get_external_proteomics_data(
        self, uniprotkb_acs: list[str], study_ids: list[int] | None = None
    ) -> list[ExternalProteinExpressionData]:
        """
        Get external proteomics data for given uniprotkb_acs and study_ids.
        """
        try:
            return self.umap_client._get_external_proteomics_data(
                uniprotkb_acs=uniprotkb_acs,
                study_ids=study_ids or []
            )
        except Exception as e:
            logger.exception(f"Error in API call for external proteomics data: {e}")
            return []

    def build_study_specific_csv(self, uniprotkb_ac: str, folder_path: str):
        """
        Build a study-specific CSV file for a given uniprotkb_ac.
        Creates a matrix where each row represents a gene and each column represents a study-indication combination,
        with values being tumor-normal ratios (tumor - normal) for each study-indication.
        """
        file_name = FileNames.STUDY_SPECIFIC_DATA.value

        # Get study metadata to map study names to study IDs
        try:
            study_metadata_response = self.umap_client._get_study_metadata()
        except Exception as e:
            logger.exception(f"Error in API call for study metadata: {e}")
            return None

        # Create mapping from study names to study IDs for regular studies and tumor_normal_studies
        study_name_to_id = {}
        for study in study_metadata_response.data:
            if study.study_name in regular_studies or study.study_name in tumor_normal_studies:
                study_name_to_id[study.study_name] = study.id

        # Get study IDs for the studies we want to include
        study_ids = list(study_name_to_id.values())

        if not study_ids:
            logger.warning("No matching studies found in study metadata")
            return None

        # Get external proteomics data for the specified studies
        external_data = self.get_external_proteomics_data(
            uniprotkb_acs=[uniprotkb_ac],
            study_ids=study_ids
        )

        # Filter data to only include studies and indications from regular_studies and tumor_normal_studies
        filtered_data = []
        for data_point in external_data:
            # Check if the study name matches a key in regular_studies
            if data_point.study_name in regular_studies:
                # Check if the indication matches the value for this study
                expected_indication = regular_studies[data_point.study_name]
                if data_point.indication.strip() == expected_indication.strip():
                    filtered_data.append(data_point)
            # Check if the study name matches a key in tumor_normal_studies
            elif data_point.study_name in tumor_normal_studies:
                # Check if the indication matches the value for this study
                expected_indication = tumor_normal_studies[data_point.study_name]
                if data_point.indication.strip() == expected_indication.strip():
                    filtered_data.append(data_point)

        if not filtered_data:
            logger.info(f"No external proteomics data found for uniprotkb_ac: {uniprotkb_ac} in configured studies")
            return None

        # Convert to DataFrame
        data_df = pd.DataFrame([obj.dict() for obj in filtered_data])

        # Log overall tissue type summary
        if not data_df.empty:
            data_df['tissue_type'].value_counts()

            # Log tissue counts per study
            for study_name in data_df['study_name'].unique():
                study_data = data_df[data_df['study_name'] == study_name]
                study_data['tissue_type'].value_counts()

        # Calculate tumor-normal differences for each protein grouped by study
        results = []

        # Process regular studies (calculate tumor-normal differences)
        for study_name in regular_studies.keys():
            study_id = study_name_to_id.get(study_name)
            if not study_id:
                continue

            # Filter data for this study
            study_data = data_df[data_df['study_name'] == study_name]

            if study_data.empty:
                continue

            # Calculate average tumor and average normal values
            tumor_data = study_data[study_data['tissue_type'].str.contains('Tumor', case=False, na=False)]
            normal_data = study_data[study_data['tissue_type'].str.contains('Normal', case=False, na=False)]

            # Log tissue type counts for this study
            study_data['tissue_type'].value_counts()

            if not tumor_data.empty and not normal_data.empty:
                avg_tumor = tumor_data['value'].mean()
                avg_normal = normal_data['value'].mean()
                tumor_normal_diff = avg_tumor - avg_normal

                # Get the symbol (should be the same for all rows in this study)
                symbol = study_data['symbol'].iloc[0]

                results.append({
                    'symbol': symbol,
                    'study_name': study_name,
                    'indication': regular_studies[study_name],
                    'tumor_normal_diff': tumor_normal_diff,
                    'avg_tumor': avg_tumor,
                    'avg_normal': avg_normal,
                    'num_tumor_samples': len(tumor_data),
                    'num_normal_samples': len(normal_data)
                })

        # Process tumor_normal_studies (already in tumor-normal format, just average them)
        for study_name in tumor_normal_studies.keys():
            study_id = study_name_to_id.get(study_name)
            if not study_id:
                continue

            # Filter data for this study
            study_data = data_df[data_df['study_name'] == study_name]

            if study_data.empty:
                continue

            # For tumor_normal_studies, the data is already in tumor-normal format
            # Just calculate the average of all values
            avg_tumor_normal = study_data['value'].mean()

            # Get the symbol (should be the same for all rows in this study)
            symbol = study_data['symbol'].iloc[0]

            results.append({
                'symbol': symbol,
                'study_name': study_name,
                'indication': tumor_normal_studies[study_name],
                'sample_type': 'tumor_normal',
                'tumor_normal_diff': avg_tumor_normal,
                'avg_tumor': None,  # Not applicable for tumor_normal_studies
                'avg_normal': None,  # Not applicable for tumor_normal_studies
                'num_tumor_samples': len(study_data),  # Total samples
                'num_normal_samples': 0  # Not applicable for tumor_normal_studies
            })

        if not results:
            logger.info(f"No external proteomics data available for tumor-normal calculations for uniprotkb_ac: {uniprotkb_ac}")
            return None

        # Create results DataFrame
        results_df = pd.DataFrame(results)

        # Use the matrix CSV creation method
        return self._create_matrix_csv(
            folder_path=folder_path,
            file_name=file_name,
            data_df=results_df,
            group_field="indication",
            value_field="tumor_normal_diff",
            gene_field="symbol",
            gene_column_name="Gene",
        )
