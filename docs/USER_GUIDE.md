# REALM Engine — User Guide

This guide walks through day-to-day workflows in **REALM Knowledge Engine**: managing Knowledge Areas, importing or linking documents, using keyboard shortcuts and `/` commands, inspecting retrieval scores, studying with flashcards, generating offline audio briefings, and customizing accessibility and backups.

---

## 1. Workspaces & Knowledge Areas

Click the active workspace name at the top-left of the sidebar to:

- **Switch Knowledge Areas** or select **Free Chat (No Area)** for direct conversation without RAG grounding.
- **Combine Multiple Areas:** Check multiple boxes in the workspace selector to search and chat across several vaults simultaneously.
- **+ New Area:** Create a fresh folder under `<data_dir>/<area_name>/` with optional starter folder templates.
- **Link Local Folder…:** Index an existing folder anywhere on your computer **in place** (no copying). Removing it via **Unlink Folder** never deletes your original files.
- **Auto-Sync Watcher:** REALM watches active vaults in the background and automatically detects edits, new Markdown notes, and folder changes (disable with `REALM_DISABLE_WATCHER=1`).

---

## 2. Adding, Editing & Clipping Documents

### Supported Formats (Documents + 35+ Code & Config Types)
| Category | Extensions | Notes |
|---|---|---|
| Notes & Markup | `.md`, `.txt`, `.html` | Supports YAML frontmatter (`title`, `description`, `tags`) and `# Title` / `Tags:` syntax. |
| Documents | `.pdf`, `.docx` | Local extraction; Office XML decompression bounded to prevent zip bombs. |
| Spreadsheets & Data | `.xlsx`, `.csv`, `.tsv` | Structured Markdown table conversion for clean retrieval and quoting. |
| Presentations | `.pptx` | Slide-by-slide text and speaker-note extraction. |
| Source Code & Config | `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.json`, `.yaml`, `.yml`, `.toml`, `.css`, `.sql`, `.sh`, `.rs`, `.go`, `.java`, `.swift`, `.dart`, etc. | Opens in the Code Editor tab with language badge, synced line-number gutter, and `Ln/Col` footer. Automatically ignores `node_modules/`, `.git/`, `dist/`, `.venv/`, `__pycache__/`, lockfiles, `.env*`, and credentials. |

- **Left Files Explorer & Tabs:** Click **Files** in the left rail to filter files live, expand/collapse folders, toggle **Auto-reveal active file** or **Always open in new tab**, create any file (`New file…` / `New note here`), rename/duplicate/move/anonymize/delete files, or manage folders. Right-click any center tab to **Pin / Unpin** (persisted per workspace) or bulk close (`Close Others`, `Close to the Right`, `Close Saved`, `Close All`).
- **Live Status Indicators & Unsaved Guard:** Chat tabs and **Recent Chats** display a spinning **Working** icon while streaming in the background and a glowing **Unread** dot if an answer completes while you're on another tab. Unsaved files show a **Modified** dot on both the tab and the Files tree, and an app-wide **Save / Discard / Keep editing** prompt protects tabs, modals, workspace switches, and window close.
- **Right Sidebar Copilot (`⌘J` / `Ctrl+J`):** Ask questions or propose structured edits beside any open file, Work OS board, workflow, or agent roster. Choose any Agent, Model, or Output Format; highlight text in a file for `✦ Ask Copilot` / `✦ Edit Selection`; type `#` to attach up to 4 extra workspace files (`#server.js`, `#API.md`); preview diffs before clicking **Apply**, and reverse changes with **1-click Undo**. Copilot threads persist automatically per workspace/context.
- **Integrated Bottom Panel Terminal (`` Ctrl+` ``):** Toggle the Bottom Panel directly onto **Terminal** to run local shell commands (`git`, `uv`, `pytest`, `npm`, `python`, etc.) inside your active workspace or linked folder. Supports ANSI colors, multiple shell sessions (`+`), `↑`/`↓` command history, `Ctrl+C` interrupt, and **`✦ Copilot`** to send selected output or the latest lines straight to Copilot for debugging.
- **Drag & Drop / Folder Import:** Drop files or nested directories onto the window (preserving native extensions for code files and skipping ignored folders), or use **Add Documents → Import Folder (with Subfolders)** via the native OS picker.
- **Web Clipper:** Inside **Add Documents**, paste any public `http(s)://` URL to clip clean article Markdown offline (available when **Strict Local-Only Lock** is disabled).
- **Subfolder Scopes & Unloading:** Click **Chat ↗** on any folder or document to scope your conversation to that exact subtree. Use **Unload** to temporarily exclude a subfolder from search, chat, Copilot, CLI, MCP, and Public API without deleting files on disk.

---

## 3. Keyboard Shortcuts & 3-Symbol Grammar (`@`, `/`, `#`)

Press **`?`** (when not typing) or **`⌘/`** (`Ctrl+/`) at any time to open the **Quick Guide & Shortcuts** dialog.

| Shortcut | Action |
|---|---|
| `⌘K` / `Ctrl+K` | **Command Palette** — fuzzy search documents, recent chats, agents, workspaces, and actions |
| `⌘P` / `Ctrl+P` | **Quick Open File** — fuzzy jump directly to any Markdown or code file in a center tab |
| `⌘J` / `Ctrl+J` | Toggle **Right Sidebar Copilot** |
| `` Ctrl+` `` | Toggle **Bottom Panel Terminal** |
| `⌘I` / `Ctrl+I` | Toggle **Engine Inspector** (Context Meter, Compress Context, Retrieval X-Ray) |
| `⌘S` / `Ctrl+S` | Save the active Markdown or Code Editor tab |
| `⌘/` / `Ctrl+/` or `?` | Open **Quick Guide & Shortcuts** |
| `/` (in main chat) | Open **Slash Commands** (`/explain`, `/summarize`, `/quiz`, `/compare`, `/factcheck`, `/translate`, or `/<format>`) |
| `@` (in main chat) | Summon any specialist agent for a single turn (e.g., `@Lisbeth`, `@Erika`, `@Plague`) |
| `#` (in Copilot) | Attach additional workspace files (`#API.md`, `#server.js`) as context chips |
| `F` (in Graph View) | Focus the 2D Knowledge Graph filter |
| `Esc` | Stop an answer or close the open dialog/popover |

---

## 4. Engine Inspector & Retrieval X-Ray (`⌘I` / `Ctrl+I`)

Open the right-hand **Engine Inspector** during any chat to see exactly what the model sees:

- **Context Window Meter:** Tracks token utilization against the active model's context budget.
- **Lossless Compress Context:** Summarizes older turns cleanly while preserving citations and key facts.
- **Retrieval X-Ray:** Displays per-passage **BM25**, **Vector Cosine**, and **RRF** scores. Click **Pin** to force a source into the next answer or **Mute** to exclude a noisy passage before re-running.
- **Mid-Chat File Attachments:** Click `+` inside the prompt pill to attach temporary files directly to the current conversation (shown as removable chips above the active input).
- **Opt-In Web Search:** Enable the Globe toggle under **Settings → RAG & Search** (DuckDuckGo, Ollama Web Search, or self-hosted SearXNG) to augment individual replies with live web snippets when Local-Only Lock is off.

---

## 5. Study Cards, Socratic Quiz, Gap Scan & Audio Briefings

- **Study Cards:** Open from **Library** to generate active-recall flashcards from your guides (with configurable count, optional AI card generation, spaced-repetition rating `1 Hard` / `2 Good` / `3 Easy`, **Socratic Quiz** mode, and **Anki `.tsv` export**).
- **Knowledge Gap Scan:** Detects thin coverage, orphan topics, and missing documentation sections across your active area.
- **Audio Briefings (Offline):** Generate Solo or Two-Voice Duo audio briefings (`.wav` + downloadable Markdown script) locally using Phonon TTS, or switch to OpenAI / ElevenLabs TTS when Cloud APIs are enabled.
- **Voice Input & Hands-Free Loop:** Dictate with Whisper/microphone or toggle **Hands-Free Voice Loop** in **Settings → AI & Voice**.
- **2D Knowledge Graph:** Visualize clusters across the active area or all areas with smooth trackpad zoom, topic filtering, and clickable jump-to-reader nodes.

---

## 6. Appearance, Accessibility, Languages & Backups

- **Languages:** Switch instantly between **English**, **Deutsch**, and **Español** in **Settings → Workspace** (all labels, starter prompts, confirmations, modals, and Quick Guide translate live).
- **Themes & Reading Comfort (WCAG 2.1 AA):** Choose **System / Dark / Light (Clear)**, pick from **15 verified AA palettes**, toggle **Fix Global Theme** (off = follows each active agent's palette; on = locks one theme across every agent and view), toggle **Sync Terminal Theme** (syncs the integrated terminal to the active theme, or switch off for a classic neutral terminal from either the terminal bar or Appearance), customize Primary Accent and Ambient Glow, upload a custom workspace logo, select **Default / Hyperlegible / Dyslexia** fonts, adjust **S / M / L / XL** text size and **Focus / Normal / Wide** line measure, or enable **High-Contrast Focus**, **Reduce Motion**, and **Eco Mode**.
- **ZIP Backup & Restore:** Under **Settings → Workspace**, download a portable single-area `.zip` archive (Markdown, text, HTML, and source/config files, empty subfolders, workspace settings, chats, Work OS, Focus, Impact, and Workflows — excluding secrets, build folders, raw binaries, model weights, and host paths) and merge-restore safely with conflict protection and rollback.
