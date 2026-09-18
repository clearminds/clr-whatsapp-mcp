"""WhatsApp linking — show the QR code as an image when not yet paired."""

from __future__ import annotations

import base64
import io
from typing import Any

from mcp.types import ImageContent, TextContent

from clr_whatsapp_mcp.tools import _register_module, get_bridge


def wa_login_qr() -> list[Any]:
    """Show the WhatsApp linking QR code so the account can be paired.

    Call this when WhatsApp is not linked yet (the other tools return nothing
    or an error). It returns a short explanation and, when pairing is needed,
    the QR code as an image to scan with the phone. If already linked, it says
    so and no QR is shown.

    Returns:
        A list with an explanation and, when unlinked, the QR image.
    """
    bridge = get_bridge()
    try:
        status = bridge.get_status()
    except Exception as exc:  # noqa: BLE001
        return [TextContent(type="text",
                            text="Could not reach the WhatsApp bridge: %s" % exc)]
    if status.get("logged_in"):
        return [TextContent(
            type="text",
            text="WhatsApp is already linked to this connector -- no QR "
                 "needed. You can read and send messages.")]
    try:
        data = bridge.get_qr()
    except Exception as exc:  # noqa: BLE001
        return [TextContent(type="text",
                            text="Not linked yet, and the QR could not be "
                                 "fetched: %s" % exc)]
    code = (data or {}).get("qr") or ""
    if not code:
        return [TextContent(
            type="text",
            text="Not linked yet, but no QR is on offer right now -- the "
                 "bridge may still be starting, or the last code expired. "
                 "Try again in a few seconds.")]

    import segno

    buf = io.BytesIO()
    segno.make(code, error="m").save(buf, kind="png", scale=6, border=2)
    png = buf.getvalue()
    explanation = (
        "This is the WhatsApp linking QR code. On your phone open WhatsApp -> "
        "Settings -> Linked devices -> Link a device, and scan this image. It "
        "links this connector as a WhatsApp companion device so it can read "
        "and send your messages. The code rotates about every 20 seconds; if "
        "it has expired, call this tool again for a fresh one.")
    return [
        TextContent(type="text", text=explanation),
        ImageContent(type="image",
                     data=base64.b64encode(png).decode(), mimeType="image/png"),
    ]


TOOLS = [wa_login_qr]

_register_module("auth", TOOLS)
