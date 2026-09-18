"""HTTP client for the WhatsApp Go bridge REST API (writes only).

The Go bridge handles all WhatsApp protocol interaction. This client
calls its REST endpoints for sending messages, files, downloading media,
and checking health/sync status.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class BridgeClient:
    """REST client for the WhatsApp Go bridge."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def send_message(self, recipient: str, message: str) -> dict[str, Any]:
        """Send a text message via the bridge.

        Args:
            recipient: JID or phone number of the recipient.
            message: Text message content.

        Returns:
            Bridge response with message ID and status.
        """
        resp = self._client.post(
            f"{self.base_url}/api/send",
            json={"recipient": recipient, "message": message},
        )
        resp.raise_for_status()
        return resp.json()

    def send_file(
        self, recipient: str, media_path: str, message: str = ""
    ) -> dict[str, Any]:
        """Send a file/media message via the bridge.

        Args:
            recipient: JID or phone number of the recipient.
            media_path: Path to the media file (accessible by the bridge).
            message: Optional caption text.

        Returns:
            Bridge response with message ID and status.
        """
        payload: dict[str, Any] = {
            "recipient": recipient,
            "media_path": media_path,
        }
        if message:
            payload["message"] = message

        resp = self._client.post(
            f"{self.base_url}/api/send",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    def download_media(self, message_id: str, chat_jid: str) -> dict[str, Any]:
        """Download media from a received message.

        Args:
            message_id: The WhatsApp message ID.
            chat_jid: The chat JID the message belongs to.

        Returns:
            Bridge response with download path or base64 data.
        """
        resp = self._client.post(
            f"{self.base_url}/api/download",
            json={"message_id": message_id, "chat_jid": chat_jid},
        )
        resp.raise_for_status()
        return resp.json()

    def health_check(self) -> bool:
        """Check if the bridge is healthy.

        Returns:
            True if bridge is reachable and healthy.
        """
        try:
            resp = self._client.get(f"{self.base_url}/api/status")
            return resp.status_code == 200
        except httpx.HTTPError:
            logger.warning("Bridge health check failed")
            return False

    def get_qr(self) -> dict[str, Any]:
        """Fetch the current pairing QR and link status from the bridge.

        Returns:
            Dict with ``logged_in`` (bool) and ``qr`` (the whatsmeow code
            string, empty once linked).
        """
        resp = self._client.get(f"{self.base_url}/api/qr")
        resp.raise_for_status()
        return resp.json()

    def get_status(self) -> dict[str, Any]:
        """Get detailed bridge status.

        Returns:
            Bridge status including connection state, uptime, etc.
        """
        resp = self._client.get(f"{self.base_url}/api/status")
        resp.raise_for_status()
        return resp.json()

    def trigger_sync(self) -> dict[str, Any]:
        """Trigger a history sync on the bridge.

        Returns:
            Bridge response confirming sync was triggered.
        """
        resp = self._client.post(f"{self.base_url}/api/sync", json={})
        resp.raise_for_status()
        return resp.json()
