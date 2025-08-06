"""Utility functions and constants for data handlers."""

from enum import Enum


class SheetNames(Enum):
    """Enum for Excel sheet names to ensure consistency across the codebase."""

    # DepMap data
    DEPMAP_DATA = "depmap_data"

    # External Protein Expression data
    NORMAL_PROTEOMICS_DATA = "normal_proteomics_data"
    EXTERNAL_PROTEOMICS_DATA = "external_proteomics_data"

    # Gene Expression data
    NORMAL_GENE_EXPRESSION = "normal_gene_expression"
    GENE_EXPRESSION = "gene_expression"
    GENE_TUMOR_NORMAL_RATIOS = "gene_tumor_normal_ratios"

    # Internal WCE data
    WCE_DATA = "wce_data"
    CELL_LINE_SIGMOIDAL_CURVES = "cell_line_sigmoidal_curves"

    # UMap data
    UMAP_DATA = "umap_data"
    CELL_LINE_TARGETING = "cell_line_targeting"

    @classmethod
    def get_all_sheet_names(cls) -> list[str]:
        """Get all sheet names as a list of strings.

        Returns:
            List of all sheet names
        """
        return [sheet.value for sheet in cls]

    @classmethod
    def get_sheet_names_by_category(cls, category: str) -> list[str]:
        """Get sheet names for a specific category.

        Args:
            category: Category name (e.g., 'depmap', 'gene_expression', 'wce', 'umap')

        Returns:
            List of sheet names for the specified category
        """
        category_mapping = {
            "depmap": [cls.DEPMAP_DATA],
            "external_protein_expression": [cls.NORMAL_PROTEOMICS_DATA, cls.EXTERNAL_PROTEOMICS_DATA],
            "gene_expression": [cls.NORMAL_GENE_EXPRESSION, cls.GENE_EXPRESSION, cls.GENE_TUMOR_NORMAL_RATIOS],
            "wce": [cls.WCE_DATA, cls.CELL_LINE_SIGMOIDAL_CURVES],
            "umap": [cls.UMAP_DATA, cls.CELL_LINE_TARGETING],
        }

        sheets = category_mapping.get(category.lower(), [])
        return [sheet.value for sheet in sheets]

    @classmethod
    def is_valid_sheet_name(cls, sheet_name: str) -> bool:
        """Check if a sheet name is valid.

        Args:
            sheet_name: Sheet name to validate

        Returns:
            True if the sheet name is valid, False otherwise
        """
        return sheet_name in cls.get_all_sheet_names()

    @classmethod
    def get_category_for_sheet(cls, sheet_name: str) -> str | None:
        """Get the category for a given sheet name.

        Args:
            sheet_name: Sheet name to get category for

        Returns:
            Category name or None if not found
        """
        category_mapping = {
            cls.DEPMAP_DATA.value: "depmap",
            cls.NORMAL_PROTEOMICS_DATA.value: "external_protein_expression",
            cls.EXTERNAL_PROTEOMICS_DATA.value: "external_protein_expression",
            cls.NORMAL_GENE_EXPRESSION.value: "gene_expression",
            cls.GENE_EXPRESSION.value: "gene_expression",
            cls.GENE_TUMOR_NORMAL_RATIOS.value: "gene_expression",
            cls.WCE_DATA.value: "wce",
            cls.CELL_LINE_SIGMOIDAL_CURVES.value: "wce",
            cls.UMAP_DATA.value: "umap",
            cls.CELL_LINE_TARGETING.value: "umap",
        }

        return category_mapping.get(sheet_name)
