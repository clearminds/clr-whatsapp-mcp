"""WhatsApp status tools — health checks, stats, sync."""

from __future__ import annotations

from typing import Any

from clr_whatsapp_mcp.tools import _register_module, get_bridge, get_supabase


def wa_status() -> dict[str, Any]:
    """Get WhatsApp system status including bridge health and message statistics.

    Returns:
        Dict with bridge connection status, chat count, message count, and latest message time.
    """
    bridge = get_bridge()
    supabase = get_supabase()

    bridge_healthy = bridge.health_check()
    bridge_status: dict[str, Any] = {}
    if bridge_healthy:
        try:
            bridge_status = bridge.get_status()
        except Exception:
            bridge_status = {"status": "reachable but status endpoint failed"}

    stats = supabase.get_stats()

    return {
        "bridge_healthy": bridge_healthy,
        "bridge_status": bridge_status,
        "chat_count": stats.get("chat_count", 0),
        "message_count": stats.get("message_count", 0),
        "latest_message_time": stats.get("latest_message_time"),
    }


def wa_sync() -> dict[str, Any]:
    """Trigger a WhatsApp history sync on the bridge.

    Asks the Go bridge to re-sync message history from WhatsApp servers.

    Returns:
        The bridge response confirming the sync was triggered.
    """
    return get_bridge().trigger_sync()


TOOLS = [
    wa_status,
    wa_sync,
]

_register_module("status", TOOLS)
