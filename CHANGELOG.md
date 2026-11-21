# Changelog

All notable changes to **REALM Knowledge Engine (`realm-engine`)** are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-11-21

### Added
- **Enterprise Security & Localhost Perimeter:** Centralized `core/net_security.py` and `core/http_guard.py` enforcing strict IP pinning (blocking link-local, multicast, CGNAT, NAT64, and cloud IMDS endpoints), strict `Host`/duplicate-header/Origin/`Referer`/`Sec-Fetch-Site` CSRF validation, CSP + `CORP` + `COOP` + `Cache-Control: no-store`, case-insensitive `excluded_subfolders` enforcement across UI/CLI/MCP/Public API, cumulative Office XML decompression limits, and secret redaction across logs and SSE streams.
- **RAM-Safe Local Ollama Coordination & Durability:** Process-wide local Ollama execution gate (`ollama_slot` / `async_ollama_slot`), automatic unload of previous local models when switching local or cloud models, bounded `keep_alive`, `num_predict`, and stream deadlines, `os.fsync()` atomic writes, timestamped `.corrupt.<ts>` recovery backups, and `index.json` schema + embedding model/dimension versioning.
- **Observability & Sanitized Diagnostics:** Centralized `core/version.py`, rotating `0o600` structured logs (`<data_dir>/logs/realm-engine.log`) with secret redaction, `GET /api/diagnostics`, and an in-app **System Diagnostics & About** card inside Settings → Privacy & GDPR Audit.
- **Cross-Platform Desktop & Packaging Hardening:** Native Finder/Windows crash dialogs, clean macOS `⌘Q` server & watcher shutdown, Windows WebView2 and Linux browser fallback, multi-size Windows `.ico` and `VSVersionInfo`, multi-language (EN/DE/ES) Inno Setup installer, non-tarbomb Windows portable ZIP, zero leaked Windows DLLs/Android JARs in macOS `.app` bundles, fixed Docker starter vault seeding, and `site-packages`-safe user data directories for Python wheel installs.
- **Upgraded 4-Tab Quick Guide & Enterprise Documentation:** Roving-tablist **Quick Guide & Shortcuts** (`?` / `⌘/` / `Ctrl+/`), complete EN/DE/ES localization, WCAG 2.1 AA contrast across all 15 Dark/Light palettes, and full `docs/` guides (`USER_GUIDE.md`, `AGENTS_AND_FORMATS.md`, `INTEGRATIONS.md`, `PRIVACY_AND_COMPLIANCE.md`), plus `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and GitHub templates.

### Fixed
- Stripped 768-dimensional float embedding arrays before persisting `chats.json` or emitting SSE sources (~125 KB saved per turn).
- Fixed Public API quota accounting so cloud embeddings no longer bypass LLM + history spend/request tracking, prevented local `budget_state.json` access in read-only containers, added fail-closed `REALM_PUBLIC_AREAS`, and sanitized `/api/public/graph` URLs.
- Fixed `.dockerignore` excluding `examples/starter_vault/` copied by `Dockerfile`.
- Fixed Windows native folder picker UTF-8 path encoding and TopMost z-order, and Linux `zenity` cancel cascade.

## [0.2.0] - 2026-11-20

### Added
- **Multi-Agent System & Answer Formats Studio:** 8 built-in specialist personas (Saga, Lisbeth, Blomkvist, Milton, Erika, Annika, Plague, Palmgren) plus custom agents, `@mention` summons, per-agent model pinning, Second Opinion, and 13 structured Answer Format blueprints with vector PDF and Markdown export.
- **Universal Document Ingestion & Live Workspace Tools:** `.xlsx`, `.pptx`, `.csv`, and `.tsv` extractors alongside `.md`, `.pdf`, `.docx`, `.txt`, `.html`; in-place Linked Local Folders with background file watcher; live Markdown editor (`⌘S`); public Web Clipper; Engine Inspector (`⌘I`) with Context Window meter, lossless Compress Context, and Retrieval X-Ray (Pin/Mute); Quick Jump (`⌘K`); `/` slash commands.
- **Learning, Voice & Developer Integrations:** Active Recall Study Cards (AI card generation, Socratic Quiz, Anki `.tsv` export), Knowledge Gap Scan, offline Solo/Duo Audio Briefings (Phonon TTS), Hands-Free Voice Loop, opt-in loopback `/v1` OpenAI-compatible API, `realm-engine ask` CLI, and `realm-engine mcp` stdio MCP server.
- **Accessibility, Themes & Multilingual UI:** Full English, Deutsch, and Español interface; System / Dark / Light (Clear) modes; 15 dual-tone palettes; Hyperlegible & Dyslexia reading fonts, S–XL text sizing, Focus/Normal/Wide layout, High-Contrast Focus, Reduce Motion, and Eco Mode.
- **Desktop Packaging:** Native macOS `.app` / `.dmg` (Apple Silicon & Intel) and Windows x64 Inno Setup `.exe` / Portable `.zip` builds.

## [0.1.0] - 2026-11-12

### Added
- Initial release of local-first Hybrid RAG (BM25 + Ollama/Cloud Cosine RRF) Knowledge Engine with FastAPI vertical-slice architecture, strict Pydantic v2 contracts, Library Reader, 2D Knowledge Graph, GDPR/DSGVO PII preview & scrub, daily cloud spend guard, ZIP backup/restore, and Headless Read-Only Public API (`REALM_MODE=public`).
