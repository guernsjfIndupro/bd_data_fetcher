import os
from collections import defaultdict

import numpy as np
import pandas as pd
import structlog
from scipy.interpolate import interp1d, splev, splrep

from bd_data_fetcher.api.umap_models import CellLineProteomicsData
from bd_data_fetcher.data_handlers.base_handler import BaseDataHandler
from bd_data_fetcher.data_handlers.utils import FileNames

logger = structlog.get_logger(__name__)


class WCEDataHandler(BaseDataHandler):
    """
    This class is responsible for handling WCE data.
    """

    def __init__(self):
        super().__init__()
        # Cache for expensive cell line data and sigmoidal curves
        self._cell_line_data_cache = {}
        self._sigmoidal_curves_cache = {}

    @staticmethod
    def build_generalizable_sigmoidal_curve(
        data: list[CellLineProteomicsData],
    ) -> list[np.ndarray]:
        """Builds a generalizable sigmoidal curve from cell line proteomics data.

        This method processes cell line proteomics data to create a standardized curve
        that represents the distribution of protein expression across cell lines. It handles
        interpolation of missing values and normalizes the data for consistent comparison.

        Args:
            data (List[CellLineProteomicsData]): List of cell line proteomics measurements,
                containing weight normalized rankings and intensities.

        Returns:
            List[np.ndarray]: A list containing two numpy arrays:
                - x-axis values representing standardized rankings (0-1000)
                - y-axis values representing log10-transformed normalized intensities
        """
        data_per_cell_line = defaultdict(list)

        for data_point in data:
            data_per_cell_line[data_point.cell_line_name].append(
                (data_point.weight_normalized_intensity_ranking, data_point.normalized_intensity)
            )

        for cell_line_name in data_per_cell_line.keys():
            data_per_cell_line[cell_line_name] = sorted(
                data_per_cell_line[cell_line_name], key=lambda x: x[0]
            )

        common_rankings = np.linspace(start=0, stop=1000, num=1001)

        weight_normalized_intensites = []

        for cell_line_name in data_per_cell_line.keys():
            # NOTE: The current implementation assumes that we have detected at least 1000
            # unique values for the weight normalized intensity ranking.
            # We interpolate the missing values.
            local_weight_normalized_intensites = [0 for i in range(1001)]

            normalized_intensity_ranking_pairs = data_per_cell_line[cell_line_name]

            # Group values by ranking to handle multiple values at the same rank
            ranking_groups = defaultdict(list)
            for (
                normalized_intensity_ranking,
                normalized_intensity,
            ) in normalized_intensity_ranking_pairs:
                ranking_groups[normalized_intensity_ranking].append(normalized_intensity)

            # Take the average of values at each ranking position
            for ranking, intensities in ranking_groups.items():
                local_weight_normalized_intensites[ranking] = np.mean(intensities)

            # Interpolate zero values.
            # Find indices and values of non-zero points for interpolation
            non_zero_indices = [
                i
                for i, val in enumerate(local_weight_normalized_intensites)
                if val != 0
            ]
            if len(non_zero_indices) > 1:  # Need at least 2 points for interpolation
                non_zero_values = [
                    local_weight_normalized_intensites[i] for i in non_zero_indices
                ]
                interpolator = interp1d(
                    non_zero_indices,
                    non_zero_values,
                    kind="linear",
                    bounds_error=False,
                    fill_value="extrapolate",
                )
                for i in range(len(local_weight_normalized_intensites)):
                    if local_weight_normalized_intensites[i] == 0:
                        local_weight_normalized_intensites[i] = interpolator(i)

            weight_normalized_intensites.append(local_weight_normalized_intensites)

        # Convert to numpy arrays and apply log10 transformation
        x_axis = common_rankings
        y_axis = np.log10(np.mean(weight_normalized_intensites, axis=0))

        return [x_axis, y_axis]

    def get_wce_data(
        self, cell_line_set: set[str], uniprotkb_ac: str
    ) -> list[CellLineProteomicsData]:
        """
        Retrieve WCE data for given cell lines and uniprotkb_ac.

        Args:
            cell_line_set: Set of cell line names
            uniprotkb_ac: UniProtKB accession number

        Returns:
            A list of CellLineProteomicsData objects
        """
        try:
            # For now, we'll use the proteomics cell line data method that takes uniprotkb_ac
            # This is more appropriate for getting data for a specific protein
            wce_data = self.umap_client._get_proteomics_cell_line_data(
                uniprotkb_ac=uniprotkb_ac
            )
            # Filter to only include the cell lines we're interested in
            filtered_data = [data for data in wce_data if data.cell_line_name in cell_line_set]
            return filtered_data
        except Exception as e:
            logger.exception(f"Error retrieving WCE data for {uniprotkb_ac}: {e}")
            return []

    def build_wce_data_csv(
        self, uniprotkb_ac: str, cell_line_set: set[str], folder_path: str
    ):
        """
        Build a WCE data CSV file for a given uniprotkb_ac and cell line set.
        Stores WCE data in the CSV file, appending to existing data.
        """
        file_name = FileNames.WCE_DATA.value
        columns = [
            "Gene",
            "Cell Line",
            "Onc Lineage",
            "Onc Subtype",
            "Weight Normalized Intensity Ranking",
            "Experiment Type",
            "Title",
            "Copies Per Cell",
            "Is Mapped",
        ]

        # Manage CSV file
        self._manage_csv_file(folder_path, file_name, columns)

        # Retrieve WCE data
        wce_data = self.get_wce_data(cell_line_set, uniprotkb_ac)
        data_df = pd.DataFrame([obj.dict(exclude_none=False) for obj in wce_data])

        if not data_df.empty:
            # Convert onc_lineage enum values to their string values
            if 'onc_lineage' in data_df.columns:
                data_df['onc_lineage'] = data_df['onc_lineage'].apply(lambda x: x.value if hasattr(x, 'value') else x)

            # Ensure is_mapped column exists and has proper values
            if 'is_mapped' not in data_df.columns:
                data_df['is_mapped'] = False

            # Transform data using common method
            column_mapping = {
                "Gene": "symbol",
                "Cell Line": "cell_line_name",
                "Onc Lineage": "onc_lineage",
                "Onc Subtype": "onc_subtype",
                "Weight Normalized Intensity Ranking": "weight_normalized_intensity_ranking",
                "Experiment Type": "experiment_type",
                "Title": "title",
                "Copies Per Cell": "copies_per_cell",
                "Is Mapped": "is_mapped",
            }
            transformed_df = self._transform_data_to_csv_format(
                data_df, column_mapping
            )

            # Append to CSV file
            self._append_to_csv_file(folder_path, file_name, transformed_df, columns)

        return data_df

    def build_cell_line_sigmoidal_curves_csv(
        self, cell_line_names: list[str], folder_path: str
    ):
        """
        This function will build the sigmoidal curves for each cell line.
        It will store them as a specialized CSV file.

        Column A: Cell Line Name
        Column B: X or Y boolean (0 for X, 1 for Y)

        The following 500 points columns will represent the points on the sigmoidal curve.

        This should allow us to plot the sigmoidal curve for each cell line and avoid the
        very expensive operation that actually builds the sigmoidal curve.

        Args:
            cell_line_names: List of cell line names to process
            folder_path: Path to save the CSV file
        """
        file_name = FileNames.CELL_LINE_SIGMOIDAL_CURVES.value

        # Create columns: Cell Line Name, X/Y indicator, and 500 curve points
        columns = ["Cell_Line_Name", "Is_Y_Axis"] + [f"Point_{i}" for i in range(500)]

        # Manage CSV file
        self._manage_csv_file(folder_path, file_name, columns)

        # Check which cell lines already exist in the file
        existing_cell_lines = set()
        try:
            csv_path = self._get_csv_path(folder_path, file_name)
            if os.path.exists(csv_path):
                existing_df = pd.read_csv(csv_path)
                if not existing_df.empty and 'Cell_Line_Name' in existing_df.columns:
                    existing_cell_lines = set(existing_df['Cell_Line_Name'].unique())
        except (FileNotFoundError, ValueError, KeyError):
            # File doesn't exist or is empty, no existing cell lines
            pass

        # Filter out cell lines that already exist
        new_cell_lines = [name for name in cell_line_names if name not in existing_cell_lines]
        skipped_cell_lines = [name for name in cell_line_names if name in existing_cell_lines]

        if skipped_cell_lines:
            logger.info(f"Skipping {len(skipped_cell_lines)} existing cell lines")

        if not new_cell_lines:
            return

        # Process new cell lines
        for cell_line_name in new_cell_lines:
            try:
                # Get WCE data for this cell line using the correct API method
                cell_line_data = self.umap_client._get_all_cell_line_proteomics_data(
                    cell_line_name=cell_line_name
                )
                
                if not cell_line_data:
                    continue

                # Build sigmoidal curve
                curve_data = self.build_generalizable_sigmoidal_curve(cell_line_data)
                x_axis, y_axis = curve_data

                # Create rows for X and Y axes
                x_row = [cell_line_name, 0] + list(x_axis[:500])  # First 500 points
                y_row = [cell_line_name, 1] + list(y_axis[:500])   # First 500 points

                # Create DataFrame for this cell line
                cell_line_df = pd.DataFrame([x_row, y_row], columns=columns)

                # Append to CSV file
                self._append_to_csv_file(folder_path, file_name, cell_line_df, columns)

            except Exception as e:
                continue
