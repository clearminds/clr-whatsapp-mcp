"""WhatsApp MCP tools — modular registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clr_whatsapp_mcp.bridge import BridgeClient
    from clr_whatsapp_mcp.supabase_client import WhatsAppSupabase

_bridge: BridgeClient | None = None
_supabase: WhatsAppSupabase | None = None


def set_bridge(b: BridgeClient) -> None:
    global _bridge
    _bridge = b


def get_bridge() -> BridgeClient:
    assert _bridge is not None, "Bridge client not initialized — call set_bridge() first"
    return _bridge


def set_supabase(s: WhatsAppSupabase) -> None:
    global _supabase
    _supabase = s


def get_supabase() -> WhatsAppSupabase:
    assert _supabase is not None, "Supabase client not initialized — call set_supabase() first"
    return _supabase


# Module registry — each value is a list of tool functions.
MODULES: dict[str, list] = {}

ALL_MODULE_NAMES = ("messages", "contacts", "groups", "media", "status")


def _register_module(name: str, tools: list) -> None:
    MODULES[name] = tools


# Import submodules so they self-register via _register_module.
from clr_whatsapp_mcp.tools import (  # noqa: E402, F401
    contacts,
    groups,
    media,
    messages,
    status,
)
