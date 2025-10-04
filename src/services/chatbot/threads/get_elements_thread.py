import logging
import threading
from typing import Any, Callable, Dict, List

from django.utils.translation import gettext_lazy as _

from src.utils.responses_generator import generate_chatbot_response


class GetElementsThread(threading.Thread):
    """
    Thread class that handles asynchronous element extraction from user prompts.

    This thread:
    - Takes a developer prompt and user input
    - Processes them to extract specific information (genes, drugs, options, etc.)
    - Delivers results via callback when processing is complete
    - Handles errors during processing
    """

    def __init__(
        self,
        developer_prompt: str,
        user_prompt: str,
        callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        super().__init__()
        self._conversation: List[Dict[str, str]] = [
            {
                "role": "developer",
                "content": developer_prompt.strip(),
            },
            {"role": "user", "content": user_prompt.strip()},
        ]
        self._callback = callback
        self._logger = logging.getLogger(__name__)

    def run(self) -> None:
        try:
            result = generate_chatbot_response(self._conversation)
            self._callback(result)
        except Exception as error:
            self._logger.error("Error at GetElementThread: %s", str(error))
            if self._callback:
                self._callback(
                    {
                        "error": _(
                            "Error at proccessing the petition. Please, try later or contact with the administrator"
                        )
                    }
                )
