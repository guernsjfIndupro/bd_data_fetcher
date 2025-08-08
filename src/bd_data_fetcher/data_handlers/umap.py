import pandas as pd
import structlog

from bd_data_fetcher.data_handlers.base_handler import BaseDataHandler
from bd_data_fetcher.data_handlers.utils import SheetNames

logger = structlog.get_logger(__name__)


class uMapDataHandler(BaseDataHandler):
    """
    This class is responsible for handling UMap data.
    """

    def get_targeted_replicate_sets(self, uniprotkb_ac: str):
        """
        Get all replicate sets that have targeted the given protein.
        """
        replicate_sets = self.umap_client._get_replicate_sets()

        return [
            replicate_set
            for replicate_set in replicate_sets
            if (
                isinstance(replicate_set.target.proteins, list)
                and len(replicate_set.target.proteins) == 1
                and replicate_set.target.proteins[0].uniprotkb_ac == uniprotkb_ac
                and len(replicate_set.cell_source.cell_lines) > 0
            )
        ]

    def get_umap_data(self, uniprotkb_ac: str, file_path: str):
        """
        Build a UMap analysis results sheet for a given uniprotkb_ac.
        Stores all analysis results data in the Excel sheet, appending to existing data.
        """
        sheet_name = SheetNames.UMAP_DATA.value
        columns = [
            "Replicate Set ID",
            "Cell Line",
            "Chemistry",
            "Target Protein",
            "Protein Symbol",
            "Protein UniProtKB AC",
            "Log2 FC",
            "P-value",
            "Number of Peptides",
            "Binder",
        ]

        # Manage Excel sheet
        self._manage_excel_sheet(file_path, sheet_name, columns)

        # Get targeted replicate sets
        replicate_sets = self.get_targeted_replicate_sets(uniprotkb_ac)

        if replicate_sets:
            # Transform data to match the sheet column structure
            transformed_data = []

            for replicate_set in replicate_sets:
                # Retrieve all replicate set data
                analysis_results = self.umap_client._get_analysis_results(
                    replicate_set_id=replicate_set.id
                )

                # Get cell line name
                cell_line = (
                    replicate_set.cell_source.cell_lines[0].name
                    if replicate_set.cell_source.cell_lines
                    else "Unknown"
                )

                # Get target protein info
                target_protein = (
                    replicate_set.target.proteins[0].symbol
                    if replicate_set.target
                    else "Unknown"
                )

                for result in analysis_results:
                    transformed_row = {
                        "Replicate Set ID": replicate_set.id,
                        "Cell Line": cell_line,
                        "Chemistry": replicate_set.chemistry,
                        "Target Protein": target_protein,
                        "Protein Symbol": result.protein.symbol,
                        "Protein UniProtKB AC": result.protein.uniprotkb_ac,
                        "Log2 FC": result.log2_fc,
                        "P-value": result.nlog10_pvalue,
                        "Number of Peptides": result.number_of_peptides,
                        "Binder": (
                            replicate_set.binder.display_name
                            if replicate_set.binder
                            else "Unknown"
                        ),
                    }
                    transformed_data.append(transformed_row)

            # Create DataFrame with the correct column structure
            transformed_df = pd.DataFrame(transformed_data)

            if not transformed_df.empty:
                # Append to Excel sheet
                self._append_to_excel_sheet(
                    file_path, sheet_name, transformed_df, columns
                )

        return replicate_sets

    def get_cell_lines(self, uniprotkb_ac: str) -> set[str]:
        """
        Get all cell lines that have targeted the given protein.

        # TODO: Determine if we should use the name or the ID.
        """
        replicate_sets = self.get_targeted_replicate_sets(uniprotkb_ac)
        return {
            replicate_set.cell_source.cell_lines[0].name
            for replicate_set in replicate_sets
        }
