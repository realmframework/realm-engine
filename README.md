# REALM Knowledge Engine (`realm-engine`)

A local-first, domain-agnostic **Hybrid RAG & Multi-Turn AI Knowledge Engine** built with FastAPI, strict Pydantic v2 contracts, and a dark minimal interface (`#04060F` / `#0B1020` / `#4BB8E8`).

Drop in your own Markdown, PDF, Word (`.docx`), TXT, or HTML files and explore them with BM25 + vector search, grounded multi-turn AI chat, a rich Markdown reader, an interactive 2D knowledge graph, and built-in DSGVO/GDPR PII redaction — 100% offline with local Ollama or optionally paired with cloud LLM providers behind a daily spend guard.

---

## Highlights

- **100% Local-First & Private by Default:** Runs on your machine with **Strict Local-Only Lock** enabled by default and zero external CDN assets.
- **Universal Document Ingestion:** Converts `.pdf`, `.docx`, `.txt`, `.html`, and `.md` (supporting both `# Title` / `Tags:` and standard YAML frontmatter) into organized Markdown guides with nested subfolders and automatic topic extraction.
- **Real Hybrid RAG:** Combines punctuation-safe BM25 lexical scoring, incremental cached vector embeddings (`index.json`), Reciprocal Rank Fusion (`RRF`), and a fast Query Intent Auto-Router.
- **Rich Reader & 2D Knowledge Graph:** Renders fenced code blocks, Markdown tables, equations, blockquotes, nested lists, clickable cross-guide `.md` links, and interactive radial knowledge galaxies.
- **App-Level Key Storage & Spend Guard:** Cloud API keys live at the application level in `./data/secrets.json` (`0600`, gitignored, never backed up) or optional `.env` / environment variables — surviving browser switches and cache clears — protected by atomic per-minute and daily request/USD caps.
- **Optional Headless Public API (`REALM_MODE=public`):** Serve selected vaults as a stateless, read-only JSON API with canonical URLs and an in-memory rate limiter for static documentation sites.

---

## Quickstart

### Download Desktop App (No Coding Required)

Download the installer for your computer from [**GitHub → Releases**](https://github.com/realmframework/realm-engine/releases):

| Computer | Download | Install Steps |
|---|---|---|
| **Mac — Apple Silicon (M1 / M2 / M3 / M4, 2020+)** | `REALM-Engine-<ver>-macos-apple-silicon.dmg` | Open the `.dmg`, drag **REALM Engine** into **Applications**, and double-click to launch. |
| **Mac — Intel (older Macs)** | `REALM-Engine-<ver>-macos-intel.dmg` | Open the `.dmg`, drag **REALM Engine** into **Applications**, and double-click to launch. |
| **Windows 10 / 11 (64-bit)** | `REALM-Engine-<ver>-windows-x64-setup.exe` *(or `-portable.zip`)* | Run the installer (no Admin needed). If Windows SmartScreen warns on an unsigned build, click **More info → Run anyway**. |

- **Not sure which Mac you have?** Click ** (Apple menu) → About This Mac**. If it says **Chip: Apple M1 / M2 / M3 / M4**, download **Apple Silicon**; if it says **Processor: Intel**, download **Intel**.
- **Clean lifecycle & private storage:** Closing the app window (or **⌘Q**) stops the local server automatically — no terminal window. Your vaults, chats, and saved API keys live in `~/Library/Application Support/REALM Engine/` (macOS) or `%APPDATA%\REALM Engine\` (Windows).
- **Verify downloads:** Every release includes a `SHA256SUMS.txt` checksum file. Maintainer build, code-signing, and Apple notarization steps live in [packaging/RELEASING.md](packaging/RELEASING.md).

### Run From Source (macOS, Windows & Linux)

Install [uv](https://docs.astral.sh/uv/), then launch with one click or command:

- **macOS:** Double-click `start.command` (or run `./start.command`)
- **Windows:** Double-click `start.bat` (or run `start.bat`)
- **Linux:** Run `./start.sh`

All three launchers run `uv run python main.py --desktop`, which starts the local FastAPI server on `http://127.0.0.1:8000` and opens a clean tabless desktop window in Chrome, Brave, or Edge (falling back to your default browser). Closing the browser window leaves the local server running; press **Ctrl+C** in its terminal to stop it cleanly. To test the native WebView desktop window from source, run `uv run --group desktop python desktop_app.py`.

### CLI & Custom Data Directory

```bash
# Desktop app window
uv run python main.py --desktop

# Standard local web server (open http://127.0.0.1:8000)
uv run python main.py

# Or via the installed package script
uv run realm-engine --port 8080 --data-dir /path/to/my-vaults

# Pre-build index.json files offline (optional --embed-provider ollama|openai|mistral|gemini)
uv run python main.py --build-index --embed-provider ollama
```

By default, all runtime files — knowledge areas, `workspace.json`, `chats.json`, `budget_state.json`, and `secrets.json` — are stored cleanly inside `./data/` (gitignored), keeping the repository root clean. Set `--data-dir` or `REALM_DATA_DIR` to store data elsewhere. A sample starter guide is included in [examples/starter_vault/welcome.md](examples/starter_vault/welcome.md).

### Docker / Compose

```bash
docker compose up
```

Open `http://127.0.0.1:8000` (set `REALM_PORT` to use another host port, or `--build` after local source edits). The container runs as an unprivileged user and persists all vaults, settings, and chats under `/data` in the `realm-data` volume. Local notes and secrets are excluded from image builds via `.dockerignore`.

---

## Choose How to Run

Open **Settings → Setup Wizard** (or **Settings → Workspace & AI**) to pick one of three modes:

1. **100% Local AI Only (Strict Privacy):** Keeps the local-only lock enabled and uses [Ollama](https://ollama.com/download). Click **Download Recommended Local AI** in the Setup Wizard to pull `qwen2.5:3b` (< 16 GB RAM) or `qwen3:8b` (≥ 16 GB RAM) plus `nomic-embed-text:v1.5` without using a terminal. When Ollama is running with `nomic-embed-text:v1.5`, embeddings are computed incrementally and cached in `index.json` for fast **Hybrid Vector + BM25 RRF** search.
2. **Local + Cloud AI (Ollama & API Keys):** Unlocks all 7 cloud providers (**OpenAI**, **Gemini**, **Anthropic**, **Kimi / Moonshot**, **DeepSeek**, **xAI**, **Mistral**) **alongside** free local Ollama. Save API keys for as many providers as you want and switch directly between local Ollama and saved cloud models right from the **Model** dropdown (protected by the daily budget guard).
3. **Search & Anonymize Only (Zero AI Setup):** Enables instant BM25 keyword search, folder organization, Library Reader, 2D Graph, and DSGVO redaction with zero models or API keys required.

---

## API Keys & Cloud Budget Guard

- **App-Level Key Storage:** Keys saved in **Settings → Workspace & AI** or the Setup Wizard are stored locally in `./data/secrets.json` with `0600` (owner-only) permissions, ignored by Git, excluded from ZIP backups, and never sent back to the browser in plain text (only a masked hint like `…9876` is shown). Keys persist across browsers, app restarts, and cache clears.
- **Optional `.env` / Shell Fallback:** Copy `.env.example` to `.env` (gitignored) or export standard variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `MOONSHOT_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `MISTRAL_API_KEY`, `XAI_API_KEY`, `ELEVENLABS_API_KEY`). Resolution order is request header → `./data/secrets.json` → `.env` / shell environment.
- **Daily Cloud Budget Guard:** Defaults to **50 cloud requests / UTC day**, **$1.00 estimated daily spend**, **12 requests / rolling minute**, and bounded output tokens (`1,024`). Usage is reserved atomically before cloud chat, embedding, or TTS dispatch; local Ollama is always free and unmetered. Dollar figures are conservative planning estimates, not provider invoices — configure provider-side billing limits for a hard ceiling.
- **Forget Saved API Key** removes saved keys from `./data/secrets.json` and clears UI fields without revoking keys at the provider.

---

## Organizing Knowledge, Scoped Chat & Backups

- **Knowledge Areas & Combined Search:** Click the active workspace name at the top of the sidebar to switch areas, create new areas (**+ New Area** with optional **Blank**, **Care & Medical**, **Personal & Finance**, or **Study** folder templates), or check multiple areas to search and chat across them together. Each custom area stores its own isolated `chats.json` and `index.json`.
- **Recursive Subfolders:** Inside **Library**, organize guides into nested folders with inline **+** child creation, **Chat ↗** subtree scoping, card folder pills, **Move guide**, and confirmed recursive deletion.
- **Scoped Conversations:** Launch **Chat ↗** on any folder or **Chat with this Document** on any guide card or Reader view. A compact removable scope chip appears inside the prompt pill only while scoped; clearing it starts a fresh area-wide chat. Saved chats remember their scope and refuse generation deterministically if no matching passages exist in scope.
- **Reader, Export & 2D Graph:** Click any citation or Library card to read full formatted guides (tables, code blocks, equations, cross-guide `.md` links). Export conversations as `.md` or save them back into the Library as `study-notes`. Open **Graph View** to explore active areas or all areas as interactive radial galaxies.
- **Settings (3 Tabs):**
  - **Workspace & AI:** Title, folder, provider/key, voice TTS (local Phonon, OpenAI, ElevenLabs), daily cloud budget, ZIP backup/restore, and Setup Wizard.
  - **RAG & Search:** Live retrieval tier status, Tutor vs. raw search toggle, retrieval mode (`Hybrid (RRF)`, `Lexical (BM25)`, `Vector (Cosine)`), `Top-K`, `RRF k`, and temperature controls.
  - **Privacy & DSGVO Audit:** Strict Local-Only Lock, recursive Markdown PII scan, confirmed bulk vault scrub, retrieval self-diagnostics, and downloadable Markdown audit report.
- **ZIP Backup & Restore:** Download a single-area `.zip` backup (Markdown guides, empty folders, workspace config, and single-area chats — excluding original binaries, API keys, model weights, and the budget ledger) and merge-restore safely into any workspace with conflict protection and rollback on error.

---

## Privacy, DSGVO Redaction & Security Boundaries

- **Strict Local-Only Lock (Default On):** Blocks server-side cloud chat, embedding, model-discovery, cloud TTS, and browser dictation routes (including Ollama model names containing `cloud`). This is an application admission control, not an OS firewall.
- **Governance & Redaction Inspector:** Staging files in **Add Documents** or clicking **Preview DSGVO Redaction** in the Reader previews matches across emails, IBANs, phone numbers, filename-derived names, IPv4 addresses, German/EU dates (`DOB`), health IDs (`HEALTH_ID`), and postal/street addresses without mutating files. Always review previews manually for false positives or missed personal data.
- **Prompt-Injection & Upload Limits:** Retrieved passages are XML-escaped inside `<untrusted_document_context>` delimiters with system instructions rejecting imperative commands from documents. Uploads and previews cap files at **15 MiB** (64 MiB batch / 30 MiB preview / 25 MiB audio) and bound `.docx` XML decompression at **20 MiB**.
- **Audit Reports:** Generated technical reports support engineering and GDPR/EU AI Act review (Articles 25/32 and 10/13/15); they are not legal certification or clinical validation.

---

## Headless Public API Mode (`REALM_MODE=public`)

Publish selected vaults as a stateless, read-only JSON API for static documentation sites while keeping all local write, upload, settings, key-management, DSGVO scrub, backup, and chat-disk routes unmounted (`404`):

```bash
REALM_MODE=public \
REALM_PUBLIC_AREAS=my_docs,guides \
REALM_PUBLIC_PROVIDER=kimi \
REALM_PUBLIC_MODEL=kimi-k3.1-pro \
REALM_PUBLIC_URL_TEMPLATE="/docs/{area}/{doc_id}" \
REALM_PUBLIC_ORIGINS="https://docs.example.com" \
uv run python main.py --public --host 0.0.0.0 --port 8000
```

Mounted endpoints in `public` mode:
- `GET /healthz` — universal liveness check (works in both local and public modes, used by Docker `HEALTHCHECK`).
- `GET /api/public/health` — loaded areas, guide/chunk counts, embedding status, and active model name (never exposes secrets).
- `GET /api/public/meta` — published areas, topic counts, starter prompts, and guide summaries with canonical URLs and YAML frontmatter descriptions.
- `GET /api/public/search` — stateless BM25/hybrid search + Auto-Router returning passages with canonical URLs and `#section` anchors.
- `POST /api/public/ask` — stateless grounded AI Tutor using the server-locked provider/model (visitors cannot override provider, model, or key). Includes a zero-dependency in-memory per-IP (`REALM_PUBLIC_IP_RPM`, `REALM_PUBLIC_IP_DAILY`) and global daily budget guard (`REALM_PUBLIC_DAILY_LIMIT`, `REALM_PUBLIC_DAILY_USD`), degrading gracefully to instant `$0` search results (`fallback_mode: "search_only"`, header `X-Realm-Fallback: quota_limit`) when capped.
- `GET /api/public/graph` — radial galaxy nodes and links with canonical page and section URLs.

---

## Architecture & Development

The codebase enforces strict architectural guardrails tested on every run in [core/test_architecture.py](core/test_architecture.py):

- **Strict Vertical Slices:** Feature logic is isolated under `features/ingestion/`, `features/search/`, `features/tutor_agent/`, and `features/ui/` with zero cross-slice imports (`features/ui/app.py` is the composition root).
- **Contract-First:** All shared Pydantic v2 schemas live in [core/contracts.py](core/contracts.py) with `ConfigDict(strict=True)`.
- **Line Ceilings:** Backend Python files stay `<= 150` lines; frontend template/script modules in `features/ui/` and static `.js`/`.css` assets stay `<= 350` lines.

### Verification Gate

```bash
uv run ruff check . && uv run pyright && uv run pytest
```

### Regenerating Self-Hosted Tailwind CSS

Runtime deployments need no Node.js or external CDN. If you add new Tailwind utility classes in `features/ui/*.py`, regenerate `features/ui/static/ui.css` with Tailwind CLI `3.4.17`:

```bash
npx --yes --package=tailwindcss@3.4.17 tailwindcss -c features/ui/tailwind.config.cjs -i features/ui/tailwind-input.css -o features/ui/static/ui.css --minify
```

---

## License

Released under the [MIT License](LICENSE).
