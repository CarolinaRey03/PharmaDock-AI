import logging
import threading
from queue import Queue
from typing import Any, Callable, Dict, List, Optional
from src.services.chatbot.states.state import State


class ChatbotThread(threading.Thread):
    """
    Thread class managing the chatbot conversation flow and state transitions.

    This class:
    - Implements the Context role in the State pattern
    - Maintains conversation state and history
    - Processes user messages asynchronously
    - Manages transitions between different conversation states
    - Stores extracted molecular docking information (gene, drug, PDB, options)
    """

    def __init__(
        self, user_prompt: str, state: State, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)

        self.user_prompt = user_prompt
        self.callback = callback

        self.gene: Optional[str] = None
        self.drug: Optional[str] = None
        self.summary: Optional[str] = None
        self.pdb: Optional[str] = None
        self.options: Optional[str] = None
        self.conversation: List[Dict[str, str]] = []
        self.transition_to(state, False)

        self._do_auto_process: bool = False
        self._keep_conversation: bool = True
        self._queue: Queue = Queue()
        self._new_message_event: threading.Event = threading.Event()
        self._completion_event: threading.Event = threading.Event()

    def transition_to(self, state: State, auto_process: bool) -> None:
        """
        Transition to a new state and optionally process user input immediately.
        """
        self._logger.debug(f"Transition to {type(state).__name__}")
        self._state = state
        self._state.context = self
        self._do_auto_process = auto_process

        if self._do_auto_process:
            self._state.process_user_input()

    def run(self) -> None:
        self._state.process_user_input()

        while self._keep_conversation:
            if not self._new_message_event.wait(timeout=300):
                self._logger.debug("Conversation timeout, ending...")
                break

            self._new_message_event.clear()
            new_message = self._queue.get()

            self.user_prompt = new_message

            self.append_messages([{"role": "user", "content": new_message}])

            self._state.process_user_input()

    def append_messages(self, message: List[Dict[str, str]]) -> None:
        """
        Add messages to the conversation history.
        """
        for msg in message:
            self.conversation.append(msg)
            self._logger.debug("Added message from list to conversation: %s", msg)

    def add_user_message(self, message: str) -> None:
        """
        Add a new user message to the processing queue.
        """
        self._queue.put(message)
        self._new_message_event.set()

    def stop_conversation(self) -> None:
        """
        Signal the conversation thread to stop processing.
        """
        self._keep_conversation = False
        self._completion_event.set()

    def wait_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for the conversation to complete.
        """
        return self._completion_event.wait(timeout=timeout)
