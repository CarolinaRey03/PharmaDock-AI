import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from src.utils.responses_generator import generate_chatbot_response


class State(ABC):
    """
    Abstract base class for chatbot conversation states.

    This class defines the interface for all states in the chatbot's state machine:
    - Maintains a reference to the context (conversation state holder)
    - Requires concrete states to implement process_user_input
    - Provides helper method for generating responses

    Each concrete state handles a specific phase of the molecular docking workflow.
    """

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)

    @property
    def context(self) -> Any:
        """
        Gets the context object that this state operates on.
        """
        return self._context

    @context.setter
    def context(self, context: Any) -> None:
        """
        Gets the context object that this state operates on.
        """
        self._context = context

    @abstractmethod
    def process_user_input(self) -> None:
        """
        Processes the current user input based on the state's behavior.
        """
        pass

    def _get_assistant_response(self) -> Dict[str, Any]:
        """
        Helper method to generate chatbot responses based on the current conversation.
        """
        interaction = generate_chatbot_response(self.context.conversation)

        if "error" in interaction:
            return interaction

        self.context.append_messages([interaction])
        return interaction
