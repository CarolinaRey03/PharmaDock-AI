from django import template

register = template.Library()


@register.simple_tag
def get_icon(tag: str) -> str:
    """
    Returns the appropriate FontAwesome icon class based on the message tag.
    """
    icon_map = {
        "success": "fa-check-circle",
        "error": "fa-times-circle",
        "warning": "fa-exclamation-triangle",
        "info": "fa-info-circle",
    }
    return icon_map.get(tag, "fa-info-circle")