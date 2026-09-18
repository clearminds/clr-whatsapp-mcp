"""WhatsApp MCP tools — modular registration."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from clr_whatsapp_mcp.bridge import BridgeClient
    from clr_whatsapp_mcp.supabase_client import WhatsAppSupabase

_bridge: BridgeClient | None = None
_supabase: WhatsAppSupabase | None = None


def set_bridge(b: BridgeClient) -> None:
    """Set the global bridge client instance.

    Args:
        b: An initialized BridgeClient.
    """
    global _bridge
    _bridge = b


def get_bridge() -> BridgeClient:
    """Return the global bridge client, raising if not yet initialized.

    Returns:
        The shared BridgeClient instance.

    Raises:
        AssertionError: If set_bridge() has not been called.
    """
    assert _bridge is not None, "Bridge client not initialized — call set_bridge() first"
    return _bridge


def set_supabase(s: WhatsAppSupabase) -> None:
    """Set the global Supabase client instance.

    Args:
        s: An initialized WhatsAppSupabase client.
    """
    global _supabase
    _supabase = s


def get_supabase() -> WhatsAppSupabase:
    """Return the global Supabase client, raising if not yet initialized.

    Returns:
        The shared WhatsAppSupabase instance.

    Raises:
        AssertionError: If set_supabase() has not been called.
    """
    assert _supabase is not None, "Supabase client not initialized — call set_supabase() first"
    return _supabase


# Module registry — each value is a list of tool functions.
MODULES: dict[str, list[Callable[..., Any]]] = {}

ALL_MODULE_NAMES: tuple[str, ...] = ("auth", "messages", "contacts", "groups", "media", "status")


def _register_module(name: str, tools: list[Callable[..., Any]]) -> None:
    """Register a list of tool functions under a module name.

    Args:
        name: The module name (e.g. "messages", "contacts").
        tools: List of tool callable functions to register.
    """
    MODULES[name] = tools


# Import submodules so they self-register via _register_module.
from clr_whatsapp_mcp.tools import (  # noqa: E402, F401
    auth,
    contacts,
    groups,
    media,
    messages,
    status,
)
