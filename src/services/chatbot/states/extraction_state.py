import threading
from abc import ABC, abstractmethod
from typing import Any, Dict

from django.utils.translation import gettext_lazy as _

from src.services.chatbot.states.state import State
from src.services.chatbot.threads.get_elements_thread import GetElementsThread


class ExtractionState(State, ABC):
    """
    Abstract base class for states that extract information from user input.

    Implements the template method pattern to define the overall extraction workflow
    while delegating specific extraction behavior to subclasses.
    """

    def __init__(self):
        super().__init__()
        self._timeout = 60

    def process_user_input(self) -> None:
        """
        Processes user input by running an extraction thread with timeout handling.

        Creates and starts an extraction thread to process user input,
        waits for completion or timeout, and handles the aftermath.
        """
        prompt = self._get_extraction_prompt()
        extraction_done = threading.Event()

        def extraction_callback(result: Dict[str, Any]) -> None:
            self._handle_extraction_result(result)
            extraction_done.set()

        extractor_thread = GetElementsThread(
            prompt, self.context.user_prompt, extraction_callback
        )
        extractor_thread.start()

        if not extraction_done.wait(timeout=self._timeout):
            self._logger.error("Extraction thread timeout")
            if self.context.callback:
                self.context.callback({"error": _("Response timeout, Try again later")})
            return

        self._after_extraction()

    @abstractmethod
    def _get_extraction_prompt(self) -> str:
        """
        Returns the prompt used for information extraction.
        """
        pass

    @abstractmethod
    def _handle_extraction_result(self, result: Dict[str, Any]) -> None:
        """
        Processes the result from the extraction operation.
        """
        pass

    @abstractmethod
    def _after_extraction(self) -> None:
        """
        Performs actions after extraction is complete.
        """
        pass
