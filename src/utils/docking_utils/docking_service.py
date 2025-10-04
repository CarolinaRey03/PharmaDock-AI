import os
import subprocess
import logging

logger = logging.getLogger(__name__)


class DockingService:
    """
    Service for executing molecular docking operations.

    Provides methods to run AutoDock Vina through Docker containers,
    handling input/output file mounting and command execution.
    """

    @staticmethod
    def run_vina_docking(
        ligand_file: str,
        drug_file: str,
        options : str,
        input_dir="data/input",
        output_dir="out/docking_result",
    ) -> bool:
        """
        Execute AutoDock Vina docking through Docker.
        """
        input_dir = os.path.abspath(input_dir)
        output_dir = os.path.abspath(output_dir)

        cmd = [
            "docker",
            "run",
            "-it",
            "--rm",
            "-v",
            f"{input_dir}:/input",
            "-v",
            f"{output_dir}:/output",
            "cafernandezlo/dock-tools:v1.0",
            "vina",
            ligand_file,
            drug_file,
        ]

        # Add options as individual arguments
        if options:
            options_list = options.split()
            cmd.extend(options_list)

        logger.debug(f"Executing docking command: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                logger.error(f"Error executing docking: {result.stderr}")
                return False

            logger.debug(f"Docking completed successfully: {result.stdout}")
            return True

        except Exception as e:
            logger.error(f"Exception during docking execution: {str(e)}")
            return False
