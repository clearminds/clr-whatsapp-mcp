"""WhatsApp MCP Server — FastMCP tools for WhatsApp via Go bridge + Supabase."""

import argparse
import logging
import sys
from typing import Any

from fastmcp import FastMCP

from clr_whatsapp_mcp.bridge import BridgeClient
from clr_whatsapp_mcp.config import Settings, configure_logging
from clr_whatsapp_mcp.supabase_client import WhatsAppSupabase
from clr_whatsapp_mcp.middleware import ToolValidationMiddleware
from clr_whatsapp_mcp.tools import ALL_MODULE_NAMES, MODULES, set_bridge, set_supabase


# Tool names that perform write/mutating operations.
WRITE_TOOLS = ["wa_send_message", "wa_send_file"]


def parse_cli_args() -> dict[str, Any]:
    """Parse CLI arguments for configuration overrides.

    Returns:
        A dict of setting overrides keyed by Settings field names.
    """
    parser = argparse.ArgumentParser(description="WhatsApp MCP Server")

    parser.add_argument("--bridge-url", type=str, help="WhatsApp bridge URL")
    parser.add_argument("--supabase-url", type=str, help="Supabase project URL")
    parser.add_argument("--supabase-key", type=str, help="Supabase anon key")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default=None,
        help="MCP transport (stdio or sse)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Log level",
    )

    args = parser.parse_args()

    overlay: dict[str, Any] = {}
    if args.bridge_url is not None:
        overlay["whatsapp_bridge_url"] = args.bridge_url
    if args.supabase_url is not None:
        overlay["whatsapp_supabase_url"] = args.supabase_url
    if args.supabase_key is not None:
        overlay["whatsapp_supabase_key"] = args.supabase_key
    if args.transport is not None:
        overlay["whatsapp_transport"] = args.transport
    if args.log_level is not None:
        overlay["whatsapp_log_level"] = args.log_level

    return overlay


def main() -> None:
    """Main entry point for the WhatsApp MCP server."""
    cli_overlay = parse_cli_args()

    try:
        settings = Settings(**cli_overlay)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    configure_logging(settings.whatsapp_log_level)
    logger = logging.getLogger(__name__)

    creds = settings.load_credentials()

    logger.info("Starting WhatsApp MCP Server")
    logger.info(
        "Config: bridge_url=%s supabase_url=%s transport=%s",
        creds.get("bridge_url", ""),
        creds.get("supabase_url", "")[:40] + "..." if creds.get("supabase_url", "") else "",
        settings.whatsapp_transport,
    )

    # Validate required credentials
    if not creds.get("supabase_url") or not creds.get("supabase_key"):
        logger.error(
            "Missing required Supabase credentials. Set WHATSAPP_SUPABASE_URL and "
            "WHATSAPP_SUPABASE_KEY env vars or create ~/.config/whatsapp/credentials.json"
        )
        sys.exit(1)

    # Initialize clients
    try:
        bridge = BridgeClient(base_url=creds["bridge_url"])
        set_bridge(bridge)
        logger.debug("Bridge client initialized: %s", creds["bridge_url"])
    except Exception as e:
        logger.error("Failed to initialize bridge client: %s", e)
        sys.exit(1)

    try:
        supabase = WhatsAppSupabase(
            supabase_url=creds["supabase_url"],
            supabase_key=creds["supabase_key"],
        )
        set_supabase(supabase)
        logger.debug("Supabase client initialized")
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", e)
        sys.exit(1)

    # Create FastMCP and register all tool modules
    mcp = FastMCP("WhatsApp")
    mcp.add_middleware(ToolValidationMiddleware())

    tool_count = 0
    for mod_name in ALL_MODULE_NAMES:
        tools = MODULES.get(mod_name, [])
        for func in tools:
            mcp.tool()(func)
            tool_count += 1
        logger.info("Loaded module '%s' (%d tools)", mod_name, len(tools))

    logger.info("Total tools registered: %d", tool_count)

    if settings.whatsapp_read_only and WRITE_TOOLS:
        removed = 0
        for name in WRITE_TOOLS:
            try:
                mcp.remove_tool(name)
                removed += 1
            except Exception:
                pass
        logger.info("Read-only mode: %d write tools removed", removed)

    # Start the server
    try:
        transport = settings.whatsapp_transport
        logger.info("Starting %s transport", transport)
        if transport == "stdio":
            mcp.run(transport=transport)
        else:
            # http/sse: bind all interfaces so the container is reachable
            # behind the gateway's auth-proxy. Host/port overridable by env.
            import os

            mcp.run(
                transport=transport,
                host=os.environ.get("MCP_HOST", "0.0.0.0"),
                port=int(os.environ.get("MCP_PORT", "8000")),
            )
    except Exception as e:
        logger.error("Failed to start MCP server: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
