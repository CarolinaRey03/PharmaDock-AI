from typing import Any, Dict

from django.utils.translation import gettext_lazy as _

from src.services.chatbot.states.extraction_state import ExtractionState
from src.services.chatbot.states.options_extraction_state import OptionsExtractionState
from src.utils.json_utils import get_pdb
from src.utils.prompts import get_pdb_extraction_prompt


class PDBExtractionState(ExtractionState):
    """
    State responsible for extracting PDB identifier when multiple options are available.

    This state:
    - Presents available PDB options to the user
    - Extracts the user's PDB selection choice
    - Transitions to options extraction after successful PDB selection
    """

    def _get_extraction_prompt(self) -> str:
        return get_pdb_extraction_prompt()

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

        self.context.pdb = get_pdb(extraction["content"])
        self._logger.debug("\nExtrated pdb: %s\n", self.context.pdb)

    def _after_extraction(self) -> None:
        interaction = self._get_assistant_response()

        self.context.transition_to(OptionsExtractionState(), False)
        self.context.callback(interaction)
