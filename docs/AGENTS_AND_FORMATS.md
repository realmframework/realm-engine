# Specialist Agents & Answer Formats Studio

REALM Engine pairs grounded Hybrid RAG with customizable **Specialist Agents** and **13 structured Answer Format blueprints** so you can move from raw notes to reviewed deliverables in seconds.

---

## 1. Built-In & Custom Agents

Open **Agents** in the left sidebar to browse, edit, duplicate, or create agents (stored as Markdown definitions under `<data_dir>/agents/`):

- **Saga** *(default)* — Calm, thorough general knowledge partner.
- **Lisbeth** — Investigative researcher & cross-reference analyst.
- **Blomkvist** — Clear editorial writer & narrative synthesizer.
- **Milton** — Security & threat-modeling reviewer.
- **Erika** — Executive communications & stakeholder strategist.
- **Annika** — Legal, contract, and policy reviewer.
- **Plague** — Systems, debugging, and root-cause engineer.
- **Palmgren** — Patient mentor, tutor, and Socratic coach.

Optionally enable **Sync Theme Palette with Active Agent** under **Settings → Appearance** to subtly adapt workspace colors as you switch specialists.

---

## 2. `@mentions` & One-Turn Summons

You do not have to switch your active agent to bring another perspective into a thread:

- Type **`@`** in the prompt box and select an agent (e.g., `@Annika check if this SLA clause conflicts with our vendor notes`).
- The mentioned specialist reads the **full shared conversation history and grounded sources**, replies under **its own name and avatar**, and leaves your active default agent unchanged for subsequent turns.
- **Second Opinion:** On any AI reply, open the reply action menu and click **Second Opinion** to ask another specialist to critically verify claims against cited passages, flag gaps, and add an independent review.

---

## 3. Per-Agent Model Pinning & Local RAM Safety

Every agent can optionally be pinned to a dedicated model inside **Agents → Edit Agent → Preferred Model**:

- Leave on **Follow active chat model** (default) to use whatever model is currently selected in the prompt pill.
- Pin a specific **local Ollama model** (e.g., `qwen3:8b`, `llama3.2:3b`) or **cloud model** (e.g., Claude, Gemini, OpenAI, DeepSeek, Kimi, Mistral, xAI) to give each specialist its ideal model automatically — even during `@mentions` and **Second Opinion**.

### How REALM Protects Your RAM
Running multiple local Ollama models simultaneously can exhaust memory on 8–16 GB laptops. REALM prevents local OOMs automatically:

1. **Process-Wide Execution Gate:** Local Ollama calls (chat, streaming, format synthesis, context compression, study cards, TTS scripts, and embeddings) acquire a single-slot coordinator so two heavy local generations never collide.
2. **Automatic Previous-Model Unload:** Whenever you switch from one local Ollama model to another — or switch from a local Ollama model to a cloud model — REALM explicitly sends `keep_alive: 0` to unload the previous local model before starting the next request.
3. **Bounded Streams & Lifetimes:** Local Ollama calls enforce `keep_alive` TTLs (`60s`–`90s`), bounded `num_predict`, and a 300-second wall-clock cap.
4. **Local-Only Respect:** If an agent is pinned to a cloud model while **Strict Local-Only Lock** is enabled, REALM blocks the cloud call safely rather than leaking data.

---

## 4. Answer Formats Studio (13 Built-In + Custom Blueprints)

Open **Answer Formats** in the sidebar to inspect or create structured output templates. You can apply a format in three ways:

1. **Inline Slash Command:** Type `/<format>` (e.g., `/adr`, `/srs`, `/postmortem`) in the prompt box to pin a format to your next message.
2. **Post-Reply Synthesis:** Click **Answer in Format…** on any reply (or in the conversation header) to transform an answer or an entire multi-turn discussion into a clean deliverable.
3. **Export or Save to Library:** Export any formatted reply or full conversation to **vector PDF** or **Markdown (`.md`)**, or click **+ Save Guide** to file it straight into your Knowledge Area.

### Built-In Blueprints
- IEEE/IREB Software Requirements Specification (`SRS`)
- Agile User Stories & Gherkin Acceptance Criteria
- MoSCoW Prioritization Matrix
- Architecture Decision Record (`ADR`)
- Lisbeth's Investigation Dossier
- Blomkvist's Investigative Article
- Milton Security Threat Assessment
- Erika's Stakeholder Brief
- Annika's Legal Review Memo
- Plague's Root-Cause Postmortem
- Palmgren's Mentoring Plan
- Executive 4W Brief
- Meeting Actions & Decisions
