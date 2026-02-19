"""Supabase reader for all WhatsApp MCP tool queries.

The Go bridge writes WhatsApp data to Supabase in real-time. This client
reads from Supabase for all query/search operations. No writes to Supabase
happen from the Python side.
"""

import logging
from typing import Any

from supabase import Client, create_client

logger = logging.getLogger(__name__)


class WhatsAppSupabase:
    """Read-only Supabase client for WhatsApp data queries."""

    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        self._client: Client = create_client(supabase_url, supabase_key)

    def list_chats(
        self, query: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """List chats, optionally filtered by name.

        Args:
            query: Optional search string to filter chat names (case-insensitive).
            limit: Maximum number of chats to return.

        Returns:
            List of chat records ordered by last_message_time descending.
        """
        builder = self._client.table("chats").select("*")

        if query:
            builder = builder.ilike("name", f"%{query}%")

        builder = builder.order("last_message_time", desc=True).limit(limit)
        response = builder.execute()
        return response.data

    def list_messages(
        self,
        chat_jid: str,
        limit: int = 50,
        after: str | None = None,
        before: str | None = None,
        query: str | None = None,
    ) -> list[dict[str, Any]]:
        """List messages in a chat with optional filters.

        Args:
            chat_jid: The chat JID to list messages for.
            limit: Maximum number of messages to return.
            after: Only messages after this ISO timestamp.
            before: Only messages before this ISO timestamp.
            query: Optional content search (case-insensitive).

        Returns:
            List of message records ordered by timestamp descending.
        """
        builder = self._client.table("messages").select("*").eq("chat_jid", chat_jid)

        if after:
            builder = builder.gte("timestamp", after)
        if before:
            builder = builder.lte("timestamp", before)
        if query:
            builder = builder.ilike("content", f"%{query}%")

        builder = builder.order("timestamp", desc=True).limit(limit)
        response = builder.execute()
        return response.data

    def search_messages(
        self,
        query: str,
        chat_jid: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search messages across chats by content.

        Args:
            query: Search string to match against message content (case-insensitive).
            chat_jid: Optional chat JID to restrict search to.
            limit: Maximum number of results.

        Returns:
            List of matching message records.
        """
        builder = self._client.table("messages").select("*")

        builder = builder.ilike("content", f"%{query}%")

        if chat_jid:
            builder = builder.eq("chat_jid", chat_jid)

        builder = builder.order("timestamp", desc=True).limit(limit)
        response = builder.execute()
        return response.data

    def get_message_context(
        self,
        message_id: str,
        before: int = 5,
        after: int = 5,
    ) -> dict[str, Any]:
        """Get a message and its surrounding context.

        Args:
            message_id: The target message ID.
            before: Number of messages before the target to include.
            after: Number of messages after the target to include.

        Returns:
            Dict with 'target' message and 'context' list of surrounding messages.
        """
        # Fetch the target message
        target_resp = (
            self._client.table("messages")
            .select("*")
            .eq("id", message_id)
            .limit(1)
            .execute()
        )

        if not target_resp.data:
            return {"target": None, "context": [], "error": "Message not found"}

        target = target_resp.data[0]
        chat_jid = target["chat_jid"]
        timestamp = target["timestamp"]

        # Fetch messages before the target
        before_resp = (
            self._client.table("messages")
            .select("*")
            .eq("chat_jid", chat_jid)
            .lt("timestamp", timestamp)
            .order("timestamp", desc=True)
            .limit(before)
            .execute()
        )

        # Fetch messages after the target
        after_resp = (
            self._client.table("messages")
            .select("*")
            .eq("chat_jid", chat_jid)
            .gt("timestamp", timestamp)
            .order("timestamp", desc=False)
            .limit(after)
            .execute()
        )

        # Combine: before (reversed to chronological) + target + after
        context = list(reversed(before_resp.data)) + [target] + after_resp.data

        return {"target": target, "context": context}

    def search_contacts(self, query: str) -> list[dict[str, Any]]:
        """Search contacts by name, phone, or JID.

        Args:
            query: Search string to match against name, phone, or jid fields.

        Returns:
            List of matching contact records.
        """
        pattern = f"%{query}%"
        response = (
            self._client.table("contacts")
            .select("*")
            .or_(f"name.ilike.{pattern},phone.ilike.{pattern},jid.ilike.{pattern}")
            .limit(50)
            .execute()
        )
        return response.data

    def list_groups(self, limit: int = 50) -> list[dict[str, Any]]:
        """List group chats.

        Args:
            limit: Maximum number of groups to return.

        Returns:
            List of group chat records ordered by last_message_time descending.
        """
        response = (
            self._client.table("chats")
            .select("*")
            .eq("is_group", True)
            .order("last_message_time", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    def get_chat(self, chat_jid: str) -> dict[str, Any] | None:
        """Get a single chat by JID.

        Args:
            chat_jid: The chat JID.

        Returns:
            Chat record or None if not found.
        """
        response = (
            self._client.table("chats")
            .select("*")
            .eq("jid", chat_jid)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    def get_stats(self) -> dict[str, Any]:
        """Get summary statistics about WhatsApp data.

        Returns:
            Dict with chat_count, message_count, and latest_message_time.
        """
        chats_resp = (
            self._client.table("chats")
            .select("*", count="exact")
            .limit(0)
            .execute()
        )

        messages_resp = (
            self._client.table("messages")
            .select("*", count="exact")
            .limit(0)
            .execute()
        )

        latest_resp = (
            self._client.table("messages")
            .select("timestamp")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )

        latest_time = None
        if latest_resp.data:
            latest_time = latest_resp.data[0]["timestamp"]

        return {
            "chat_count": chats_resp.count or 0,
            "message_count": messages_resp.count or 0,
            "latest_message_time": latest_time,
        }
