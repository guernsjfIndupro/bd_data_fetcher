import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OncLineageEnum(enum.Enum):
    LUNG = "Lung"
    NORMAL = "Normal"
    EYE = "Eye"
    BONE = "Bone"
    VULVA_VAGINA = "Vulva/Vagina"
    LYMPHOID = "Lymphoid"
    OTHER = "Other"
    LIVER = "Liver"
    FIBROBLAST = "Fibroblast"
    UTERUS = "Uterus"
    THYROID = "Thyroid"
    ESOPHAGUS_STOMACH = "Esophagus/Stomach"
    TESTIS = "Testis"
    HAIR = "Hair"
    SKIN = "Skin"
    SOFTTISSUE = "Soft Tissue"
    AMPULLAOFVATER = "Ampulla of Vater"
    CERVIX = "Cervix"
    BLADDER_URINARYTRACT = "Bladder/Urinary Tract"
    KIDNEY = "Kidney"
    HEADANDNECK = "Head and Neck"
    BOWEL = "Bowel"
    BILIARYTRACT = "Biliary Tract"
    CNS_BRAIN = "CNS/Brain"
    PANCREAS = "Pancreas"
    OVARY_FALLOPIANTUBE = "Ovary/Fallopian Tube"
    ADRENALGLAND = "Adrenal Gland"
    PLEURA = "Pleura"
    PERIPHERALNERVOUSSYSTEM = "Peripheral Nervous System"
    EMBRYONAL = "Embryonal"
    BREAST = "Breast"
    PROSTATE = "Prostate"
    MUSCLE = "Muscle"
    MYELOID = "Myeloid"
    UNKNOWN = "Unknown"


# Pydantic deserialzation models
class CellLineProteomicsData(BaseModel):
    intensity: float
    normalized_intensity: float
    intensity_ranking: int | None = None
    weight_normalized_intensity_ranking: int | None = None
    symbol: str
    uniprotkb_ac: str
    experiment_type: str
    cell_line_name: str
    onc_lineage: OncLineageEnum
    onc_subtype: str | None = None
    title: str | None = None
    copies_per_cell: float
    is_mapped: bool | None = None


class CellLineData(BaseModel):
    ccle_model_id: str | None = None
    rrid: str | None = None
    name: str
    ccle_name: str | None = None
    onc_lineage: OncLineageEnum | None = None
    onc_primary_disease: str | None = None
    onc_subtype: str | None = None
    experiment_count: int


class ReciprocalMicroMapData(BaseModel):
    target_name: str
    cell_source_name: str
    onc_lineage: str
    chemistry: str
    id: int
    log2_fc: float | None = None
    nlog10_pvalue: float | None = None
    proximal_uniprotkb_ac: str
    target_uniprotkb_ac: str


class TissueSampleDiaIntensity(BaseModel):
    intensity: float
    normalized_intensity: float
    intensity_ranking: int | None = None
    weight_normalized_intensity_ranking: int | None = None
    symbol: str
    uniprotkb_ac: str
    experiment_type: str
    title: str
    benchling_aliquot_registry_id: str
    benchling_human_donor_registry_id: str
    vendor_aliquot_id: str
    aliquot_name: str | None = None
    diagnosis: str | None = None
    tissue_type: str | None = None


class RNAGeneExpressionData(BaseModel):
    detailed_category: str
    expression_id: int
    expression_value: float
    gender: str
    symbol: str
    uniprotkb_ac: str
    primary_disease_or_tissue: str
    primary_site: str
    tcga_primary_site: str
    sample_name: str
    sample_type: str
    study: str
    is_cancer: bool


class ProteomicsNormalExpressionData(BaseModel):
    id: int
    copies_per_cell: float
    indication: str
    protein_symbol: str
    protein_uniprotkb_ac: str


class ExternalProteinExpressionData(BaseModel):
    value: float
    uniprotkb_ac: str
    symbol: str
    indication: str
    tissue_type: str
    sample_name: str
    sample_type: str
    study_name: str
    study_id: int | None = None
    paired_sample_group: str | None = None


class DepMapData(BaseModel):
    protein_symbol: str
    uniprotkb_ac: str
    cell_line_name: str
    onc_lineage: str
    onc_primary_disease: str
    onc_subtype: str | None = None
    tpm_log2: float
    gene_level_copy_number: float | None = None


class DepMapResponse(BaseModel):
    current_page: int
    next_page: int | None = None
    page_size: int
    total_items: int
    total_pages: int
    data: list[DepMapData]


# Replicate Sets Models
class Protein(BaseModel):
    uniprotkb_ac: str
    symbol: str
    mass_da: float
    aa_res_length: int
    is_isoform: bool
    canonical_protein: str | None = None
    pdb: str | None = None
    pubmeb_ids: str | None = None
    max_drug_targetability: str | None = None
    sequence: str | None = None
    id: int


class Target(BaseModel):
    name: str
    description: str | None = None
    proteins: list[Protein]
    type: str
    id: int


class ProcessedDataObject(BaseModel):
    object_type: str
    s3_bucket: str
    s3_key: str
    errors: str | None = None
    id: int


class Experiment(BaseModel):
    id: int
    description: str
    raw_data_object_id: int | None = None


class Analysis(BaseModel):
    id: int
    flyte_execution_name: str
    flyte_launchplan_version: str
    flyte_workflow_name: str
    flyte_workflow_project: str
    flyte_workflow_domain: str
    requested_by_azure_user: str | None = None
    status: str
    prominence: str
    replicate_set_id: int
    warning_message: str | None = None


class CellLine(BaseModel):
    ccle_model_id: str | None = None
    rrid: str | None = None
    name: str
    ccle_name: str | None = None
    onc_lineage: str | None = None
    onc_primary_disease: str | None = None
    onc_subtype: str | None = None
    age: int | None = None
    sex: str | None = None
    collection_site: str | None = None
    type: str | None = None
    growth_pattern: str | None = None
    source: str | None = None
    engineering_type: str | None = None
    engineering_description: str | None = None
    id: int


class CellSource(BaseModel):
    name: str
    id: int
    cell_lines: list[CellLine]
    immune_cell_sample_pools: list = []  # Empty list as per example
    dissociated_tumor_cells: list = []  # Empty list as per example


class Binder(BaseModel):
    entity_registry_id: str
    name: str
    web_url: str
    display_name: str
    protein_complex: str | None
    antigen_targets: str | None
    type: str
    benchling_created_date: datetime
    created_at: datetime
    updated_at: datetime
    id: int


class ReplicateSet(BaseModel):
    description: str | None = None
    id: int
    target: Target
    cell_line: str | None = None
    cell_source_id: int
    binder: Binder | None = None
    chemistry: str
    processed_data_object: ProcessedDataObject | None = None
    replicate_column_prefix: str
    control_column_prefix: str
    num_control_columns: int | None = None
    num_experimental_columns: int | None = None
    valid: bool | None = None
    internal_dev_valid: bool | None = None
    invalidation_reason: str | None = None
    azure_user_invalidator: str | None = None
    experiment: Experiment
    analyses: list[Analysis]
    cell_source: CellSource


class ReplicateSetsResponse(BaseModel):
    current_page: int
    next_page: int | None = None
    page_size: int
    total_items: int
    total_pages: int
    data: list[ReplicateSet]


# Analysis Results Models
class AnalysisResult(BaseModel):
    id: int
    log2_fc: float
    nlog10_pvalue: float
    number_of_peptides: int
    protein_id: int
    analysis_id: int
    analysis: Analysis
    protein: Protein


class AnalysisResultsResponse(BaseModel):
    current_page: int
    next_page: int | None = None
    page_size: int
    total_items: int
    total_pages: int
    data: list[AnalysisResult]


# Study Metadata Models
class StudyMetadata(BaseModel):
    id: int
    study_name: str
    link: str | None = None
    clinical_data_context: str | None = None
    experiment_type: str | None = None
    study_type: str | None = None
    pdc_study_id: str | None = None
    study_id: str | None = None
    study_submitter_id: str | None = None
    project_name: str | None = None
    program_name: str | None = None
    authors: str | None = None
    normalization_method: str | None = None
    additional_column_metadata: dict[str, Any] | None = None
    num_of_samples: int


class StudyMetadataResponse(BaseModel):
    current_page: int
    next_page: int
    page_size: int
    total_items: int
    total_pages: int
    data: list[StudyMetadata]
