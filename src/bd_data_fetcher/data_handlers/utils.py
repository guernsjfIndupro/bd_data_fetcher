"""Utility functions and constants for data handlers."""

from enum import Enum


class FileNames(Enum):
    """Enum for CSV file names to ensure consistency across the codebase."""

    # DepMap data
    DEPMAP_DATA = "depmap_data.csv"

    # External Protein Expression data
    NORMAL_PROTEOMICS_DATA = "normal_proteomics_data.csv"
    EXTERNAL_PROTEOMICS_DATA = "external_proteomics_data.csv"
    STUDY_SPECIFIC_DATA = "study_specific_data.csv"
    PROTEIN_EXPRESSION = "protein_expression.csv"

    # Gene Expression data
    NORMAL_GENE_EXPRESSION = "normal_gene_expression.csv"
    GENE_EXPRESSION = "gene_expression.csv"
    GENE_TUMOR_NORMAL_RATIOS = "gene_tumor_normal_ratios.csv"

    # Internal WCE data
    WCE_DATA = "wce_data.csv"
    CELL_LINE_SIGMOIDAL_CURVES = "cell_line_sigmoidal_curves.csv"

    # UMap data
    UMAP_DATA = "umap_data.csv"
    CELL_LINE_TARGETING = "cell_line_targeting.csv"

    @classmethod
    def get_all_file_names(cls) -> list[str]:
        """Get all file names as a list of strings.

        Returns:
            List of all file names
        """
        return [file.value for file in cls]

    @classmethod
    def get_file_names_by_category(cls, category: str) -> list[str]:
        """Get file names for a specific category.

        Args:
            category: Category name (e.g., 'depmap', 'gene_expression', 'wce', 'umap')

        Returns:
            List of file names for the specified category
        """
        category_mapping = {
            "depmap": [cls.DEPMAP_DATA],
            "external_protein_expression": [cls.NORMAL_PROTEOMICS_DATA, cls.EXTERNAL_PROTEOMICS_DATA, cls.STUDY_SPECIFIC_DATA, cls.PROTEIN_EXPRESSION],
            "gene_expression": [cls.NORMAL_GENE_EXPRESSION, cls.GENE_EXPRESSION, cls.GENE_TUMOR_NORMAL_RATIOS],
            "wce": [cls.WCE_DATA, cls.CELL_LINE_SIGMOIDAL_CURVES],
            "umap": [cls.UMAP_DATA, cls.CELL_LINE_TARGETING],
        }

        files = category_mapping.get(category.lower(), [])
        return [file.value for file in files]

    @classmethod
    def is_valid_file_name(cls, file_name: str) -> bool:
        """Check if a file name is valid.

        Args:
            file_name: File name to validate

        Returns:
            True if the file name is valid, False otherwise
        """
        return file_name in cls.get_all_file_names()

    @classmethod
    def get_category_for_file(cls, file_name: str) -> str | None:
        """Get the category for a given file name.

        Args:
            file_name: File name to get category for

        Returns:
            Category name or None if not found
        """
        category_mapping = {
            cls.DEPMAP_DATA.value: "depmap",
            cls.NORMAL_PROTEOMICS_DATA.value: "external_protein_expression",
            cls.EXTERNAL_PROTEOMICS_DATA.value: "external_protein_expression",
            cls.STUDY_SPECIFIC_DATA.value: "external_protein_expression",
            cls.PROTEIN_EXPRESSION.value: "external_protein_expression",
            cls.NORMAL_GENE_EXPRESSION.value: "gene_expression",
            cls.GENE_EXPRESSION.value: "gene_expression",
            cls.GENE_TUMOR_NORMAL_RATIOS.value: "gene_expression",
            cls.WCE_DATA.value: "wce",
            cls.CELL_LINE_SIGMOIDAL_CURVES.value: "wce",
            cls.UMAP_DATA.value: "umap",
            cls.CELL_LINE_TARGETING.value: "umap",
        }

        return category_mapping.get(file_name)
