# REALM Knowledge Engine (`realm-engine`)

A local-first, domain-agnostic **Hybrid RAG & Multi-Turn AI Knowledge Engine** built with FastAPI, strict Pydantic v2 contracts, and a clean, minimalist desktop & web interface (Dark & Light WCAG 2.1 AA themes, English / Deutsch / Español).

Drop in Markdown, PDF, Word (`.docx`), Excel (`.xlsx`), PowerPoint (`.pptx`), CSV/TSV, TXT, or HTML files — or **link existing folders in place** — and explore them with BM25 + vector hybrid search, grounded multi-turn AI chat, customizable specialist agents with `@mentions` and per-agent model pinning, structured Answer Formats, Study Cards, offline Audio Briefings, an interactive 2D knowledge graph, and built-in GDPR/DSGVO PII redaction. Runs 100% offline with local [Ollama](https://ollama.com/download) or optionally alongside 7 cloud providers behind a daily spend guard.

---

## Highlights

- **100% Local-First & Private by Default:** Starts with **Strict Local-Only Lock** enabled, zero external CDN or telemetry requests, loopback-only binding, strict Host/Origin/CSRF/CSP middleware, and `0o600` owner-only local secret storage.
- **Universal Ingestion & Live Sync (9 Formats):** Imports `.md`, `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.csv`, `.tsv`, `.txt`, and `.html` (with YAML frontmatter or `# Title` / `Tags:`), clips public web articles into Markdown, supports **Link Local Folder…** without copying files, and watches vaults automatically for changes.
- **Hybrid RAG + Retrieval X-Ray:** Combines punctuation-safe BM25 lexical search, incremental cached vector embeddings (`index.json` with schema & model versioning), Reciprocal Rank Fusion (`RRF`), Query Intent Auto-Router, and an **Engine Inspector (`⌘I` / `Ctrl+I`)** with live Context Window meter, lossless **Compress Context**, and per-passage Pin/Mute controls.
- **Specialist Agents, `@mentions`, Slash Commands & Answer Formats:** Chat with **Saga** or switch/summon specialists (`@Lisbeth`, `@Blomkvist`, `@Milton`, `@Erika`, `@Annika`, `@Plague`, `@Palmgren`, or custom agents) with optional per-agent local/cloud model pinning and RAM-safe Ollama serialization. Trigger `/` quick actions, **Second Opinion**, or synthesize structured deliverables using **13 built-in Answer Formats** (SRS, User Stories, ADR, Threat Assessment, Postmortem, Dossier, Executive Brief, etc.) plus custom blueprints.
- **Reader, Markdown Editor, Study Cards, Gap Scan & 2D Graph:** Edit guides live (`⌘S` with Write/Preview), explore clustered 2D constellations, generate **Active Recall Study Cards** (AI-enhanced + **Anki `.tsv` export** + **Socratic Quiz**), run **Knowledge Gap Scans**, and synthesize offline Solo/Duo **Audio Briefings** (`.wav` + script).
- **Accessibility & Multilingual UI:** **English**, **Deutsch**, and **Español** interface; **15 WCAG 2.1 AA Dark/Light palettes**, Atkinson Hyperlegible & OpenDyslexic-style fonts, S–XL text sizing, Focus/Normal/Wide layout, High-Contrast Focus, Reduce Motion, and **Eco Mode** for 8 GB / CPU laptops.
- **Developer & Headless Integrations:** Opt-in loopback-only **OpenAI-compatible `/v1` API**, terminal CLI (`realm-engine ask`), **stdio MCP server** (`realm-engine mcp`) for Claude Desktop / Cursor / VS Code, and **Headless Read-Only Public API** (`REALM_MODE=public`) for static sites.

---

## Quickstart

### Download Desktop App (macOS & Windows)

Download signed/packaged releases from [**GitHub → Releases**](https://github.com/realmframework/realm-engine/releases):

| Platform | Download | Install & Notes |
|---|---|---|
| **macOS — Apple Silicon (M1–M4, 2020+)** | `REALM-Engine-<ver>-macos-apple-silicon.dmg` | Open the `.dmg`, drag **REALM Engine** to **Applications**, and launch. Native WebKit desktop window with clean `⌘Q` shutdown. |
| **macOS — Intel** | `REALM-Engine-<ver>-macos-intel.dmg` | Open the `.dmg`, drag **REALM Engine** to **Applications**, and launch. |
| **Windows 10 / 11 (64-bit)** | `REALM-Engine-<ver>-windows-x64-setup.exe` *(or `-portable.zip`)* | Run the per-user installer (no Admin needed, EN/DE/ES wizard) or extract the portable folder. Uses Edge WebView2 automatically and falls back cleanly to your default browser if WebView2 is absent. |

- **Private desktop storage:** Vaults, chats, logs (`logs/realm-engine.log`, `0600`), and saved API keys live in `~/Library/Application Support/REALM Engine/` (macOS), `%APPDATA%\REALM Engine\` (Windows), or `~/.local/share/realm-engine/` (Linux).
- **Verify downloads:** Every release ships a `SHA256SUMS.txt` checksum manifest. Maintainer build, signing, and Apple notarization instructions live in [packaging/RELEASING.md](packaging/RELEASING.md).

### Run From Source (macOS, Windows & Linux)

Install [uv](https://docs.astral.sh/uv/), then launch directly:

- **macOS:** Double-click `start.command` (or `./start.command`)
- **Windows:** Double-click `start.bat` (or `start.bat`)
- **Linux:** Run `./start.sh`

All launchers run `uv run python main.py --desktop` on `http://127.0.0.1:8000` (clean browser app window; press **Ctrl+C** in the terminal to stop). To launch the native WebView window from source, run `uv run --group desktop python desktop_app.py`.

### CLI, Python Package & MCP Server

```bash
# Local web server (open http://127.0.0.1:8000)
uv run python main.py

# Or via the installed console script (pip / uv tool install)
realm-engine --port 8080 --data-dir /path/to/my-vaults

# One-shot grounded CLI query (optional --json, --area, --model)
realm-engine ask "Summarize our deployment checklist"

# Start stdio Model Context Protocol (MCP) server for Claude Desktop / Cursor / VS Code
realm-engine mcp

# Pre-build index.json embeddings offline (ollama | openai | mistral | gemini)
uv run python main.py --build-index --embed-provider ollama

# Print application version
realm-engine --version
```

By default when run from a git checkout, runtime files live inside `./data/` (gitignored). When installed as a Python package (`site-packages`), runtime data automatically resolves to your OS user data directory unless `--data-dir` or `REALM_DATA_DIR` is set.

### Docker / Docker Compose

```bash
docker compose up
```

Open `http://127.0.0.1:8000` (override host port with `REALM_PORT`). The image runs as an unprivileged user (`uid 1000`, `HOME=/data`), seeds the starter guide on first boot, persists vaults and settings in the `realm-data` volume, and maps `host.docker.internal` so you can optionally connect to a host Ollama instance (`OLLAMA_HOST=http://host.docker.internal:11434` with `REALM_ALLOW_REMOTE_OLLAMA=1`).

---

## AI Modes, API Keys & Local RAM Safety

Open **Settings → Setup Wizard** (or press `?` / `⌘/` for the in-app **Quick Guide**) to choose your mode:

1. **100% Local AI Only (Strict Privacy — Default):** Runs offline with [Ollama](https://ollama.com/download). Click **Download Recommended Local AI** in the Setup Wizard to pull a hardware-matched model (`qwen2.5:3b` for < 16 GB RAM, `qwen3:8b` for ≥ 16 GB RAM) plus `nomic-embed-text:v1.5` without opening a terminal.
2. **Local + Cloud AI (Ollama & API Keys):** Unlocks **OpenAI**, **Gemini**, **Anthropic**, **Kimi / Moonshot**, **DeepSeek**, **xAI**, and **Mistral** alongside local Ollama. Switch models per chat or pin individual specialist agents to dedicated local or cloud models.
3. **Search & Anonymize Only (Zero AI Setup):** Instant BM25 search, folder organization, Markdown editor, 2D Graph, Study Cards, and GDPR redaction with zero models or keys.

- **RAM-Safe Local Ollama Coordination:** Concurrent local requests are serialized through an internal execution gate, bounded by `keep_alive`, output token limits, and stream deadlines, and automatically unload the previous local model before loading a different local or cloud model to protect memory on 8–16 GB laptops.
- **App-Level Secret Storage & Cloud Spend Guard:** API keys saved in Settings live in `<data_dir>/secrets.json` (`0600`, never exported in backups, never returned in plaintext). Resolution order: request header → `secrets.json` → `.env` / shell environment. Cloud usage is guarded by atomic daily request (default `50`), daily estimated USD (default `$1.00`), and per-minute (`12 RPM`) limits; local Ollama is always free and unmetered.

---

## Documentation

| Guide | What It Covers |
|---|---|
| [User Guide](docs/USER_GUIDE.md) | Workspaces, 9 file formats, Linked Folders, live Editor, `⌘K` Quick Jump, `/` commands, Engine Inspector (`⌘I`), Study Cards & Anki export, Audio Briefings, 2D Graph, Reading Comfort, and Backups. |
| [Agents & Answer Formats](docs/AGENTS_AND_FORMATS.md) | Built-in & custom agents, `@mention` syntax, per-agent model pinning & RAM safety, Second Opinion, 13 structured Answer Formats, and PDF/Markdown synthesis. |
| [Integrations & Public API](docs/INTEGRATIONS.md) | Local OpenAI-compatible `/v1` API, `realm-engine ask` CLI, `realm-engine mcp` setup for Claude Desktop / Cursor / VS Code, and Headless Read-Only Public API (`REALM_MODE=public`). |
| [Privacy, Security & Compliance](docs/PRIVACY_AND_COMPLIANCE.md) | Threat model, Strict Local-Only Lock, localhost CSRF/SSRF/CSP perimeter, GDPR/DSGVO redaction, EU AI Act audit reports, diagnostics, and backup boundaries. |
| [Packaging & Releasing](packaging/RELEASING.md) | Building macOS `.dmg` (signed & notarized), Windows `.exe`/`.zip`, Linux launchers, Python wheels, and Docker images. |
| [Security Policy](SECURITY.md) | Responsible vulnerability disclosure and supported versions. |
| [Contributing](CONTRIBUTING.md) | Architectural rules, local verification gate, and pull request workflow. |
| [Changelog](CHANGELOG.md) | Release history and notable changes. |

---

## Architecture & Development

Every run enforces strict architectural boundaries in [core/test_architecture.py](core/test_architecture.py):

- **Strict Vertical Slices:** Feature slices live in `features/ingestion/`, `features/search/`, `features/tutor_agent/`, and `features/ui/` with zero cross-slice imports (`features/ui/app.py` is the composition root).
- **Contract-First:** Shared Pydantic v2 models live in [core/contracts.py](core/contracts.py) with `ConfigDict(strict=True)`.
- **Line Ceilings:** Backend Python files stay `<= 150` lines; frontend template/script modules in `features/ui/` and static `.js`/`.css` assets stay `<= 350` lines.

### Verification Gate

```bash
uv run ruff check . && uv run pyright && uv run pytest
```

### Regenerating Self-Hosted Tailwind CSS

Runtime deployments require zero Node.js or external CDNs. After adding new Tailwind utility classes in `features/ui/*.py`, rebuild `features/ui/static/ui.css`:

```bash
npx --yes --package=tailwindcss@3.4.17 tailwindcss -c features/ui/tailwind.config.cjs -i features/ui/tailwind-input.css -o features/ui/static/ui.css --minify
```

---

## License

Released under the [MIT License](LICENSE).
