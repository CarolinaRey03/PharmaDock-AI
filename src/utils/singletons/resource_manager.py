import logging
import os

import pandas as pd

from src.utils.files_generator import create_drug_file, download_pdb_file
from src.utils.singletons.singleton_meta import SingletonMeta


class ResourceManager(metaclass=SingletonMeta):
    """
    Provides centralized access to databases, file paths, and molecular structures.
    Implements caching mechanisms to avoid redundant downloads and file creation.
    Ensures consistent access to resources throughout the application.
    """

    def __init__(self):
        self._databases = {
            "drug_db": os.path.join("data", "databases", "docking", "drug_db.xlsx"),
            "genes_db": os.path.join("data", "databases", "docking", "genes_db.xlsx"),
        }
        self._pdb_files = {}
        self._drug_files = {}
        self._pos_files = {}
        self._ligand_files = {}
        self._receptor_files = {}
        self._log_files = {}
        self._input_dir = os.path.join("data", "input")
        self._output_dir = os.path.join("out", "docking_result")

        os.makedirs(self._input_dir, exist_ok=True)
        os.makedirs(self._output_dir, exist_ok=True)

        self._logger = logging.getLogger(__name__)

    def load_databases(
        self, drug_name=None, gene_name=None
    ) -> pd.DataFrame | pd.DataFrame:
        """
        Load and filter drug and gene databases based on provided names.
        """
        drug_db_path = self._databases["drug_db"]
        gene_db_path = self._databases["genes_db"]
        drug_db = pd.read_excel(drug_db_path, usecols=["Name", "Description", "SMILES"])
        gene_db = pd.read_excel(
            gene_db_path,
            usecols=["hgnc_symbol", "gene_name", "gene_description", "pdb"],
        )

        gene_found = False
        drug_found = False

        if drug_name:
            drug_db = drug_db[drug_db["Name"].str.lower() == drug_name.lower()]
            drug_found = True

        if gene_name:
            gene_db = gene_db[
                (gene_db["hgnc_symbol"].str.lower() == gene_name.lower())
                | (gene_db["gene_name"].str.lower() == gene_name.lower())
            ]
            gene_found = True

        drug_db = drug_db if drug_found else None
        gene_db = gene_db if gene_found else None

        return drug_db, gene_db

    def get_pdbs(self, gene: str) -> list:
        """
        Get available PDB IDs for a specific gene.

        Args:
            gene: Gene symbol to search for

        Returns:
            List of PDB IDs associated with the gene
        """
        try:
            _, gene_df = self.load_databases(gene_name=gene)

            gene_records = gene_df[gene_df["hgnc_symbol"].str.lower() == gene.lower()]
            self._logger.debug(gene_records)

            if gene_records.empty:
                self._logger.debug("No records found for gene: %s", gene)
                return []

            if "pdb" in gene_records.columns:
                pdb_raw = gene_records["pdb"].dropna().unique().tolist()

                if not pdb_raw:
                    return []

                pdbs = []
                for pdb_entry in pdb_raw:
                    if isinstance(pdb_entry, str):
                        split_pdbs = [
                            p.strip() for p in pdb_entry.split(";") if p.strip()
                        ]
                        pdbs.extend(split_pdbs)
                    else:
                        pdbs.append(str(pdb_entry))

                self._logger.debug(
                    "Found %d PDBs for gene %s: %s", len(pdbs), gene, pdbs
                )
                return pdbs
            else:
                self._logger.warning("No 'pdb_id' column in gene database")
                return []

        except Exception as e:
            self._logger.error("Error checking multiple PDBs: %s", str(e))
            return []

    def load_pdb_file(self, pdb_name: str) -> str:
        """
        Download or retrieve a cached PDB file.
        """
        if pdb_name in self._pdb_files:
            self._logger.debug("PDB file already exists. Skiping the download...\n")
            return self._pdb_files[pdb_name]

        pdb_file = f"{pdb_name}.pdb"
        if not self._is_file_available(self._input_dir, pdb_file):
            download_pdb_file(pdb_file, self._input_dir)
        else:
            self._logger.debug("PDB file already exists. Skiping the download...\n")

        self._pdb_files[pdb_name] = pdb_file
        return pdb_file

    def load_drug_file(self, drug_name: str) -> str:
        """
        Create or retrieve a cached drug structure file.
        """
        if drug_name in self._drug_files:
            self._logger.debug("Drug file already exists. Skiping the creation...\n")
            return self._drug_files[drug_name]

        drug_file = f"{drug_name}.sdf"
        if not self._is_file_available(self._input_dir, drug_file):
            drug_db, _ = self.load_databases(drug_name=drug_name)
            create_drug_file(drug_file, drug_db, self._input_dir)
        else:
            self._logger.debug("Drug file already exists. Skiping the creation...\n")

        self._drug_files[drug_name] = drug_file
        return drug_file

    def get_docking_files(self, result_name: str) -> dict:
        """
        Retrieve receptor, ligand position and ligand files for docking results.
        """
        # Check if all required result files (receptor, ligand, and position) are already cached
        all_docking_files_cached = (
            result_name in self._receptor_files
            and result_name in self._ligand_files
            and result_name in self._pos_files
        )

        if all_docking_files_cached:
            self._logger.debug(
                "The docking files already exists. Skiping the docking..."
            )
            return {
                "receptor_file": self._receptor_files[result_name],
                "pos_file": self._pos_files[result_name],
                "ligand_file": self._ligand_files[result_name],
            }

        receptor_file = f"{result_name}_receptor.pdbqt"
        pos_file = f"{result_name}_pos.pdbqt"
        ligand_file = f"{result_name}_ligand.pdbqt.sdf"

        # Check if all the required result files exists
        result_files_exists = (
            self._is_file_available(self._output_dir, receptor_file)
            and self._is_file_available(self._output_dir, pos_file)
            and self._is_file_available(self._output_dir, ligand_file)
        )

        if not result_files_exists:
            return {
            "receptor_file": None,
            "pos_file": None,
            "ligand_file": None,
        }

        self._receptor_files[result_name] = receptor_file
        self._pos_files[result_name] = pos_file
        self._ligand_files[result_name] = ligand_file
        self._logger.debug("The docking files already exists. Skiping the docking...")

        return {
            "receptor_file": self._receptor_files[result_name],
            "pos_file": self._pos_files[result_name],
            "ligand_file": self._ligand_files[result_name],
        }

    def get_log_file(self, result_name: str) -> str:
        """
        Retrieve log file for docking results.
        """
        if result_name in self._log_files:
            self._logger.debug("The log file already exists. Skiping the docking...")
            return self._log_files[result_name]

        log_file = f"{result_name}_vina.log"
        if not self._is_file_available(self._output_dir, log_file):
            return None

        self._log_files[result_name] = log_file
        self._logger.debug("The log file already exists. Skiping the docking...")

        return log_file

    def _is_file_available(self, dir: str, file_name: str) -> bool:
        """
        Check if a file exists in a directory.
        """
        for filename in os.listdir(dir):
            if filename.lower() == f"{file_name}".lower():
                return True

        return False
