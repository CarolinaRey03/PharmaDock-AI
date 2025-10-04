from typing import Any, Dict

from django.utils.translation import gettext_lazy as _

from src.services.chatbot.states.docking_execution_state import DockingExecutionState
from src.services.chatbot.states.extraction_state import ExtractionState
from src.utils.json_utils import get_options
from src.utils.prompts import get_options_extraction_prompt


class OptionsExtractionState(ExtractionState):
    """
    State responsible for extracting molecular docking configuration options.

    This state:
    - Extracts docking parameters
    - Validates extracted options
    - Transitions to docking execution after successful extraction
    """

    def _get_extraction_prompt(self) -> str:
        return get_options_extraction_prompt()

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

        self.context.options = get_options(extraction)
        self._logger.debug("\nExtrated options: %s\n", self.context.options)

    def _after_extraction(self) -> None:
        self.context.transition_to(DockingExecutionState(), True)
