import json
import os
import threading
from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from src.services.chatbot.chatbot_thread import ChatbotThread
from src.services.chatbot.states.gene_drug_extraction import GeneDrugExtractionState

from .decorators import account_activated_required


def home(request: HttpRequest) -> HttpResponse:
    """
    Render the home page
    """
    return render(request, "home.html")


@account_activated_required
def chat(request: HttpRequest) -> HttpResponse:
    """
    Render the chat interface for authenticated
    and activated users.
    """
    return render(request, "chat.html")


active_conversations = {}


@require_POST
def chat_message(request: HttpRequest) -> JsonResponse:
    """
    Processes chat messages
    asynchronously using ChatbotThread.
    """
    try:
        data = json.loads(request.body)
        user_prompt = data.get("user_prompt", "")

        session_id = _get_or_create_session_id(request)

        result_container: Dict[str, Any] = {
            "assistant": None,
            "event": threading.Event(),
        }

        if session_id in active_conversations:
            _process_existing_conversation(session_id, user_prompt, result_container)
        else:
            _process_new_conversation(session_id, user_prompt, result_container)

        timeout = 300
        if not result_container["event"].wait(timeout=timeout):
            _handle_timeout(session_id, result_container)
            return JsonResponse(
                {"error": _("The response is taking a lot of time. Please try again")}
            )

        return JsonResponse(result_container["assistant"])

    except Exception as e:
        return JsonResponse(
            {
                "error": _(
                    f"There's been an error. Please, try later or contact with the administrator"
                )
            }
        )


def _get_or_create_session_id(request: HttpRequest) -> str:
    """
    Gets the current session ID or creates a new one if none exists.
    """
    session_id = request.session.session_key
    if not session_id:
        request.session.create()
        session_id = request.session.session_key
    return session_id


def _process_existing_conversation(
    session_id: str, user_prompt: str, result_container: Dict[str, Any]
) -> None:
    """
    Processes a message in an existing conversation thread.
    """
    chatbot_thread = active_conversations[session_id]

    original_callback = chatbot_thread.callback

    def temp_callback(result: Dict[str, Any]) -> None:
        result_container["assistant"] = result
        result_container["event"].set()

    chatbot_thread.callback = temp_callback

    chatbot_thread.add_user_message(user_prompt)
    result_container["original_callback"] = original_callback


def _process_new_conversation(
    session_id: str, user_prompt: str, result_container: Dict[str, Any]
) -> None:
    """
    Creates and starts a new conversation thread.
    """

    def _on_thread_finished(result: Dict[str, Any]) -> None:
        result_container["assistant"] = result
        result_container["event"].set()

    chatbot_thread = ChatbotThread(
        user_prompt, GeneDrugExtractionState(), _on_thread_finished
    )
    chatbot_thread.start()

    active_conversations[session_id] = chatbot_thread


def _handle_timeout(session_id: str, result_container: Dict[str, Any]) -> None:
    """
    Handles timeout situation for a conversation.
    """
    if session_id not in active_conversations:
        return

    chatbot_thread = active_conversations[session_id]

    if "original_callback" in result_container:
        chatbot_thread.callback = result_container["original_callback"]
    else:
        del active_conversations[session_id]


def get_docking_file(request: HttpRequest, file_path: str) -> HttpResponse:
    base_path = os.path.dirname(settings.BASE_DIR)
    full_path = os.path.join(base_path, file_path)

    if not os.path.exists(full_path):
        return HttpResponseNotFound(_(f"File not found: {file_path}"))

    try:
        file_ext = os.path.splitext(file_path)[1].lower()

        # Select the appropriate open mode and content type based on the file extension.
        if file_ext == ".sdf":
            mode = "rb"
            content_type = "chemical/x-mdl-sdfile"
        else:
            mode = "r"
            content_type = "chemical/x-pdb"

        with open(full_path, mode) as f:
            content = f.read()

        return HttpResponse(content, content_type=content_type)
    except Exception as e:
        return HttpResponseNotFound(_(f"Docking file not found: {str(e)}"))


def get_docking_log(request: HttpRequest, file_path: str) -> HttpResponse:
    """
    Retrieves and serves molecular docking log files.
    """
    base_path = os.path.dirname(settings.BASE_DIR)
    full_path = os.path.join(base_path, file_path)

    if not os.path.exists(full_path):
        return HttpResponseNotFound(_(f"Log file not found"))

    try:
        with open(full_path, "r") as f:
            content = f.read()

        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            f'attachment; filename="{os.path.basename(file_path)}"'
        )
        return response
    except Exception as e:
        return HttpResponseNotFound(f"Error: {str(e)}")


@require_POST
def end_conversation(request: HttpRequest) -> JsonResponse:
    """
    Terminates an active conversation thread.
    """
    try:
        session_id = request.session.session_key
        if session_id in active_conversations:
            chatbot_thread = active_conversations[session_id]
            chatbot_thread.stop_conversation()

            chatbot_thread.wait_completion(timeout=5)

            del active_conversations[session_id]

        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"error": _(f"The conversation cannot be finished")})
