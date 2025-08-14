"""Shared colors for graph visualization."""

import matplotlib.pyplot as plt
import numpy as np


class TumorNormalColors:
    """Colors for tumor vs normal tissue."""
    
    NORMAL = '#2ecc71'  # Green
    TUMOR = '#e74c3c'   # Red
    
    @classmethod
    def get_palette(cls):
        """Get colors as list for seaborn/matplotlib."""
        return [cls.NORMAL, cls.TUMOR]


class OncLineageColors:
    """Colors for onc lineages."""
    
    # Predefined colors for each OncLineageEnum value
    LINEAGE_COLORS = {
        'Lung': '#ff7f0e',                    # Orange
        'Normal': '#2ecc71',                  # Green
        'Eye': '#9467bd',                     # Purple
        'Bone': '#8c564b',                    # Brown
        'Vulva/Vagina': '#e377c2',            # Pink
        'Lymphoid': '#17becf',                # Cyan
        'Other': '#7f7f7f',                   # Gray
        'Liver': '#d62728',                   # Red
        'Fibroblast': '#bcbd22',              # Olive
        'Uterus': '#1f77b4',                  # Blue
        'Thyroid': '#ff9896',                 # Light red
        'Esophagus/Stomach': '#98df8a',       # Light green
        'Testis': '#ffbb78',                  # Light orange
        'Hair': '#c5b0d5',                    # Light purple
        'Skin': '#c49c94',                    # Light brown
        'Soft Tissue': '#f7b6d2',             # Light pink
        'Ampulla of Vater': '#c7c7c7',        # Light gray
        'Cervix': '#dbdb8d',                  # Light olive
        'Bladder/Urinary Tract': '#9edae5',   # Light cyan
        'Kidney': '#aec7e8',                  # Light blue
        'Head and Neck': '#ff7f0e',           # Orange
        'Bowel': '#2ca02c',                   # Green
        'Biliary Tract': '#d62728',           # Red
        'CNS/Brain': '#9467bd',               # Purple
        'Pancreas': '#8c564b',                # Brown
        'Ovary/Fallopian Tube': '#e377c2',    # Pink
        'Adrenal Gland': '#17becf',           # Cyan
        'Pleura': '#bcbd22',                  # Olive
        'Peripheral Nervous System': '#1f77b4', # Blue
        'Embryonal': '#ff9896',               # Light red
        'Breast': '#98df8a',                  # Light green
        'Prostate': '#ffbb78',                # Light orange
        'Muscle': '#c5b0d5',                  # Light purple
        'Myeloid': '#c49c94',                 # Light brown
        'Unknown': '#7f7f7f',                 # Gray
    }
    
    @classmethod
    def get_color_map(cls, lineages):
        """Get color mapping for lineages using predefined colors."""
        color_map = {}
        for lineage in lineages:
            if lineage in cls.LINEAGE_COLORS:
                color_map[lineage] = cls.LINEAGE_COLORS[lineage]
            else:
                # Fallback to Set3 colormap for unknown lineages
                colors = plt.cm.Set3(np.linspace(0, 1, len([lineage])))
                color_map[lineage] = colors[0]
        return color_map


class ProteinColors:
    """Colors for specific proteins."""
    
    ANCHOR = '#e74c3c'    # Red for anchor protein
    TAPA = '#ff8c00'      # Distinct orange for TAPA protein
    
    @classmethod
    def get_color(cls, protein_name):
        """Get color for a specific protein."""
        if protein_name.lower() == 'tapa':
            return cls.TAPA
        else:
            return cls.ANCHOR  # Default to anchor color for other proteins








