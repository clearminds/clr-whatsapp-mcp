# clr-whatsapp-mcp

[![PyPI](https://img.shields.io/pypi/v/clr-whatsapp-mcp)](https://pypi.org/project/clr-whatsapp-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

MCP server for WhatsApp messaging -- read conversations, search messages, send texts, and manage media through AI assistants like Claude.

## Features

- **Chat browsing** -- list and filter WhatsApp chats by name
- **Message history** -- read messages with date range and content filters
- **Full-text search** -- search messages across all chats or within a single chat
- **Message context** -- view surrounding messages for any message ID
- **Send messages** -- send text messages to contacts or groups
- **Media support** -- send files and download media from received messages
- **Contact search** -- find contacts by name, phone number, or JID
- **Group management** -- list group chats and view group details
- **System status** -- health checks, message statistics, and history sync
- **Split architecture** -- Go bridge handles WhatsApp protocol, Supabase stores data, Python serves MCP tools

## Installation

```bash
pip install clr-whatsapp-mcp
# or
uvx clr-whatsapp-mcp
```

## Configuration

**Preferred:** Configuration file at `~/.config/whatsapp/credentials.json` (chmod 600):

```json
{
  "bridge_url": "http://localhost:8080",
  "supabase_url": "https://your-project.supabase.co",
  "supabase_key": "your-supabase-anon-key"
}
```

**Alternative:** Environment variables are also supported:

| Variable | Description | Example |
|----------|-------------|---------|
| `WHATSAPP_BRIDGE_URL` | Go bridge REST API URL | `http://localhost:8080` |
| `WHATSAPP_SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `WHATSAPP_SUPABASE_KEY` | Supabase anon/service key | `eyJhbGci...` |

Optional:

| Variable | Description | Default |
|----------|-------------|---------|
| `WHATSAPP_TRANSPORT` | Transport protocol (`stdio` or `sse`) | `stdio` |
| `WHATSAPP_LOG_LEVEL` | Log level | `INFO` |

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "uvx",
      "args": ["clr-whatsapp-mcp"]
    }
  }
}
```

### Claude Code

Add via CLI:

```bash
claude mcp add whatsapp -- uvx clr-whatsapp-mcp
```

Or add to your `.mcp.json`:

```json
{
  "whatsapp": {
    "command": "uvx",
    "args": ["clr-whatsapp-mcp"]
  }
}
```

### VS Code

Add to your VS Code settings or `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "whatsapp": {
        "command": "uvx",
        "args": ["clr-whatsapp-mcp"]
      }
    }
  }
}
```

**Note:** Configuration is read from `~/.config/whatsapp/credentials.json` or environment variables. No need to specify credentials in MCP config files.

## Tools

### Messages

| Tool | Description | Parameters |
|------|-------------|------------|
| `wa_list_chats` | List chats, optionally filtered by name | `query?`, `limit?` |
| `wa_list_messages` | List messages in a chat with date/content filters | `chat_jid`, `limit?`, `after?`, `before?`, `query?` |
| `wa_search_messages` | Search messages by content across all chats | `query`, `chat_jid?`, `limit?` |
| `wa_get_message_context` | Get a message and its surrounding messages | `message_id`, `before?`, `after?` |
| `wa_send_message` | Send a text message | `recipient`, `message` |

### Contacts

| Tool | Description | Parameters |
|------|-------------|------------|
| `wa_search_contacts` | Search contacts by name, phone number, or JID | `query` |

### Groups

| Tool | Description | Parameters |
|------|-------------|------------|
| `wa_list_groups` | List group chats ordered by most recent message | `limit?` |
| `wa_get_group_info` | Get details for a group chat | `chat_jid` |

### Media

| Tool | Description | Parameters |
|------|-------------|------------|
| `wa_send_file` | Send a file/media message with optional caption | `recipient`, `media_path`, `message?` |
| `wa_download_media` | Download media from a received message | `message_id`, `chat_jid` |

### Status

| Tool | Description | Parameters |
|------|-------------|------------|
| `wa_status` | Get bridge health, chat count, message count, and latest message time | -- |
| `wa_sync` | Trigger a WhatsApp history sync on the bridge | -- |

## Example Usage

Once connected, you can ask your AI assistant things like:

- "Show me my recent WhatsApp chats"
- "What messages did I get from Daniel today?"
- "Search all chats for messages about the meeting"
- "Send a message to +46701234567 saying I'm running late"
- "Show me the context around that message"
- "What group chats am I in?"
- "Is the WhatsApp bridge healthy?"
- "Trigger a history sync"

## Safety

### Read-only tools (query data only)

- `wa_list_chats`, `wa_list_messages`, `wa_search_messages`, `wa_get_message_context`
- `wa_search_contacts`
- `wa_list_groups`, `wa_get_group_info`
- `wa_status`

### Write tools (perform actions)

- `wa_send_message` -- sends a text message to a recipient
- `wa_send_file` -- sends a file/media message to a recipient
- `wa_download_media` -- downloads media from the bridge (no WhatsApp-side effect)
- `wa_sync` -- triggers a history re-sync on the bridge (non-destructive)

No tools modify or delete existing messages, contacts, or group settings.

## Technical Notes

### Architecture

This MCP server uses a split architecture with three components:

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Python MCP      │      │  Go Bridge       │      │  Supabase        │
│  (this server)   │─────>│  (WhatsApp       │─────>│  (PostgreSQL     │
│                  │      │   protocol)      │      │   data store)    │
│  Reads from      │      │  Sends messages  │      │  Chats, messages │
│  Supabase +      │      │  Receives msgs   │      │  contacts, media │
│  sends via       │      │  Syncs history   │      │  metadata        │
│  bridge          │      │  Writes to       │      │                  │
│                  │<─────│  Supabase        │      │                  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
     MCP tools              REST API on              Queried by Python
     (stdio/sse)            :8080                    via supabase-py
```

- **Go bridge** -- handles WhatsApp Web protocol (via whatsmeow), receives and sends messages, writes all data to Supabase in real-time
- **Supabase** -- PostgreSQL database storing chats, messages, contacts, and media metadata; the Go bridge is the only writer
- **Python MCP server** (this package) -- reads from Supabase for all query operations, calls the Go bridge REST API for send/sync operations

### Key design decisions

- **Read path** (Supabase): All query/search/list tools read from Supabase, giving fast indexed queries without hitting WhatsApp rate limits
- **Write path** (Go bridge): Send and sync operations go through the bridge REST API, which handles the WhatsApp protocol
- **No direct Supabase writes**: The Python MCP server never writes to Supabase -- only the Go bridge does
- **JID format**: WhatsApp uses JIDs (Jabber IDs) like `46701234567@s.whatsapp.net` for contacts and `120363012345678901@g.us` for groups
- **Bridge URL default**: Defaults to `http://localhost:8080` if not configured

## Development

```bash
git clone https://github.com/clearminds/clr-whatsapp-mcp.git
cd clr-whatsapp-mcp
uv sync
uv run clr-whatsapp-mcp
```

## License

MIT
