# Contributing to REALM Knowledge Engine

Thank you for your interest in contributing to **REALM Engine**! We keep the codebase small, strict, predictable, and safe across macOS, Windows, Linux, and Docker.

## Development Setup

Requirements: Python **3.12+**, [uv](https://docs.astral.sh/uv/), and optionally Node.js 20+ (only for JS syntax checks or rebuilding Tailwind CSS).

```bash
git clone https://github.com/realmframework/realm-engine.git
cd realm-engine
uv sync --frozen
uv run python main.py
```

## Architectural Rules (Enforced Automatically)

All rules below are checked on every commit by [core/test_architecture.py](core/test_architecture.py):

1. **Strict Vertical Slices:** Feature logic belongs in `features/<slice_name>/` (`ingestion`, `search`, `tutor_agent`, `ui`). Slices may only import from `core/` — never from sibling slices (`features/ui/app.py` is the composition root).
2. **Contract-First Schemas:** Shared Pydantic v2 models live in [core/contracts.py](core/contracts.py) with `model_config = ConfigDict(strict=True)`.
3. **Pure Functions:** Prefer stateless functions over classes (use classes only for Pydantic schemas or thin runtime helpers).
4. **Line Ceilings:**
   - Backend Python modules (`core/*.py`, `main.py`, `desktop_app.py`, routes, services, and `test_*.py`): **`<= 150` lines**.
   - Frontend UI template/script modules (`features/ui/*_script.py`, `template.py`, `modals.py`, `chat_actions.py`, `features/ui/static/*.{js,css}`): **`<= 350` lines**.
5. **Minimalist UI & Accessibility Guardrails:**
   - Keep the hero canvas ("Where should we start?") and prompt pill uncluttered.
   - Maintain WCAG 2.1 AA contrast (`>= 4.5:1`), semantic native `<dialog>` elements, labeled form controls, keyboard accessibility, and 100% **EN / DE / ES** i18n parity (`features/ui/test_visual_a11y_i18n.py`).
   - Use crisp 1.5px monochrome SVG icons — never emojis in UI chrome.
   - Keep Settings organized cleanly into its 5 tabs.

## Mandatory Verification Gate

Before opening a pull request, every check below must return **0 errors**:

```bash
uv run ruff check .
uv run pyright
uv run pyright --pythonplatform Windows
uv run pytest
```

If you modified client JavaScript or Tailwind utility classes:

```bash
# Verify assembled client JS syntax
uv run python -c "import re, subprocess; from features.ui.script import CLIENT_SCRIPT; js = re.sub(r'^\s*<script>\s*|\s*</script>\s*$', '', CLIENT_SCRIPT); subprocess.run(['node', '--check'], input=js, text=True, check=True)"

# Rebuild self-hosted Tailwind CSS when adding new utility classes
npx --yes --package=tailwindcss@3.4.17 tailwindcss -c features/ui/tailwind.config.cjs -i features/ui/tailwind-input.css -o features/ui/static/ui.css --minify
```

## Pull Request Checklist

- [ ] Scoped to a clear bug fix, hardening pass, or focused feature.
- [ ] Unit/regression tests added or updated.
- [ ] All checks pass (`ruff`, `pyright` macOS + Windows, `pytest`, `node --check`).
- [ ] EN/DE/ES translations updated for any new user-facing copy.
- [ ] Documentation (`README.md`, `docs/`, `CHANGELOG.md`) updated if user-facing behavior changed.
