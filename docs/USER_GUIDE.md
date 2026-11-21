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

### Supported Formats (9)
| Category | Extensions | Notes |
|---|---|---|
| Notes & Markup | `.md`, `.txt`, `.html` | Supports YAML frontmatter (`title`, `description`, `tags`) and `# Title` / `Tags:` syntax. |
| Documents | `.pdf`, `.docx` | Local extraction; Office XML decompression bounded to prevent zip bombs. |
| Spreadsheets & Data | `.xlsx`, `.csv`, `.tsv` | Structured Markdown table conversion for clean retrieval and quoting. |
| Presentations | `.pptx` | Slide-by-slide text and speaker-note extraction. |

- **Drag & Drop / Folder Import:** Drop files or nested directories onto the window, or use **Add Documents → Import Folder (with Subfolders)** via the native OS picker.
- **Live Markdown Editor:** Open any guide in **Library** and click **Edit** (Write / Split / Preview + `⌘S` / `Ctrl+S`), or click **+ New Note** to create Markdown directly inside any subfolder.
- **Web Clipper:** Inside **Add Documents**, paste any public `http(s)://` URL to clip clean article Markdown offline (available when **Strict Local-Only Lock** is disabled).
- **Subfolder Scopes & Unloading:** Click **Chat ↗** on any folder or document to scope your conversation to that exact subtree. Use **Unload** to temporarily exclude a subfolder from search, chat, CLI, MCP, and Public API without deleting files on disk.

---

## 3. Keyboard Shortcuts & Slash Commands

Press **`?`** (when not typing) or **`⌘/`** (`Ctrl+/`) at any time to open the 4-tab **Quick Guide & Shortcuts** dialog.

| Shortcut | Action |
|---|---|
| `⌘K` / `Ctrl+K` | **Quick Jump** — fuzzy search documents, recent chats, agents, workspaces, and actions |
| `⌘I` / `Ctrl+I` | Toggle **Engine Inspector** (Context Meter, Compress Context, Retrieval X-Ray) |
| `⌘/` / `Ctrl+/` or `?` | Open **Quick Guide & Shortcuts** |
| `/` (in prompt box) | Open **Slash Commands** (`/summarize`, `/quiz`, `/table`, `/actions`, `/compare`, `/eli5`, `/critique`, or `/<format>`) |
| `@` (in prompt box) | Summon any specialist agent for a single turn (e.g., `@Lisbeth`, `@Annika`, `@Plague`) |
| `⌘S` / `Ctrl+S` | Save while inside the Markdown Editor |
| `F` (in Graph View) | Focus the 2D Knowledge Graph filter |
| `Esc` | Close the open dialog or popover |

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
- **Themes & Reading Comfort (WCAG 2.1 AA):** Choose **System / Dark / Light (Clear)**, pick from **15 verified AA palettes**, customize Primary Accent and Ambient Glow, upload a custom workspace logo, select **Default / Hyperlegible / Dyslexia** fonts, adjust **S / M / L / XL** text size and **Focus / Normal / Wide** line measure, or enable **High-Contrast Focus**, **Reduce Motion**, and **Eco Mode** (optimized for 8 GB / CPU machines).
- **ZIP Backup & Restore:** Under **Settings → Workspace**, download a portable single-area `.zip` archive (Markdown guides, empty subfolders, workspace settings, and area chats — excluding raw binaries, API keys, model weights, and host file paths) and merge-restore safely with conflict protection and rollback.
