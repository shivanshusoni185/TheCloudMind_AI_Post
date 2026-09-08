# TheCloudMind.ai MCP server

A **read-only** [Model Context Protocol](https://modelcontextprotocol.io) server
that exposes the public news + jobs data of https://cloudmindai.in as tools, so
Claude (Desktop, Code, or a claude.ai custom connector) can browse and search
the site.

## Tools

| Tool | What it does |
|------|--------------|
| `search_articles(query, tag, limit)` | Search news by text / tag |
| `list_recent_articles(limit)` | Newest published articles |
| `get_article(slug)` | Full article body (Markdown) |
| `search_jobs(query, category, tag, remote_only, limit)` | Search the jobs board |
| `get_job(slug)` | Full job posting |
| `list_job_categories()` | All job categories |
| `get_overview()` | Counts + top article tags |

All data is already public on the website; nothing here can write to or modify
the site.

## Install

```bash
cd mcp-server
python -m venv .venv
# Windows:  .venv\Scripts\python -m pip install -r requirements.txt
# macOS/Linux: .venv/bin/python -m pip install -r requirements.txt
```

## A) Local use — Claude Code / Claude Desktop (stdio)

No hosting or token needed; runs on your machine.

### Claude Code (CLI)

```bash
claude mcp add thecloudmind -- /ABS/PATH/mcp-server/.venv/Scripts/python /ABS/PATH/mcp-server/server.py
```

(Use `.venv/bin/python` on macOS/Linux.) Then `/mcp` inside Claude Code to confirm it's connected.

### Claude Desktop

Add to `claude_desktop_config.json`
(Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "thecloudmind": {
      "command": "C:\\ABS\\PATH\\mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["C:\\ABS\\PATH\\mcp-server\\server.py"]
    }
  }
}
```

Restart Claude Desktop.

## B) Remote use — claude.ai / Claude Desktop custom connector (HTTPS)

Run the server in **streamable-http** mode behind your existing nginx/HTTPS and
gate it with a static bearer token.

### 1. Run it (on the VPS)

```bash
MCP_TRANSPORT=http \
MCP_HOST=127.0.0.1 \
MCP_PORT=8765 \
MCP_AUTH_TOKEN='choose-a-long-random-secret' \
/opt/cloudmind/mcp-server/.venv/bin/python /opt/cloudmind/mcp-server/server.py
```

(Best run as a systemd unit or a Docker service — see below.)

### 2. Proxy it with nginx

Inside the `server { listen 443 ... cloudmindai.in }` block, add:

```nginx
location /mcp {
    proxy_pass         http://127.0.0.1:8765/mcp;
    proxy_http_version 1.1;
    proxy_set_header   Host $host;
    proxy_set_header   Connection "";      # keep-alive for SSE streaming
    proxy_set_header   X-Forwarded-For $remote_addr;
    proxy_buffering    off;                # required: don't buffer the SSE stream
    proxy_read_timeout 3600s;
}
```

Reload nginx. The endpoint is now `https://cloudmindai.in/mcp`.

### 3. Add it in Claude

- **Claude Desktop / Code (custom connector, header auth):** add a remote MCP
  server with URL `https://cloudmindai.in/mcp` and header
  `Authorization: Bearer <your token>`.
- **claude.ai web connectors:** the custom-connector UI expects OAuth for a
  fully polished connector; header-token remote servers are supported best from
  Claude Desktop/Code today. (OAuth can be layered on later without changing the
  tools.)

## Configuration (env vars)

| Var | Default | Meaning |
|-----|---------|---------|
| `TCM_API_BASE` | `https://cloudmindai.in/api` | Public API base URL |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `http` |
| `MCP_HOST` | `0.0.0.0` | Bind host (http) |
| `MCP_PORT` | `8765` | Bind port (http) |
| `MCP_PATH` | `/mcp` | URL path (http) |
| `MCP_AUTH_TOKEN` | _(empty)_ | If set (http), requires `Authorization: Bearer <token>` |
