"""WhatsApp message tools — list, search, send messages."""

from __future__ import annotations

from typing import Any

from clr_whatsapp_mcp.tools import _register_module, get_bridge, get_supabase


def wa_list_chats(query: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """List WhatsApp chats, optionally filtered by name.

    Args:
        query: Optional search string to filter chat names (case-insensitive).
        limit: Maximum number of chats to return (default 20).

    Returns a list of chats ordered by most recent message.
    """
    return get_supabase().list_chats(query=query, limit=limit)


def wa_list_messages(
    chat_jid: str,
    limit: int = 50,
    after: str | None = None,
    before: str | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    """List messages in a WhatsApp chat.

    Args:
        chat_jid: The chat JID to list messages for.
        limit: Maximum number of messages to return (default 50).
        after: Only messages after this ISO timestamp (e.g. "2024-01-15T10:00:00Z").
        before: Only messages before this ISO timestamp.
        query: Optional content search within the chat (case-insensitive).

    Returns a list of messages ordered by most recent first.
    """
    return get_supabase().list_messages(
        chat_jid=chat_jid, limit=limit, after=after, before=before, query=query
    )


def wa_search_messages(
    query: str,
    chat_jid: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search WhatsApp messages by content across all chats.

    Args:
        query: Search string to match against message content (case-insensitive).
        chat_jid: Optional chat JID to restrict search to a single chat.
        limit: Maximum number of results (default 50).

    Returns a list of matching messages ordered by most recent first.
    """
    return get_supabase().search_messages(query=query, chat_jid=chat_jid, limit=limit)


def wa_get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5,
) -> dict[str, Any]:
    """Get a message and its surrounding context (nearby messages in the same chat).

    Args:
        message_id: The target message ID.
        before: Number of messages before the target to include (default 5).
        after: Number of messages after the target to include (default 5).

    Returns the target message and a chronological list of surrounding messages.
    """
    return get_supabase().get_message_context(
        message_id=message_id, before=before, after=after
    )


def wa_send_message(recipient: str, message: str) -> dict[str, Any]:
    """Send a WhatsApp text message.

    Args:
        recipient: Phone number or JID of the recipient (e.g. "46701234567" or "46701234567@s.whatsapp.net").
        message: Text message content.

    Returns the bridge response with message ID and delivery status.
    """
    return get_bridge().send_message(recipient=recipient, message=message)


TOOLS = [
    wa_list_chats,
    wa_list_messages,
    wa_search_messages,
    wa_get_message_context,
    wa_send_message,
]

_register_module("messages", TOOLS)
