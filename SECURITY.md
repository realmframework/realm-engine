# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| `0.3.x` / `main` | Yes |
| `< 0.3.0` | No (please upgrade) |

## Security Model & Trust Boundaries

REALM Knowledge Engine is designed as a **single-user, local-first application** with an optional **stateless read-only Public API (`REALM_MODE=public`)**:

- **Strict Local-Only Lock (Default ON):** Blocks server-side cloud LLM, embedding, model-discovery, cloud TTS, dictation, web search, and web clipping routes, and enforces loopback-only `OLLAMA_HOST` unless `REALM_ALLOW_REMOTE_OLLAMA=1` is explicitly set.
- **Localhost Defense-in-Depth:** Binds to `127.0.0.1` by default, rejects spoofed `Host` / duplicate security headers, enforces same-origin `Origin` / `Referer` / `Sec-Fetch-Site` checks and Content-Type guards on state-changing routes, blocks cross-site `GET` requests to `/api/*` and `/v1/*`, and attaches CSP, `Cross-Origin-Resource-Policy: same-origin`, `Cross-Origin-Opener-Policy: same-origin`, and `Cache-Control: no-store`.
- **SSRF & File Boundary Enforcement:** Outbound web clipping and SearXNG requests resolve DNS, reject private/loopback/link-local/multicast/CGNAT/NAT64/cloud-metadata IPs, and pin connections per hop. Vault file reads/writes enforce canonical path containment (`O_NOFOLLOW`), case-insensitive `excluded_subfolders` filtering, and bounded archive/XML/upload sizes.
- **Secret Handling:** Saved API keys live in `<data_dir>/secrets.json` (`0600`), are excluded from ZIP backups and diagnostics, are never sent back to the browser in plaintext, and are scrubbed from error responses and rotating logs.

See [docs/PRIVACY_AND_COMPLIANCE.md](docs/PRIVACY_AND_COMPLIANCE.md) for the complete security architecture and compliance boundaries.

## Reporting a Vulnerability

**Please do not report security vulnerabilities in public GitHub issues.**

1. Use **GitHub Private Vulnerability Reporting** on this repository (**Security → Advisories → Report a vulnerability**).
2. Include a clear description of the issue, affected component/version, reproduction steps or proof-of-concept, and any suggested mitigation.
3. Expect an acknowledgement within **72 hours** and a remediation timeline once reproduced. Coordinated disclosure will credit reporters unless anonymity is requested.
