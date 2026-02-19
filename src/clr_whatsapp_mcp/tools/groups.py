"""WhatsApp group tools — list and inspect groups."""

from __future__ import annotations

from typing import Any

from clr_whatsapp_mcp.tools import _register_module, get_supabase


def wa_list_groups(limit: int = 50) -> list[dict[str, Any]]:
    """List WhatsApp group chats.

    Args:
        limit: Maximum number of groups to return (default 50).

    Returns a list of group chats ordered by most recent message.
    """
    return get_supabase().list_groups(limit=limit)


def wa_get_group_info(chat_jid: str) -> dict[str, Any]:
    """Get details for a WhatsApp group chat.

    Args:
        chat_jid: The group chat JID (e.g. "120363012345678901@g.us").

    Returns the group chat record or an error if not found.
    """
    result = get_supabase().get_chat(chat_jid=chat_jid)
    if result is None:
        return {"error": f"Group not found: {chat_jid}"}
    return result


TOOLS = [
    wa_list_groups,
    wa_get_group_info,
]

_register_module("groups", TOOLS)
