---
title: Welcome to REALM Knowledge Engine
description: Quick starter handbook covering Knowledge Areas, 9 document formats, Agents, shortcuts, Study Cards, Privacy Lock, and developer APIs.
tags: [getting-started, rag, local-first, shortcuts]
---

# Welcome to REALM Knowledge Engine

## How Knowledge Areas Work
Each Knowledge Area lives cleanly inside `./data/<area_name>/` (or your desktop application data folder / `REALM_DATA_DIR`). Click **+ Add Documents** (or drag and drop files and nested folders) to import **9 formats**: `.md`, `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.csv`, `.tsv`, `.txt`, and `.html`. Prefer not to copy files? Choose **Link Local Folder…** to index an existing folder in place with live background sync.

You can also create and edit Markdown directly inside the Library (**+ New Note** or **Edit** with live Preview and `⌘S` / `Ctrl+S`), clip public web articles to Markdown (when Local-Only Lock is off), or explore relationships visually in **Graph View**.

## Hybrid Retrieval & Privacy
By default, **Strict Local-Only Lock** keeps every document, search query, and AI prompt on your computer. When local [Ollama](https://ollama.com/download) is running with `nomic-embed-text:v1.5`, embeddings are computed incrementally and cached in `index.json` for fast **Hybrid BM25 + Vector RRF** search.

Open **Settings → Privacy & GDPR Audit** to scan or redact personal data (emails, IBANs, dates, addresses), inspect sanitized system diagnostics, export a GDPR/EU AI Act report, or back up and restore workspaces as portable `.zip` archives.

## Agents, Slash Commands & Shortcuts
- **Quick Jump (`⌘K` / `Ctrl+K`):** Jump to any document, chat, agent, workspace, or action in one keystroke.
- **Quick Guide (`?` or `⌘/` / `Ctrl+/`):** Open the built-in 4-tab keyboard and feature reference anytime.
- **Slash Commands (`/`):** Type `/` in the chat box to trigger `/summarize`, `/quiz`, `/table`, `/actions`, `/compare`, `/eli5`, `/critique`, or pin any Answer Format (`/<format>`).
- **Specialist Agents (`@mention`):** Type `@` to summon a specialist such as `@Lisbeth`, `@Blomkvist`, `@Milton`, `@Annika`, `@Plague`, or your own custom agents for a single turn — or configure a **pinned local or cloud model** per agent inside **Agents**.
- **Engine Inspector (`⌘I` / `Ctrl+I`):** Monitor live context usage, run lossless **Compress Context**, inspect BM25/Vector/RRF scores (**Retrieval X-Ray**), and Pin or Mute individual sources.
- **Study Cards & Audio Briefings:** Open **Study Cards** in the Library to review flashcards (with optional AI card generation, **Socratic Quiz**, and **Anki `.tsv` export**), run **Gap Scan**, or create offline Solo/Duo **Audio Briefings**.

## Publishing a Read-Only Public API
Enable the loopback-only OpenAI-compatible `/v1` API in **Settings → AI & Voice** to connect VS Code, Cursor, Raycast, or Apple Shortcuts, or run `realm-engine ask "..."` and `realm-engine mcp` from your terminal.

To publish selected vaults as a stateless read-only JSON API for static documentation websites, launch:
`REALM_MODE=public REALM_PUBLIC_AREAS=my_docs uv run python main.py --public`
