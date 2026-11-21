# Privacy, Security & Compliance Architecture

REALM Knowledge Engine is built around a **local-first, defense-in-depth** architecture designed for personal, engineering, and regulated-environment knowledge bases.

---

## 1. Strict Local-Only Lock (Default ON)

Every fresh installation starts with **Strict Local-Only Lock** enabled:

- Blocks all server-side cloud LLM chat/streaming, cloud embeddings, cloud model discovery, cloud TTS, browser dictation, opt-in web search, and web clipping endpoints.
- Rejects Ollama model identifiers containing `cloud` while locked.
- Enforces **loopback-only `OLLAMA_HOST`** (`127.0.0.1`, `::1`, `localhost`) while locked unless you explicitly opt in via `REALM_ALLOW_REMOTE_OLLAMA=1` (for example, Docker targeting `host.docker.internal`).
- Serves 100% of CSS, JavaScript, icons, and fonts locally with **zero third-party CDN requests or telemetry**.

> **Boundary note:** Strict Local-Only Lock is an application admission control, not an OS firewall. For air-gapped compliance, pair it with OS/network egress rules.

---

## 2. Localhost HTTP & Browser Perimeter (`core/http_guard.py`)

Because local web apps run on `127.0.0.1`, malicious browser tabs could attempt DNS rebinding or cross-site requests. REALM enforces multiple layers in middleware:

- **Host & Header Hygiene:** Rejects missing, malformed, userinfo-bearing, or non-loopback `Host` headers and rejects duplicate security-sensitive headers (`Host`, `Origin`, `Referer`, `Sec-Fetch-Site`, `Content-Type`, `Authorization`, `Content-Length`).
- **CSRF & Cross-Site Protection:** Blocks cross-site `GET` requests to `/api/*` and `/v1/*`; enforces same-origin `Sec-Fetch-Site`, `Origin`, and `Referer` checks on all state-changing requests; rejects CSRF-prone `Content-Type` values (`text/plain`, `application/x-www-form-urlencoded`, non-upload `multipart/form-data`).
- **Security Headers:** Attaches strict `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cross-Origin-Resource-Policy: same-origin`, `Cross-Origin-Opener-Policy: same-origin`, and `Cache-Control: no-store` on API routes.
- **Safe Error Handling:** 422 validation errors strip raw user input (`input` field), 500 errors hide Python stack traces, and stream/log error helpers redact API keys and bearer tokens (`scrub_secrets`).

---

## 3. Outbound SSRF & File Boundary Protection (`core/net_security.py`)

- **Web Clipper & SearXNG:** Resolve DNS explicitly, block loopback, private RFC 1918/4193, link-local, multicast, CGNAT (`100.64.0.0/10`), NAT64 (`64:ff9b::/96`, `64:ff9b:1::/48`), and cloud metadata IPs (`169.254.169.254`, `100.100.100.200`, `192.0.0.192`, `fd00:ec2::254`), restrict ports to `{80, 443, 8080, 8443}`, validate `Content-Type` before reading, and pin connections per redirect hop.
- **Document & Archive Safety:** Enforces `15 MiB` per-file upload/local-ingest cap (`64 MiB` batch, `30 MiB` preview, `25 MiB` audio), `20 MiB` per-member / `40 MiB` cumulative Office XML decompression cap, `O_NOFOLLOW` symlink checks, canonical path containment, and system-directory blocking on folder linking/importing.
- **Excluded Subfolders:** Unloaded subfolders are enforced consistently with Unicode NFC + `.casefold()` matching across UI search, chat, preview, editor, CLI, MCP, and Public API — preventing case-sensitivity bypasses on macOS (APFS) and Windows (NTFS).
- **Prompt-Injection Defense:** Retrieved passages are XML-escaped inside `<untrusted_document_context>` delimiters accompanied by system instructions treating document text strictly as data, never executable instructions.

---

## 4. Secrets, Durability & Sanitized Diagnostics

- **Secret Storage:** API keys saved in Settings live in `<data_dir>/secrets.json` with `0o600` (owner-only) permissions, written atomically with `os.fsync()`. Plaintext keys are never echoed back to the browser, never included in ZIP backups, and never printed in logs or diagnostics.
- **Crash Durability:** Vault indexes (`index.json` with `schema_version` and `embedding_model` metadata), chats, workspace config, budgets, custom formats, and linked vaults use atomic temp-file + `os.fsync()` + `os.replace()` writes and preserve corrupt files as `.corrupt` / `.corrupt.<timestamp>` backups instead of silently discarding them.
- **Structured Logging & Diagnostics:** Rotating `0o600` logs (`<data_dir>/logs/realm-engine.log`, 5 MiB × 3) pass through a secret-redacting filter. Inspect app version, Python/platform info, loaded Ollama models, and copy a **Sanitized Diagnostics Report** inside **Settings → Privacy & GDPR Audit → System Diagnostics & About** (`GET /api/diagnostics`).

---

## 5. GDPR / DSGVO & EU AI Act Tooling

- **PII Preview & Vault Scrub:** Detect or redact emails, IBANs, phone numbers, filename-derived names, IPv4 addresses, EU/German dates (`DOB`), health IDs (`HEALTH_ID`), and postal/street addresses before importing or across an existing vault. Always review previews manually for false positives or edge cases.
- **Backup Hygiene:** Exported `.zip` backups strip host filesystem paths (`file_path`) and raw embedding float arrays, and exclude `secrets.json`, raw binaries, model weights, and `budget_state.json`.
- **Compliance Audit Reports:** Generate a downloadable Markdown technical summary mapping controls to **GDPR Articles 25 & 32** and **EU AI Act Articles 10, 13 & 15**. These technical artifacts assist internal review and do not constitute formal legal certification.
