import json
import logging


def _correct_json_response(json_response: str) -> str:
    """
    Attempt to correct malformed JSON by cleaning and reformatting.
    """
    json_response = json_response.replace("```json", "").replace("```", "").strip()
    json_response = json_response.strip("{}")
    lines = json_response.split("\n")
    corrected_lines = []

    for line in lines:
        line = line.strip().rstrip(",")
        if line and not line.startswith("{") and not line.endswith("}"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().strip('"')
                corrected_lines.append(f'"{key}": {value.strip()}')
            else:
                corrected_lines.append(line)

    corrected_json = ",".join(corrected_lines)
    corrected_json = "{" + corrected_json + "}"

    return corrected_json


def is_json_data(response: str) -> bool:
    """
    Check if a response can be parsed as valid JSON.
    """
    json_data = _correct_json_response(response)
    try:
        json_data = json.load(json_data)
        return True
    except json.JSONDecodeError:
        return False


def _load_json_data(json_data: dict | str) -> dict | None:
    """
    Attempt to load JSON data from various formats.

    Handles dict objects, chatbot responses with content fields,
    and attempts to correct malformed JSON strings.
    """
    if isinstance(json_data, dict):
        if "role" in json_data and "content" in json_data:
            content = json_data["content"]
            return _extract_json_from_markdown(content)
        return json_data

    try:
        json_data = json.loads(json_data)
        return json_data
    except json.JSONDecodeError as json_error:
        corrected_json = _correct_json_response(json_data)

        try:
            json_data = json.loads(corrected_json)
            return json_data
        except json.JSONDecodeError as json_error:
            logger = logging.getLogger(__name__)
            error_message = f"Error during JSON decoding: {str(json_error)}. The JSON data is: {json_data}"
            logger.error(error_message)
            return None


def _extract_json_from_markdown(content : str) -> dict | None:
    """
    Extract JSON data from markdown-formatted text.
    """
    if "```json" in content:
        content = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return _load_json_data(content)


def get_protein_and_drug(json_data: dict | str) -> tuple[str | None, str | None]:
    json_data = _load_json_data(json_data)

    if not json_data:
        return None, None

    protein = json_data.get("protein")
    drug = json_data.get("drug")

    return protein, drug


def get_pdb(json_data: str | dict) -> str | None:
    """
    Extract PDB identifier from JSON data.
    """
    json_data = _load_json_data(json_data)

    if not json_data:
        return None

    pdb = json_data.get("pdb")
    return pdb


def get_options(json_data: dict | str) -> str | None:
    """
    Extract and format docking options from JSON data.

    Processes configuration options like box size, center coordinates,
    and other docking parameters, converting them to command line arguments.
    """
    json_data = _load_json_data(json_data)
    options = []

    if not json_data:
        return None

    box_enveloping = json_data.get("box_enveloping")
    if isinstance(box_enveloping, str):
        box_enveloping = box_enveloping.lower() == "true"
    if box_enveloping:
        return "--box_enveloping"

    box_size = json_data.get("box_size")
    if box_size:
        options.append(f"--box_size {box_size}")

    box_center = json_data.get("box_center")
    if box_center:
        options.append(f"--box_center {box_center}")

    padding = json_data.get("padding")
    if padding:
        options.append(f"--padding {padding}")

    exhaustiveness = json_data.get("exhaustiveness")
    if exhaustiveness:
        options.append(f"--exhaustiveness {exhaustiveness}")

    scoring = json_data.get("scoring")
    if scoring:
        options.append(f"--scoring {scoring}")

    # Add the option "--box_enveloping" if "box_center" and "box_size" is not used, otherwise the docking won't work
    if not f"--box_center {box_center}" in options:
        options.append(f"--box_enveloping")

    return " ".join(options)
