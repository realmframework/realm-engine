---
title: Welcome to REALM Knowledge Engine
description: Local-first Hybrid RAG and Multi-Turn AI Knowledge Engine starter guide.
tags: [getting-started, rag, local-first]
---

# Welcome to REALM Knowledge Engine

## How Knowledge Areas Work
Each Knowledge Area lives cleanly inside `./data/<area_name>/` (or the directory passed via `REALM_DATA_DIR` / `--data-dir`). Add Markdown, PDF, DOCX, TXT, or HTML files via **Add Documents** or drop Markdown files straight into your vault.

## Hybrid Retrieval & Privacy
By default, **Strict Local-Only Lock** keeps all queries and documents on your machine. When local Ollama is running with `nomic-embed-text:v1.5`, embeddings are cached incrementally in `index.json` for fast Hybrid BM25 + Cosine RRF search.

## Publishing a Read-Only Public API
Run `REALM_MODE=public REALM_PUBLIC_AREAS=ai-engineering,realm uv run python main.py --public` to expose only the stateless read-only `/api/public/*` endpoints for websites and static Next.js knowledge hubs.
