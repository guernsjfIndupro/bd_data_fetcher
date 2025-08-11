# Data Directory Structure

This directory contains multiple folders containing data about a collection of proteins. This file explains what each file in those folders contains.

## Data Files Overview

The following CSV files are generated for each protein analysis:

### Gene Expression Data

#### `gene_tumor_normal_ratios.csv`
This file contains gene expression ratios comparing tumor tissue to normal tissue across different cancer types. The data shows how gene expression levels differ between cancerous and normal tissues.

**Headers:**
- **Gene**: Gene symbol of a protein
- **Cancer Indications**: A series of cancer indication columns with ratio values

#### `gene_expression.csv`
This file contains gene expression data with expression values for various genes across different tissue types and cancer status.

**Headers:**
- **Gene**: Gene symbol of a protein
- **Expression Value**: Log2 expression value
- **Primary Site**: Site of the cancer sample
- **Is Cancer**: Boolean value indicating if this sample was cancerous

#### `normal_gene_expression.csv`
This file contains gene expression data specifically from normal (non-cancerous) tissues across various anatomical sites.

**Headers:**
- **Gene**: Gene symbol of a protein
- **Cancer Indications**: A series of cancer indication columns with normal expression values

### Proteomics Data

#### `study_specific_data.csv`
This file contains study-specific protein expression data across different cancer types and subtypes from specific research studies.

**Headers:**
- **Gene**: Gene symbol of a protein
- **Cancer Indications**: A series of cancer indication columns with study-specific expression values

#### `protein_expression.csv`
This file contains protein expression data from various studies, including different tissue types and sample information.

**Headers:**
- **Protein**: Gene symbol
- **Expression Value**: Log2 protein expression
- **Indication**: Cancer indication
- **Tissue Type**
- **Sample Name**
- **Sample Type** 
- **Study Name**: Name of the research study

#### `normal_proteomics_data.csv`
This file contains proteomics data from normal tissues across various sites.

**Headers:**
- **Gene**: Gene symbol of a protein
- **Cancer Indications**: A series of cancer indication columns with normal proteomics values

### Cell Line and Dependency Data

#### `depmap_data.csv`
This file contains DepMap (Cancer Dependency Map) data showing protein expression across different cell lines with cancer lineage and disease information.

**Headers:**
- **Protein Symbol**: Gene symbol of the protein
- **UniProtKB AC**: UniProtKB accession number
- **Cell Line**: Name of the cell line
- **Onc Lineage**: Cancer lineage classification
- **Onc Primary Disease**: Primary disease classification
- **Onc Subtype**: Cancer subtype classification
- **TPM Log2**: Log2 transformed TPM (Transcripts Per Million) values

#### `wce_data.csv`
This file contains whole cell extract (WCE) data with protein intensity rankings from specific cell lines.

**Headers:**
- **Gene**: Gene symbol of a protein
- **Cell Line**: Name of the cell line
- **Onc Lineage**: Cancer lineage classification
- **Onc Subtype**: Cancer subtype classification
- **Weight Normalized Intensity Ranking**: Normalized intensity ranking
- **Experiment Type**: Type of experiment performed
- **Title**: Experiment title
- **Copies Per Cell**: Estimated protein copies per cell
- **Is Mapped**: Mapping status (currently broken, may be removed)

#### `cell_line_sigmoidal_curves.csv`
This file contains sigmoidal curve definitions for WCE DIA data for multiple cell lines.

**Headers:**
- **Cell_Line_Name**: Name of a cell line
- **Is_Y_Axis**: Boolean indicating if the data is for the X or Y axis
- **Point_0 through Point_499**: Points on the sigmoidal curve (500 total points)

### UMap Analysis Data

#### `umap_data.csv`
This file contains uMap replicate set data for targeted proteomics analysis.

**Headers:**
- **Replicate Set ID**: Unique identifier for the replicate set
- **Cell Line**: Name of the cell line
- **Chemistry**: Chemistry type used in the experiment
- **Target Protein**: Target protein identifier
- **Protein Symbol**: Gene symbol of the protein
- **Protein UniProtKB AC**: UniProtKB accession number
- **Log2 FC**: Log2 fold change value
- **P-value**: Statistical p-value
- **Number of Peptides**: Number of peptides identified
- **Binder**: Binding classification

## File Organization

Each protein folder contains these CSV files organized as follows:

```
[PROTEIN_NAME]/
├── gene_expression.csv
├── gene_tumor_normal_ratios.csv
├── normal_gene_expression.csv
├── study_specific_data.csv
├── protein_expression.csv
├── normal_proteomics_data.csv
├── depmap_data.csv
├── wce_data.csv
├── cell_line_sigmoidal_curves.csv
└── umap_data.csv
```
 