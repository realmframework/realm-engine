# Developer Integrations, CLI, MCP & Public API

REALM Engine works both as a standalone desktop/web workspace and as a local knowledge backend for editors, terminals, AI clients, and static documentation sites.

---

## 1. Local OpenAI-Compatible API (`/v1`)

Connect **VS Code**, **Cursor**, **Raycast**, **Apple Shortcuts**, or custom scripts directly to your grounded local vaults:

1. Enable **Local OpenAI-Compatible API (`/v1`)** in **Settings → AI & Voice** (or start with `REALM_ENABLE_LOCAL_API=1`).
2. Optionally set `REALM_LOCAL_API_TOKEN` in `.env` / environment to require a `Bearer` token on `/v1/*` requests.
3. Point your client to the Base URL displayed in Settings (default `http://127.0.0.1:8000/v1`).

**Security notes:**
- Strictly **loopback-only** (`127.0.0.1` / `::1`) — requests from non-loopback peers or missing client metadata fail closed with `403`.
- Cross-site browser requests are blocked by the `Sec-Fetch-Site` / `Origin` middleware.
- Supported endpoints: `GET /v1/models` and `POST /v1/chat/completions` (non-streaming and SSE streaming).

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"realm-local","messages":[{"role":"user","content":"Summarize our onboarding guide"}]}'
```

---

## 2. Terminal CLI (`realm-engine ask`)

Query your vaults directly from any shell or script without opening the browser:

```bash
# Grounded answer using the active area
realm-engine ask "How does Hybrid RRF scoring work?"

# Target a specific area and output machine-readable JSON
realm-engine ask --area engineering --json "List our ADR conventions"

# Print version
realm-engine --version
```

`realm-engine ask` respects `excluded_subfolders` and works identically from source (`uv run python main.py ask ...`), installed Python wheels, and packaged desktop binaries.

---

## 3. Model Context Protocol Server (`realm-engine mcp`)

Expose your local REALM vaults to **Claude Desktop**, **Cursor**, **VS Code**, or any MCP-compatible host over `stdio`:

```json
{
  "mcpServers": {
    "realm-engine": {
      "command": "realm-engine",
      "args": ["mcp"],
      "env": {
        "REALM_DATA_DIR": "/path/to/your/realm/data",
        "REALM_MCP_AREAS": "knowledge_base,engineering"
      }
    }
  }
}
```

If running directly from a source checkout, replace `"command": "realm-engine", "args": ["mcp"]` with `"command": "uv", "args": ["run", "--directory", "/path/to/realm-engine", "python", "main.py", "mcp"]`.

**MCP Safety Guarantees:**
- Read-only vault tools respecting case-insensitive `excluded_subfolders` and optional `REALM_MCP_AREAS` allowlist.
- Bounded 256 KiB JSON-RPC stdin line reads, `O_NOFOLLOW` symlink protection, and sanitized error messages.

---

## 4. Headless Read-Only Public API (`REALM_MODE=public`)

Publish selected vaults as a stateless, read-only JSON API for static websites, Next.js docs, or internal portals:

```bash
REALM_MODE=public \
REALM_PUBLIC_AREAS=my_docs,guides \
REALM_PUBLIC_PROVIDER=kimi \
REALM_PUBLIC_MODEL=kimi-k3.1-pro \
REALM_PUBLIC_URL_TEMPLATE="/docs/{area}/{doc_id}" \
REALM_PUBLIC_ORIGINS="https://docs.example.com" \
REALM_PUBLIC_TRUSTED_PROXIES="127.0.0.1,::1" \
uv run python main.py --public --host 0.0.0.0 --port 8000
```

### Mounted Endpoints
| Endpoint | Purpose |
|---|---|
| `GET /healthz` | Liveness probe returning app version and mode (used by Docker `HEALTHCHECK`). |
| `GET /api/public/health` | Loaded areas, document/chunk counts, embedding status, and server-locked model name. |
| `GET /api/public/meta` | Published areas, topic counts, starter prompts, and guide metadata with canonical URLs. |
| `GET /api/public/search` | Stateless BM25 / Hybrid RRF search + Auto-Router with `#section` anchors. |
| `POST /api/public/ask` | Stateless grounded Tutor using the server-locked provider/model (visitors cannot override keys/models). |
| `GET /api/public/graph` | 2D constellation nodes & links with sanitized canonical URLs. |

### Public Mode Hardening
- **Fail-Closed Area Selection:** Refuses to expose vaults if `REALM_PUBLIC_AREAS` is unset or empty, and filters out `excluded_subfolders` configured in `workspace.json`.
- **Unmounted Admin Surface:** All local write, upload, settings, secret, backup, and GDPR scrub routes are completely unmounted (`404`).
- **Complete Quota Accounting & Graceful Degradation:** Tracks combined embedding + LLM + conversation history cost per IP (`REALM_PUBLIC_IP_RPM`, `REALM_PUBLIC_IP_DAILY`) and globally (`REALM_PUBLIC_DAILY_LIMIT`, `REALM_PUBLIC_DAILY_USD`) with a per-process random IP salt, never touches local `budget_state.json` (safe on read-only containers), and falls back cleanly to `$0` search results (`fallback_mode: "search_only"`, header `X-Realm-Fallback: quota_limit`).
- **Trusted Proxy Verification:** Only honors `X-Forwarded-For` from loopback or IPs explicitly listed in `REALM_PUBLIC_TRUSTED_PROXIES`.
