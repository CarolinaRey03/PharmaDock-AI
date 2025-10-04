from typing import Any, Dict

from django.utils.translation import gettext_lazy as _

from src.services.chatbot.states.extraction_state import ExtractionState
from src.services.chatbot.states.options_extraction_state import OptionsExtractionState
from src.services.chatbot.states.pdb_extraction_state import PDBExtractionState
from src.utils.json_utils import get_protein_and_drug
from src.utils.prompts import (
    get_gene_drug_extraction_prompt,
    get_user_interaction_prompt,
)
from src.utils.singletons.resource_manager import ResourceManager


class GeneDrugExtractionState(ExtractionState):
    """
    State responsible for extracting gene and drug information from user input.

    This state:
    - Extracts gene/protein and drug names from user messages
    - Validates the extracted data against databases
    - Provides informative responses about the gene-drug interaction
    - Transitions to PDB selection or options extraction based on available data
    """

    def _get_extraction_prompt(self) -> str:
        return get_gene_drug_extraction_prompt()

    def _handle_extraction_result(self, extraction: Dict[str, Any]) -> None:
        if "error" in extraction:
            error = extraction["error"]
            self._logger.error("Error receiving the extraction: %s", error)
            self.context.callback(
                _(
                    "Error at proccessing the petition. Please, try later or contact with the administrator"
                )
            )
            return

        self.context.append_messages([extraction])
        gene, drug = get_protein_and_drug(extraction["content"])

        self.context.gene = gene if gene else self.context.gene
        self.context.drug = drug if drug else self.context.drug

        self._logger.debug(
            "\nExtrated gene: %s\nExtrated drug: %s\n",
            self.context.gene,
            self.context.drug,
        )

    def _after_extraction(self) -> None:
        drugs_db, genes_db = ResourceManager().load_databases(
            self.context.drug, self.context.gene
        )
        self.context.append_messages(
            [
                {
                    "role": "system",
                    "content": get_user_interaction_prompt(drugs_db, genes_db),
                },
                {"role": "user", "content": self.context.user_prompt},
            ]
        )
        summary = self._get_assistant_response()

        self.context.append_messages([summary])
        self.context.callback(summary)

        is_gene_drug_data_available = not genes_db.empty and not drugs_db.empty

        if is_gene_drug_data_available:
            self._process_gene_pdbs()

    def _process_gene_pdbs(self) -> None:
        """
        Processes available PDB structures for the extracted gene.

        - If no PDBs are available: Logs the unavailability
        - If exactly one PDB is available: Uses it and transitions to options extraction
        - If multiple PDBs are available: Transitions to PDB selection state
        """
        avaliable_pdbs = ResourceManager().get_pdbs(self.context.gene)

        if not avaliable_pdbs:
            self._logger.debug(f"No PDBs for gene {self.context.gene}")
        elif len(avaliable_pdbs) == 1:
            self.context.pdb = avaliable_pdbs[0]
            self.context.transition_to(OptionsExtractionState(), False)
        else:
            self.context.transition_to(PDBExtractionState(), False)
