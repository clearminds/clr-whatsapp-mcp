"""WhatsApp contact tools — search contacts."""

from __future__ import annotations

from typing import Any

from clr_whatsapp_mcp.tools import _register_module, get_supabase


def wa_search_contacts(query: str) -> list[dict[str, Any]]:
    """Search WhatsApp contacts by name, phone number, or JID.

    Args:
        query: Search string to match against contact name, phone, or jid fields (case-insensitive).

    Returns:
        A list of matching contact records.
    """
    return get_supabase().search_contacts(query=query)


TOOLS = [
    wa_search_contacts,
]

_register_module("contacts", TOOLS)
