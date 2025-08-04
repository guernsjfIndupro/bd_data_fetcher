import enum
from typing import Optional, List
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
    intensity_ranking: Optional[int] = None
    weight_normalized_intensity_ranking: Optional[int] = None
    symbol: str
    uniprotkb_ac: str
    experiment_type: str
    cell_line_name: str
    onc_lineage: OncLineageEnum
    onc_subtype: Optional[str] = None
    title: str

class CellLineData(BaseModel):
    ccle_model_id: Optional[str] = None
    rrid: Optional[str] = None
    name: str
    ccle_name: Optional[str] = None
    onc_lineage: Optional[OncLineageEnum] = None
    onc_primary_disease: Optional[str] = None
    onc_subtype: Optional[str] = None
    experiment_count: int

class ReciprocalMicroMapData(BaseModel):
    target_name: str
    cell_source_name: str
    onc_lineage: str
    chemistry: str
    id: int
    log2_fc: Optional[float] = None
    nlog10_pvalue: Optional[float] = None
    proximal_uniprotkb_ac: str
    target_uniprotkb_ac: str

class TissueSampleDiaIntensity(BaseModel):
    intensity: float
    normalized_intensity: float
    intensity_ranking: Optional[int] = None
    weight_normalized_intensity_ranking: Optional[int] = None
    symbol: str
    uniprotkb_ac: str
    experiment_type: str
    title: str
    benchling_aliquot_registry_id: str
    benchling_human_donor_registry_id: str
    vendor_aliquot_id: str
    aliquot_name: Optional[str] = None
    diagnosis: Optional[str] = None
    tissue_type: Optional[str] = None

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
    log2_expression: float
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
    paired_sample_group: Optional[str] = None

# Replicate Sets Models
class Protein(BaseModel):
    uniprotkb_ac: str
    symbol: str
    mass_da: float
    aa_res_length: int
    is_isoform: bool
    canonical_protein: Optional[str] = None
    pdb: Optional[str] = None
    pubmeb_ids: Optional[str] = None
    max_drug_targetability: Optional[str] = None
    sequence: str
    id: int

class Target(BaseModel):
    name: str
    description: Optional[str] = None
    proteins: List[Protein]
    type: str
    id: int

class ProcessedDataObject(BaseModel):
    object_type: str
    s3_bucket: str
    s3_key: str
    errors: Optional[str] = None
    id: int

class Experiment(BaseModel):
    id: int
    description: str
    raw_data_object_id: int

class Analysis(BaseModel):
    id: int
    flyte_execution_name: str
    flyte_launchplan_version: str
    flyte_workflow_name: str
    flyte_workflow_project: str
    flyte_workflow_domain: str
    requested_by_azure_user: Optional[str] = None
    status: str
    prominence: str
    replicate_set_id: int
    warning_message: Optional[str] = None

class CellLine(BaseModel):
    ccle_model_id: Optional[str] = None
    rrid: Optional[str] = None
    name: str
    ccle_name: Optional[str] = None
    onc_lineage: Optional[str] = None
    onc_primary_disease: Optional[str] = None
    onc_subtype: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    collection_site: Optional[str] = None
    type: Optional[str] = None
    growth_pattern: Optional[str] = None
    source: Optional[str] = None
    engineering_type: Optional[str] = None
    engineering_description: Optional[str] = None
    id: int

class CellSource(BaseModel):
    name: str
    id: int
    cell_lines: List[CellLine]
    immune_cell_sample_pools: List = []  # Empty list as per example
    dissociated_tumor_cells: List = []   # Empty list as per example

class ReplicateSet(BaseModel):
    description: Optional[str] = None
    id: int
    target: Target
    cell_line: str
    cell_source_id: int
    binder: Optional[str] = None
    chemistry: str
    processed_data_object: ProcessedDataObject
    replicate_column_prefix: str
    control_column_prefix: str
    num_control_columns: int
    num_experimental_columns: int
    valid: bool
    internal_dev_valid: bool
    invalidation_reason: Optional[str] = None
    azure_user_invalidator: Optional[str] = None
    experiment: Experiment
    analyses: List[Analysis]
    cell_source: CellSource

class ReplicateSetsResponse(BaseModel):
    current_page: int
    next_page: Optional[int] = None
    page_size: int
    total_items: int
    total_pages: int
    data: List[ReplicateSet]

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
    next_page: Optional[int] = None
    page_size: int
    total_items: int
    total_pages: int
    data: List[AnalysisResult]
