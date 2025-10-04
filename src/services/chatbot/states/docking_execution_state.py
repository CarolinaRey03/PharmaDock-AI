import os

from django.utils.translation import gettext_lazy as _

from src.services.chatbot.states.state import State
from src.utils.docking_utils.docking_result import DockingResult
from src.utils.docking_utils.docking_service import DockingService
from src.utils.singletons.resource_manager import ResourceManager


class DockingExecutionState(State):
    """
    State responsible for executing molecular docking operations.

    This state:
    - Uses ResourceManager to access receptor and ligand files
    - Executes docking using DockingService
    - Handles file management (naming, cleanup, storage)
    - Returns docking results with file paths
    """

    def __init__(self):
        super().__init__()
        self._resource_manager = ResourceManager()

    def process_user_input(self) -> None:
        docking_result = self._do_docking()

        if not docking_result.success:
            self.context.callback(
                {
                    "error": _(
                        "There's been an error while executing the docking. Please, try again later or contact with the administrator"
                    )
                }
            )
            return

        receptor_file_path = os.path.join(
            "out", "docking_result", docking_result.receptor_file
        )
        pos_file_path = os.path.join("out", "docking_result", docking_result.pos_file)
        ligand_file_path = os.path.join(
            "out", "docking_result", docking_result.ligand_file
        )
        log_file_path = os.path.join("out", "docking_result", docking_result.log_file)

        interaction = self._get_assistant_response()
        interaction = {
            "role": "assistant",
            "content": interaction["content"],
            "receptor_file": receptor_file_path,
            "pos_file": pos_file_path,
            "ligand_file": ligand_file_path,
            "docking_result_log": log_file_path,
        }

        from src.services.chatbot.states.gene_drug_extraction import (
            GeneDrugExtractionState,
        )

        self.context.transition_to(GeneDrugExtractionState(), False)
        self.context.callback(interaction)

    def _do_docking(self) -> DockingResult:
        """
        Executes the molecular docking process.

        Checks for existing results or runs new docking operation
        if needed.
        """
        result_base_name = self._generate_result_base_name()

        result_files = self._resource_manager.get_docking_files(result_base_name)
        log_file = self._resource_manager.get_log_file(result_base_name)

        docking_result_files_available = (
            result_files["receptor_file"] is not None
            and result_files["pos_file"] is not None
            and result_files["ligand_file"] is not None
            and log_file is not None
        )
        if docking_result_files_available:
            return DockingResult(
                receptor_file=result_files["receptor_file"],
                pos_file=result_files["pos_file"],
                ligand_file=result_files["ligand_file"],
                log_file=log_file,
            )

        # Result files don't exist, proceed with docking
        ligand_file = self._resource_manager.load_pdb_file(self.context.pdb)
        drug_file = self._resource_manager.load_drug_file(self.context.drug)

        success = DockingService.run_vina_docking(
            ligand_file=ligand_file, drug_file=drug_file, options=self.context.options
        )

        if success:
            self._rename_files(result_base_name)

            result_files = self._resource_manager.get_docking_files(result_base_name)
            log_file = self._resource_manager.get_log_file(result_base_name)

            return DockingResult(
                receptor_file=result_files["receptor_file"],
                pos_file=result_files["pos_file"],
                ligand_file=result_files["ligand_file"],
                log_file=log_file,
            )
        else:
            self._logger.error("Docking failed. Unable to generate results.")
            return DockingResult()

    def _generate_result_base_name(self) -> str:
        """
        Generates a base filename for docking results based on
        PDB ID, drug name, and docking options.
        """
        options_suffix = ""
        if hasattr(self.context, "options") and self.context.options:
            options_normalized = (
                self.context.options.replace(" ", "_")
                .replace("-", "")
                .replace("=", "_")
            )
            options_suffix = f"_{options_normalized}"

        return f"{self.context.pdb}_{self.context.drug}{options_suffix}"

    def _rename_files(self, result_base_name: str) -> None:
        """
        Handles post-docking file renaming.

        Standardizes filenames based on result_base_name.
        """
        output_dir = os.path.join("out", "docking_result")

        file_mapping = {
            f"{self.context.pdb}.pdbqt": f"{result_base_name}_receptor.pdbqt",
            f"{self.context.pdb}_{self.context.drug}_out.pdbqt": f"{result_base_name}_pos.pdbqt",
            f"{self.context.pdb}_{self.context.drug}_vina.log": f"{result_base_name}_vina.log",
            f"{self.context.pdb}_{self.context.drug}_out.pdbqt.sdf": f"{result_base_name}_ligand.pdbqt.sdf",
        }

        try:
            for orig_file, new_file in file_mapping.items():
                orig_path = os.path.join(output_dir, orig_file)
                new_path = os.path.join(output_dir, new_file)

                if os.path.exists(orig_path):
                    os.rename(orig_path, new_path)
                    self._logger.debug(f"Renamed {orig_file} to {new_file}")

        except Exception as e:
            self._logger.error(f"Error handling result files: {str(e)}")
