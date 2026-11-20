# AI Engineering Knowledge Engine - AI Agent Constitution

## Verification Gate (MANDATORY)
After ANY code change, you MUST run this exact command:
`uv run ruff check . && uv run pyright && uv run pytest`
You are forbidden from finishing your turn until all three tools return 0 errors.

## Architectural Constraints
1. **Strict Vertical Slices:** All features live inside `features/<slice_name>/` containing only `service.py`, `router.py`, and `test_<slice_name>.py`.
2. **Contract-First:** All shared Pydantic models MUST live in `core/contracts.py`. Use Pydantic v2 syntax (`model_config = ConfigDict(strict=True)`).
3. **No Cross-Slice Imports:** Files inside `features/<slice_name>/` may ONLY import from `core/`. Never import from another feature slice.
4. **Pure Functions:** Prefer stateless functions over classes. Only use classes for Pydantic `BaseModel` schemas.
5. **Line Ceilings:** Backend Python logic and FastAPI routes stay at or below 150 lines. Frontend HTML/JS template modules in `features/ui/` and `.js`/`.css` assets in `features/ui/static/` may use up to 350 lines. Keep frontend code readable; do not compress or remove interactions to satisfy the backend limit. `core/test_architecture.py` owns the executable classification.


## Immutable Gemini UI & Minimalism Guardrails
1. **Sacred Hero & Prompt Canvas:** NEVER place dropdowns, toolbars, banners or extra controls between “Where should we start?” and the single prompt pill, or floating above the docked chat pill.
2. **Fixed Prompt Pill Anatomy:** The pill may ONLY contain the circular `+` on the left; the text input in the center, plus a compact removable `[Folder/File SVG] <Name> ✕` chip ONLY for an actively selected non-default scope; and `Model ⌄`, microphone and submit-arrow controls on the right. The scope chip MUST be completely hidden (`display: none`) in default `Entire Area` mode.
3. **Progressive Disclosure Over Clutter:** Configuration, folder scoping, voice settings and diagnostics MUST live in the left sidebar, Library or native `<dialog>` modals—NEVER on the primary chat canvas.
4. **Zero Raw Tokens or Emojis:** NEVER expose raw `[REDACTED_*]` tokens or generic `Page N` labels in hero starter prompts. Use crisp 1.5px stroke monochrome SVG icons, NEVER cartoon emojis.
