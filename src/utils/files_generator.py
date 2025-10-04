import logging
from pathlib import Path

import requests
from django.utils.translation import gettext_lazy as _
from pandas import DataFrame
from rdkit import Chem
from rdkit.Chem import AllChem


def download_pdb_file(pdb_file: str, dir: str):
    """
    Download a protein structure file from RCSB Protein Data Bank.
    """
    logger = logging.getLogger(__name__)
    url = f"https://files.rcsb.org/download/{pdb_file}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(
            _(f"\nError downloading PDB file {pdb_file}: {response.status_code}\n")
        )

    file_path_str = f"{dir}/{pdb_file}"
    file_path = Path(file_path_str)
    with open(file_path, "w") as file:
        file.write(response.text)

    logger.debug("File %s downloaded successfully\n", file_path)


def create_drug_file(drug_file: str, drug_db: DataFrame, dir: str):
    """
    Create a drug structure file from SMILES strings.
    """
    logger = logging.getLogger(__name__)
    smiles_column = drug_db["SMILES"]
    logger.debug("SMILES column obtained: %s\n", smiles_column)

    writer = Chem.SDWriter(f"{dir}/{drug_file}")

    for idx, smiles in smiles_column.items():
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(
                "The SMILE cannot be processed at index %d: %s\n", idx, smiles
            )
            continue

        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol)
        AllChem.UFFOptimizeMolecule(mol)

        writer.write(mol)

    logger.debug(f"File {drug_file} created\n")
    writer.close()
