"""WhatsApp media tools — send files and download media."""

from __future__ import annotations

from typing import Any

from clr_whatsapp_mcp.tools import _register_module, get_bridge


def wa_send_file(
    recipient: str,
    media_path: str,
    message: str = "",
) -> dict[str, Any]:
    """Send a file/media message via WhatsApp.

    Args:
        recipient: Phone number or JID of the recipient.
        media_path: Path to the media file (must be accessible by the WhatsApp bridge).
        message: Optional caption text for the media.

    Returns the bridge response with message ID and delivery status.
    """
    return get_bridge().send_file(recipient=recipient, media_path=media_path, message=message)


def wa_download_media(message_id: str, chat_jid: str) -> dict[str, Any]:
    """Download media from a received WhatsApp message.

    Args:
        message_id: The WhatsApp message ID containing the media.
        chat_jid: The chat JID the message belongs to.

    Returns the bridge response with the download path or media data.
    """
    return get_bridge().download_media(message_id=message_id, chat_jid=chat_jid)


TOOLS = [
    wa_send_file,
    wa_download_media,
]

_register_module("media", TOOLS)
