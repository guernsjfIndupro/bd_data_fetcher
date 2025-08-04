import enum
from typing import Optional
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
